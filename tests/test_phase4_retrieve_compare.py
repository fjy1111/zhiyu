import json
from zhiyu.factual.aggregate import aggregate_claim
from zhiyu.factual.compare import InvalidComparisonOutput, parse_comparisons
from zhiyu.factual.corpus import ReferenceDocument
from zhiyu.factual.retrieve import retrieve_claim
from zhiyu.models.factual import (
    AtomicClaim, ComparisonResult, ComparisonStatus, EvidenceRetrievalResult,
    FactualRelation, PairwiseComparison, PairwiseRelation, RetrievalStatus,
    TrustedEvidenceCandidate,
)
import pytest


def _claim():
    return AtomicClaim("cid", "cand", "c", 0, 5, "09:00", "library opens 09:00")


def _ref(i, text, path=None, digest=None):
    return ReferenceDocument(
        reference_id=f"ref{i}", document_id=f"d{i}", relative_path=path or f"p{i}",
        content_hash=digest or f"h{i}", text=text,
    )


def test_topk_and_overlap_filter():
    refs = [_ref(1, "library opens 09:00"), _ref(2, "unrelated weather report"), _ref(3, "library opens 09:00")]
    result = retrieve_claim(_claim(), refs, "cand", "path", "hash")
    assert result.status is RetrievalStatus.OK
    assert len(result.evidence_candidates) <= 3


def test_overlap_id_path_hash_and_all_filtered():
    refs = [_ref(1, "library opens 09:00", path="same", digest="hh")]
    by_id = retrieve_claim(_claim(), refs, "d1", "x", "y")
    assert by_id.status is RetrievalStatus.NO_EVIDENCE
    by_path = retrieve_claim(_claim(), refs, "z", "same", "y")
    assert by_path.status is RetrievalStatus.NO_EVIDENCE
    by_hash = retrieve_claim(_claim(), refs, "z", "x", "hh")
    assert by_hash.status is RetrievalStatus.NO_EVIDENCE
    assert by_id.overlap_rejected == 1


def test_parse_comparisons_cases():
    expected = {"r1", "r2"}
    raw = json.dumps({"comparisons": [
        {"reference_id": "r1", "relation": "SUPPORTS", "rationale": "a"},
        {"reference_id": "r2", "relation": "NOT_ENOUGH", "rationale": "b"},
    ]})
    pairs = parse_comparisons(raw, expected)
    assert {p.reference_id for p in pairs} == expected
    with pytest.raises(InvalidComparisonOutput):
        parse_comparisons(json.dumps({"comparisons": [{"reference_id": "nope", "relation": "SUPPORTS", "rationale": "x"}]}), expected)
    with pytest.raises(InvalidComparisonOutput):
        parse_comparisons(json.dumps({"comparisons": [
            {"reference_id": "r1", "relation": "SUPPORTS", "rationale": "a"},
            {"reference_id": "r1", "relation": "NOT_ENOUGH", "rationale": "b"},
        ]}), expected)
    with pytest.raises(InvalidComparisonOutput):
        parse_comparisons(json.dumps({"comparisons": [
            {"reference_id": "r1", "relation": "SUPPORTS", "rationale": "a"},
        ]}), expected)
    with pytest.raises(InvalidComparisonOutput):
        parse_comparisons("not-json", expected)


def _cand(ref="r1"):
    return TrustedEvidenceCandidate(ref, "d", "p", "h", 0.1, 0, 5, "09:00")


def _cmp(pairs, status=ComparisonStatus.OK):
    return ComparisonResult("cid", status, pairs=tuple(pairs))


def _ret(status=RetrievalStatus.OK, cands=(_cand(),)):
    return EvidenceRetrievalResult("cid", status, evidence_candidates=tuple(cands))


def test_aggregation_table():
    claim = _claim()
    support = PairwiseComparison("r1", PairwiseRelation.SUPPORTS, "s")
    contra = PairwiseComparison("r2", PairwiseRelation.CONTRADICTS, "c")
    none = PairwiseComparison("r3", PairwiseRelation.NOT_ENOUGH, "n")
    assert aggregate_claim(claim, _ret(), _cmp([support])).relation is FactualRelation.SUPPORTED
    assert aggregate_claim(claim, _ret(), _cmp([contra])).relation is FactualRelation.CONTRADICTORY
    assert aggregate_claim(claim, _ret(), _cmp([none])).relation is FactualRelation.INSUFFICIENT_EVIDENCE
    mixed = aggregate_claim(claim, _ret(cands=(_cand("r1"), _cand("r2"))), _cmp([support, contra]))
    assert mixed.relation is FactualRelation.INSUFFICIENT_EVIDENCE
    none_ev = aggregate_claim(claim, _ret(RetrievalStatus.NO_EVIDENCE, ()), None)
    assert none_ev.relation is FactualRelation.INSUFFICIENT_EVIDENCE
    assert none_ev.aggregation_reason == "NO_TRUSTED_EVIDENCE"
    assert aggregate_claim(claim, _ret(RetrievalStatus.ERROR, ()), None) is None
    assert aggregate_claim(claim, _ret(), _cmp([], ComparisonStatus.ERROR)) is None


def test_traceability_spans():
    claim = _claim()
    text = "library opens 09:00"
    assert text[0:len(text)] == text
    ev = aggregate_claim(claim, _ret(), _cmp([PairwiseComparison("r1", PairwiseRelation.SUPPORTS, "s")]))
    assert ev.claim_excerpt == claim.excerpt
    assert ev.reference_provenance[0]["reference_id"] == "r1"
