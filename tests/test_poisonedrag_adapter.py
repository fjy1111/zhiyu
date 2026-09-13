import json
import pytest
from zhiyu.datasets.poisonedrag_adapter import expand_case, expand_dataset, external_sample_id

CASE = {
    "id": "c1",
    "question": "Q?",
    "correct answer": "yes",
    "incorrect answer": "no",
    "adv_texts": ["p0", "p1", "p2"],
    "extra": "keep",
}

def test_expands_each_adv_text():
    rows = expand_case("nq", "c1", CASE)
    assert [r["adv_text_index"] for r in rows] == [0, 1, 2]
    assert [r["text"] for r in rows] == ["p0", "p1", "p2"]
    assert all(r["question"] == "Q?" and r["correct_answer"] == "yes" and r["target_answer"] == "no" for r in rows)
    assert all(r["source"] == "poisonedrag" and r["attack_family"] == "KNOWLEDGE_CORRUPTION" for r in rows)
    assert all(r["upstream_metadata"]["extra"] == "keep" for r in rows)

def test_external_sample_id_is_deterministic():
    a = expand_case("nq", "c1", CASE)
    b = expand_case("nq", "c1", CASE)
    assert [r["external_sample_id"] for r in a] == [r["external_sample_id"] for r in b]
    assert a[1]["external_sample_id"] == external_sample_id("nq", "c1", 1) == "poisonedrag:nq:c1:1"

def test_malformed_case_fails_loudly():
    with pytest.raises(ValueError):
        expand_case("nq", "c1", {"id": "c1", "question": "Q?"})

def test_rebuild_is_deterministic():
    data = {"c1": CASE, "c0": {**CASE, "id": "c0"}}
    assert expand_dataset("nq", data) == expand_dataset("nq", data)
