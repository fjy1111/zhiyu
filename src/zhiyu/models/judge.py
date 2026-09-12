from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from zhiyu.models.detection import Decision, RuleEvent
from zhiyu.models.factual import FactualEvidence
from zhiyu.models.semantic import BehaviorEvidence

RULE_EVENT_REF_VERSION = "phase5.rule_event_ref.v1"
EXECUTION_PLAN_VERSION = "phase5.execution_plan.v1"
DECISION_POLICY_VERSION = "phase5.risk_engine.v1"
JUDGE_PROMPT_VERSION = "phase5.judge.v1"


class Ablation(str, Enum):
    RULE_ONLY = "rule_only_baseline"
    RULE_SEMANTIC = "rule_plus_semantic_baseline"
    FULL_EVIDENCE = "full_evidence_no_judge"
    FULL_JUDGE = "full_judge"


class Component(str, Enum):
    RULE = "RULE"
    SEMANTIC = "SEMANTIC"
    FACTUAL_CLAIM = "FACTUAL_CLAIM"
    FACTUAL_RETRIEVAL = "FACTUAL_RETRIEVAL"
    FACTUAL_COMPARE = "FACTUAL_COMPARE"
    UNIFIED_JUDGE = "UNIFIED_JUDGE"


class StatusKind(str, Enum):
    OK = "OK"
    SKIPPED = "SKIPPED"
    NO_CLAIM = "NO_CLAIM"
    NO_EVIDENCE = "NO_EVIDENCE"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    ERROR = "ERROR"


class BehaviorAssessment(str, Enum):
    NONE = "NONE"
    SUSPICIOUS = "SUSPICIOUS"
    STRONG_CONTROL = "STRONG_CONTROL"


class FactualAssessment(str, Enum):
    NONE = "NONE"
    SUPPORTED_ONLY = "SUPPORTED_ONLY"
    CONTRADICTION_PRESENT = "CONTRADICTION_PRESENT"
    INSUFFICIENT_OR_MIXED = "INSUFFICIENT_OR_MIXED"


class EvidenceCoherence(str, Enum):
    CONSISTENT = "CONSISTENT"
    MIXED = "MIXED"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT = "INSUFFICIENT"


class Uncertainty(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class AnalysisStatusRecord:
    component: Component
    status: StatusKind
    attempted: bool
    skip_reason: str | None = None
    error_code: str | None = None
    chunk_id: str | None = None
    claim_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component.value,
            "status": self.status.value,
            "attempted": self.attempted,
            "skip_reason": self.skip_reason,
            "error_code": self.error_code,
            "chunk_id": self.chunk_id,
            "claim_id": self.claim_id,
        }


@dataclass(frozen=True)
class RuleEventRecord:
    rule_event_ref: str
    event: RuleEvent

    def to_dict(self) -> dict[str, Any]:
        return {"rule_event_ref": self.rule_event_ref, "event": self.event.to_dict()}


@dataclass(frozen=True)
class UnifiedRiskAssessment:
    document_id: str
    cited_rule_event_refs: tuple[str, ...]
    cited_behavior_evidence_ids: tuple[str, ...]
    cited_factual_evidence_ids: tuple[str, ...]
    behavior_assessment: BehaviorAssessment
    factual_assessment: FactualAssessment
    evidence_coherence: EvidenceCoherence
    uncertainty: Uncertainty
    analyzer_failures: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "cited_rule_event_refs": list(self.cited_rule_event_refs),
            "cited_behavior_evidence_ids": list(self.cited_behavior_evidence_ids),
            "cited_factual_evidence_ids": list(self.cited_factual_evidence_ids),
            "behavior_assessment": self.behavior_assessment.value,
            "factual_assessment": self.factual_assessment.value,
            "evidence_coherence": self.evidence_coherence.value,
            "uncertainty": self.uncertainty.value,
            "analyzer_failures": list(self.analyzer_failures),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class Phase5Decision:
    document_id: str
    decision: Decision
    decision_kind: str
    poison_gate_refs: tuple[str, ...]
    review_reasons: tuple[str, ...]
    unexpected_missing: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "decision": self.decision.value,
            "decision_kind": self.decision_kind,
            "poison_gate_refs": list(self.poison_gate_refs),
            "review_reasons": list(self.review_reasons),
            "unexpected_missing": list(self.unexpected_missing),
        }


@dataclass(frozen=True)
class DocumentEvidence:
    document_id: str
    expected_chunk_ids: tuple[str, ...]
    rule_events: tuple[RuleEventRecord, ...]
    behavior_evidence: tuple[BehaviorEvidence, ...]
    factual_evidence: tuple[FactualEvidence, ...]
    statuses: tuple[AnalysisStatusRecord, ...]

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "expected_chunk_ids": list(self.expected_chunk_ids),
            "rule_events": [item.to_dict() for item in self.rule_events],
            "behavior_evidence": [item.to_dict() for item in self.behavior_evidence],
            "factual_evidence": [item.to_dict() for item in self.factual_evidence],
            "statuses": [item.to_dict() for item in self.statuses],
        }
