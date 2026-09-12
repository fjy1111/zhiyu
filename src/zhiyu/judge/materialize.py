"""Build a document evidence record using frozen Phase 2/3/4 implementations."""
from __future__ import annotations
from zhiyu.detector.scanner import RuleScanner
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.judge.refs import rule_event_ref
from zhiyu.models.detection import DetectionInput
from zhiyu.models.judge import (
    AnalysisStatusRecord, Component, DocumentEvidence, RuleEventRecord, StatusKind,
)
from zhiyu.models.semantic import SKIP_RULE_HIGH, SemanticAnalysisInput, SemanticStatus
from zhiyu.semantic.analyzer import SemanticAnalyzer, should_skip


def materialize_document(
    document_id: str,
    chunks: list[DetectionInput],
    candidate_path: str,
    candidate_hash: str,
    scanner: RuleScanner,
    semantic: SemanticAnalyzer,
    factual: FactualEvidencePipeline,
) -> DocumentEvidence:
    rule_records: list[RuleEventRecord] = []
    behaviors = []
    facts = []
    statuses: list[AnalysisStatusRecord] = []
    chunk_ids = []
    for item in chunks:
        chunk_ids.append(item.chunk_id)
        events = scanner.scan(item)
        statuses.append(AnalysisStatusRecord(Component.RULE, StatusKind.OK, True, chunk_id=item.chunk_id))
        for event in events:
            rule_records.append(RuleEventRecord(rule_event_ref(event), event))
        sem = semantic.analyze(SemanticAnalysisInput(item, tuple(events)))
        skip = sem.skip_reason if sem.status is SemanticStatus.SKIPPED else None
        statuses.append(AnalysisStatusRecord(
            Component.SEMANTIC, StatusKind(sem.status.value),
            attempted=sem.status is not SemanticStatus.SKIPPED,
            skip_reason=skip, error_code=sem.error_code, chunk_id=item.chunk_id,
        ))
        behaviors.extend(sem.behavior_evidence)
        fact = factual.process_chunk(item, candidate_path, candidate_hash)
        claim_status = fact.extraction.status.value
        statuses.append(AnalysisStatusRecord(
            Component.FACTUAL_CLAIM, StatusKind(claim_status),
            attempted=claim_status not in {"NO_CLAIM"},
            error_code=fact.extraction.error_code, chunk_id=item.chunk_id,
        ))
        for retrieval in fact.retrievals:
            statuses.append(AnalysisStatusRecord(
                Component.FACTUAL_RETRIEVAL, StatusKind(retrieval.status.value),
                attempted=True, error_code=retrieval.error_code,
                chunk_id=item.chunk_id, claim_id=retrieval.claim_id,
            ))
        for comparison in fact.comparisons:
            statuses.append(AnalysisStatusRecord(
                Component.FACTUAL_COMPARE, StatusKind(comparison.status.value),
                attempted=True, error_code=comparison.error_code,
                chunk_id=item.chunk_id, claim_id=comparison.claim_id,
            ))
        facts.extend(fact.factual_evidence)
    return DocumentEvidence(
        document_id=document_id,
        expected_chunk_ids=tuple(chunk_ids),
        rule_events=tuple(rule_records),
        behavior_evidence=tuple(behaviors),
        factual_evidence=tuple(facts),
        statuses=tuple(statuses),
    )
