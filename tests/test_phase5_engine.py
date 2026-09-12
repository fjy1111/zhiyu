from zhiyu.judge.engine import decide, poison_gate_refs
from zhiyu.judge.plan import expected_components, unexpected_missing
from zhiyu.judge.refs import rule_event_ref
from zhiyu.judge.validate import InvalidJudgeOutput, parse_assessment
from zhiyu.models.detection import Confidence, Decision, EventClass, Measurement, Mechanism, RuleEvent
from zhiyu.models.factual import FactualEvidence, FactualRelation
from zhiyu.models.judge import (
    Ablation, AnalysisStatusRecord, Component, DocumentEvidence, EvidenceCoherence,
    RuleEventRecord, StatusKind, UnifiedRiskAssessment, BehaviorAssessment,
    FactualAssessment, Uncertainty,
)
from zhiyu.models.semantic import BehaviorEvidence, SemanticIntent
import json
import pytest


def _rule(**kwargs):
    payload = dict(
        rule_id="pi.instruction_override.en", mechanism=Mechanism.PROMPT_INJECTION,
        event_class=EventClass.MECHANISM, confidence=Confidence.HIGH,
        document_id="d", chunk_id="c0", span_start=0, span_end=5, excerpt="xxxxx",
        rationale="override",
    )
    payload.update(kwargs)
    event = RuleEvent(**payload)
    return RuleEventRecord(rule_event_ref(event), event)


def _beh(**kwargs):
    payload = dict(
        evidence_id="b1", document_id="d", chunk_id="c0",
        intent=SemanticIntent.IMPLICIT_CONTROL, mechanism=Mechanism.HIDDEN_INSTRUCTION,
        confidence=Confidence.HIGH, span_start=0, span_end=5, excerpt="xxxxx",
        rationale="implicit",
    )
    payload.update(kwargs)
    return BehaviorEvidence(**payload)


def _fact(**kwargs):
    payload = dict(
        evidence_id="f1", claim_id="cl1", document_id="d", chunk_id="c0",
        claim_excerpt="opens 09:00", normalized_claim="library opens 09:00",
        relation=FactualRelation.SUPPORTED, supporting_reference_ids=("r1",),
        contradicting_reference_ids=(), insufficient_reference_ids=(),
        reference_provenance=(), aggregation_reason="SUPPORTS_WITHOUT_CONTRADICTS",
    )
    payload.update(kwargs)
    return FactualEvidence(**payload)


def _st(component, status, chunk="c0", **kwargs):
    attempted = status not in {StatusKind.SKIPPED, StatusKind.NO_CLAIM}
    if status is StatusKind.SKIPPED:
        attempted = False
    return AnalysisStatusRecord(component, status, attempted=kwargs.pop("attempted", True if status is not StatusKind.SKIPPED else False), chunk_id=chunk, **kwargs)


def _doc(rules=(), beh=(), facts=(), statuses=None):
    if statuses is None:
        statuses = (
            _st(Component.RULE, StatusKind.OK),
            _st(Component.SEMANTIC, StatusKind.OK),
            _st(Component.FACTUAL_CLAIM, StatusKind.NO_CLAIM, skip_reason=None),
        )
    return DocumentEvidence("d", ("c0",), tuple(rules), tuple(beh), tuple(facts), tuple(statuses))


def test_rule_event_ref_stable_and_span_sensitive():
    a = _rule()
    b = _rule()
    assert a.rule_event_ref == b.rule_event_ref
    c = _rule(span_end=6, excerpt="xxxxxx")
    assert a.rule_event_ref != c.rule_event_ref


def test_poison_from_rule_high_not_canceled_by_supported_or_judge_failure():
    doc = _doc([_rule()], facts=[_fact()])
    result = decide(doc, Ablation.FULL_JUDGE, judge_status=_st(Component.UNIFIED_JUDGE, StatusKind.ERROR, chunk=None))
    assert result.decision is Decision.POISON
    assert poison_gate_refs(doc)


def test_poison_from_behavior_high():
    doc = _doc(beh=[_beh()])
    assert decide(doc, Ablation.FULL_EVIDENCE).decision is Decision.POISON


