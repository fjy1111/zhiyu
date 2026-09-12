from zhiyu.decision.semantic_aggregator import aggregate_rule_plus_semantic
from zhiyu.models.detection import (
    Confidence, Decision, EventClass, Measurement, Mechanism, RuleEvent,
)
from zhiyu.models.semantic import (
    SKIP_RULE_HIGH, BehaviorEvidence, SemanticAnalysisResult, SemanticIntent, SemanticStatus,
)


def _rule(**kwargs):
    payload = dict(
        rule_id="pi.instruction_override.en",
        mechanism=Mechanism.PROMPT_INJECTION,
        event_class=EventClass.MECHANISM,
        confidence=Confidence.HIGH,
        document_id="d", chunk_id="c", span_start=0, span_end=5, excerpt="xxxxx",
        rationale="instruction-override",
    )
    payload.update(kwargs)
    return RuleEvent(**payload)


def _evidence(**kwargs):
    payload = dict(
        evidence_id="e", document_id="d", chunk_id="c",
        intent=SemanticIntent.IMPLICIT_CONTROL,
        mechanism=Mechanism.HIDDEN_INSTRUCTION,
        confidence=Confidence.HIGH,
        span_start=0, span_end=5, excerpt="xxxxx", rationale="implicit control",
    )
    payload.update(kwargs)
    return BehaviorEvidence(**payload)


def test_rule_high_poisons_and_cannot_be_downgraded():
    skipped = SemanticAnalysisResult(
        "d", "c", SemanticStatus.SKIPPED, skip_reason=SKIP_RULE_HIGH,
    )
    result = aggregate_rule_plus_semantic("d", [_rule()], [skipped])
    assert result.decision is Decision.POISON
    assert result.decision_kind == "rule_plus_semantic_baseline"


def test_semantic_high_poisons_without_rules():
    ok = SemanticAnalysisResult("d", "c", SemanticStatus.OK, behavior_evidence=(_evidence(),))
    result = aggregate_rule_plus_semantic("d", [], [ok])
    assert result.decision is Decision.POISON


def test_medium_semantic_does_not_stack_to_poison():
    items = tuple(
        _evidence(evidence_id=str(i), confidence=Confidence.MEDIUM, span_start=i, span_end=i + 5)
        for i in range(3)
    )
    ok = SemanticAnalysisResult("d", "c", SemanticStatus.OK, behavior_evidence=items)
    assert aggregate_rule_plus_semantic("d", [], [ok]).decision is Decision.REVIEW


def test_error_and_invalid_are_review_not_safe_or_poison():
    err = SemanticAnalysisResult("d", "c", SemanticStatus.ERROR, error_code="TIMEOUT")
    inv = SemanticAnalysisResult("d", "c2", SemanticStatus.INVALID_OUTPUT, error_code="INVALID_OUTPUT")
    assert aggregate_rule_plus_semantic("d", [], [err]).decision is Decision.REVIEW
    assert aggregate_rule_plus_semantic("d", [], [inv]).decision is Decision.REVIEW


def test_ok_no_control_without_rules_is_safe():
    ok = SemanticAnalysisResult("d", "c", SemanticStatus.OK, behavior_evidence=())
    assert aggregate_rule_plus_semantic("d", [], [ok]).decision is Decision.SAFE


def test_no_control_does_not_erase_statistical_rule():
    stat = _rule(
        rule_id="rh.line_repetition",
        mechanism=Mechanism.RETRIEVAL_HIJACKING,
        event_class=EventClass.STATISTICAL,
        confidence=Confidence.HIGH,
        measurement=Measurement("repetition_ratio", 0.8, 0.5),
    )
    ok = SemanticAnalysisResult("d", "c", SemanticStatus.OK, behavior_evidence=())
    assert aggregate_rule_plus_semantic("d", [stat], [ok]).decision is Decision.REVIEW


def test_uncertain_is_review():
    ok = SemanticAnalysisResult(
        "d", "c", SemanticStatus.OK,
        behavior_evidence=(_evidence(intent=SemanticIntent.UNCERTAIN, mechanism=None, confidence=Confidence.LOW),),
    )
    assert aggregate_rule_plus_semantic("d", [], [ok]).decision is Decision.REVIEW
