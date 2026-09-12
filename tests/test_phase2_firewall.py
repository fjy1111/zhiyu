import ast
import inspect
import json
from pathlib import Path
import pytest
from zhiyu.detector.pipeline import RuleOnlyBaseline
from zhiyu.detector.scanner import RuleScanner
from zhiyu.models.detection import DetectionInput, RuntimeContext

ROOT = Path(__file__).resolve().parents[1]


def test_detection_input_rejects_labels():
    with pytest.raises(TypeError):
        DetectionInput("d", "c", "text", original_label="poison")  # type: ignore[call-arg]


def test_scanner_accepts_only_detection_input():
    scanner = RuleScanner()
    with pytest.raises(TypeError):
        scanner.scan({"document_id": "d", "text": "x", "original_label": "poison"})  # type: ignore[arg-type]


def test_pipeline_output_has_no_ground_truth():
    result = RuleOnlyBaseline().scan_document(
        "d", [DetectionInput("d", "c", "ordinary office hours are 09:00-17:00.")]
    )
    dumped = json.dumps(result.to_dict())
    for forbidden in ("original_label", "attack_type", "facts", "target_answer", "ground_truth"):
        assert forbidden not in dumped


def test_runtime_still_rejects_evaluator_fields():
    with pytest.raises(TypeError):
        DetectionInput("d", "c", "x", RuntimeContext(request_id="r"), attack_type="x")  # type: ignore[call-arg]


def test_detector_modules_do_not_import_eval_or_labels():
    scanner_src = inspect.getsource(RuleScanner)
    assert "original_label" not in scanner_src
    assert "zhiyu.eval" not in scanner_src
    detector_root = ROOT / "src" / "zhiyu" / "detector"
    for path in detector_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("zhiyu.eval"):
                raise AssertionError(f"{path} imports evaluator package")
