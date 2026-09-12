"""Document-level discrete decision table for the rule-only baseline."""
from __future__ import annotations
from zhiyu.models.detection import (
    Confidence,
    Decision,
    DetectionResult,
    EventClass,
    Mechanism,
    RuleEvent,
)

_POISON_MECHANISMS = {Mechanism.PROMPT_INJECTION, Mechanism.HIDDEN_INSTRUCTION}


def aggregate(document_id: str, events: list[RuleEvent] | tuple[RuleEvent, ...]) -> DetectionResult:
    ordered = tuple(events)
    if any(event.document_id != document_id for event in ordered):
        raise ValueError("RuleEvent document_id mismatch")
    if not ordered:
        decision = Decision.SAFE
    elif any(
        event.mechanism in _POISON_MECHANISMS
        and event.event_class is EventClass.MECHANISM
        and event.confidence is Confidence.HIGH
        for event in ordered
    ):
        decision = Decision.POISON
    else:
        decision = Decision.REVIEW
    return DetectionResult(
        document_id=document_id,
        decision=decision,
        decision_kind="rule_only_baseline",
        rule_events=ordered,
    )
