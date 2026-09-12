"""Generic lexical retrieval over frozen Phase 4 references. No similarity cutoff."""
from __future__ import annotations
import re
from zhiyu.models.factual import TOP_K, TrustedEvidenceCandidate, EvidenceRetrievalResult, RetrievalStatus, AtomicClaim
from zhiyu.factual.corpus import ReferenceDocument, overlaps

_TOKEN = re.compile(r"\w+", re.UNICODE)


def _grams(text: str) -> set[str]:
    tokens = {token.lower() for token in _TOKEN.findall(text) if token}
    compact = re.sub(r"\s+", "", text)
    grams = {compact[i:i + 2] for i in range(max(0, len(compact) - 1))}
    return tokens | grams


def lexical_score(query: str, document: str) -> float:
    left = _grams(query)
    right = _grams(document)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left)


def retrieve_claim(
    claim: AtomicClaim,
    references: list[ReferenceDocument],
    candidate_id: str,
    candidate_path: str,
    candidate_hash: str,
) -> EvidenceRetrievalResult:
    rejected = 0
    scored: list[tuple[float, ReferenceDocument]] = []
    query = f"{claim.normalized_claim}\n{claim.excerpt}"
    try:
        for ref in references:
            if overlaps(candidate_id, candidate_path, candidate_hash, ref):
                rejected += 1
                continue
            scored.append((lexical_score(query, ref.text), ref))
    except Exception:
        return EvidenceRetrievalResult(claim.claim_id, RetrievalStatus.ERROR, error_code="RETRIEVAL_ERROR")
    scored.sort(key=lambda item: (-item[0], item[1].reference_id))
    chosen = scored[:TOP_K]
    if not chosen:
        return EvidenceRetrievalResult(
            claim.claim_id, RetrievalStatus.NO_EVIDENCE, overlap_rejected=rejected,
        )
    candidates = []
    for score, ref in chosen:
        excerpt = ref.text
        candidates.append(TrustedEvidenceCandidate(
            reference_id=ref.reference_id,
            reference_document_id=ref.document_id,
            reference_path=ref.relative_path,
            reference_content_hash=ref.content_hash,
            retrieval_score=round(score, 6),
            span_start=0,
            span_end=len(excerpt),
            excerpt=excerpt,
        ))
        if excerpt != ref.text[0:len(excerpt)]:
            return EvidenceRetrievalResult(claim.claim_id, RetrievalStatus.ERROR, error_code="SPAN_MISMATCH")
    return EvidenceRetrievalResult(
        claim.claim_id,
        RetrievalStatus.OK,
        evidence_candidates=tuple(candidates),
        overlap_rejected=rejected,
    )