def test_medium_cannot_accumulate_to_poison():
    events = [_rule(confidence=Confidence.MEDIUM, rule_id=f"pi.x.{i}", span_start=i, span_end=i + 5) for i in range(5)]
    doc = _doc(events)
    assert decide(doc, Ablation.RULE_ONLY).decision is Decision.REVIEW


def test_contradictory_and_insufficient_are_review():
    assert decide(_doc(facts=[_fact(relation=FactualRelation.CONTRADICTORY)]), Ablation.FULL_EVIDENCE).decision is Decision.REVIEW
    assert decide(_doc(facts=[_fact(relation=FactualRelation.INSUFFICIENT_EVIDENCE)]), Ablation.FULL_EVIDENCE).decision is Decision.REVIEW


def test_analyzer_error_review_not_poison():
    statuses = (
        _st(Component.RULE, StatusKind.OK),
        _st(Component.SEMANTIC, StatusKind.ERROR, error_code="TIMEOUT"),
        _st(Component.FACTUAL_CLAIM, StatusKind.NO_CLAIM),
    )
    doc = _doc(statuses=statuses)
    assert decide(doc, Ablation.FULL_EVIDENCE).decision is Decision.REVIEW


def test_clean_path_safe():
    doc = _doc()
    assert decide(doc, Ablation.FULL_EVIDENCE).decision is Decision.SAFE


def test_supported_cannot_cancel_poison():
    doc = _doc([_rule()], facts=[_fact()])
    assert decide(doc, Ablation.FULL_EVIDENCE).decision is Decision.POISON


def test_ablation_omission_is_not_unexpected_missing():
    doc = _doc()
    assert unexpected_missing(doc, Ablation.RULE_ONLY) == ()
    assert Component.UNIFIED_JUDGE not in expected_components(Ablation.FULL_EVIDENCE)
    assert "UNIFIED_JUDGE" not in unexpected_missing(doc, Ablation.FULL_EVIDENCE)


def test_missing_semantic_is_unexpected_for_full():
    statuses = (_st(Component.RULE, StatusKind.OK), _st(Component.FACTUAL_CLAIM, StatusKind.NO_CLAIM))
    doc = _doc(statuses=statuses)
    missing = unexpected_missing(doc, Ablation.FULL_EVIDENCE)
    assert any(item.startswith("SEMANTIC") for item in missing)
    assert decide(doc, Ablation.FULL_EVIDENCE).decision is Decision.REVIEW


def test_judge_invalid_unknown_and_duplicate_refs():
    rec = _rule()
    doc = _doc([rec])
    good = {
        "document_id": "d",
        "cited_rule_event_refs": [rec.rule_event_ref],
        "cited_behavior_evidence_ids": [],
        "cited_factual_evidence_ids": [],
        "behavior_assessment": "NONE",
        "factual_assessment": "NONE",
        "evidence_coherence": "CONSISTENT",
        "uncertainty": "LOW",
        "analyzer_failures": [],
        "rationale": "ok",
    }
    parse_assessment(json.dumps(good), doc)
    with pytest.raises(InvalidJudgeOutput):
        parse_assessment(json.dumps({**good, "cited_rule_event_refs": ["nope"]}), doc)
    with pytest.raises(InvalidJudgeOutput):
        parse_assessment(json.dumps({**good, "cited_rule_event_refs": [rec.rule_event_ref, rec.rule_event_ref]}), doc)
    with pytest.raises(InvalidJudgeOutput):
        parse_assessment(json.dumps({**good, "SAFE": True}), doc)
    other = _rule(document_id="other")
    with pytest.raises(InvalidJudgeOutput):
        parse_assessment(json.dumps({**good, "cited_rule_event_refs": [other.rule_event_ref]}), doc)


def test_judge_only_poison_impossible_without_strong_evidence():
    doc = _doc()
    assessment = UnifiedRiskAssessment(
        "d", (), (), (), BehaviorAssessment.STRONG_CONTROL,
        FactualAssessment.NONE, EvidenceCoherence.CONSISTENT, Uncertainty.LOW, (), "invented",
    )
    result = decide(doc, Ablation.FULL_JUDGE, assessment=assessment)
    assert result.decision is not Decision.POISON
