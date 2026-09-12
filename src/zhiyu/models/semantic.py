from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from zhiyu.models.detection import Confidence, DetectionInput, Mechanism, RuleEvent


class SemanticIntent(str, Enum):
    IMPLICIT_CONTROL = "IMPLICIT_CONTROL"
    NO_CONTROL = "NO_CONTROL"
    UNCERTAIN = "UNCERTAIN"


class SemanticStatus(str, Enum):
    OK = "OK"
    SKIPPED = "SKIPPED"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    ERROR = "ERROR"


SKIP_RULE_HIGH = "RULE_HIGH_ALREADY_SUFFICIENT"
MAX_DRAFTS = 3
MAX_EXCERPT = 240


@dataclass(frozen=True)
class SemanticAnalysisInput:
    detection_input: DetectionInput
    rule_events: tuple[RuleEvent, ...] = ()

    def __post_init__(self):
        if not isinstance(self.detection_input, DetectionInput):
            raise TypeError("detection_input must be DetectionInput")
        document_id = self.detection_input.document_id
        chunk_id = self.detection_input.chunk_id
        for event in self.rule_events:
            if event.document_id != document_id or event.chunk_id != chunk_id:
                raise ValueError("rule_events must belong to the current chunk")

    def to_dict(self) -> dict[str, Any]:
        return {
            "detection_input": self.detection_input.to_dict(),
            "rule_events": [event.to_dict() for event in self.rule_events],
        }


@dataclass(frozen=True)
class SemanticObservationDraft:
    intent: SemanticIntent
    mechanism: Mechanism | None
    confidence: Confidence
    excerpt: str
    rationale: str
    source_rule_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class BehaviorEvidence:
    evidence_id: str
    document_id: str
    chunk_id: str
    intent: SemanticIntent
    mechanism: Mechanism | None
    confidence: Confidence
    span_start: int
    span_end: int
    excerpt: str
    rationale: str
    source_rule_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if self.intent is SemanticIntent.NO_CONTROL:
            raise ValueError("NO_CONTROL must not become BehaviorEvidence")
        if self.intent is SemanticIntent.IMPLICIT_CONTROL and self.mechanism not in {
            Mechanism.PROMPT_INJECTION,
            Mechanism.HIDDEN_INSTRUCTION,
        }:
            raise ValueError("IMPLICIT_CONTROL requires PI or HI")
        if self.mechanism in {Mechanism.FACT_TAMPERING, Mechanism.KNOWLEDGE_CONFLICT, Mechanism.RETRIEVAL_HIJACKING}:
            raise ValueError("semantic behavior evidence cannot use factual/retrieval mechanisms")
        if self.span_end - self.span_start != len(self.excerpt):
            raise ValueError("excerpt length must match span")

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "intent": self.intent.value,
            "mechanism": None if self.mechanism is None else self.mechanism.value,
            "confidence": self.confidence.value,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "excerpt": self.excerpt,
            "rationale": self.rationale,
            "source_rule_ids": list(self.source_rule_ids),
        }


@dataclass(frozen=True)
class SemanticAnalysisResult:
    document_id: str
    chunk_id: str
    status: SemanticStatus
    behavior_evidence: tuple[BehaviorEvidence, ...] = ()
    skip_reason: str | None = None
    error_code: str | None = None

    def __post_init__(self):
        if self.status is SemanticStatus.SKIPPED and not self.skip_reason:
            raise ValueError("SKIPPED requires skip_reason")
        if self.status in {SemanticStatus.INVALID_OUTPUT, SemanticStatus.SKIPPED, SemanticStatus.ERROR}:
            if self.behavior_evidence:
                raise ValueError("non-OK status cannot carry behavior_evidence")
        if self.status is SemanticStatus.OK and self.skip_reason:
            raise ValueError("OK cannot carry skip_reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "status": self.status.value,
            "skip_reason": self.skip_reason,
            "error_code": self.error_code,
            "behavior_evidence": [item.to_dict() for item in self.behavior_evidence],
        }
