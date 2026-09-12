from __future__ import annotations
import json
from zhiyu.models.judge import (
    BehaviorAssessment,
    DocumentEvidence,
    EvidenceCoherence,
    FactualAssessment,
    Uncertainty,
    UnifiedRiskAssessment,
)

FORBIDDEN_VERDICT = {"SAFE", "REVIEW", "POISON", "final_risk_level", "final_risk_score"}
_BEH = {item.value: item for item in BehaviorAssessment}
_FACT = {item.value: item for item in FactualAssessment}
_COH = {item.value: item for item in EvidenceCoherence}
_UNC = {item.value: item for item in Uncertainty}


class InvalidJudgeOutput(ValueError):
    pass


def parse_assessment(raw: str, doc: DocumentEvidence) -> UnifiedRiskAssessment:
    text = raw.strip()
    if text.startswith("```"):
        raise InvalidJudgeOutput("markdown fence is not allowed")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidJudgeOutput("json decode failed") from exc
    if not isinstance(payload, dict):
        raise InvalidJudgeOutput("payload must be an object")
    required = {"document_id", "cited_rule_event_refs", "cited_behavior_evidence_ids", "cited_factual_evidence_ids", "behavior_assessment", "factual_assessment", "evidence_coherence", "uncertainty", "analyzer_failures", "rationale"}
    if set(payload) != required:
        raise InvalidJudgeOutput("schema keys mismatch")
    if any(key in payload for key in FORBIDDEN_VERDICT):
        raise InvalidJudgeOutput("forbidden verdict field")
    if payload.get("document_id") != doc.document_id:
        raise InvalidJudgeOutput("document_id mismatch")
    known_rules = {item.rule_event_ref for item in doc.rule_events}
    known_behavior = {item.evidence_id for item in doc.behavior_evidence}
    known_factual = {item.evidence_id for item in doc.factual_evidence}

    def _ids(name: str, known: set[str]) -> tuple[str, ...]:
        values = payload.get(name, [])
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise InvalidJudgeOutput(f"invalid {name}")
        if len(values) != len(set(values)):
            raise InvalidJudgeOutput(f"duplicate {name}")
        for item in values:
            if item not in known:
                raise InvalidJudgeOutput(f"unknown {name}")
        return tuple(values)

    try:
        behavior = _BEH[payload["behavior_assessment"]]
        factual = _FACT[payload["factual_assessment"]]
        coherence = _COH[payload["evidence_coherence"]]
        uncertainty = _UNC[payload["uncertainty"]]
    except KeyError as exc:
        raise InvalidJudgeOutput("invalid assessment enum") from exc
    rationale = payload.get("rationale", "")
    failures = payload.get("analyzer_failures", [])
    if not isinstance(rationale, str) or not isinstance(failures, list):
        raise InvalidJudgeOutput("invalid rationale or failures")
    return UnifiedRiskAssessment(
        document_id=doc.document_id,
        cited_rule_event_refs=_ids("cited_rule_event_refs", known_rules),
        cited_behavior_evidence_ids=_ids("cited_behavior_evidence_ids", known_behavior),
        cited_factual_evidence_ids=_ids("cited_factual_evidence_ids", known_factual),
        behavior_assessment=behavior,
        factual_assessment=factual,
        evidence_coherence=coherence,
        uncertainty=uncertainty,
        analyzer_failures=tuple(str(item) for item in failures),
        rationale=rationale,
    )
