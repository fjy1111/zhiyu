"""One-shot Phase 5 replacement Judge evaluation on the frozen replacement bundle."""
from __future__ import annotations
import json
import subprocess
from collections import Counter
from _common import ROOT, write_json
from zhiyu.eval.phase5 import apply_ablation, in_scope_failure, summarize
from zhiyu.factual.corpus import sha256_file
from zhiyu.judge.provider import DeepSeekJudgeProvider
from zhiyu.judge.bundle import load_bundle
from zhiyu.judge.judge import UnifiedJudge
from zhiyu.models.judge import (
    Ablation,
    DECISION_POLICY_VERSION,
    EXECUTION_PLAN_VERSION,
    JUDGE_PROMPT_VERSION,
    RULE_EVENT_REF_VERSION,
)
from zhiyu.semantic.env import load_project_env, public_llm_config

EXPECTED_BUNDLE = ROOT / "datasets/processed/phase5/evidence_bundle_replacement.jsonl"
EXPECTED_SHA = "fbee0a73b54d0ebffd576b66526af21ca1f7c4e1829ad5338983b9082727fe89"
JUDGE_SCHEMA_KEYS = [
    "document_id",
    "cited_rule_event_refs",
    "cited_behavior_evidence_ids",
    "cited_factual_evidence_ids",
    "behavior_assessment",
    "factual_assessment",
    "evidence_coherence",
    "uncertainty",
    "analyzer_failures",
    "rationale",
]


class CountingJudgeProvider(DeepSeekJudgeProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.complete_calls = 0

    def complete(self, system: str, user: str) -> str:
        self.complete_calls += 1
        return super().complete(system, user)


def _tracked_tree_clean() -> tuple[bool, str]:
    output = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    return output.strip() == "", output


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    if not cfg["api_key_present"] or not cfg["model"]:
        print("EVAL BLOCKED: missing LLM config")
        return 2
    clean, dirty = _tracked_tree_clean()
    if not clean:
        print("EVAL BLOCKED: tracked working tree is not clean")
        print(dirty)
        return 2
    digest = sha256_file(EXPECTED_BUNDLE)
    if digest != EXPECTED_SHA:
        print("EVAL BLOCKED: replacement bundle SHA mismatch")
        print(digest)
        return 2
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    docs = load_bundle(EXPECTED_BUNDLE)
    labels = json.loads((ROOT / "datasets/manifests/phase4_evaluator_labels.json").read_text(encoding="utf-8"))
    provider = CountingJudgeProvider(temperature=0.0, max_tokens=800, timeout_sec=60, retries=1)
    judge = UnifiedJudge(provider)
    report = {
        "experiment_kind": "REAL LLM",
        "config": {
            "evaluation_code_commit": commit,
            "working_tree_tracked_clean": True,
            "bundle_sha256": digest,
            "bundle_path": "datasets/processed/phase5/evidence_bundle_replacement.jsonl",
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "judge_schema_keys": JUDGE_SCHEMA_KEYS,
            "decision_policy_version": DECISION_POLICY_VERSION,
            "execution_plan_version": EXECUTION_PLAN_VERSION,
            "rule_event_ref_version": RULE_EVENT_REF_VERSION,
            "model": cfg["model"],
            "base_url": cfg["base_url"],
            "api_key_present": True,
        },
        "ablations": {},
        "split_ablations": {"development_tune": {}, "development_generalization": {}},
        "notes": {
            "review_is_not_positive": True,
            "same_bundle": True,
            "replacement_bundle": True,
            "provider_error_invalid_remain_review": True,
        },
    }
    transitions = Counter()
    no_judge_verdict = {}
    replay_rows = []
    judge_status_counts = Counter()
    for ablation in Ablation:
        rows = []
        for index, doc in enumerate(docs, start=1):
            meta = labels.get(doc.document_id) or {}
            label = meta.get("original_label")
            split = meta.get("split")
            use_judge = judge if ablation is Ablation.FULL_JUDGE else None
            decision, assessment, judge_status = apply_ablation(doc, ablation, use_judge)
            extra = (judge_status,) if judge_status is not None else ()
            had_failure = in_scope_failure(doc, ablation, extra_statuses=extra)
            row = {
                "document_id": doc.document_id,
                "original_label": label,
                "split": split,
                "decision": decision.decision.value,
                "poison_gate_refs": list(decision.poison_gate_refs),
                "unexpected_missing": list(decision.unexpected_missing),
                "had_failure": had_failure,
            }
            rows.append(row)
            if ablation is Ablation.FULL_EVIDENCE:
                no_judge_verdict[doc.document_id] = decision.decision.value
            if ablation is Ablation.FULL_JUDGE:
                if judge_status is not None:
                    judge_status_counts[judge_status.status.value] += 1
                prev = no_judge_verdict.get(doc.document_id)
                if prev and prev != decision.decision.value:
                    transitions[f"{prev}->{decision.decision.value}"] += 1
                replay_rows.append({
                    "document_id": doc.document_id,
                    "split": split,
                    "judge_status": judge_status.to_dict() if judge_status is not None else None,
                    "validated_unified_risk_assessment": assessment.to_dict() if assessment is not None else None,
                    "final_decision": decision.decision.value,
                    "triggered_decision_gates": {
                        "decision_kind": decision.decision_kind,
                        "poison_gate_refs": list(decision.poison_gate_refs),
                        "review_reasons": list(decision.review_reasons),
                        "unexpected_missing": list(decision.unexpected_missing),
                    },
                })
                print("judge", index, len(docs), judge_status.status.value if judge_status else "NONE", flush=True)
        report["ablations"][ablation.value] = summarize(rows, include_details=False)
        for split_name in ("development_tune", "development_generalization"):
            report["split_ablations"][split_name][ablation.value] = summarize(
                [row for row in rows if row["split"] == split_name],
                include_details=False,
            )
        print(ablation.value, report["ablations"][ablation.value]["primary"], flush=True)
    report["judge_call_count"] = provider.complete_calls
    report["judge_status_counts"] = {name: judge_status_counts.get(name, 0) for name in ("OK", "INVALID_OUTPUT", "ERROR")}
    report["judge_vs_no_judge_transitions"] = dict(transitions)
    report["judge_only_poison_count"] = report["ablations"]["full_judge"]["judge_only_poison_count"]
    report["unsafe_safe_on_failure_count"] = report["ablations"]["full_judge"]["unsafe_safe_on_failure_count"]
    out = ROOT / "experiments" / "phase5"
    write_json(out / "unified_judge_replacement.json", report)
    replay_path = out / "unified_judge_replacement_replay.jsonl"
    replay_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in replay_rows), encoding="utf-8")
    lines = ["# Phase 5 Replacement Unified Judge Evaluation", "", "frozen replacement bundle", ""]
    for name, payload in report["ablations"].items():
        lines.append(f"## {name}")
        lines.append(f"- primary: {payload['primary']}")
        lines.append(f"- decisions: {payload['decision_counts']}")
        lines.append(f"- judge_only_poison_count: {payload['judge_only_poison_count']}")
        lines.append(f"- unsafe_safe_on_failure_count: {payload['unsafe_safe_on_failure_count']}")
        lines.append("")
    lines.append(f"- judge_call_count: {report['judge_call_count']}")
    lines.append(f"- judge_status_counts: {report['judge_status_counts']}")
    lines.append(f"- transitions: {report['judge_vs_no_judge_transitions']}")
    (out / "unified_judge_replacement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
