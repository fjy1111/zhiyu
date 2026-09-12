from pathlib import Path
import pytest
from zhiyu.eval.phase4 import load_phase4_split

ROOT = Path(__file__).resolve().parents[1]


def test_phase4_loader_strips_to_detection_input():
    rows = load_phase4_split(ROOT, "development_tune")
    assert rows
    dumped = rows[0][1].to_dict()
    assert "original_label" not in dumped
    assert "facts" not in dumped


def test_phase4_loader_rejects_unknown_split():
    with pytest.raises(PermissionError):
        load_phase4_split(ROOT, "poisonedrag")
