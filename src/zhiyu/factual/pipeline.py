"""Phase 4 chunk pipeline. No SAFE/REVIEW/POISON mapping."""
from __future__ import annotations
import json
from dataclasses import dataclass
from zhiyu.models.detection import DetectionInput
from zhiyu.models.factual import (
    AtomicClaim,
    ClaimExtractionResult,
    ClaimStatus,
    ComparisonResult,
    ComparisonStatus,
    EvidenceRetrievalResult,
    FactualEvidence,
    RetrievalStatus,
)
from zhiyu.factual.aggregate import aggregate_claim
from zhiyu.factual.claims import InvalidClaimOutput, materialize_claims
from zhiyu.factual.compare import InvalidComparisonOutput, parse_comparisons
from zhiyu.factual.corpus import ReferenceDocument
from zhiyu.factual.prompt import CLAIM_SYSTEM, COMPARE_SYSTEM
from zhiyu.factual.provider import FactualProvider, FactualProviderError
from zhiyu.factual.retrieve import retrieve_claim


@dataclass(frozen=True)
class ChunkFactualResult:
    extraction: ClaimExtractionResult
    retrievals: tuple[EvidenceRetrievalResult, ...]
    comparisons: tuple[ComparisonResult, ...]
    factual_evidence: tuple[FactualEvidence, ...]
    llm_calls: int


class FactualEvidencePipeline:
    def __init__(self, provider: FactualProvider, references: list[ReferenceDocument]):
        self.provider = provider
        self.references = references
        self.llm_calls = 0

    def _chat(self, system: str, user: str) -> str:
        self.llm_calls += 1
        return self.provider.complete(system, user)

    def extract(self, item: DetectionInput) -> ClaimExtractionResult:
        if not isinstance(item, DetectionInput):
            raise TypeError("Claim extractor only accepts DetectionInput")
        try:
            raw = self._chat(CLAIM_SYSTEM, json.dumps({"source_text": item.text}, ensure_ascii=False))
            claims = materialize_claims(item, raw)
        except FactualProviderError as exc:
            return ClaimExtractionResult(item.document_id, item.chunk_id, ClaimStatus.ERROR, error_code=exc.code)
        except InvalidClaimOutput:
            return ClaimExtractionResult(item.document_id, item.chunk_id, ClaimStatus.INVALID_OUTPUT, error_code="INVALID_OUTPUT")
        if not claims:
            return ClaimExtractionResult(item.document_id, item.chunk_id, ClaimStatus.NO_CLAIM)
        return ClaimExtractionResult(item.document_id, item.chunk_id, ClaimStatus.OK, claims=claims)

    def compare_claim(self, claim: AtomicClaim, retrieval: EvidenceRetrievalResult) -> ComparisonResult:
        expected = {item.reference_id for item in retrieval.evidence_candidates}
        payload = {
            "claim_excerpt": claim.excerpt,
            "normalized_claim": claim.normalized_claim,
            "references": [
                {"reference_id": item.reference_id, "excerpt": item.excerpt}
                for item in retrieval.evidence_candidates
            ],
        }
        try:
            raw = self._chat(COMPARE_SYSTEM, json.dumps(payload, ensure_ascii=False))
            pairs = parse_comparisons(raw, expected)
        except FactualProviderError as exc:
            return ComparisonResult(claim.claim_id, ComparisonStatus.ERROR, error_code=exc.code)
        except InvalidComparisonOutput:
            return ComparisonResult(claim.claim_id, ComparisonStatus.INVALID_OUTPUT, error_code="INVALID_OUTPUT")
        return ComparisonResult(claim.claim_id, ComparisonStatus.OK, pairs=pairs)

    def process_chunk(
        self,
        item: DetectionInput,
        candidate_path: str = "",
        candidate_hash: str = "",
    ) -> ChunkFactualResult:
        before = self.llm_calls
        extraction = self.extract(item)
        retrievals: list[EvidenceRetrievalResult] = []
        comparisons: list[ComparisonResult] = []
        evidences: list[FactualEvidence] = []
        if extraction.status is ClaimStatus.OK:
            for claim in extraction.claims:
                retrieval = retrieve_claim(
                    claim, self.references, item.document_id, candidate_path, candidate_hash,
                )
                retrievals.append(retrieval)
                comparison = None
                if retrieval.status is RetrievalStatus.OK:
                    comparison = self.compare_claim(claim, retrieval)
                    comparisons.append(comparison)
                evidence = aggregate_claim(claim, retrieval, comparison)
                if evidence is not None:
                    evidences.append(evidence)
        return ChunkFactualResult(
            extraction=extraction,
            retrievals=tuple(retrievals),
            comparisons=tuple(comparisons),
            factual_evidence=tuple(evidences),
            llm_calls=self.llm_calls - before,
        )
