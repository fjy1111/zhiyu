from __future__ import annotations
import json
from pathlib import Path
from zhiyu.models.detection import Confidence, EventClass, Mechanism, Measurement, RuleEvent
from zhiyu.models.factual import FactualEvidence, FactualRelation
from zhiyu.models.judge import AnalysisStatusRecord, Component, DocumentEvidence, RuleEventRecord, StatusKind
from zhiyu.models.semantic import BehaviorEvidence, SemanticIntent
from zhiyu.judge.refs import rule_event_ref


def rule_event_from_dict(row: dict) -> RuleEvent:
    measurement = None
    if row.get("measurement"):
        measurement = Measurement(**row["measurement"])
    return RuleEvent(
        rule_id=row["rule_id"],
        mechanism=Mechanism(row["mechanism"]),
        event_class=EventClass(row["event_class"]),
        confidence=Confidence(row["confidence"]),
        document_id=row["document_id"],
        chunk_id=row["chunk_id"],
        span_start=row["span_start"],
        span_end=row["span_end"],
        excerpt=row["excerpt"],
        rationale=row["rationale"],
        measurement=measurement,
    )


def behavior_from_dict(row: dict) -> BehaviorEvidence:
    mech = row.get("mechanism")
    return BehaviorEvidence(
        evidence_id=row["evidence_id"],
        document_id=row["document_id"],
        chunk_id=row["chunk_id"],
        intent=SemanticIntent(row["intent"]),
        mechanism=None if mech is None else Mechanism(mech),
        confidence=Confidence(row["confidence"]),
        span_start=row["span_start"],
        span_end=row["span_end"],
        excerpt=row["excerpt"],
        rationale=row["rationale"],
        source_rule_ids=tuple(row.get("source_rule_ids") or ()),
    )


def factual_from_dict(row: dict) -> FactualEvidence:
    return FactualEvidence(
        evidence_id=row["evidence_id"],
        claim_id=row["claim_id"],
        document_id=row["document_id"],
        chunk_id=row["chunk_id"],
        claim_excerpt=row["claim_excerpt"],
        normalized_claim=row["normalized_claim"],
        relation=FactualRelation(row["relation"]),
        supporting_reference_ids=tuple(row.get("supporting_reference_ids") or ()),
        contradicting_reference_ids=tuple(row.get("contradicting_reference_ids") or ()),
        insufficient_reference_ids=tuple(row.get("insufficient_reference_ids") or ()),
        reference_provenance=tuple(row.get("reference_provenance") or ()),
        aggregation_reason=row.get("aggregation_reason") or "",
        rationale=row.get("rationale") or "",
    )


def document_from_dict(row: dict) -> DocumentEvidence:
    rules = []
    for item in row["rule_events"]:
        event = rule_event_from_dict(item["event"])
        ref = item.get("rule_event_ref") or rule_event_ref(event)
        rules.append(RuleEventRecord(ref, event))
    statuses = tuple(
        AnalysisStatusRecord(
            component=Component(item["component"]),
            status=StatusKind(item["status"]),
            attempted=item["attempted"],
            skip_reason=item.get("skip_reason"),
            error_code=item.get("error_code"),
            chunk_id=item.get("chunk_id"),
            claim_id=item.get("claim_id"),
        )
        for item in row["statuses"]
    )
    return DocumentEvidence(
        document_id=row["document_id"],
        expected_chunk_ids=tuple(row["expected_chunk_ids"]),
        rule_events=tuple(rules),
        behavior_evidence=tuple(behavior_from_dict(item) for item in row["behavior_evidence"]),
        factual_evidence=tuple(factual_from_dict(item) for item in row["factual_evidence"]),
        statuses=statuses,
    )


def load_bundle(path: Path) -> list[DocumentEvidence]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(document_from_dict(json.loads(line)))
    return rows
