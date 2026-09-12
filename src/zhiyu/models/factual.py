from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from zhiyu.models.detection import DetectionInput

MAX_CLAIMS = 3
TOP_K = 3
MAX_CLAIM_EXCERPT = 240
MAX_NORMALIZED_CLAIM = 400


class ClaimStatus(str, Enum):
    OK = "OK"
    NO_CLAIM = "NO_CLAIM"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    ERROR = "ERROR"


class RetrievalStatus(str, Enum):
    OK = "OK"
    NO_EVIDENCE = "NO_EVIDENCE"
    ERROR = "ERROR"


class PairwiseRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NOT_ENOUGH = "NOT_ENOUGH"


class FactualRelation(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTORY = "CONTRADICTORY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ComparisonStatus(str, Enum):
    OK = "OK"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    ERROR = "ERROR"


@dataclass(frozen=True)
class CandidateIdentity:
    document_id: str
    relative_path: str
    content_hash: str


@dataclass(frozen=True)
class ClaimDraft:
    excerpt: str
    normalized_claim: str
    claim_type: str | None = None
    rationale: str = ""


@dataclass(frozen=True)
class AtomicClaim:
    claim_id: str
    document_id: str
    chunk_id: str
    span_start: int
    span_end: int
    excerpt: str
    normalized_claim: str
    claim_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "excerpt": self.excerpt,
            "normalized_claim": self.normalized_claim,
            "claim_type": self.claim_type,
        }


@dataclass(frozen=True)
class ClaimExtractionResult:
    document_id: str
    chunk_id: str
    status: ClaimStatus
    claims: tuple[AtomicClaim, ...] = ()
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "status": self.status.value,
            "error_code": self.error_code,
            "claims": [claim.to_dict() for claim in self.claims],
        }


@dataclass(frozen=True)
class TrustedEvidenceCandidate:
    reference_id: str
    reference_document_id: str
    reference_path: str
    reference_content_hash: str
    retrieval_score: float
    span_start: int
    span_end: int
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_document_id": self.reference_document_id,
            "reference_path": self.reference_path,
            "reference_content_hash": self.reference_content_hash,
            "retrieval_score": self.retrieval_score,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True)
class EvidenceRetrievalResult:
    claim_id: str
    status: RetrievalStatus
    evidence_candidates: tuple[TrustedEvidenceCandidate, ...] = ()
    overlap_rejected: int = 0
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status.value,
            "overlap_rejected": self.overlap_rejected,
            "error_code": self.error_code,
            "evidence_candidates": [item.to_dict() for item in self.evidence_candidates],
        }


@dataclass(frozen=True)
class PairwiseComparison:
    reference_id: str
    relation: PairwiseRelation
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "relation": self.relation.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ComparisonResult:
    claim_id: str
    status: ComparisonStatus
    pairs: tuple[PairwiseComparison, ...] = ()
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status.value,
            "error_code": self.error_code,
            "pairs": [item.to_dict() for item in self.pairs],
        }


@dataclass(frozen=True)
class FactualEvidence:
    evidence_id: str
    claim_id: str
    document_id: str
    chunk_id: str
    claim_excerpt: str
    normalized_claim: str
    relation: FactualRelation
    supporting_reference_ids: tuple[str, ...]
    contradicting_reference_ids: tuple[str, ...]
    insufficient_reference_ids: tuple[str, ...]
    reference_provenance: tuple[dict[str, Any], ...]
    aggregation_reason: str
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim_id": self.claim_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "claim_excerpt": self.claim_excerpt,
            "normalized_claim": self.normalized_claim,
            "relation": self.relation.value,
            "supporting_reference_ids": list(self.supporting_reference_ids),
            "contradicting_reference_ids": list(self.contradicting_reference_ids),
            "insufficient_reference_ids": list(self.insufficient_reference_ids),
            "reference_provenance": list(self.reference_provenance),
            "aggregation_reason": self.aggregation_reason,
            "rationale": self.rationale,
        }
