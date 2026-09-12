"""Chunk-level semantic analyzer with invocation gate."""
from __future__ import annotations
from zhiyu.models.detection import Confidence, EventClass, Mechanism, RuleEvent
from zhiyu.models.semantic import (
    SKIP_RULE_HIGH,
    SemanticAnalysisInput,
    SemanticAnalysisResult,
    SemanticStatus,
)
from zhiyu.semantic.provider import SemanticProvider, SemanticProviderError
from zhiyu.semantic.validate import InvalidSemanticOutput, materialize_behavior_evidence


def should_skip(rule_events: tuple[RuleEvent, ...] | list[RuleEvent]) -> bool:
    return any(
        event.mechanism in {Mechanism.PROMPT_INJECTION, Mechanism.HIDDEN_INSTRUCTION}
        and event.event_class is EventClass.MECHANISM
        and event.confidence is Confidence.HIGH
        for event in rule_events
    )


def _observation_context(rule_events: tuple[RuleEvent, ...]) -> list[dict]:
    return [
        {
            "rule_id": event.rule_id,
            "mechanism": event.mechanism.value,
            "event_class": event.event_class.value,
            "confidence": event.confidence.value,
            "excerpt": event.excerpt,
            "rationale": event.rationale,
        }
        for event in rule_events
    ]


class SemanticAnalyzer:
    def __init__(self, provider: SemanticProvider):
        self.provider = provider

    def analyze(self, analysis_input: SemanticAnalysisInput) -> SemanticAnalysisResult:
        if not isinstance(analysis_input, SemanticAnalysisInput):
            raise TypeError("SemanticAnalyzer only accepts SemanticAnalysisInput")
        document_id = analysis_input.detection_input.document_id
        chunk_id = analysis_input.detection_input.chunk_id
        if should_skip(analysis_input.rule_events):
            return SemanticAnalysisResult(
                document_id=document_id,
                chunk_id=chunk_id,
                status=SemanticStatus.SKIPPED,
                skip_reason=SKIP_RULE_HIGH,
            )
        try:
            raw = self.provider.complete(
                analysis_input.detection_input.text,
                _observation_context(analysis_input.rule_events),
            )
            evidence = materialize_behavior_evidence(analysis_input, raw)
        except SemanticProviderError as exc:
            return SemanticAnalysisResult(
                document_id=document_id,
                chunk_id=chunk_id,
                status=SemanticStatus.ERROR,
                error_code=exc.code,
            )
        except InvalidSemanticOutput:
            return SemanticAnalysisResult(
                document_id=document_id,
                chunk_id=chunk_id,
                status=SemanticStatus.INVALID_OUTPUT,
                error_code="INVALID_OUTPUT",
            )
        return SemanticAnalysisResult(
            document_id=document_id,
            chunk_id=chunk_id,
            status=SemanticStatus.OK,
            behavior_evidence=evidence,
        )
