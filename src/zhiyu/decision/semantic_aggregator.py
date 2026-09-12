"""Document-level discrete table for rule_plus_semantic_baseline."""
from __future__ import annotations
from zhiyu.models.detection import (
    Confidence,
    Decision,
    DetectionResult,
    EventClass,
    Mechanism,
    RuleEvent,
)
from zhiyu.models.semantic import SemanticAnalysisResult, SemanticIntent, SemanticStatus

_POISON_MECHANISMS = {Mechanism.PROMPT_INJECTION, Mechanism.HIDDEN_INSTRUCTION}


def aggregate_rule_plus_semantic(
    document_id: str,
    rule_events: list[RuleEvent] | tuple[RuleEvent, ...],
    semantic_results: list[SemanticAnalysisResult] | tuple[SemanticAnalysisResult, ...],
) -> DetectionResult:
    rules = tuple(rule_events)
    semantics = tuple(semantic_results)
    if any(event.document_id != document_id for event in rules):
        raise ValueError("RuleEvent document_id mismatch")
    if any(result.document_id != document_id for result in semantics):
        raise ValueError("SemanticAnalysisResult document_id mismatch")

    if any(
        event.mechanism in _POISON_MECHANISMS
        and event.event_class is EventClass.MECHANISM
        and event.confidence is Confidence.HIGH
        for event in rules
    ):
        decision = Decision.POISON
    elif any(
        evidence.intent is SemanticIntent.IMPLICIT_CONTROL
        and evidence.mechanism in _POISON_MECHANISMS
        and evidence.confidence is Confidence.HIGH
        for result in semantics
        for evidence in result.behavior_evidence
    ):
        decision = Decision.POISON
    elif (
        rules
        or any(
            result.status in {SemanticStatus.ERROR, SemanticStatus.INVALID_OUTPUT}
            or any(
                evidence.confidence in {Confidence.LOW, Confidence.MEDIUM}
                or evidence.intent is SemanticIntent.UNCERTAIN
                for evidence in result.behavior_evidence
            )
            for result in semantics
        )
    ):
        decision = Decision.REVIEW
    else:
        decision = Decision.SAFE

    return DetectionResult(
        document_id=document_id,
        decision=decision,
        decision_kind="rule_plus_semantic_baseline",
        rule_events=rules,
        semantic_results=semantics,
    )
