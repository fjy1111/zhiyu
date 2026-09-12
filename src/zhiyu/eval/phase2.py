"""Phase 2 rule-only evaluation. Ground truth never enters the detector."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
from zhiyu.detector.pipeline import RuleOnlyBaseline
from zhiyu.models.detection import DetectionInput, DetectionResult

ALLOWED_SPLITS = {
    "development_tune": (
        "benchmark_tune_documents.jsonl",
        "benchmark_tune_chunks.jsonl",
    ),
    "development_generalization": (
        "benchmark_generalization_documents.jsonl",
        "benchmark_generalization_chunks.jsonl",
    ),
}
FORBIDDEN_PATH_MARKERS = (
    "external_frozen",
    "blind_test_set",
    "third_party_blind",
    "stress_set",
    "poisonedrag",
    "raw/trusted_provenance",
)
POSITIVE_LABELS = {"poison"}
NEGATIVE_LABELS = {"normal", "hard_negative"}
DECISIONS = ("SAFE", "REVIEW", "POISON")


def _jsonl(path: Path) -> list[dict]:
    resolved = path.resolve()
    posix = resolved.as_posix()
    for marker in FORBIDDEN_PATH_MARKERS:
        if marker in posix:
            raise PermissionError(f"Phase 2 evaluation cannot read {marker}")
    rows = []
    with resolved.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _to_inputs(document_id: str, chunks: list[dict], fallback_text: str) -> list[DetectionInput]:
    if not chunks:
        return [DetectionInput(document_id, f"{document_id}:full", fallback_text)]
    return [
        DetectionInput(document_id, str(chunk["chunk_id"]), str(chunk["text"]))
        for chunk in chunks
    ]


def load_split(project: Path, split: str) -> list[tuple[str, str, list[DetectionInput]]]:
    if split not in ALLOWED_SPLITS:
        raise PermissionError(f"split not allowed for Phase 2: {split}")
    processed = Path(project).resolve() / "datasets/processed/trusted_provenance"
    doc_name, chunk_name = ALLOWED_SPLITS[split]
    documents = _jsonl(processed / doc_name)
    chunks = _jsonl(processed / chunk_name)
    by_doc: dict[str, list[dict]] = {}
    for chunk in chunks:
        by_doc.setdefault(chunk["document_id"], []).append(chunk)
    loaded = []
    for document in documents:
        document_id = document["document_id"]
        label = document["original_label"]
        text = document.get("benchmark_text") or ""
        inputs = _to_inputs(document_id, by_doc.get(document_id, []), text)
        for item in inputs:
            dumped = item.to_dict()
            for forbidden in (
                "original_label",
                "label",
                "attack_type",
                "facts",
                "question",
                "target_answer",
                "correct_answer",
            ):
                if forbidden in dumped:
                    raise RuntimeError("ground truth leaked into DetectionInput")
        loaded.append((document_id, label, inputs))
    return loaded


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or (precision + recall) == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def _label_decision_rate(rows: list[dict], label: str, decision: str) -> float | None:
    subset = [row for row in rows if row["original_label"] == label]
    return _ratio(sum(row["decision"] == decision for row in subset), len(subset))


def summarize_split(split: str, rows: list[dict], include_details: bool) -> dict:
    tp = fp = tn = fn = 0
    for row in rows:
        label = row["original_label"]
        predicted = row["decision"] == "POISON"
        if label in POSITIVE_LABELS:
            if predicted:
                tp += 1
            else:
                fn += 1
        elif label in NEGATIVE_LABELS:
            if predicted:
                fp += 1
            else:
                tn += 1
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    payload = {
        "split": split,
        "documents": len(rows),
        "primary": {
            "predicted_positive": "decision == POISON",
            "review_is_not_detection_success": True,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": _f1(precision, recall),
            "fpr": _ratio(fp, fp + tn),
        },
        "auxiliary": {
            "review_rate_overall": _ratio(sum(row["decision"] == "REVIEW" for row in rows), len(rows)),
            "review_rate_normal": _label_decision_rate(rows, "normal", "REVIEW"),
            "review_rate_hard_negative": _label_decision_rate(rows, "hard_negative", "REVIEW"),
            "review_rate_poison": _label_decision_rate(rows, "poison", "REVIEW"),
            "safe_rate_normal": _label_decision_rate(rows, "normal", "SAFE"),
            "safe_rate_hard_negative": _label_decision_rate(rows, "hard_negative", "SAFE"),
            "safe_rate_poison": _label_decision_rate(rows, "poison", "SAFE"),
            "poison_rate_normal": _label_decision_rate(rows, "normal", "POISON"),
            "poison_rate_hard_negative": _label_decision_rate(rows, "hard_negative", "POISON"),
            "poison_review_rate": _label_decision_rate(rows, "poison", "REVIEW"),
        },
        "conflict_distribution": {
            "conflict_safe_rate": _label_decision_rate(rows, "conflict", "SAFE"),
            "conflict_review_rate": _label_decision_rate(rows, "conflict", "REVIEW"),
            "conflict_poison_rate": _label_decision_rate(rows, "conflict", "POISON"),
        },
        "diagnostics": _diagnostics(rows),
    }
    if include_details:
        payload["details"] = [
            {
                "document_id": row["document_id"],
                "original_label": row["original_label"],
                "decision": row["decision"],
                "events": row["events"],
            }
            for row in rows
        ]
    return payload


def _diagnostics(rows: list[dict]) -> dict:
    mechanisms: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    confidences: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    triggers: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    for row in rows:
        decisions[row["decision"]] += 1
        labels[row["original_label"]] += 1
        for event in row["events"]:
            mechanisms[event["mechanism"]] += 1
            classes[event["event_class"]] += 1
            confidences[event["confidence"]] += 1
            if (
                row["decision"] == "POISON"
                and event["event_class"] == "MECHANISM"
                and event["confidence"] == "HIGH"
                and event["mechanism"] in {"PROMPT_INJECTION", "HIDDEN_INSTRUCTION"}
            ):
                triggers[event["rule_id"]] += 1
    return {
        "label_counts": dict(labels),
        "decision_counts": {name: decisions.get(name, 0) for name in DECISIONS},
        "event_count_by_mechanism": dict(mechanisms),
        "event_count_by_event_class": dict(classes),
        "event_count_by_confidence": dict(confidences),
        "poison_trigger_rule_families": dict(triggers),
    }


def evaluate_split(project: Path, split: str, baseline: RuleOnlyBaseline | None = None) -> dict:
    baseline = baseline or RuleOnlyBaseline()
    include_details = split == "development_tune"
    rows = []
    for document_id, label, inputs in load_split(project, split):
        result: DetectionResult = baseline.scan_document(document_id, inputs)
        rows.append(
            {
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
            }
        )
    return summarize_split(split, rows, include_details=include_details)


def evaluate_phase2(project: Path) -> dict:
    return {
        "decision_kind": "rule_only_baseline",
        "splits": {
            "development_tune": evaluate_split(project, "development_tune"),
            "development_generalization": evaluate_split(project, "development_generalization"),
        },
        "notes": {
            "review_is_not_positive": True,
            "conflict_excluded_from_primary_binary": True,
            "frozen_external_unused": True,
            "no_score_threshold": True,
        },
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Phase 2 Rule-only Baseline Evaluation",
        "",
        "All numbers are generated by `scripts/evaluate_phase2.py`.",
        "REVIEW is not counted as detection success.",
        "conflict is excluded from primary Precision/Recall/F1/FPR.",
        "frozen/external were not used.",
        "",
    ]
    for split, payload in report["splits"].items():
        primary = payload["primary"]
        aux = payload["auxiliary"]
        conflict = payload["conflict_distribution"]
        lines.extend(
            [
                f"## {split}",
                "",
                f"- documents: {payload['documents']}",
                f"- tp/fp/tn/fn: {primary['tp']}/{primary['fp']}/{primary['tn']}/{primary['fn']}",
                f"- precision: {primary['precision']}",
                f"- recall: {primary['recall']}",
                f"- f1: {primary['f1']}",
                f"- fpr: {primary['fpr']}",
                f"- review_rate_overall: {aux['review_rate_overall']}",
                f"- review_rate_normal: {aux['review_rate_normal']}",
                f"- review_rate_hard_negative: {aux['review_rate_hard_negative']}",
                f"- review_rate_poison: {aux['review_rate_poison']}",
                f"- poison_rate_normal: {aux['poison_rate_normal']}",
                f"- poison_rate_hard_negative: {aux['poison_rate_hard_negative']}",
                f"- conflict_safe_rate: {conflict['conflict_safe_rate']}",
                f"- conflict_review_rate: {conflict['conflict_review_rate']}",
                f"- conflict_poison_rate: {conflict['conflict_poison_rate']}",
                f"- diagnostics: {payload['diagnostics']}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"
