import hashlib
import json
from pathlib import Path
from zhiyu.factual.corpus import load_references, overlaps, sha256_file

ROOT = Path(__file__).resolve().parents[1]
FROZEN = {
    "datasets/processed/trusted_provenance/benchmark_tune_documents.jsonl": "4f80e90b0184b775b2de3622aed0bdd52a88d9401223a3dc4988bfefc6d6bec8",
    "datasets/processed/trusted_provenance/benchmark_tune_chunks.jsonl": "cf136225c0828bbdb2a945979069792727030fdfd0510f7811a42e50dc64d90d",
    "datasets/processed/trusted_provenance/benchmark_generalization_documents.jsonl": "c29d60c7c7df4d26c44103342db3055e6f93d4e16969e2c7ddc260aa7c0ec2af",
    "datasets/processed/trusted_provenance/benchmark_generalization_chunks.jsonl": "864fc5298f48e7e52f231ebed13332bbd21c61d7467c75195dbf740662e2ba30",
}


def test_phase2_phase3_frozen_artifacts_unchanged():
    for rel, expected in FROZEN.items():
        assert sha256_file(ROOT / rel) == expected


def test_zero_overlap_audit():
    audit = json.loads((ROOT / "datasets/manifests/phase4_overlap_audit.json").read_text(encoding="utf-8"))
    assert audit["pass"] is True
    assert audit["remaining_overlap_count"] == 0


def test_reference_only_absent_from_candidate_view():
    refs = load_references(ROOT / "datasets/processed/phase4/references.jsonl")
    ref_ids = {item.document_id for item in refs}
    for name in (
        "candidate_development_tune_documents.jsonl",
        "candidate_development_generalization_documents.jsonl",
    ):
        rows = [json.loads(line) for line in (ROOT / "datasets/processed/phase4" / name).read_text(encoding="utf-8").splitlines() if line.strip()]
        ids = {row["document_id"] for row in rows}
        assert not (ref_ids & ids)
        for row in rows:
            assert "original_label" not in row
            assert "facts" not in row
            assert "metadata" not in row


def test_overlap_helpers_reject_id_path_hash():
    refs = load_references(ROOT / "datasets/processed/phase4/references.jsonl")
    ref = refs[0]
    assert overlaps(ref.document_id, "other", "otherhash", ref)
    assert overlaps("other", ref.relative_path, "otherhash", ref)
    assert overlaps("other", "other", ref.content_hash, ref)
    assert not overlaps("other", "other", "otherhash", ref)
