from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from _common import ROOT
from zhiyu.demo.prescan_checkpoint import (
    CheckpointHeader,
    append_jsonl_record,
    initialize_checkpoint,
)
from zhiyu.detector.scanner import RuleScanner
from zhiyu.factual.corpus import load_references, sha256_file, sha256_text
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.judge.engine import decide
from zhiyu.judge.judge import UnifiedJudge
from zhiyu.judge.materialize import materialize_document
from zhiyu.judge.provider import DeepSeekJudgeProvider
from zhiyu.models.detection import DetectionInput
from zhiyu.models.judge import Ablation
from zhiyu.semantic.analyzer import SemanticAnalyzer
from zhiyu.semantic.env import load_project_env, public_llm_config
from zhiyu.semantic.provider import DeepSeekSemanticProvider


def main():
    load_project_env(ROOT)
    cfg = public_llm_config()
    assert cfg["api_key_present"] and cfg["model"] == "deepseek-flash"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    kb = ROOT / "demo/demo_knowledge_base_v2.jsonl"
    manifest = ROOT / "demo/demo_scenario_manifest_v2.json"
    kb_sha = sha256_file(kb)
    manifest_sha = sha256_file(manifest)
    rows = [json.loads(x) for x in kb.read_text(encoding="utf-8").splitlines()]
    refs = load_references(ROOT / "datasets/processed/phase4/references.jsonl")
    scanner = RuleScanner()
    semantic = SemanticAnalyzer(
        DeepSeekSemanticProvider(
            model=cfg["model"],
            base_url=cfg["base_url"],
            temperature=0,
            max_tokens=800,
            timeout_sec=60,
            retries=1,
        )
    )
    factual = FactualEvidencePipeline(
        DeepSeekFactualProvider(
            model=cfg["model"],
            base_url=cfg["base_url"],
            temperature=0,
            max_tokens=800,
            timeout_sec=60,
            retries=1,
        ),
        refs,
    )
    judge = UnifiedJudge(
        DeepSeekJudgeProvider(
            model=cfg["model"],
            base_url=cfg["base_url"],
            temperature=0,
            max_tokens=800,
            timeout_sec=60,
            retries=1,
        )
    )
    cp = ROOT / "experiments/phase7/prescan_checkpoint.jsonl"
    header = CheckpointHeader(
        demo_kb_sha256=kb_sha,
        manifest_sha256=manifest_sha,
        model=cfg["model"],
        base_url=cfg["base_url"],
    )
    done = initialize_checkpoint(cp, header)
    calls = {"semantic": 0, "factual": 0, "judge": 0}
    out = list(done.values())
    for i, r in enumerate(rows, 1):
        if r["demo_document_id"] in done:
            continue
        item = DetectionInput(r["demo_document_id"], r["demo_document_id"] + ":0", r["runtime_text"])
        doc = materialize_document(item.document_id, [item], "", sha256_text(item.text), scanner, semantic, factual)
        calls["semantic"] += 1
        calls["factual"] += factual.llm_calls
        factual.llm_calls = 0
        status, assessment = judge.assess(doc)
        calls["judge"] += 1
        decision = decide(doc, Ablation.FULL_JUDGE, assessment, status)
        statuses = Counter(x.status.value for x in doc.statuses)
        row = {
            "document_id": r["demo_document_id"],
            "intended_mechanism": r["mechanism"],
            "intended_role": r["demo_role"],
            "decision": decision.decision.value,
            "component_statuses": dict(statuses),
            "rule_event_count": len(doc.rule_events),
            "behavior_evidence_count": len(doc.behavior_evidence),
            "factual_evidence_summary": dict(Counter(x.relation.value for x in doc.factual_evidence)),
            "judge_status": status.status.value,
            "provider_errors_invalid": sum(
                v for k, v in statuses.items() if k in ("ERROR", "INVALID_OUTPUT")
            ),
        }
        out.append(row)
        append_jsonl_record(cp, row)
        print(i, "/", len(rows), r["demo_document_id"], decision.decision.value, flush=True)
    artifact = {
        "kind": "phase7_demo_prescan_real_llm",
        "model": cfg["model"],
        "base_url": cfg["base_url"],
        "code_commit": commit,
        "demo_kb_sha256": kb_sha,
        "manifest_sha256": manifest_sha,
        "documents": out,
        "provider_calls": calls,
    }
    if len(out) != len(rows):
        print("COMPLETE", len(out), "/", len(rows))
        return
    if len({x["document_id"] for x in out}) != len(rows):
        raise RuntimeError("checkpoint duplicate/missing")
    path = ROOT / "experiments/phase7/prescan_final.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
