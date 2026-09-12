from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvaluatorKind(str, Enum):
    CLEAN = "CLEAN"
    POISON = "POISON"


class RetrievalStatus(str, Enum):
    OK = "OK"
    NO_CONTEXT = "NO_CONTEXT"


NO_CONTEXT = RetrievalStatus.NO_CONTEXT


@dataclass(frozen=True)
class RuntimeQuery:
    query_id: str
    query_text: str

    def __post_init__(self) -> None:
        if not self.query_id or not isinstance(self.query_id, str):
            raise ValueError("query_id must be a non-empty string")
        if not isinstance(self.query_text, str):
            raise ValueError("query_text must be a string")

    def to_runtime_dict(self) -> dict[str, str]:
        return {"query_id": self.query_id, "query_text": self.query_text}


@dataclass(frozen=True)
class EvaluatorRecord:
    query_id: str
    kind: EvaluatorKind
    gold_answer: str | None = None
    attack_success_criteria: str | None = None

    def __post_init__(self) -> None:
        if not self.query_id or not isinstance(self.query_id, str):
            raise ValueError("query_id must be a non-empty string")
        if not isinstance(self.kind, EvaluatorKind):
            raise TypeError("kind must be EvaluatorKind")

    def to_evaluator_dict(self) -> dict[str, Any]:
        payload = {"query_id": self.query_id, "kind": self.kind.value}
        if self.gold_answer is not None:
            payload["gold_answer"] = self.gold_answer
        if self.attack_success_criteria is not None:
            payload["attack_success_criteria"] = self.attack_success_criteria
        return payload


@dataclass(frozen=True)
class RetrieverConfig:
    method: str = "lexical"
    k: int = 3

    def __post_init__(self) -> None:
        if self.method != "lexical":
            raise ValueError("Phase 6 foundation retriever method must be lexical")
        if self.k < 1:
            raise ValueError("k must be >= 1")


@dataclass(frozen=True)
class IndexedChunk:
    document_id: str
    chunk_id: str
    text: str


@dataclass(frozen=True)
class KnowledgeIndex:
    name: str
    chunks: tuple[IndexedChunk, ...]
    config: RetrieverConfig

    @property
    def document_ids(self) -> frozenset[str]:
        return frozenset(chunk.document_id for chunk in self.chunks)


@dataclass(frozen=True)
class RetrievalHit:
    document_id: str
    chunk_id: str
    text: str
    score: float


@dataclass(frozen=True)
class RetrievalResult:
    status: RetrievalStatus
    hits: tuple[RetrievalHit, ...]

    @property
    def allows_cic(self) -> bool:
        return self.status is RetrievalStatus.OK and len(self.hits) > 0

    @property
    def allows_generator(self) -> bool:
        return self.status is RetrievalStatus.OK and len(self.hits) > 0


@dataclass(frozen=True)
class BuiltIndexes:
    vanilla: KnowledgeIndex
    protected: KnowledgeIndex
    config: RetrieverConfig
