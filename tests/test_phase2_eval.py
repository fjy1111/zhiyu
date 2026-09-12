from pathlib import Path
import pytest
from zhiyu.eval.phase2 import (
    ALLOWED_SPLITS,
    FORBIDDEN_PATH_MARKERS,
    load_split,
    summarize_split,
)

ROOT = Path(__file__).resolve().parents[1]


def test_review_is_not_positive():
    rows = [
        {"document_id": "p1", "original_label": "poison", "decision": "POISON", "events": []},
        {"document_id": "p2", "original_label": "poison", "decision": "REVIEW", "events": []},
        {"document_id": "n1", "original_label": "normal", "decision": "SAFE", "events": []},
        {"document_id": "h1", "original_label": "hard_negative", "decision": "SAFE", "events": []},
        {"document_id": "c1", "original_label": "conflict", "decision": "REVIEW", "events": []},
    ]
    summary = summarize_split("development_tune", rows, include_details=True)
    assert summary["primary"]["tp"] == 1
    assert summary["primary"]["fn"] == 1
    assert summary["primary"]["fp"] == 0
    assert summary["primary"]["tn"] == 2
    assert summary["auxiliary"]["poison_review_rate"] == 0.5
    assert "details" in summary
    assert summary["conflict_distribution"]["conflict_review_rate"] == 1.0


def test_generalization_summary_has_no_details():
    rows = [
        {"document_id": "n1", "original_label": "normal", "decision": "SAFE", "events": []},
    ]
    summary = summarize_split("development_generalization", rows, include_details=False)
    assert "details" not in summary


def test_load_split_strips_to_detection_input():
    loaded = load_split(ROOT, "development_tune")
    document_id, label, inputs = loaded[0]
    assert label in {"poison", "normal", "hard_negative", "conflict"}
    dumped = inputs[0].to_dict()
    assert set(dumped) <= {"document_id", "chunk_id", "text", "runtime"}
    assert "original_label" not in dumped


def test_load_split_rejects_frozen_names():
    with pytest.raises(PermissionError):
        load_split(ROOT, "frozen_holdout")
    with pytest.raises(PermissionError):
        load_split(ROOT, "poisonedrag")


def test_allowed_files_are_only_tune_and_generalization():
    names = {name for pair in ALLOWED_SPLITS.values() for name in pair}
    assert names == {
        "benchmark_tune_documents.jsonl",
        "benchmark_tune_chunks.jsonl",
        "benchmark_generalization_documents.jsonl",
        "benchmark_generalization_chunks.jsonl",
    }
    for marker in ("external_frozen", "poisonedrag", "blind_test_set"):
        assert marker in FORBIDDEN_PATH_MARKERS
