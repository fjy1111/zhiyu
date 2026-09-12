import ast
import json
from pathlib import Path
import pytest
from zhiyu.models.detection import DetectionInput
from zhiyu.models.semantic import SemanticAnalysisInput
from zhiyu.semantic.analyzer import SemanticAnalyzer
from zhiyu.semantic.provider import MockSemanticProvider

ROOT = Path(__file__).resolve().parents[1]


def test_semantic_input_rejects_non_detection_input():
    with pytest.raises(TypeError):
        SemanticAnalysisInput({"text": "x", "original_label": "poison"})  # type: ignore[arg-type]


def test_analyzer_accepts_only_semantic_input():
    analyzer = SemanticAnalyzer(MockSemanticProvider())
    with pytest.raises(TypeError):
        analyzer.analyze({"original_label": "poison"})  # type: ignore[arg-type]


def test_semantic_input_dump_has_no_ground_truth():
    dumped = json.dumps(SemanticAnalysisInput(DetectionInput("d", "c", "plain text"), ()).to_dict())
    for forbidden in ("original_label", "attack_type", "facts", "target_answer", "ground_truth"):
        assert forbidden not in dumped


def test_semantic_package_does_not_import_eval():
    root = ROOT / "src" / "zhiyu" / "semantic"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("zhiyu.eval"):
                raise AssertionError(f"{path} imports evaluator package")
