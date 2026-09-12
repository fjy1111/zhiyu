from __future__ import annotations
import json
from zhiyu.models.rag import (
    CicVerdict,
    EvaluatorRecord,
    GenerationOutcome,
    GenerationStatus,
    GeneratorConfig,
    RetrievalHit,
    RetrievalResult,
    RetrievalStatus,
    RuntimeQuery,
)
from zhiyu.rag.cic import ContextIntegrityChecker, maybe_run_cic
from zhiyu.rag.firewall import QueryFirewallError


class GeneratorProviderError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def serialize_generation_input(query: RuntimeQuery, hits: tuple[RetrievalHit, ...]) -> dict:
    if isinstance(query, EvaluatorRecord) or not isinstance(query, RuntimeQuery):
        raise QueryFirewallError("generator accepts RuntimeQuery only")
    return {
        "query_id": query.query_id,
        "query_text": query.query_text,
        "chunks": [
            {"document_id": hit.document_id, "chunk_id": hit.chunk_id, "text": hit.text}
            for hit in hits
        ],
    }


class SharedGenerator:
    def __init__(self, config: GeneratorConfig, provider):
        self.config = config
        self.provider = provider

    def generate(self, query: RuntimeQuery, retrieval: RetrievalResult) -> GenerationOutcome:
        payload = serialize_generation_input(query, retrieval.hits)
        try:
            raw = self.provider.complete(self.config.system_prompt, json.dumps(payload, ensure_ascii=False))
        except GeneratorProviderError as exc:
            return GenerationOutcome(GenerationStatus.ERROR, None, self.config, error_code=exc.code)
        except Exception:
            return GenerationOutcome(GenerationStatus.ERROR, None, self.config, error_code="UNKNOWN")
        if not isinstance(raw, str) or not raw.strip():
            return GenerationOutcome(GenerationStatus.INVALID_OUTPUT, None, self.config, error_code="EMPTY_CONTENT")
        return GenerationOutcome(GenerationStatus.OK, raw.strip(), self.config)


def _require_query(query) -> RuntimeQuery:
    if isinstance(query, EvaluatorRecord) or not isinstance(query, RuntimeQuery):
        raise QueryFirewallError("generation path accepts RuntimeQuery only")
    return query


def run_vanilla_path(query, retrieval: RetrievalResult, generator: SharedGenerator) -> GenerationOutcome:
    _require_query(query)
    if retrieval.status is RetrievalStatus.NO_CONTEXT or not retrieval.hits:
        return GenerationOutcome(GenerationStatus.NO_CONTEXT, None, generator.config)
    return generator.generate(query, retrieval)


def run_protected_path(query, retrieval: RetrievalResult, generator: SharedGenerator, cic: ContextIntegrityChecker) -> GenerationOutcome:
    query = _require_query(query)
    if retrieval.status is RetrievalStatus.NO_CONTEXT or not retrieval.hits:
        return GenerationOutcome(GenerationStatus.NO_CONTEXT, None, generator.config)
    cic_result = maybe_run_cic("protected", query, retrieval, cic)
    if cic_result is None:
        return GenerationOutcome(GenerationStatus.NO_CONTEXT, None, generator.config)
    if cic_result.verdict is CicVerdict.ABSTAIN:
        return GenerationOutcome(GenerationStatus.ABSTAIN, None, generator.config, cic=cic_result)
    outcome = generator.generate(query, retrieval)
    return GenerationOutcome(outcome.status, outcome.answer, generator.config, cic=cic_result, error_code=outcome.error_code)
