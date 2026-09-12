from pathlib import Path
import pytest
from zhiyu.eval.phase2 import ALLOWED_SPLITS, FORBIDDEN_PATH_MARKERS, load_split
from zhiyu.eval.phase3 import compare_paths

ROOT = Path(__file__).resolve().parents[1]


def test_phase3_uses_same_split_loader_as_phase2():
    loaded = load_split(ROOT, "development_tune")
    assert loaded
    dumped = loaded[0][2][0].to_dict()
    assert "original_label" not in dumped


def test_phase3_rejects_frozen_splits():
    with pytest.raises(PermissionError):
        load_split(ROOT, "poisonedrag")
    assert "external_frozen" in FORBIDDEN_PATH_MARKERS
    assert "benchmark_tune_documents.jsonl" in {name for pair in ALLOWED_SPLITS.values() for name in pair}


def test_compare_paths_does_not_treat_review_as_success():
    left = {
        "primary": {"recall": 0.0, "f1": None, "fpr": 0.0},
        "auxiliary": {"poison_rate_hard_negative": 0.0},
    }
    right = {
        "primary": {"recall": 0.2, "f1": 0.3, "fpr": 0.0},
        "auxiliary": {"poison_rate_hard_negative": 0.0},
    }
    delta = compare_paths(left, right)
    assert delta["delta_recall"] == 0.2
    assert delta["delta_hard_negative_poison_rate"] == 0.0
