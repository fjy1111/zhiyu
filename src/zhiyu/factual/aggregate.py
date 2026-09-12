"""Deterministic claim-level factual relation aggregation."""
from __future__ import annotations
import hashlib
from zhiyu.models.factual import (
    AtomicClaim,
    ComparisonResult,
    ComparisonStatus,
    EvidenceRetrievalResult,
    FactualEvidence,
    FactualRelation,
    PairwiseRelation,
    RetrievalStatus,
    TrustedEvidenceCandidate,
)


def _evidence_id(claim_id: str, relation: str) -> str:
    return hashlib.sha256(f"{claim_id}|{relation}".encode("utf-8")).hexdigest()


def aggregate_claim(
    claim: AtomicClaim,
    retrieval: EvidenceRetrievalResult,
    comparison: ComparisonResult | None,
) -> FactualEvidence | None:
    if retrieval.status is RetrievalStatus.ERROR:
        return None
    if retrieval.status is RetrievalStatus.NO_EVIDENCE:
        return FactualEvidence(
            evidence_id=_evidence_id(claim.claim_id, FactualRelation.INSUFFICIENT_EVIDENCE.value),
            claim_id=claim.claim_id,
            document_id=claim.document_id,
            chunk_id=claim.chunk_id,
            claim_excerpt=claim.excerpt,
            normalized_claim=claim.normalized_claim,
            relation=FactualRelation.INSUFFICIENT_EVIDENCE,
            supporting_reference_ids=(),
            contradicting_reference_ids=(),
            insufficient_reference_ids=(),
            reference_provenance=(),
            aggregation_reason="NO_TRUSTED_EVIDENCE",
        )
    if comparison is None or comparison.status is not ComparisonStatus.OK:
        return None
    supports = tuple(p.reference_id for p in comparison.pairs if p.relation is PairwiseRelation.SUPPORTS)
    contradicts = tuple(p.reference_id for p in comparison.pairs if p.relation is PairwiseRelation.CONTRADICTS)
    not_enough = tuple(p.reference_id for p in comparison.pairs if p.relation is PairwiseRelation.NOT_ENOUGH)
    if supports and not contradicts:
        relation, reason = FactualRelation.SUPPORTED, "SUPPORTS_WITHOUT_CONTRADICTS"
    elif contradicts and not supports:
        relation, reason = FactualRelation.CONTRADICTORY, "CONTRADICTS_WITHOUT_SUPPORTS"
    elif supports and contradicts:
        relation, reason = FactualRelation.INSUFFICIENT_EVIDENCE, "MIXED_SUPPORT_AND_CONTRADICT"
    else:
        relation, reason = FactualRelation.INSUFFICIENT_EVIDENCE, "ALL_NOT_ENOUGH"
    by_id = {item.reference_id: item for item in retrieval.evidence_candidates}
    provenance = tuple(
        {
            "reference_id": item.reference_id,
            "reference_document_id": item.reference_document_id,
            "reference_path": item.reference_path,
            "reference_content_hash": item.reference_content_hash,
            "retrieval_score": item.retrieval_score,
            "span_start": item.span_start,
            "span_end": item.span_end,
        }
        for item in retrieval.evidence_candidates
    )
    return FactualEvidence(
        evidence_id=_evidence_id(claim.claim_id, relation.value),
        claim_id=claim.claim_id,
        document_id=claim.document_id,
        chunk_id=claim.chunk_id,
        claim_excerpt=claim.excerpt,
        normalized_claim=claim.normalized_claim,
        relation=relation,
        supporting_reference_ids=supports,
        contradicting_reference_ids=contradicts,
        insufficient_reference_ids=not_enough,
        reference_provenance=provenance,
        aggregation_reason=reason,
        rationale="; ".join(p.rationale for p in comparison.pairs if p.rationale),
    )
