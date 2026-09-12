"""Phase 2 Rule Scanner: chunk in, RuleEvent[] out."""
from __future__ import annotations
from zhiyu.detector.rules_hidden import find_hidden_events, find_hidden_regions
from zhiyu.detector.rules_injection import find_injection_events
from zhiyu.detector.rules_retrieval import find_retrieval_events
from zhiyu.models.detection import DetectionInput, RuleEvent


class RuleScanner:
    def scan(self, item: DetectionInput) -> list[RuleEvent]:
        if not isinstance(item, DetectionInput):
            raise TypeError("RuleScanner only accepts DetectionInput")
        hidden_regions = tuple(find_hidden_regions(item.text))
        events: list[RuleEvent] = []
        events.extend(find_hidden_events(item))
        events.extend(find_injection_events(item, skip_spans=hidden_regions))
        events.extend(find_retrieval_events(item))
        return events
