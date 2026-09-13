"""Phase 7 prescan JSONL checkpoint I/O. No LLM calls."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import shutil
from pathlib import Path

HEADER_RECORD_TYPE = "phase7_prescan_header"
LITERAL_BACKSLASH_N = "\\n"


class CheckpointError(ValueError):
    """Raised when a checkpoint cannot be loaded, written, or recovered safely."""


@dataclass(frozen=True)
class CheckpointHeader:
    demo_kb_sha256: str
    manifest_sha256: str
    model: str
    base_url: str

    def to_record(self) -> dict:
        return {
            "record_type": HEADER_RECORD_TYPE,
            "demo_kb_sha256": self.demo_kb_sha256,
            "manifest_sha256": self.manifest_sha256,
            "model": self.model,
            "base_url": self.base_url,
        }

    @classmethod
    def from_record(cls, record: dict) -> "CheckpointHeader":
        try:
            header = cls(
                demo_kb_sha256=record["demo_kb_sha256"],
                manifest_sha256=record["manifest_sha256"],
                model=record["model"],
                base_url=record["base_url"],
            )
        except KeyError as exc:
            raise CheckpointError("malformed checkpoint header") from exc
        values = (
            header.demo_kb_sha256,
            header.manifest_sha256,
            header.model,
            header.base_url,
        )
        if not all(isinstance(value, str) and value for value in values):
            raise CheckpointError("malformed checkpoint header")
        return header

    def compatible_with(self, other: "CheckpointHeader") -> bool:
        return (
            self.demo_kb_sha256 == other.demo_kb_sha256
            and self.manifest_sha256 == other.manifest_sha256
            and self.model == other.model
            and self.base_url == other.base_url
        )


def encode_jsonl_record(record: dict) -> str:
    if not isinstance(record, dict):
        raise CheckpointError("record must be a JSON object")
    return json.dumps(record, ensure_ascii=False) + "\n"


def append_jsonl_record(path: Path, record: dict) -> None:
    payload = encode_jsonl_record(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def load_checkpoint(path: Path, expected: CheckpointHeader) -> dict[str, dict]:
    if not path.is_file():
        raise CheckpointError(f"checkpoint not found: {path}")
    header: CheckpointHeader | None = None
    records: dict[str, dict] = {}
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.strip() == "":
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CheckpointError(f"malformed JSONL record at line {line_no}") from exc
        if not isinstance(record, dict):
            raise CheckpointError(f"malformed JSONL record at line {line_no}: not an object")
        if record.get("record_type") == HEADER_RECORD_TYPE:
            if header is not None:
                raise CheckpointError(f"duplicate checkpoint header at line {line_no}")
            if records:
                raise CheckpointError(
                    f"checkpoint header must be the first record (line {line_no})"
                )
            header = CheckpointHeader.from_record(record)
            continue
        document_id = record.get("document_id")
        if not isinstance(document_id, str) or not document_id:
            raise CheckpointError(
                f"malformed JSONL record at line {line_no}: missing document_id"
            )
        if document_id in records:
            raise CheckpointError(
                f"duplicate document_id {document_id!r} at line {line_no}"
            )
        records[document_id] = record
    if header is None:
        raise CheckpointError("malformed checkpoint: missing compatibility header")
    if not header.compatible_with(expected):
        raise CheckpointError(
            "checkpoint is incompatible with Demo KB SHA / manifest SHA / model / base_url"
        )
    return records


def initialize_checkpoint(path: Path, header: CheckpointHeader) -> dict[str, dict]:
    if path.exists():
        return load_checkpoint(path, expected=header)
    append_jsonl_record(path, header.to_record())
    return {}


def recover_literal_backslash_n_records(text: str) -> list[dict]:
    """Recover JSON objects separated by literal backslash-n.

    Uses JSONDecoder.raw_decode so JSON-escaped \\n inside strings is not a separator.
    """
    if not isinstance(text, str) or text == "":
        raise CheckpointError("unrecoverable malformed checkpoint: empty")
    decoder = json.JSONDecoder()
    records: list[dict] = []
    seen: set[str] = set()
    index = 0
    length = len(text)
    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index >= length:
            break
        if text.startswith(LITERAL_BACKSLASH_N, index):
            index += 2
            continue
        try:
            obj, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise CheckpointError("unrecoverable malformed checkpoint") from exc
        if not isinstance(obj, dict):
            raise CheckpointError(
                "unrecoverable malformed checkpoint: record is not an object"
            )
        json.loads(json.dumps(obj, ensure_ascii=False))
        document_id = obj.get("document_id")
        if not isinstance(document_id, str) or not document_id:
            raise CheckpointError(
                "unrecoverable malformed checkpoint: missing document_id"
            )
        if document_id in seen:
            raise CheckpointError(
                "unrecoverable malformed checkpoint: duplicate document_id"
            )
        seen.add(document_id)
        records.append(obj)
        index = end
        while index < length and text[index].isspace():
            index += 1
        if text.startswith(LITERAL_BACKSLASH_N, index):
            index += 2
    if not records:
        raise CheckpointError("unrecoverable malformed checkpoint: no records")
    leftover = text[index:]
    leftover_stripped = leftover.strip()
    if leftover_stripped not in {"", LITERAL_BACKSLASH_N}:
        raise CheckpointError("unrecoverable malformed checkpoint: leftover data")
    return records


def backup_malformed_checkpoint(path: Path, backup_path: Path) -> Path:
    if not path.is_file():
        raise CheckpointError(f"checkpoint not found: {path}")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        raise CheckpointError(f"backup already exists: {backup_path}")
    shutil.copy2(path, backup_path)
    return backup_path


def mark_unrecoverable(path: Path, reason: str) -> Path:
    marker = path.with_name(path.name + ".unrecoverable.json")
    payload = {
        "path": str(path),
        "unrecoverable": True,
        "reason": reason,
    }
    marker.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return marker


def write_checkpoint_atomically(
    path: Path,
    header: CheckpointHeader,
    records: list[dict],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    seen: set[str] = set()
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(encode_jsonl_record(header.to_record()))
        for record in records:
            document_id = record.get("document_id")
            if not isinstance(document_id, str) or not document_id:
                raise CheckpointError("missing document_id")
            if document_id in seen:
                raise CheckpointError(f"duplicate document_id {document_id!r}")
            seen.add(document_id)
            handle.write(encode_jsonl_record(record))
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def recover_checkpoint_file(
    src: Path,
    dest: Path,
    header: CheckpointHeader,
) -> list[dict]:
    records = recover_literal_backslash_n_records(src.read_text(encoding="utf-8"))
    write_checkpoint_atomically(dest, header, records)
    loaded = load_checkpoint(dest, expected=header)
    if set(loaded) != {record["document_id"] for record in records}:
        raise CheckpointError("unrecoverable malformed checkpoint: reload mismatch")
    return records
