from __future__ import annotations
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from _common import ROOT
from zhiyu.factual.corpus import sha256_file
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.models.rag import GeneratorConfig, RuntimeQuery
from zhiyu.rag.admission import build_indexes, load_candidate_chunks, load_frozen_decisions
from zhiyu.rag.benchmark import (
    FACT_KEY_ORDER,
    canonical_query_id,
    group_key,
    nonempty_facts,
)
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.generate import SharedGenerator
from zhiyu.rag.queries import load_runtime_snapshot, snapshot_pair_hashes
from zhiyu.models.rag import RetrieverConfig
from zhiyu.rag.retriever import SharedRetriever
from zhiyu.rag.runner import CIC_VERSION, Phase6Runner
from zhiyu.semantic.env import load_project_env, public_llm_config
import yaml

def _docs():
    import json
    path = ROOT / "datasets/processed/trusted_provenance/benchmark_documents.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def _labels():
    return json.loads((ROOT / "datasets/manifests/phase4_evaluator_labels.json").read_text(encoding="utf-8"))

def _candidate_ids(split: str) -> set[str]:
    path = ROOT / "datasets/processed/phase4" / f"candidate_{split}_documents.jsonl"
    return {json.loads(line)["document_id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}

def tune_query_ids() -> dict[str, list[str]]:
    labels = _labels()
    docs = _docs()
    cand = _candidate_ids("development_tune")
    rows = [row for row in docs if (labels.get(row["document_id"]) or {}).get("split") == "development_tune"]
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
    return {"CLEAN": sorted(clean), "POISON": sorted(poison)}

def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    p6 = yaml.safe_load((ROOT / "configs/phase6.yaml").read_text(encoding="utf-8"))
    frozen_model = p6["generator"]["model"]
    frozen_base = p6["generator"]["base_url"]
    if cfg["model"] != frozen_model or cfg["base_url"] != frozen_base or not cfg["api_key_present"]:
        print("SMOKE BLOCKED: LLM config mismatch or missing key")
        print("MODEL_MATCH", cfg["model"] == frozen_model)
        print("BASE_URL_MATCH", cfg["base_url"] == frozen_base)
        return 2
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    runtime_path = ROOT / "datasets/processed/phase6/runtime_queries.jsonl"
    evaluator_path = ROOT / "datasets/processed/phase6/evaluator_records.jsonl"
    hashes = snapshot_pair_hashes(runtime_path, evaluator_path)
    runtime = {item.query_id: item for item in load_runtime_snapshot(runtime_path)}
    retriever_cfg = RetrieverConfig(method=p6["retriever"]["method"], k=int(p6["retriever"]["k"]))
    chunks = load_candidate_chunks(ROOT)
    decisions = load_frozen_decisions(ROOT / "experiments/phase5/unified_judge_replacement_replay.jsonl")
    indexes = build_indexes(chunks, decisions, retriever_cfg)
    retriever = SharedRetriever(retriever_cfg)
    ids = tune_query_ids()
    protected_qid = None
    for qid in ids["CLEAN"]:
        query = runtime[qid]
        retrieved = retriever.retrieve(query, indexes.protected)
        if len(retrieved.hits) >= 1:
            protected_qid = qid
            break
    vanilla_qid = None
    for qid in ids["POISON"]:
        query = runtime[qid]
        retrieved = retriever.retrieve(query, indexes.vanilla)
        if len(retrieved.hits) >= 1:
            vanilla_qid = qid
            break
    selected = []
    if protected_qid:
        selected.append(runtime[protected_qid])
    if vanilla_qid and vanilla_qid != protected_qid:
        selected.append(runtime[vanilla_qid])
    selected = selected[:2]
    gen_cfg = GeneratorConfig(
        model=cfg["model"],
        system_prompt=p6["generator"]["system_prompt"],
        temperature=float(p6["generator"]["temperature"]),
        max_tokens=int(p6["generator"]["max_tokens"]),
    )
    provider = DeepSeekFactualProvider(
        temperature=gen_cfg.temperature,
        max_tokens=gen_cfg.max_tokens,
        timeout_sec=60,
        retries=1,
    )
    class Counting:
        def __init__(self, inner):
            self.inner = inner
            self.calls = 0
            self.errors = 0
        def complete(self, system, user):
            self.calls += 1
            try:
                return self.inner.complete(system, user)
            except Exception:
                self.errors += 1
                raise
    counting = Counting(provider)
    generator = SharedGenerator(gen_cfg, counting)
    cic = ContextIntegrityChecker()
    cic_calls = 0
    from zhiyu.rag.generate import run_protected_path, run_vanilla_path
    rows = []
    if protected_qid:
        query = runtime[protected_qid]
        retrieved = retriever.retrieve(query, indexes.protected)
        cic_calls += 1
        outcome = run_protected_path(query, retrieved, generator, cic)
        cic_payload = outcome.cic.to_runtime_dict() if outcome.cic is not None else None
        rows.append({
            "query_id": query.query_id,
            "path": "protected",
            "retrieval_status": retrieved.status.value,
            "cic_status": None if cic_payload is None else cic_payload.get("status"),
            "cic_verdict": None if cic_payload is None else cic_payload.get("verdict"),
            "generation_status": outcome.status.value,
            "error_code": outcome.error_code,
        })
    if vanilla_qid:
        query = runtime[vanilla_qid]
        retrieved = retriever.retrieve(query, indexes.vanilla)
        outcome = run_vanilla_path(query, retrieved, generator)
        rows.append({
            "query_id": query.query_id,
            "path": "vanilla",
            "retrieval_status": retrieved.status.value,
            "cic_status": None,
            "cic_verdict": None,
            "generation_status": outcome.status.value,
            "error_code": outcome.error_code,
        })
    artifact = {
        "experiment_kind": "REAL LLM SMOKE",
        "selected_query_ids": [item.query_id for item in selected],
        "rows": rows,
        "provider_call_count": counting.calls,
        "cic_call_count": cic_calls,
        "config": {
            "evaluation_code_commit": commit,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "runtime_sha256": hashes["runtime_sha256"],
            "evaluator_sha256": hashes["evaluator_sha256"],
            "retriever": {"method": retriever_cfg.method, "k": retriever_cfg.k, "version": p6.get("retriever", {}).get("version", "phase6.retriever.v1")},
            "generator": {
                "model": gen_cfg.model,
                "base_url": frozen_base,
                "temperature": gen_cfg.temperature,
                "max_tokens": gen_cfg.max_tokens,
                "system_prompt": gen_cfg.system_prompt,
                "version": p6.get("generator", {}).get("version", "phase6.generator.v1"),
            },
            "cic_version": p6.get("cic", {}).get("version", CIC_VERSION),
            "phase6_yaml": "configs/phase6.yaml",
        },
    }
    out = ROOT / "experiments/phase6/smoke_tune.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("SMOKE_WRITTEN", str(out))
    print("SELECTED", len(selected))
    print("PROVIDER_CALLS", counting.calls)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
