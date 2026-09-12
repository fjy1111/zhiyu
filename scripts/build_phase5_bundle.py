"""Materialize Phase5EvidenceBundle once from frozen Phase 2/3/4 implementations."""
from __future__ import annotations
import json
import subprocess
from _common import ROOT, write_json
from zhiyu.detector.scanner import RuleScanner
from zhiyu.eval.phase4 import load_phase4_split
from zhiyu.factual.corpus import load_references, sha256_file
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.judge.materialize import materialize_document
from zhiyu.models.detection import DetectionInput
from zhiyu.models.judge import EXECUTION_PLAN_VERSION, RULE_EVENT_REF_VERSION
from zhiyu.semantic.analyzer import SemanticAnalyzer
from zhiyu.semantic.env import load_project_env, public_llm_config
from zhiyu.semantic.provider import DeepSeekSemanticProvider
from collections import defaultdict


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    if not cfg["api_key_present"] or not cfg["model"]:
        print("BUNDLE BLOCKED: missing LLM config")
        return 2
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    if dirty.strip():
        print("BUNDLE BLOCKED: tracked working tree is not clean")
        print(dirty)
        return 2
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    refs = load_references(ROOT / "datasets/processed/phase4/references.jsonl")
    scanner = RuleScanner()
    semantic = SemanticAnalyzer(DeepSeekSemanticProvider(temperature=0.0, max_tokens=800, timeout_sec=60, retries=1))
    factual = FactualEvidencePipeline(DeepSeekFactualProvider(temperature=0.0, max_tokens=800, timeout_sec=60, retries=1), refs)
    out_path = ROOT / "datasets/processed/phase5/evidence_bundle.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    docs = []
    for split in ("development_tune", "development_generalization"):
        grouped: dict[str, list] = defaultdict(list)
        meta: dict[str, tuple[str, str]] = {}
        for document_id, item, path, digest in load_phase4_split(ROOT, split):
            grouped[document_id].append(item)
            meta[document_id] = (path, digest)
        for document_id, chunks in grouped.items():
            path, digest = meta[document_id]
            record = materialize_document(document_id, chunks, path, digest, scanner, semantic, factual)
            payload = record.to_runtime_dict()
            for forbidden in ("original_label", "attack_type", "facts", "split"):
                if forbidden in payload:
                    raise RuntimeError("bundle leaked evaluator field")
            docs.append(payload)
            print("bundled", document_id[:12], "chunks", len(chunks), flush=True)
    out_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in docs), encoding="utf-8")
    write_json(ROOT / "datasets/manifests/phase5_evidence_bundle_manifest.json", {
        "evidence_bundle_build_commit": commit,
        "documents": len(docs),
        "bundle_path": "datasets/processed/phase5/evidence_bundle.jsonl",
        "bundle_sha256": sha256_file(out_path),
        "candidate_snapshot_sha256": {
            "tune_docs": sha256_file(ROOT / "datasets/processed/phase4/candidate_development_tune_documents.jsonl"),
            "gen_docs": sha256_file(ROOT / "datasets/processed/phase4/candidate_development_generalization_documents.jsonl"),
        },
        "execution_plan_version": EXECUTION_PLAN_VERSION,
        "rule_event_ref_version": RULE_EVENT_REF_VERSION,
        "working_tree_tracked_clean": True,
    })
    print("bundle documents", len(docs), "sha256", sha256_file(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
