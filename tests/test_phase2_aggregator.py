from zhiyu.decision.aggregator import aggregate
from zhiyu.models.detection import (
    Confidence,
    Decision,
    EventClass,
    Measurement,
    Mechanism,
    RuleEvent,
)


def _event(**kwargs):
    payload = dict(
        rule_id="pi.instruction_override.en",
        mechanism=Mechanism.PROMPT_INJECTION,
        event_class=EventClass.MECHANISM,
        confidence=Confidence.HIGH,
        document_id="d",
        chunk_id="c",
        span_start=0,
        span_end=5,
        excerpt="xxxxx",
        rationale="instruction-override mechanism",
    )
    payload.update(kwargs)
    return RuleEvent(**payload)


def test_no_events_safe():
    assert aggregate("d", []).decision is Decision.SAFE


def test_rh_high_review():
    event = _event(
        rule_id="rh.line_repetition",
        mechanism=Mechanism.RETRIEVAL_HIJACKING,
        event_class=EventClass.STATISTICAL,
        confidence=Confidence.HIGH,
        measurement=Measurement("repetition_ratio", 0.8, 0.5),
    )
    result = aggregate("d", [event])
    assert result.decision is Decision.REVIEW
    assert result.decision_kind == "rule_only_baseline"


def test_three_rh_high_still_review():
    events = [
        _event(
            rule_id=f"rh.{i}",
            mechanism=Mechanism.RETRIEVAL_HIJACKING,
            event_class=EventClass.STATISTICAL,
            confidence=Confidence.HIGH,
            measurement=Measurement("repetition_ratio", 0.9, 0.5),
        )
        for i in range(3)
    ]
    assert aggregate("d", events).decision is Decision.REVIEW


def test_medium_injection_review():
    event = _event(confidence=Confidence.MEDIUM)
    assert aggregate("d", [event]).decision is Decision.REVIEW


def test_medium_plus_rh_review():
    events = [
        _event(confidence=Confidence.MEDIUM),
        _event(
            rule_id="rh.term_concentration",
            mechanism=Mechanism.RETRIEVAL_HIJACKING,
            event_class=EventClass.STATISTICAL,
            confidence=Confidence.HIGH,
            measurement=Measurement("term_concentration", 0.5, 0.28),
        ),
    ]
    assert aggregate("d", events).decision is Decision.REVIEW


def test_one_high_injection_poison():
    assert aggregate("d", [_event()]).decision is Decision.POISON


def test_hidden_high_with_stats_poison():
    events = [
        _event(rule_id="hi.html_comment", mechanism=Mechanism.HIDDEN_INSTRUCTION),
        _event(
            rule_id="rh.ngram_dominance",
            mechanism=Mechanism.RETRIEVAL_HIJACKING,
            event_class=EventClass.STATISTICAL,
            confidence=Confidence.HIGH,
            measurement=Measurement("ngram_dominance", 0.4, 0.22),
        ),
    ]
    assert aggregate("d", events).decision is Decision.POISON


def test_no_score_accumulation():
    lows = [_event(confidence=Confidence.LOW, rule_id=f"pi.low.{i}") for i in range(5)]
    assert aggregate("d", lows).decision is Decision.REVIEW
