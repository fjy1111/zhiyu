"""Rule-only ingestion baseline: chunk scan then document aggregation."""
from __future__ import annotations
from zhiyu.decision.aggregator import aggregate
from zhiyu.detector.scanner import RuleScanner
from zhiyu.models.detection import DetectionInput, DetectionResult, RuleEvent


class RuleOnlyBaseline:
    def __init__(self, scanner: RuleScanner | None = None):
        self.scanner = scanner or RuleScanner()

    def scan_chunk(self, item: DetectionInput) -> list[RuleEvent]:
        return self.scanner.scan(item)

    def scan_document(self, document_id: str, chunks: list[DetectionInput]) -> DetectionResult:
        events: list[RuleEvent] = []
        for item in chunks:
            if item.document_id != document_id:
                raise ValueError("chunk document_id mismatch")
            events.extend(self.scan_chunk(item))
        return aggregate(document_id, events)
