"""All-or-nothing conversion of LLM drafts into BehaviorEvidence."""
from __future__ import annotations
import hashlib
import json
from zhiyu.models.detection import Confidence, Mechanism
from zhiyu.models.semantic import (
    MAX_DRAFTS,
    BehaviorEvidence,
    SemanticAnalysisInput,
    SemanticIntent,
    SemanticObservationDraft,
)
from zhiyu.semantic.binding import bind_unique_excerpt

_INTENTS = {item.value: item for item in SemanticIntent}
_CONF = {item.value: item for item in Confidence}
_MECH = {
    Mechanism.PROMPT_INJECTION.value: Mechanism.PROMPT_INJECTION,
    Mechanism.HIDDEN_INSTRUCTION.value: Mechanism.HIDDEN_INSTRUCTION,
}


class InvalidSemanticOutput(ValueError):
    pass


def parse_observation_payload(raw: str) -> list[dict]:
    text = raw.strip()
    if text.startswith("```"):
        raise InvalidSemanticOutput("markdown fence is not allowed")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidSemanticOutput("json decode failed") from exc
    if not isinstance(payload, dict) or "observations" not in payload:
        raise InvalidSemanticOutput("missing observations")
    observations = payload["observations"]
    if not isinstance(observations, list) or len(observations) > MAX_DRAFTS:
        raise InvalidSemanticOutput("observations must be a short list")
    return observations


def _parse_draft(row: dict, allowed_rule_ids: set[str]) -> SemanticObservationDraft:
    if not isinstance(row, dict):
        raise InvalidSemanticOutput("draft must be an object")
    allowed_keys = {
        "intent", "mechanism", "confidence", "excerpt", "rationale", "source_rule_ids",
    }
    if set(row) - allowed_keys:
        raise InvalidSemanticOutput("unexpected draft field")
    try:
        intent = _INTENTS[row["intent"]]
        confidence = _CONF[row["confidence"]]
    except KeyError as exc:
        raise InvalidSemanticOutput("invalid intent or confidence") from exc
    mechanism_raw = row.get("mechanism")
    if mechanism_raw in (None, "null"):
        mechanism = None
    else:
        if mechanism_raw not in _MECH:
            raise InvalidSemanticOutput("invalid mechanism")
        mechanism = _MECH[mechanism_raw]
    excerpt = row.get("excerpt")
    rationale = row.get("rationale")
    if not isinstance(excerpt, str) or not isinstance(rationale, str):
        raise InvalidSemanticOutput("excerpt and rationale must be strings")
    source_raw = row.get("source_rule_ids", [])
    if source_raw is None:
        source_raw = []
    if not isinstance(source_raw, list) or any(not isinstance(item, str) for item in source_raw):
        raise InvalidSemanticOutput("source_rule_ids must be a string list")
    if any(item not in allowed_rule_ids for item in source_raw):
        raise InvalidSemanticOutput("unknown source_rule_id")
    if intent is SemanticIntent.NO_CONTROL:
        if mechanism is not None:
            raise InvalidSemanticOutput("NO_CONTROL requires null mechanism")
    elif intent is SemanticIntent.IMPLICIT_CONTROL:
        if mechanism not in {Mechanism.PROMPT_INJECTION, Mechanism.HIDDEN_INSTRUCTION}:
            raise InvalidSemanticOutput("IMPLICIT_CONTROL requires PI or HI")
        if not excerpt:
            raise InvalidSemanticOutput("IMPLICIT_CONTROL requires excerpt")
    elif intent is SemanticIntent.UNCERTAIN:
        if not excerpt:
            raise InvalidSemanticOutput("UNCERTAIN requires excerpt")
    return SemanticObservationDraft(
        intent=intent,
        mechanism=mechanism,
        confidence=confidence,
        excerpt=excerpt,
        rationale=rationale,
        source_rule_ids=tuple(source_raw),
    )


def _evidence_id(document_id: str, chunk_id: str, start: int, end: int, intent: str, mechanism: str | None) -> str:
    payload = f"{document_id}|{chunk_id}|{start}|{end}|{intent}|{mechanism or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def materialize_behavior_evidence(
    analysis_input: SemanticAnalysisInput,
    raw: str,
) -> tuple[BehaviorEvidence, ...]:
    observations = parse_observation_payload(raw)
    allowed_rule_ids = {event.rule_id for event in analysis_input.rule_events}
    drafts = [_parse_draft(row, allowed_rule_ids) for row in observations]
    text = analysis_input.detection_input.text
    document_id = analysis_input.detection_input.document_id
    chunk_id = analysis_input.detection_input.chunk_id
    evidence: list[BehaviorEvidence] = []
    for draft in drafts:
        if draft.intent is SemanticIntent.NO_CONTROL:
            if draft.excerpt:
                bound = bind_unique_excerpt(text, draft.excerpt)
                if bound is None:
                    raise InvalidSemanticOutput("NO_CONTROL excerpt failed unique bind")
            continue
        bound = bind_unique_excerpt(text, draft.excerpt)
        if bound is None:
            raise InvalidSemanticOutput("excerpt failed unique bind")
        start, end = bound
        evidence.append(
            BehaviorEvidence(
                evidence_id=_evidence_id(
                    document_id, chunk_id, start, end, draft.intent.value,
                    None if draft.mechanism is None else draft.mechanism.value,
                ),
                document_id=document_id,
                chunk_id=chunk_id,
                intent=draft.intent,
                mechanism=draft.mechanism,
                confidence=draft.confidence,
                span_start=start,
                span_end=end,
                excerpt=draft.excerpt,
                rationale=draft.rationale,
                source_rule_ids=draft.source_rule_ids,
            )
        )
    return tuple(evidence)
