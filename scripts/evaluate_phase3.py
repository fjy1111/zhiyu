"""Official Phase 3 real-LLM evaluation. Run once after tests and smoke pass."""
import subprocess
from _common import ROOT, write_json
from zhiyu.eval.phase3 import (
    compare_paths,
    evaluate_rule_only,
    evaluate_rule_plus_semantic,
    render_markdown,
)
from zhiyu.semantic.env import load_project_env, public_llm_config
from zhiyu.semantic.prompt import PROMPT_VERSION, SCHEMA_VERSION
from zhiyu.semantic.provider import DeepSeekSemanticProvider
import yaml


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    if not cfg["api_key_present"] or not cfg["model"]:
        print("EVAL BLOCKED: missing DEEPSEEK_API_KEY or DEEPSEEK_MODEL")
        return 2
    frozen = yaml.safe_load((ROOT / "configs/phase3_eval.yaml").read_text(encoding="utf-8"))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    provider = DeepSeekSemanticProvider(
        temperature=float(frozen["temperature"]),
        max_tokens=int(frozen["max_tokens"]),
        timeout_sec=float(frozen["timeout_sec"]),
        retries=int(frozen["retries"]),
    )
    report = {
        "experiment_kind": "REAL LLM",
        "decision_kinds": ["rule_only_baseline", "rule_plus_semantic_baseline"],
        "config": {
            **frozen,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "phase2_commit": commit,
            "api_key_present": True,
        },
        "splits": {},
        "notes": {
            "review_is_not_positive": True,
            "conflict_excluded_from_primary_binary": True,
            "frozen_external_unused": True,
            "mock_not_used": True,
        },
    }
    for split in ("development_tune", "development_generalization"):
        rule_only = evaluate_rule_only(ROOT, split)
        rule_plus = evaluate_rule_plus_semantic(ROOT, split, provider)
        report["splits"][split] = {
            "rule_only_baseline": rule_only,
            "rule_plus_semantic_baseline": rule_plus,
            "deltas": compare_paths(rule_only, rule_plus),
        }
    out = ROOT / "experiments" / "phase3"
    write_json(out / "rule_vs_rule_plus_semantic.json", report)
    (out / "rule_vs_rule_plus_semantic.md").write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
