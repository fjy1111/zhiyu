"""Phase 4 trusted reference corpus and candidate identity. No ground truth."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

OFFICIAL_SOURCE_LEVELS = frozenset({"school_official", "college_official"})
FORBIDDEN_RUNTIME_FIELDS = (
    "original_label", "attack_type", "facts", "label", "target_answer",
    "correct_answer", "expected_answer", "question",
)


@dataclass(frozen=True)
class ReferenceDocument:
    reference_id: str
    document_id: str
    relative_path: str
    content_hash: str
    text: str

    def to_runtime_dict(self) -> dict:
        return {
            "reference_id": self.reference_id,
            "document_id": self.document_id,
            "relative_path": self.relative_path,
            "content_hash": self.content_hash,
            "text": self.text,
        }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_runtime_clean(row: dict) -> None:
    for key in FORBIDDEN_RUNTIME_FIELDS:
        if key in row:
            raise ValueError(f"runtime corpus leaked {key}")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_references(path: Path) -> list[ReferenceDocument]:
    docs = []
    seen_hash: set[str] = set()
    for row in load_jsonl(path):
        assert_runtime_clean(row)
        expected = sha256_text(row["text"])
        if row["content_hash"] != expected:
            raise ValueError("content_hash must equal sha256(runtime text)")
        if expected in seen_hash:
            raise ValueError("reference corpus contains duplicate runtime content_hash")
        seen_hash.add(expected)
        docs.append(ReferenceDocument(
            reference_id=row["reference_id"],
            document_id=row["document_id"],
            relative_path=row["relative_path"],
            content_hash=row["content_hash"],
            text=row["text"],
        ))
    return docs


def overlaps(candidate_id: str, candidate_path: str, candidate_hash: str, ref: ReferenceDocument) -> bool:
    return (
        candidate_id == ref.document_id
        or (bool(candidate_path) and candidate_path == ref.relative_path)
        or (bool(candidate_hash) and candidate_hash == ref.content_hash)
    )


def audit_runtime_overlap(references: list[dict], candidates: list[dict]) -> dict:
    for row in list(references) + list(candidates):
        if row.get("content_hash") != sha256_text(row.get("text") or ""):
            raise ValueError("content_hash must equal sha256(runtime detector-visible text)")
    ref_ids = {row["document_id"] for row in references}
    ref_paths = {row["relative_path"] for row in references if row.get("relative_path")}
    ref_hashes = {row["content_hash"] for row in references}
    cand_ids = {row["document_id"] for row in candidates}
    cand_paths = {row["relative_path"] for row in candidates if row.get("relative_path")}
    cand_hashes = {row["content_hash"] for row in candidates}
    remaining = {
        "document_id": sorted(ref_ids & cand_ids),
        "relative_path": sorted(ref_paths & cand_paths),
        "content_hash": sorted(ref_hashes & cand_hashes),
    }
    remaining_count = sum(len(values) for values in remaining.values())
    return {
        "remaining_overlap": remaining,
        "remaining_overlap_count": remaining_count,
        "pass": remaining_count == 0,
    }
