from __future__ import annotations
import json
from pathlib import Path
from zhiyu.models.detection import Decision
from zhiyu.models.rag import BuiltIndexes, IndexedChunk, KnowledgeIndex, RetrieverConfig
from zhiyu.rag.firewall import FORBIDDEN_RUNTIME_FIELDS, QueryFirewallError

SPLITS = ("development_tune", "development_generalization")


def _clean_row(row: dict) -> None:
    for key in FORBIDDEN_RUNTIME_FIELDS:
        if key in row:
            raise QueryFirewallError(f"GT field leaked into admission input: {key}")


def load_candidate_chunks(project: Path, split: str | None = None) -> tuple[IndexedChunk, ...]:
    if split is None:
        selected = SPLITS
    else:
        if split not in SPLITS:
            raise ValueError(f"unsupported Phase 6 split: {split}")
        selected = (split,)
    chunks: list[IndexedChunk] = []
    for name in selected:
        path = Path(project) / "datasets/processed/phase4" / f"candidate_{name}_chunks.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            _clean_row(row)
            chunks.append(IndexedChunk(row["document_id"], row["chunk_id"], row["text"]))
    return tuple(chunks)


def load_frozen_decisions(path: Path) -> dict[str, Decision]:
    decisions: dict[str, Decision] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        document_id = row["document_id"]
        decision = Decision(row["final_decision"])
        decisions[document_id] = decision
    return decisions


def build_indexes(
    chunks: tuple[IndexedChunk, ...] | list[IndexedChunk],
    decisions: dict[str, Decision],
    config: RetrieverConfig,
) -> BuiltIndexes:
    vanilla_chunks = tuple(chunks)
    protected_chunks = tuple(chunk for chunk in vanilla_chunks if decisions.get(chunk.document_id) is Decision.SAFE)
    if any(decisions.get(chunk.document_id) is not Decision.SAFE for chunk in protected_chunks):
        raise RuntimeError("Protected index admitted a non-SAFE document")
    vanilla = KnowledgeIndex("vanilla", vanilla_chunks, config)
    protected = KnowledgeIndex("protected", protected_chunks, config)
    return BuiltIndexes(vanilla, protected, config)
