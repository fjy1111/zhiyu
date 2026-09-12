import json
import pytest
from zhiyu.models.detection import DetectionInput
from zhiyu.models.factual import ClaimStatus
from zhiyu.factual.claims import InvalidClaimOutput, materialize_claims
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.provider import MockFactualProvider


def _item(text="The library opens at 09:00 every weekday."):
    return DetectionInput("d", "c", text)


def test_valid_unique_excerpt():
    text = "The library opens at 09:00 every weekday."
    raw = json.dumps({"status": "OK", "claims": [{
        "excerpt": "The library opens at 09:00",
        "normalized_claim": "The library opening time is 09:00",
        "claim_type": None, "rationale": "time",
    }]})
    claims = materialize_claims(_item(text), raw)
    assert len(claims) == 1
    assert text[claims[0].span_start:claims[0].span_end] == claims[0].excerpt


def test_absent_and_duplicate_excerpt_invalid():
    with pytest.raises(InvalidClaimOutput):
        materialize_claims(_item(), json.dumps({"status": "OK", "claims": [{
            "excerpt": "missing", "normalized_claim": "x",
        }]}))
    text = "open open"
    with pytest.raises(InvalidClaimOutput):
        materialize_claims(_item(text), json.dumps({"status": "OK", "claims": [{
            "excerpt": "open", "normalized_claim": "it is open",
        }]}))


def test_no_claim_status():
    claims = materialize_claims(_item(), json.dumps({"status": "NO_CLAIM", "claims": []}))
    assert claims == ()


def test_empty_ok_claims_invalid():
    with pytest.raises(InvalidClaimOutput):
        materialize_claims(_item(), json.dumps({"status": "OK", "claims": []}))


def test_malformed_and_too_many():
    with pytest.raises(InvalidClaimOutput):
        materialize_claims(_item(), "not-json")
    claims = [{
        "excerpt": f"The library opens at 09:0{i}",
        "normalized_claim": f"t{i}",
    } for i in range(4)]
    with pytest.raises(InvalidClaimOutput):
        materialize_claims(_item("The library opens at 09:00 extra"), json.dumps({"status": "OK", "claims": claims}))


def test_all_or_nothing_second_bad():
    text = "Alpha fact is 1. Unique closing time is 18:00."
    raw = json.dumps({"status": "OK", "claims": [
        {"excerpt": "Alpha fact is 1", "normalized_claim": "alpha=1"},
        {"excerpt": "not present", "normalized_claim": "x"},
    ]})
    with pytest.raises(InvalidClaimOutput):
        materialize_claims(_item(text), raw)


def test_pipeline_no_claim():
    provider = MockFactualProvider(raw=json.dumps({"status": "NO_CLAIM", "claims": []}))
    result = FactualEvidencePipeline(provider, []).process_chunk(_item())
    assert result.extraction.status is ClaimStatus.NO_CLAIM
    assert result.factual_evidence == ()
