import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_saved_corpus_offsets_and_splits():
    folder = ROOT / "datasets/processed/trusted_provenance"
    docs = [json.loads(line) for line in (folder / "development_documents.jsonl").read_text(encoding="utf-8").splitlines()]
    chunks = [json.loads(line) for line in (folder / "development_chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(docs) == 180
    index = {d["document_id"]: d for d in docs}
    assert {d["source_split"] for d in docs} == {"demo_set", "dev_set"}
    for chunk in chunks:
        doc = index[chunk["document_id"]]
        assert chunk["text"] == doc["text"][chunk["start_char"]:chunk["end_char"]]

def test_audit_contains_only_hashes_paths_and_statistics():
    audit = json.loads((ROOT / "datasets/manifests/split_leakage_audit.json").read_text(encoding="utf-8"))
    assert audit["parse_failures"] == 0
    for row in audit["files"]:
        assert set(row) <= {"path", "sha256", "normalized_sha256", "empty_text", "parse_failed"}
        assert len(row["sha256"]) == 64
    for pair in audit["near_duplicate"]["pairs"]:
        assert all(p.split("/")[0] in {"demo_set", "dev_set"} for p in pair["paths"])

def test_real_validation():
    report = json.loads((ROOT / "datasets/manifests/parser_validation.json").read_text(encoding="utf-8"))
    assert report["total"] == report["success"] == 33
    assert report["failed"] == 0
    assert set(report["by_format"]) == {".txt", ".md", ".html", ".pdf", ".docx"}
