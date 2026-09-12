"""Build Phase 4 reference corpus and derived candidate view. Does not rewrite Phase 2/3 artifacts."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from _common import ROOT, MANIFESTS, write_json
from zhiyu.datasets.trusted_provenance_adapter import adapt
from zhiyu.factual.corpus import OFFICIAL_SOURCE_LEVELS, audit_runtime_overlap, sha256_file, sha256_text

PROCESSED = ROOT / "datasets/processed/trusted_provenance"
PHASE4 = ROOT / "datasets/processed/phase4"
FROZEN_DOCS = {
    "development_tune": PROCESSED / "benchmark_tune_documents.jsonl",
    "development_generalization": PROCESSED / "benchmark_generalization_documents.jsonl",
}
FROZEN_CHUNKS = {
    "development_tune": PROCESSED / "benchmark_tune_chunks.jsonl",
    "development_generalization": PROCESSED / "benchmark_generalization_chunks.jsonl",
}


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _runtime_candidate(row: dict, identity: dict[str, dict]) -> dict:
    text = row.get("benchmark_text") or row.get("text") or ""
    source = identity.get(row["document_id"], {})
    rel = source.get("relative_path") or (row.get("metadata") or {}).get("relative_path") or row.get("relative_path") or ""
    payload = {
        "document_id": row["document_id"],
        "relative_path": rel,
        "content_hash": sha256_text(text),
        "text": text,
    }
    source_file_hash = source.get("sha256") or row.get("sha256")
    if source_file_hash and source_file_hash != payload["content_hash"]:
        payload["source_file_hash"] = source_file_hash
    return payload


def _runtime_chunk(row: dict, documents: dict[str, dict]) -> dict | None:
    parent = documents.get(row["document_id"])
    if parent is None:
        return None
    return {
        "document_id": row["document_id"],
        "chunk_id": row["chunk_id"],
        "text": row["text"],
        "start_char": row.get("start_char", 0),
        "end_char": row.get("end_char", len(row["text"])),
        "relative_path": parent["relative_path"],
        "content_hash": parent["content_hash"],
    }


def main() -> int:
    development = _jsonl(PROCESSED / "development_documents.jsonl")
    identity = {
        row["document_id"]: {
            "relative_path": row.get("relative_path") or "",
            "sha256": row.get("sha256") or "",
        }
        for row in development
    }
    selected = []
    for row in development:
        meta = row.get("metadata") or {}
        if meta.get("original_label") != "normal":
            continue
        if meta.get("source_level") not in OFFICIAL_SOURCE_LEVELS:
            continue
        adapted = adapt(type("Doc", (), {"document_id": row["document_id"], "text": row["text"], "metadata": meta})())
        text = adapted.benchmark_text
        selected.append({
            "reference_id": f"ref:{row['document_id']}",
            "document_id": row["document_id"],
            "relative_path": row.get("relative_path") or "",
            "content_hash": sha256_text(text),
            "text": text,
        })
    selected.sort(key=lambda item: item["document_id"])
    source_count = len(selected)
    unique = []
    duplicates = []
    seen_hash: dict[str, str] = {}
    for item in selected:
        digest = item["content_hash"]
        if digest in seen_hash:
            duplicates.append({
                "content_hash": digest,
                "kept_document_id": seen_hash[digest],
                "duplicate_document_id": item["document_id"],
            })
            continue
        seen_hash[digest] = item["document_id"]
        unique.append(item)
    selected = unique
    source_ids = {item["document_id"] for item in selected} | {row["duplicate_document_id"] for row in duplicates}
    # also keep source ids from original official-normal set
    official_ids = source_ids
    ref_ids = {item["document_id"] for item in selected}
    ref_paths = {item["relative_path"] for item in selected if item["relative_path"]}
    ref_hashes = {item["content_hash"] for item in selected}

    PHASE4.mkdir(parents=True, exist_ok=True)
    _write_jsonl(PHASE4 / "references.jsonl", selected)

    evaluator_labels = {}
    overlap = []
    snapshot = {}
    for split, path in FROZEN_DOCS.items():
        snapshot[str(path.relative_to(ROOT).as_posix())] = sha256_file(path)
        rows = _jsonl(path)
        kept_docs = []
        for row in rows:
            runtime = _runtime_candidate(row, identity)
            label = row.get("original_label")
            evaluator_labels[runtime["document_id"]] = {
                "original_label": label,
                "split": split,
            }
            if (
                runtime["document_id"] in official_ids
                or runtime["document_id"] in ref_ids
                or (runtime["relative_path"] and runtime["relative_path"] in ref_paths)
                or runtime["content_hash"] in ref_hashes
            ):
                overlap.append({
                    "split": split,
                    "document_id": runtime["document_id"],
                    "reason": "excluded_as_reference",
                })
                continue
            kept_docs.append(runtime)
        _write_jsonl(PHASE4 / f"candidate_{split}_documents.jsonl", kept_docs)
        chunks_path = FROZEN_CHUNKS[split]
        snapshot[str(chunks_path.relative_to(ROOT).as_posix())] = sha256_file(chunks_path)
        by_id = {doc["document_id"]: doc for doc in kept_docs}
        kept_chunks = []
        for row in _jsonl(chunks_path):
            chunk = _runtime_chunk(row, by_id)
            if chunk is not None:
                kept_chunks.append(chunk)
        _write_jsonl(PHASE4 / f"candidate_{split}_chunks.jsonl", kept_chunks)

    # overlap between written references and written candidates must be zero
    cand_ids, cand_paths, cand_hashes = set(), set(), set()
    for split in FROZEN_DOCS:
        for row in _jsonl(PHASE4 / f"candidate_{split}_documents.jsonl"):
            cand_ids.add(row["document_id"])
            cand_paths.add(row["relative_path"])
            cand_hashes.add(row["content_hash"])
    refs_written = _jsonl(PHASE4 / "references.jsonl")
    cands_written = []
    for split in FROZEN_DOCS:
        cands_written.extend(_jsonl(PHASE4 / f"candidate_{split}_documents.jsonl"))
    audit = audit_runtime_overlap(refs_written, cands_written)
    remaining = audit["remaining_overlap"]
    remaining_count = audit["remaining_overlap_count"]
    corpus_hash = sha256_text("\n".join(
        f"{item['reference_id']}|{item['content_hash']}" for item in selected
    ))
    write_json(MANIFESTS / "phase4_reference_manifest.json", {
        "selection": {
            "source": "datasets/processed/trusted_provenance/development_documents.jsonl",
            "rule": "original_label==normal AND source_level in {school_official, college_official}",
            "models": "administrator-curated official reference documents",
            "source_reference_document_count": source_count,
            "unique_reference_text_count": len(selected),
            "count": len(selected),
        },
        "duplicates": duplicates,
        "reference_ids": [item["reference_id"] for item in selected],
        "corpus_sha256": corpus_hash,
        "frozen_phase2_phase3_snapshot_sha256": snapshot,
        "phase4_outputs": {
            "references": "datasets/processed/phase4/references.jsonl",
            "candidate_development_tune": "datasets/processed/phase4/candidate_development_tune_documents.jsonl",
            "candidate_development_generalization": "datasets/processed/phase4/candidate_development_generalization_documents.jsonl",
        },
    })
    write_json(MANIFESTS / "phase4_overlap_audit.json", {
        "excluded_from_candidate_view": len(overlap),
        "remaining_overlap": remaining,
        "remaining_overlap_count": remaining_count,
        "pass": remaining_count == 0,
        "hash_definition": "sha256(runtime detector-visible text)",
    })
    write_json(MANIFESTS / "phase4_evaluator_labels.json", evaluator_labels)
    print(json.dumps({
        "source_reference_document_count": source_count,
        "unique_reference_text_count": len(selected),
        "overlap_pass": remaining_count == 0,
        "excluded": len(overlap),
    }))
    return 0 if remaining_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
