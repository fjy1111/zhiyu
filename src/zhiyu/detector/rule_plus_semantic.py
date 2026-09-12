"""Rule + Semantic baseline. Does not modify the Phase 2 Rule Scanner."""
from __future__ import annotations
from zhiyu.decision.semantic_aggregator import aggregate_rule_plus_semantic
from zhiyu.detector.scanner import RuleScanner
from zhiyu.models.detection import DetectionInput, DetectionResult, RuleEvent
from zhiyu.models.semantic import SemanticAnalysisInput
from zhiyu.semantic.analyzer import SemanticAnalyzer


class RulePlusSemanticBaseline:
    def __init__(self, analyzer: SemanticAnalyzer, scanner: RuleScanner | None = None):
        self.scanner = scanner or RuleScanner()
        self.analyzer = analyzer

    def scan_document(self, document_id: str, chunks: list[DetectionInput]) -> DetectionResult:
        rule_events: list[RuleEvent] = []
        semantic_results = []
        for item in chunks:
            if item.document_id != document_id:
                raise ValueError("chunk document_id mismatch")
            chunk_events = self.scanner.scan(item)
            rule_events.extend(chunk_events)
            semantic_results.append(
                self.analyzer.analyze(
                    SemanticAnalysisInput(detection_input=item, rule_events=tuple(chunk_events))
                )
            )
        return aggregate_rule_plus_semantic(document_id, rule_events, semantic_results)
