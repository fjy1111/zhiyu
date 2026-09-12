from __future__ import annotations
import json
import subprocess
from collections import defaultdict
from pathlib import Path
import yaml
from _common import ROOT, write_json
from zhiyu.factual.corpus import sha256_file
from zhiyu.factual.provider import DeepSeekFactualProvider, FactualProviderError
from zhiyu.models.rag import GeneratorConfig, RetrieverConfig
from zhiyu.rag.admission import build_indexes, load_candidate_chunks, load_frozen_decisions
from zhiyu.rag.benchmark import FACT_KEY_ORDER, canonical_query_id, group_key, nonempty_facts
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.evaluate import evaluate_system
from zhiyu.rag.generate import SharedGenerator
from zhiyu.rag.queries import load_evaluator_snapshot, load_runtime_snapshot, snapshot_pair_hashes
from zhiyu.rag.retriever import SharedRetriever
from zhiyu.rag.runner import CIC_VERSION, Phase6Runner
from zhiyu.semantic.env import load_project_env, public_llm_config

EXPECTED_RUNTIME = "50753f8a5fbed7677e5ac445003d091de413aafbfee2bb1d1d4c6b8e9feeb9f5"
EXPECTED_EVAL = "050aaf2c59c0adfadf40a0aaadaf9d4c134ba0148cb3c1c8a9de7c58de673b47"


class CountingProvider:
    def __init__(self, inner):
        self.inner = inner
        self.calls = 0
        self.error = 0
        self.invalid = 0

    def complete(self, system, user):
        self.calls += 1
        try:
            raw = self.inner.complete(system, user)
        except FactualProviderError as exc:
            self.error += 1
            raise
        if not isinstance(raw, str) or not raw.strip():
            self.invalid += 1
        return raw


