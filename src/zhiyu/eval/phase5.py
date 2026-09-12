from __future__ import annotations
from collections import Counter
from zhiyu.judge.engine import decide, poison_gate_refs
from zhiyu.judge.judge import UnifiedJudge
from zhiyu.models.detection import Decision
from zhiyu.models.judge import Ablation, AnalysisStatusRecord, Component, DocumentEvidence, StatusKind

POSITIVE = {"poison"}
NEGATIVE = {"normal", "hard_negative"}


def apply_ablation(doc: DocumentEvidence, ablation: Ablation, judge: UnifiedJudge | None = None):
    assessment = None
    judge_status = None
    if ablation is Ablation.FULL_JUDGE:
        if judge is None:
            raise ValueError("full_judge requires UnifiedJudge")
        judge_status, assessment = judge.assess(doc)
        statuses = doc.statuses + (judge_status,)
        doc = DocumentEvidence(
            doc.document_id, doc.expected_chunk_ids, doc.rule_events,
            doc.behavior_evidence, doc.factual_evidence, statuses,
        )
    return decide(doc, ablation, assessment, judge_status), assessment, judge_status


def _ratio(n, d):
    return None if d == 0 else n / d


def summarize(rows: list[dict], include_details: bool) -> dict:
    tp = fp = tn = fn = 0
    decisions = Counter()
    labels = Counter()
    for row in rows:
        labels[row["original_label"]] += 1
        decisions[row["decision"]] += 1
        pred = row["decision"] == "POISON"
        lab = row["original_label"]
        if lab in POSITIVE:
            if pred:
                tp += 1
            else:
                fn += 1
        elif lab in NEGATIVE:
            if pred:
                fp += 1
            else:
                tn += 1
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
    poison_n = labels.get("poison", 0)
    poison_safe = sum(1 for row in rows if row["original_label"] == "poison" and row["decision"] == "SAFE")
    poison_nonsafe = sum(1 for row in rows if row["original_label"] == "poison" and row["decision"] in {"POISON", "REVIEW"})
    payload = {
        "documents": len(rows),
        "primary": {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1,
            "fpr": _ratio(fp, fp + tn),
        },
        "decision_counts": {name: decisions.get(name, 0) for name in ("SAFE", "REVIEW", "POISON")},
        "review_rate_overall": _ratio(decisions["REVIEW"], len(rows)),
        "review_rate_poison": _ratio(sum(1 for r in rows if r["original_label"]=="poison" and r["decision"]=="REVIEW"), labels.get("poison", 0)),
        "review_rate_normal": _ratio(sum(1 for r in rows if r["original_label"]=="normal" and r["decision"]=="REVIEW"), labels.get("normal", 0)),
        "review_rate_hard_negative": _ratio(sum(1 for r in rows if r["original_label"]=="hard_negative" and r["decision"]=="REVIEW"), labels.get("hard_negative", 0)),
        "review_rate_conflict": _ratio(sum(1 for r in rows if r["original_label"]=="conflict" and r["decision"]=="REVIEW"), labels.get("conflict", 0)),
        "hard_negative_poison_rate": _ratio(sum(1 for r in rows if r["original_label"]=="hard_negative" and r["decision"]=="POISON"), labels.get("hard_negative", 0)),
        "conflict_distribution": {
            "SAFE": _ratio(sum(1 for r in rows if r["original_label"]=="conflict" and r["decision"]=="SAFE"), labels.get("conflict", 0)),
            "REVIEW": _ratio(sum(1 for r in rows if r["original_label"]=="conflict" and r["decision"]=="REVIEW"), labels.get("conflict", 0)),
            "POISON": _ratio(sum(1 for r in rows if r["original_label"]=="conflict" and r["decision"]=="POISON"), labels.get("conflict", 0)),
        },
        "unsafe_auto_admission_rate": _ratio(poison_safe, poison_n),
        "poison_non_safe_rate": _ratio(poison_nonsafe, poison_n),
        "judge_only_poison_count": sum(1 for r in rows if r["decision"]=="POISON" and not r["poison_gate_refs"]),
        "unsafe_safe_on_failure_count": sum(
            1 for r in rows if r["decision"]=="SAFE" and (r["unexpected_missing"] or r.get("had_failure"))
        ),
    }
    if include_details:
        payload["details"] = [
            {"document_id": r["document_id"], "original_label": r["original_label"], "decision": r["decision"]}
            for r in rows
        ]
    return payload
