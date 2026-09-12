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


def test_factual_rebuild_loads_project_env():
    text = Path("scripts/rebuild_phase5_factual.py").read_text(encoding="utf-8")
    assert "from zhiyu.semantic.env import load_project_env" in text
    assert "load_project_env(ROOT)" in text


def test_replacement_manifest_provenance_is_truthful():
    import subprocess
    from zhiyu.factual.corpus import sha256_file

    root = Path(__file__).resolve().parents[1]
    man = json.loads((root / "datasets/manifests/phase5_evidence_bundle_replacement_manifest.json").read_text(encoding="utf-8"))
    bundle = root / "datasets/processed/phase5/evidence_bundle_replacement.jsonl"
    assert man["bundle_sha256"] == sha256_file(bundle)
    assert man["bundle_sha256"] == "fbee0a73b54d0ebffd576b66526af21ca1f7c4e1829ad5338983b9082727fe89"
    assert man["supersedes_bundle_sha"] == sha256_file(root / "datasets/processed/phase5/evidence_bundle.jsonl")
    assert man["original_run_uncommitted_tracked_code"] is True
    assert man["original_run_working_tree_tracked_clean"] is False
    assert man.get("working_tree_tracked_clean") is not True
    assert man["only_generator_diff"] == "load_project_env(ROOT)"
    assert man["provenance_repair_without_rerun"] is True
    generator = man["generator_commit"]
    shown = subprocess.check_output(["git", "show", f"{generator}:scripts/rebuild_phase5_factual.py"], cwd=root, text=True)
    assert "load_project_env(ROOT)" in shown
    assert (root / "scripts/rebuild_phase5_factual.py").read_text(encoding="utf-8") == shown
    base = man["generator_base_commit"]
    diff = subprocess.check_output(["git", "diff", base, generator, "--", "scripts/rebuild_phase5_factual.py"], cwd=root, text=True)
    assert "load_project_env(ROOT)" in diff
    assert "DeepSeekFactualProvider(temperature=0.0,max_tokens=800,timeout_sec=60,retries=1)" in shown


def test_replacement_bundle_reuses_security_layers():
    from zhiyu.eval.phase4 import load_phase4_split
    from zhiyu.judge.bundle import load_bundle
    from zhiyu.models.judge import Component

    root = Path(__file__).resolve().parents[1]
    old = load_bundle(root / "datasets/processed/phase5/evidence_bundle.jsonl")
    new = load_bundle(root / "datasets/processed/phase5/evidence_bundle_replacement.jsonl")
    assert len(new) == 93
    tune=set(); gen=set()
    for did, item, path, digest in load_phase4_split(root, "development_tune"):
        tune.add(did)
    for did, item, path, digest in load_phase4_split(root, "development_generalization"):
        gen.add(did)
    new_ids = {d.document_id for d in new}
    assert len(new_ids & tune) == 54
    assert len(new_ids & gen) == 39
    old_by = {d.document_id: d for d in old}
    for doc in new:
        prev = old_by[doc.document_id]
        assert doc.rule_events == prev.rule_events
        assert doc.behavior_evidence == prev.behavior_evidence
        old_kept = tuple(s for s in prev.statuses if s.component not in {Component.FACTUAL_CLAIM, Component.FACTUAL_RETRIEVAL, Component.FACTUAL_COMPARE})
        new_kept = tuple(s for s in doc.statuses if s.component not in {Component.FACTUAL_CLAIM, Component.FACTUAL_RETRIEVAL, Component.FACTUAL_COMPARE})
        assert new_kept == old_kept