def gen_query_ids():
    labels = json.loads((ROOT / "datasets/manifests/phase4_evaluator_labels.json").read_text(encoding="utf-8"))
    docs = [json.loads(line) for line in (ROOT / "datasets/processed/trusted_provenance/benchmark_documents.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    cand = {json.loads(line)["document_id"] for line in (ROOT / "datasets/processed/phase4/candidate_development_generalization_documents.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    rows = [row for row in docs if (labels.get(row["document_id"]) or {}).get("split") == "development_generalization"]
    groups = defaultdict(lambda: {"normal": [], "poison": []})
    for row in rows:
        label = row.get("original_label")
        if label in {"normal", "poison"}:
            groups[group_key(row.get("metadata") or {})][label].append(row)
    for bucket in groups.values():
        bucket["normal"].sort(key=lambda item: item["document_id"])
    clean, poison = [], []
    for row in rows:
        if row.get("original_label") == "normal" and row["document_id"] in cand:
            facts = nonempty_facts(row.get("metadata") or {})
            key = next((item for item in FACT_KEY_ORDER if item in facts), None)
            if key:
                clean.append(canonical_query_id("CLEAN", row["document_id"], key))
        if row.get("original_label") == "poison" and row["document_id"] in cand:
            normals = groups[group_key(row.get("metadata") or {})]["normal"]
            if not normals:
                continue
            poison_facts = nonempty_facts(row.get("metadata") or {})
            normal_facts = nonempty_facts(normals[0].get("metadata") or {})
            diffs = [key for key in FACT_KEY_ORDER if key in poison_facts and key in normal_facts and poison_facts[key] != normal_facts[key]]
            if len(diffs) == 1:
                poison.append(canonical_query_id("POISON", row["document_id"], diffs[0]))
    return clean, poison


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    p6 = yaml.safe_load((ROOT / "configs/phase6.yaml").read_text(encoding="utf-8"))
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    if dirty.strip():
        print("EVAL BLOCKED: tracked working tree is not clean")
        return 2
    if cfg["model"] != p6["generator"]["model"] or cfg["base_url"] != p6["generator"]["base_url"] or not cfg["api_key_present"]:
        print("EVAL BLOCKED: LLM config mismatch")
        return 2
    runtime_path = ROOT / "datasets/processed/phase6/runtime_queries.jsonl"
    evaluator_path = ROOT / "datasets/processed/phase6/evaluator_records.jsonl"
    hashes = snapshot_pair_hashes(runtime_path, evaluator_path)
    if hashes["runtime_sha256"] != EXPECTED_RUNTIME or hashes["evaluator_sha256"] != EXPECTED_EVAL:
        print("EVAL BLOCKED: snapshot SHA mismatch")
        return 2
    clean_ids, poison_ids = gen_query_ids()
    if len(clean_ids) != 12 or len(poison_ids) != 12:
        print("EVAL BLOCKED: expected 12/12 gen queries")
        return 2
    wanted = set(clean_ids + poison_ids)
    runtime = [item for item in load_runtime_snapshot(runtime_path) if item.query_id in wanted]
    records = [item for item in load_evaluator_snapshot(evaluator_path) if item.query_id in wanted]
    runtime.sort(key=lambda item: item.query_id)
    retriever_cfg = RetrieverConfig(method=p6["retriever"]["method"], k=int(p6["retriever"]["k"]))
    eval_split = "development_generalization"
    indexes = build_indexes(
        load_candidate_chunks(ROOT, split=eval_split),
        load_frozen_decisions(ROOT / "experiments/phase5/unified_judge_replacement_replay.jsonl"),
        retriever_cfg,
    )
    tune_ids = {chunk.document_id for chunk in load_candidate_chunks(ROOT, split="development_tune")}
    if len(indexes.vanilla.document_ids) != 39 or len(indexes.vanilla.chunks) != 39:
        print("EVAL BLOCKED: gen Vanilla must be 39 docs / 39 chunks")
        return 2
    if len(indexes.protected.document_ids) != 0 or len(indexes.protected.chunks) != 0:
        print("EVAL BLOCKED: gen Protected must be 0 docs / 0 chunks")
        return 2
    if indexes.vanilla.document_ids & tune_ids:
        print("EVAL BLOCKED: tune docs leaked into gen index")
        return 2
    gen_cfg = GeneratorConfig(
        model=p6["generator"]["model"],
        system_prompt=p6["generator"]["system_prompt"],
        temperature=float(p6["generator"]["temperature"]),
        max_tokens=int(p6["generator"]["max_tokens"]),
    )
    counting = CountingProvider(DeepSeekFactualProvider(temperature=gen_cfg.temperature, max_tokens=gen_cfg.max_tokens, timeout_sec=60, retries=1))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    bundle = ROOT / "datasets/processed/phase5/evidence_bundle_replacement.jsonl"
    if not bundle.is_file():
        bundle = ROOT / "datasets/processed/phase5/evidence_bundle.jsonl"
    runner = Phase6Runner(
        indexes,
        SharedRetriever(retriever_cfg),
        SharedGenerator(gen_cfg, counting),
        ContextIntegrityChecker(),
        {
            "evaluation_code_commit": commit,
            "working_tree_tracked_clean": True,
            "runtime_sha256": hashes["runtime_sha256"],
            "evaluator_sha256": hashes["evaluator_sha256"],
            "phase5_bundle_sha256": sha256_file(bundle),
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "split": "development_generalization",
        },
    )
    print("queries", len(runtime), "protected_docs", len(indexes.protected.document_ids), flush=True)
    result = runner.run(tuple(runtime))
    metrics = evaluate_system(records, result.outcomes)
    cic_calls = sum(1 for row in result.replay if row["path"] == "protected" and row.get("cic"))
    out_dir = ROOT / "experiments/phase6"
    out_dir.mkdir(parents=True, exist_ok=True)
    runner.write_replay(out_dir / "official_generalization_replay.jsonl", result)
    report = {
        "experiment_kind": "REAL LLM",
        "split": "development_generalization",
        "config": result.provenance,
        "provider_call_count": counting.calls,
        "provider_error_count": counting.error,
        "provider_invalid_count": counting.invalid,
        "cic_call_count": cic_calls,
        "metrics": metrics,
        "query_counts": {"CLEAN": 12, "POISON": 12},
        "protected_document_count": len(indexes.protected.document_ids),
        "vanilla_document_count": len(indexes.vanilla.document_ids),
        "notes": {
            "review_is_not_positive": True,
            "no_context_not_asr": True,
            "generation_failure_not_asr": True,
            "abstain_not_asr": True,
        },
    }
    write_json(out_dir / "official_generalization.json", report)
    print("EVAL_WRITTEN", flush=True)
    print("PROVIDER_CALLS", counting.calls, "CIC_CALLS", cic_calls, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
