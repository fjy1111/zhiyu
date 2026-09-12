"""Official Phase 4 evaluation. Run once after tests and smoke."""
import json
import subprocess
import yaml
from _common import ROOT, write_json
from zhiyu.eval.phase4 import evaluate_split
from zhiyu.factual.corpus import load_references, sha256_file
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.prompt import CLAIM_PROMPT_VERSION, COMPARE_PROMPT_VERSION
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.semantic.env import load_project_env, public_llm_config

PHASE4 = ROOT / "datasets/processed/phase4"
SNAPSHOT_FILES = {
    "references": PHASE4 / "references.jsonl",
    "candidate_development_tune_documents": PHASE4 / "candidate_development_tune_documents.jsonl",
    "candidate_development_tune_chunks": PHASE4 / "candidate_development_tune_chunks.jsonl",
    "candidate_development_generalization_documents": PHASE4 / "candidate_development_generalization_documents.jsonl",
    "candidate_development_generalization_chunks": PHASE4 / "candidate_development_generalization_chunks.jsonl",
}


def _tracked_tree_clean() -> tuple[bool, str]:
    output = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    return output.strip() == "", output


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    if not cfg["api_key_present"] or not cfg["model"]:
        print("EVAL BLOCKED: missing DEEPSEEK_API_KEY or DEEPSEEK_MODEL")
        return 2
    clean, dirty = _tracked_tree_clean()
    if not clean:
        print("EVAL BLOCKED: tracked working tree is not clean")
        print(dirty)
        return 2
    frozen = yaml.safe_load((ROOT / "configs/phase4_eval.yaml").read_text(encoding="utf-8"))
    code_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    refs = load_references(SNAPSHOT_FILES["references"])
    pipeline = FactualEvidencePipeline(
        DeepSeekFactualProvider(
            temperature=float(frozen["temperature"]),
            max_tokens=int(frozen["max_tokens"]),
            timeout_sec=float(frozen["timeout_sec"]),
            retries=int(frozen["retries"]),
        ),
        refs,
    )
    manifest_obj = json.loads((ROOT / "datasets/manifests/phase4_reference_manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "datasets/manifests/phase4_overlap_audit.json").read_text(encoding="utf-8"))
    report = {
        "experiment_kind": "REAL LLM",
        "config": {
            **frozen,
            "claim_prompt_version": CLAIM_PROMPT_VERSION,
            "compare_prompt_version": COMPARE_PROMPT_VERSION,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "evaluation_code_commit": code_commit,
            "working_tree_tracked_clean": True,
            "api_key_present": True,
            "reference_corpus_sha256": manifest_obj["corpus_sha256"],
            "phase4_dataset_snapshot_sha256": {
                name: sha256_file(path) for name, path in SNAPSHOT_FILES.items()
            },
            "frozen_phase2_phase3_snapshot_sha256": manifest_obj["frozen_phase2_phase3_snapshot_sha256"],
        },
        "reference_manifest": manifest_obj["selection"],
        "overlap_audit": audit,
        "splits": {},
        "notes": {
            "phase4_does_not_output_poison": True,
            "insufficient_is_not_poison": True,
            "mock_not_used": True,
            "previous_run_superseded": True,
        },
    }
    for split in ("development_tune", "development_generalization"):
        report["splits"][split] = evaluate_split(ROOT, split, pipeline)
    out = ROOT / "experiments" / "phase4"
    write_json(out / "factual_evidence.json", report)
    lines = ["# Phase 4 Factual Evidence Evaluation", "", f"experiment_kind: {report['experiment_kind']}", ""]
    for split, payload in report["splits"].items():
        lines.append(f"## {split}")
        for key in (
            "documents", "claim_extraction_status_counts", "claim_count",
            "retrieval_status_counts", "overlap_rejection_count",
            "pairwise_relation_counts", "comparison_status_counts",
            "factual_evidence_relation_counts", "llm_call_count",
        ):
            lines.append(f"- {key}: {payload.get(key)}")
        lines.append("")
    lines.append(f"- overlap_audit_pass: {audit.get('pass')}")
    lines.append(f"- unique_reference_text_count: {manifest_obj['selection'].get('unique_reference_text_count')}")
    lines.append(f"- evaluation_code_commit: {code_commit}")
    (out / "factual_evidence.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
