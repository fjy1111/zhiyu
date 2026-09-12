from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Mechanism(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    HIDDEN_INSTRUCTION = "HIDDEN_INSTRUCTION"
    FACT_TAMPERING = "FACT_TAMPERING"
    KNOWLEDGE_CONFLICT = "KNOWLEDGE_CONFLICT"
    RETRIEVAL_HIJACKING = "RETRIEVAL_HIJACKING"


class EventClass(str, Enum):
    MECHANISM = "MECHANISM"
    STATISTICAL = "STATISTICAL"


class Confidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Decision(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    POISON = "POISON"


@dataclass(frozen=True)
class RuntimeContext:
    request_id: str | None = None
    file_format: str | None = None


@dataclass(frozen=True)
class DetectionInput:
    document_id: str
    chunk_id: str
    text: str
    runtime: RuntimeContext | None = None

    def __post_init__(self):
        if self.runtime is not None and not isinstance(self.runtime, RuntimeContext):
            raise TypeError("runtime must be RuntimeContext")

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Measurement:
    name: str
    value: float
    threshold: float

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "threshold": self.threshold}


@dataclass(frozen=True)
class RuleEvent:
    rule_id: str
    mechanism: Mechanism
    event_class: EventClass
    confidence: Confidence
    document_id: str
    chunk_id: str
    span_start: int
    span_end: int
    excerpt: str
    rationale: str
    measurement: Measurement | None = None

    def __post_init__(self):
        if not isinstance(self.mechanism, Mechanism):
            raise TypeError("mechanism must be Mechanism")
        if not isinstance(self.event_class, EventClass):
            raise TypeError("event_class must be EventClass")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be Confidence")
        if self.span_start < 0 or self.span_end <= self.span_start:
            raise ValueError("invalid span")
        if not self.excerpt:
            raise ValueError("excerpt must be non-empty")
        if self.span_end - self.span_start != len(self.excerpt):
            raise ValueError("excerpt length must match span")
        if self.event_class is EventClass.MECHANISM and self.measurement is not None:
            raise ValueError("MECHANISM events cannot carry measurement")
        if self.event_class is EventClass.STATISTICAL and self.mechanism is not Mechanism.RETRIEVAL_HIJACKING:
            raise ValueError("STATISTICAL events must use RETRIEVAL_HIJACKING in Phase 2")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "rule_id": self.rule_id,
            "mechanism": self.mechanism.value,
            "event_class": self.event_class.value,
            "confidence": self.confidence.value,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "excerpt": self.excerpt,
            "rationale": self.rationale,
            "measurement": None if self.measurement is None else self.measurement.to_dict(),
        }
        return payload


ALLOWED_DECISION_KINDS = frozenset({
    "rule_only_baseline",
    "rule_plus_semantic_baseline",
})


@dataclass(frozen=True)
class DetectionResult:
    document_id: str
    decision: Decision
    decision_kind: str
    rule_events: tuple[RuleEvent, ...]
    semantic_results: tuple[Any, ...] = ()

    def __post_init__(self):
        if not isinstance(self.decision, Decision):
            raise TypeError("decision must be Decision")
        if self.decision_kind not in ALLOWED_DECISION_KINDS:
            raise ValueError("unsupported decision_kind")
        if any(event.document_id != self.document_id for event in self.rule_events):
            raise ValueError("rule_events document_id mismatch")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "document_id": self.document_id,
            "decision": self.decision.value,
            "decision_kind": self.decision_kind,
            "rule_events": [event.to_dict() for event in self.rule_events],
        }
        if self.semantic_results:
            payload["semantic_results"] = [
                result.to_dict() if hasattr(result, "to_dict") else result
                for result in self.semantic_results
            ]
        return payload
