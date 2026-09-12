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
    blob = json.dumps(row, ensure_ascii=False)
    for key in FORBIDDEN_RUNTIME_FIELDS:
        if key in row:
            raise ValueError(f"runtime corpus leaked {key}")
        if key in blob and key in ("original_label", "attack_type", "target_answer"):
            raise ValueError(f"runtime corpus leaked {key}")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_references(path: Path) -> list[ReferenceDocument]:
    docs = []
    for row in load_jsonl(path):
        assert_runtime_clean(row)
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
