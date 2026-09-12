"""Phase 3 Rule Only vs Rule + Semantic evaluation. Ground truth stays in the evaluator."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from zhiyu.detector.pipeline import RuleOnlyBaseline
from zhiyu.detector.rule_plus_semantic import RulePlusSemanticBaseline
from zhiyu.eval.phase2 import load_split, summarize_split
from zhiyu.models.semantic import SemanticStatus
from zhiyu.semantic.analyzer import SemanticAnalyzer
from zhiyu.semantic.provider import SemanticProvider


def _delta(left, right):
    if left is None or right is None:
        return None
    return right - left


def _semantic_stats(rows: list[dict]) -> dict:
    statuses = Counter()
    calls = skips = errors = invalids = 0
    evidence_conf = Counter()
    evidence_mech = Counter()
    for row in rows:
        for result in row.get("semantic_results", []):
            status = result["status"]
            statuses[status] += 1
            if status == SemanticStatus.SKIPPED.value:
                skips += 1
            elif status == SemanticStatus.ERROR.value:
                errors += 1
            elif status == SemanticStatus.INVALID_OUTPUT.value:
                invalids += 1
            elif status == SemanticStatus.OK.value:
                calls += 1
            for evidence in result.get("behavior_evidence", []):
                evidence_conf[evidence["confidence"]] += 1
                evidence_mech[str(evidence["mechanism"])] += 1
    return {
        "semantic_call_count": calls,
        "semantic_skip_count": skips,
        "semantic_error_count": errors,
        "invalid_output_count": invalids,
        "status_counts": dict(statuses),
        "behavior_evidence_by_confidence": dict(evidence_conf),
        "behavior_evidence_by_mechanism": dict(evidence_mech),
    }


def evaluate_rule_only(project: Path, split: str) -> dict:
    baseline = RuleOnlyBaseline()
    include_details = split == "development_tune"
    rows = []
    for document_id, label, inputs in load_split(project, split):
        result = baseline.scan_document(document_id, inputs)
        rows.append({
            "document_id": document_id,
            "original_label": label,
            "decision": result.decision.value,
            "events": [
                {
                    "rule_id": event.rule_id,
                    "mechanism": event.mechanism.value,
                    "event_class": event.event_class.value,
                    "confidence": event.confidence.value,
                }
                for event in result.rule_events
            ],
        })
    payload = summarize_split(split, rows, include_details=include_details)
    payload["decision_kind"] = "rule_only_baseline"
    return payload


def evaluate_rule_plus_semantic(project: Path, split: str, provider: SemanticProvider) -> dict:
    baseline = RulePlusSemanticBaseline(SemanticAnalyzer(provider))
    include_details = split == "development_tune"
    rows = []
    for document_id, label, inputs in load_split(project, split):
        result = baseline.scan_document(document_id, inputs)
        rows.append({
            "document_id": document_id,
            "original_label": label,
            "decision": result.decision.value,
            "events": [
                {
                    "rule_id": event.rule_id,
                    "mechanism": event.mechanism.value,
                    "event_class": event.event_class.value,
                    "confidence": event.confidence.value,
                }
                for event in result.rule_events
            ],
            "semantic_results": [item.to_dict() for item in result.semantic_results],
        })
    payload = summarize_split(split, rows, include_details=include_details)
    payload["decision_kind"] = "rule_plus_semantic_baseline"
    payload["semantic_diagnostics"] = _semantic_stats(rows)
    return payload


def compare_paths(rule_only: dict, rule_plus: dict) -> dict:
    left = rule_only["primary"]
    right = rule_plus["primary"]
    return {
        "delta_recall": _delta(left["recall"], right["recall"]),
        "delta_f1": _delta(left["f1"], right["f1"]),
        "delta_fpr": _delta(left["fpr"], right["fpr"]),
        "delta_hard_negative_poison_rate": _delta(
            rule_only["auxiliary"]["poison_rate_hard_negative"],
            rule_plus["auxiliary"]["poison_rate_hard_negative"],
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Phase 3 Rule Only vs Rule + Semantic",
        "",
        f"experiment_kind: {report['experiment_kind']}",
        "REVIEW is not counted as detection success.",
        "conflict is excluded from primary Precision/Recall/F1/FPR.",
        "frozen/external were not used.",
        "",
    ]
    for split, payload in report["splits"].items():
        lines.append(f"## {split}")
        lines.append("")
        for name in ("rule_only_baseline", "rule_plus_semantic_baseline"):
            block = payload[name]
            primary = block["primary"]
            aux = block["auxiliary"]
            lines.extend([
                f"### {name}",
                f"- documents: {block['documents']}",
                f"- tp/fp/tn/fn: {primary['tp']}/{primary['fp']}/{primary['tn']}/{primary['fn']}",
                f"- precision: {primary['precision']}",
                f"- recall: {primary['recall']}",
                f"- f1: {primary['f1']}",
                f"- fpr: {primary['fpr']}",
                f"- hard_negative_poison_rate: {aux['poison_rate_hard_negative']}",
                f"- poison_review_rate: {aux['poison_review_rate']}",
                "",
            ])
            if "semantic_diagnostics" in block:
                lines.append(f"- semantic_diagnostics: {block['semantic_diagnostics']}")
                lines.append("")
        lines.append(f"- deltas: {payload['deltas']}")
        lines.append("")
    return "\n".join(lines) + "\n"
