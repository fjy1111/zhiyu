from __future__ import annotations
import re
from zhiyu.models.rag import (
    EvaluatorRecord,
    KnowledgeIndex,
    RetrievalHit,
    RetrievalResult,
    RetrievalStatus,
    RetrieverConfig,
    RuntimeQuery,
)

NO_CONTEXT = RetrievalStatus.NO_CONTEXT
_ASCII = re.compile(r"[A-Za-z0-9]+")
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")


def _tokens(text: str) -> set[str]:
    tokens = {match.group(0).lower() for match in _ASCII.finditer(text)}
    for run in _CJK_RUN.findall(text):
        tokens.update(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


def lexical_score(query: str, document: str) -> float:
    left = _tokens(query)
    right = _tokens(document)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left)


class SharedRetriever:
    def __init__(self, config: RetrieverConfig):
        self.config = config

    def retrieve(self, query: RuntimeQuery, index: KnowledgeIndex) -> RetrievalResult:
        if isinstance(query, EvaluatorRecord) or not isinstance(query, RuntimeQuery):
            raise TypeError("retriever accepts RuntimeQuery only")
        if index.config != self.config:
            raise ValueError("index retriever config must match shared retriever")
        scored: list[tuple[float, object]] = []
        for chunk in index.chunks:
            score = lexical_score(query.query_text, chunk.text)
            if score > 0.0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].document_id, item[1].chunk_id))
        chosen = scored[: self.config.k]
        if not chosen:
            return RetrievalResult(RetrievalStatus.NO_CONTEXT, ())
        hits = tuple(
            RetrievalHit(chunk.document_id, chunk.chunk_id, chunk.text, round(score, 6))
            for score, chunk in chosen
        )
        return RetrievalResult(RetrievalStatus.OK, hits)
