from __future__ import annotations
import json
from zhiyu.detector.rules_hidden import find_hidden_events, find_hidden_regions
from zhiyu.detector.rules_injection import find_injection_events
from zhiyu.models.detection import DetectionInput, Mechanism
from zhiyu.models.rag import (
    ALLOWED_CIC_MECHANISMS,
    CIC_SCHEMA_KEYS,
    CicCitation,
    CicResult,
    CicStatus,
    CicVerdict,
    EvaluatorRecord,
    RetrievalResult,
    RetrievalStatus,
    RuntimeQuery,
)
from zhiyu.rag.firewall import QueryFirewallError


class CicBoundaryError(RuntimeError):
    pass


class CicProviderError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class InvalidCicOutput(ValueError):
    pass


def _map_mechanism(rule_id: str, mechanism: Mechanism) -> str | None:
    if mechanism is Mechanism.HIDDEN_INSTRUCTION or rule_id.startswith("hi."):
        return "hidden_instruction"
    if "role_manipulation" in rule_id:
        return "role_hijack"
    if mechanism is Mechanism.PROMPT_INJECTION:
        return "instruction_override"
    return None


def scan_hits(retrieval: RetrievalResult) -> tuple[CicCitation, ...]:
    citations: list[CicCitation] = []
    for hit in retrieval.hits:
        item = DetectionInput(hit.document_id, hit.chunk_id, hit.text)
        hidden_regions = tuple(find_hidden_regions(item.text))
        events = list(find_hidden_events(item))
        events.extend(find_injection_events(item, skip_spans=hidden_regions))
        for event in events:
            mapped = _map_mechanism(event.rule_id, event.mechanism)
            if mapped is None:
                continue
            citations.append(CicCitation(
                document_id=event.document_id,
                chunk_id=event.chunk_id,
                span_start=event.span_start,
                span_end=event.span_end,
                excerpt=event.excerpt,
                mechanism=mapped,
            ))
    return tuple(citations)


def _hit_index(retrieval: RetrievalResult) -> dict[tuple[str, str], str]:
    return {(hit.document_id, hit.chunk_id): hit.text for hit in retrieval.hits}


def parse_cic_assessment(raw: str, query: RuntimeQuery, retrieval: RetrievalResult) -> CicResult:
    text = raw.strip()
    if text.startswith("```"):
        raise InvalidCicOutput("markdown fence is not allowed")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidCicOutput("json decode failed") from exc
    if not isinstance(payload, dict) or set(payload) != CIC_SCHEMA_KEYS:
        raise InvalidCicOutput("schema keys mismatch")
    forbidden = {"SAFE", "REVIEW", "POISON", "score", "risk", "final_risk_level"}
    if any(key in payload for key in forbidden):
        raise InvalidCicOutput("forbidden risk field")
    if payload.get("query_id") != query.query_id:
        raise InvalidCicOutput("query_id mismatch")
    integrity = payload.get("integrity")
    if integrity not in {"PASS", "FAIL"}:
        raise InvalidCicOutput("invalid integrity")
    mechanisms = payload.get("mechanisms")
    citations = payload.get("citations")
    rationale = payload.get("rationale")
    if not isinstance(mechanisms, list) or not isinstance(citations, list) or not isinstance(rationale, str):
        raise InvalidCicOutput("invalid field types")
    if any(item not in ALLOWED_CIC_MECHANISMS for item in mechanisms):
        raise InvalidCicOutput("unknown mechanism")
    if len(mechanisms) != len(set(mechanisms)):
        raise InvalidCicOutput("duplicate mechanism")
    known = _hit_index(retrieval)
    parsed: list[CicCitation] = []
    seen: set[tuple[str, str, int, int]] = set()
    for row in citations:
        if not isinstance(row, dict):
            raise InvalidCicOutput("invalid citation")
        required = {"document_id", "chunk_id", "span_start", "span_end"}
        if set(row) != required:
            raise InvalidCicOutput("citation schema mismatch")
        key = (row["document_id"], row["chunk_id"])
        if key not in known:
            raise InvalidCicOutput("unknown or cross-context citation")
        start, end = row["span_start"], row["span_end"]
        body = known[key]
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start or end > len(body):
            raise InvalidCicOutput("citation span out of bounds")
        span_key = (key[0], key[1], start, end)
        if span_key in seen:
            raise InvalidCicOutput("duplicate citation")
        seen.add(span_key)
        parsed.append(CicCitation(key[0], key[1], start, end, body[start:end], mechanisms[0] if mechanisms else "instruction_override"))
    if integrity == "PASS":
        if mechanisms or parsed:
            raise InvalidCicOutput("PASS must not cite failures")
        return CicResult(CicVerdict.PASS, CicStatus.OK, (), (), rationale)
    if not mechanisms or not parsed:
        raise InvalidCicOutput("FAIL requires mechanisms and citations")
    bound = []
    for cite, row in zip(parsed, citations):
        mech = mechanisms[0]
        bound.append(CicCitation(cite.document_id, cite.chunk_id, cite.span_start, cite.span_end, cite.excerpt, mech))
    return CicResult(CicVerdict.ABSTAIN, CicStatus.OK, tuple(bound), tuple(mechanisms), rationale)


class ContextIntegrityChecker:
    def __init__(self, provider=None):
        self.provider = provider

    def assess(self, query, retrieval: RetrievalResult, *, index_name: str = "protected") -> CicResult:
        if index_name != "protected":
            raise CicBoundaryError("CIC never runs on Vanilla")
        if retrieval.status is RetrievalStatus.NO_CONTEXT or not retrieval.hits:
            raise CicBoundaryError("CIC not called on NO_CONTEXT")
        if isinstance(query, EvaluatorRecord) or not isinstance(query, RuntimeQuery):
            raise QueryFirewallError("CIC accepts RuntimeQuery only")
        if self.provider is None:
            citations = scan_hits(retrieval)
            if citations:
                mechanisms = tuple(dict.fromkeys(item.mechanism for item in citations))
                return CicResult(CicVerdict.ABSTAIN, CicStatus.OK, citations, mechanisms, "retrieved context failed integrity scan")
            return CicResult(CicVerdict.PASS, CicStatus.OK, (), (), "retrieved context has no control instruction")
        try:
            raw = self.provider.complete("cic", json.dumps({"query": query.to_runtime_dict(), "chunks": [
                {"document_id": hit.document_id, "chunk_id": hit.chunk_id, "text": hit.text} for hit in retrieval.hits
            ]}, ensure_ascii=False))
            return parse_cic_assessment(raw, query, retrieval)
        except CicProviderError as exc:
            return CicResult(CicVerdict.ABSTAIN, CicStatus.ERROR, (), (), exc.code)
        except InvalidCicOutput:
            return CicResult(CicVerdict.ABSTAIN, CicStatus.INVALID_OUTPUT, (), (), "INVALID_OUTPUT")
        except Exception:
            return CicResult(CicVerdict.ABSTAIN, CicStatus.ERROR, (), (), "UNKNOWN")


def maybe_run_cic(index_name: str, query, retrieval: RetrievalResult, checker: ContextIntegrityChecker) -> CicResult | None:
    if index_name != "protected" or not retrieval.allows_cic:
        return None
    return checker.assess(query, retrieval, index_name=index_name)
