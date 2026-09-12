"""Official Phase 5 same-bundle ablation. Judge calls only for full_judge."""
from __future__ import annotations
import json
import subprocess
from collections import Counter
from _common import ROOT, write_json
from zhiyu.eval.phase5 import apply_ablation, summarize
from zhiyu.factual.corpus import sha256_file
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.judge.bundle import load_bundle
from zhiyu.judge.judge import UnifiedJudge
from zhiyu.models.judge import Ablation, DECISION_POLICY_VERSION, JUDGE_PROMPT_VERSION
from zhiyu.semantic.env import load_project_env, public_llm_config


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    if not cfg["api_key_present"] or not cfg["model"]:
        print("EVAL BLOCKED: missing LLM config")
        return 2
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    if dirty.strip():
        print("EVAL BLOCKED: tracked working tree is not clean")
        print(dirty)
        return 2
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    bundle_path = ROOT / "datasets/processed/phase5/evidence_bundle.jsonl"
    docs = load_bundle(bundle_path)
    labels = json.loads((ROOT / "datasets/manifests/phase4_evaluator_labels.json").read_text(encoding="utf-8"))
    judge = UnifiedJudge(DeepSeekFactualProvider(temperature=0.0, max_tokens=800, timeout_sec=60, retries=1, json_mode=True))
    report = {
        "experiment_kind": "REAL LLM",
        "config": {
            "evaluation_code_commit": commit,
            "working_tree_tracked_clean": True,
            "bundle_sha256": sha256_file(bundle_path),
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "decision_policy_version": DECISION_POLICY_VERSION,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "api_key_present": True,
        },
        "ablations": {},
        "notes": {"review_is_not_positive": True, "same_bundle": True},
    }
    transitions = Counter()
    no_judge_verdict = {}
    for ablation in Ablation:
        rows = []
        for doc in docs:
            label = (labels.get(doc.document_id) or {}).get("original_label")
            use_judge = judge if ablation is Ablation.FULL_JUDGE else None
            decision, assessment, judge_status = apply_ablation(doc, ablation, use_judge)
            had_failure = any(item.status.value in {"ERROR", "INVALID_OUTPUT"} for item in doc.statuses)
            if judge_status and judge_status.status.value in {"ERROR", "INVALID_OUTPUT"}:
                had_failure = True
            row = {
                "document_id": doc.document_id,
                "original_label": label,
                "decision": decision.decision.value,
                "poison_gate_refs": list(decision.poison_gate_refs),
                "unexpected_missing": list(decision.unexpected_missing),
                "had_failure": had_failure,
            }
            rows.append(row)
            if ablation is Ablation.FULL_EVIDENCE:
                no_judge_verdict[doc.document_id] = decision.decision.value
            if ablation is Ablation.FULL_JUDGE:
                prev = no_judge_verdict.get(doc.document_id)
                if prev and prev != decision.decision.value:
                    transitions[f"{prev}->{decision.decision.value}"] += 1
        include = False  # aggregate only; no gen sample dump
        report["ablations"][ablation.value] = summarize(rows, include_details=False)
        print(ablation.value, report["ablations"][ablation.value]["primary"], flush=True)
    report["judge_vs_no_judge_transitions"] = dict(transitions)
    out = ROOT / "experiments/phase5"
    write_json(out / "unified_judge.json", report)
    lines = ["# Phase 5 Unified Judge Evaluation", "", "same frozen bundle for all ablations", ""]
    for name, payload in report["ablations"].items():
        lines.append(f"## {name}")
        lines.append(f"- primary: {payload['primary']}")
        lines.append(f"- decisions: {payload['decision_counts']}")
        lines.append(f"- judge_only_poison_count: {payload['judge_only_poison_count']}")
        lines.append(f"- unsafe_safe_on_failure_count: {payload['unsafe_safe_on_failure_count']}")
        lines.append("")
    lines.append(f"- transitions: {report['judge_vs_no_judge_transitions']}")
    (out / "unified_judge.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
