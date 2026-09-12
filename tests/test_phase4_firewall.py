import ast
import json
from pathlib import Path
import pytest
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.provider import MockFactualProvider
from zhiyu.models.detection import DetectionInput

ROOT = Path(__file__).resolve().parents[1]


def test_extractor_only_detection_input():
    pipe = FactualEvidencePipeline(MockFactualProvider(raw=json.dumps({"status": "NO_CLAIM", "claims": []})), [])
    with pytest.raises(TypeError):
        pipe.extract({"original_label": "poison", "text": "x"})  # type: ignore[arg-type]


def test_extractor_payload_has_no_gt():
    provider = MockFactualProvider(raw=json.dumps({"status": "NO_CLAIM", "claims": []}))
    pipe = FactualEvidencePipeline(provider, [])
    pipe.extract(DetectionInput("d", "c", "The office opens at 09:00."))
    user = provider.messages[0][1]
    assert "original_label" not in user
    assert "attack_type" not in user
    assert "facts" not in user
    assert "target_answer" not in user


def test_factual_package_does_not_import_eval_or_labels():
    root = ROOT / "src" / "zhiyu" / "factual"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("zhiyu.eval")
                assert "phase4_evaluator_labels" not in node.module
