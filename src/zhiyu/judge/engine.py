"""Deterministic non-compensatory Phase 5 risk engine."""
from __future__ import annotations
from zhiyu.models.detection import Confidence, Decision, EventClass, Mechanism
from zhiyu.models.factual import FactualRelation
from zhiyu.models.judge import (
    Ablation,
    AnalysisStatusRecord,
    Component,
    DocumentEvidence,
    EvidenceCoherence,
    Phase5Decision,
    StatusKind,
    UnifiedRiskAssessment,
)
from zhiyu.models.semantic import SemanticIntent
from zhiyu.judge.plan import unexpected_missing
from zhiyu.judge.refs import rule_event_ref

_CONTROL = {Mechanism.PROMPT_INJECTION, Mechanism.HIDDEN_INSTRUCTION}
_FAIL = {StatusKind.ERROR, StatusKind.INVALID_OUTPUT}


def poison_gate_refs(doc: DocumentEvidence) -> tuple[str, ...]:
    refs: list[str] = []
    for record in doc.rule_events:
        event = record.event
        if (
            event.mechanism in _CONTROL
            and event.event_class is EventClass.MECHANISM
            and event.confidence is Confidence.HIGH
        ):
            refs.append(record.rule_event_ref)
    for evidence in doc.behavior_evidence:
        if (
            evidence.intent is SemanticIntent.IMPLICIT_CONTROL
            and evidence.mechanism in _CONTROL
            and evidence.confidence is Confidence.HIGH
        ):
            refs.append(evidence.evidence_id)
    return tuple(refs)


def _in_scope_statuses(doc: DocumentEvidence, ablation: Ablation) -> list[AnalysisStatusRecord]:
    from zhiyu.judge.plan import expected_components
    expected = expected_components(ablation)
    return [item for item in doc.statuses if item.component in expected]


def decide(
    doc: DocumentEvidence,
    ablation: Ablation,
    assessment: UnifiedRiskAssessment | None = None,
    judge_status: AnalysisStatusRecord | None = None,
) -> Phase5Decision:
    missing = unexpected_missing(doc, ablation)
    poison_refs = poison_gate_refs(doc)
    if poison_refs:
        return Phase5Decision(doc.document_id, Decision.POISON, ablation.value, poison_refs, (), missing)

    reasons: list[str] = []
    if ablation in {Ablation.RULE_ONLY, Ablation.RULE_SEMANTIC, Ablation.FULL_EVIDENCE, Ablation.FULL_JUDGE}:
        for record in doc.rule_events:
            event = record.event
            strong = (
                event.mechanism in _CONTROL
                and event.event_class is EventClass.MECHANISM
                and event.confidence is Confidence.HIGH
            )
            if not strong:
                reasons.append(f"weak_rule:{record.rule_event_ref}")
    if ablation in {Ablation.RULE_SEMANTIC, Ablation.FULL_EVIDENCE, Ablation.FULL_JUDGE}:
        for evidence in doc.behavior_evidence:
            strong = (
                evidence.intent is SemanticIntent.IMPLICIT_CONTROL
                and evidence.mechanism in _CONTROL
                and evidence.confidence is Confidence.HIGH
            )
            if not strong:
                reasons.append(f"weak_behavior:{evidence.evidence_id}")
    if ablation in {Ablation.FULL_EVIDENCE, Ablation.FULL_JUDGE}:
        for evidence in doc.factual_evidence:
            if evidence.relation is FactualRelation.CONTRADICTORY:
                reasons.append(f"contradictory:{evidence.evidence_id}")
            elif evidence.relation is FactualRelation.INSUFFICIENT_EVIDENCE:
                reasons.append(f"insufficient:{evidence.evidence_id}")
    if ablation is Ablation.FULL_JUDGE and assessment is not None:
        if assessment.evidence_coherence in {EvidenceCoherence.MIXED, EvidenceCoherence.CONFLICTING, EvidenceCoherence.INSUFFICIENT}:
            reasons.append(f"coherence:{assessment.evidence_coherence.value}")
        if assessment.behavior_assessment.value == "SUSPICIOUS":
            reasons.append("judge_behavior_suspicious")

    fail_reasons: list[str] = []
    for rec in _in_scope_statuses(doc, ablation):
        if rec.status in _FAIL:
            fail_reasons.append(f"failure:{rec.component.value}:{rec.status.value}")
    if judge_status is not None and judge_status.status in _FAIL:
        fail_reasons.append(f"failure:UNIFIED_JUDGE:{judge_status.status.value}")
    if missing:
        fail_reasons.append("unexpected_missing")

    if reasons or fail_reasons:
        return Phase5Decision(
            doc.document_id, Decision.REVIEW, ablation.value, (),
            tuple(reasons + fail_reasons), missing,
        )
    return Phase5Decision(doc.document_id, Decision.SAFE, ablation.value, (), (), missing)
