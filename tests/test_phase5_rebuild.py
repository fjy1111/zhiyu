import json
from pathlib import Path
from unittest.mock import patch

from zhiyu.judge.provider import DeepSeekJudgeProvider


class _Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps(self.payload).encode()


def _provider(payload):
    p = DeepSeekJudgeProvider(api_key="k", model="m", retries=0)
    with patch("urllib.request.urlopen", return_value=_Response({"choices":[{"message":payload}]})):
        return p.complete("s", "u")


def test_judge_provider_content_and_json_mode():
    assert _provider({"content": "{\"x\":1}"}) == '{"x":1}'
    p = DeepSeekJudgeProvider(api_key="k", model="m", retries=0)
    with patch("urllib.request.urlopen", return_value=_Response({"choices":[{"message":{"content":"{}"}}]})) as call:
        p.complete("s", "u")
        body = json.loads(call.call_args.kwargs["data"] if "data" in call.call_args.kwargs else call.call_args.args[0].data)
    assert body["response_format"] == {"type":"json_object"}


def test_judge_provider_reasoning_and_list_fallback():
    assert _provider({"content":"", "reasoning_content":"{\"a\":1}"}) == '{"a":1}'
    assert _provider({"content":[{"text":"{"}, {"text":"}"}]}) == "{}"


def test_factual_rebuild_is_layer_scoped_and_reuses_security_layers():
    text = Path("scripts/rebuild_phase5_factual.py").read_text(encoding="utf-8")
    assert "old_doc.rule_events" in text and "old_doc.behavior_evidence" in text
    assert "Component.FACTUAL_CLAIM,Component.FACTUAL_RETRIEVAL,Component.FACTUAL_COMPARE" in text
    assert "RuleScanner" not in text and "SemanticAnalyzer" not in text and "DeepSeekSemanticProvider" not in text
    assert "reused_layers" in text and "recomputed_layers" in text
