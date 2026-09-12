"""Structurally hidden control-payload rules."""
from __future__ import annotations
import re
from zhiyu.detector.context import is_hard_negative_context
from zhiyu.detector.rules_injection import _PATTERNS
from zhiyu.models.detection import (
    Confidence,
    DetectionInput,
    EventClass,
    Mechanism,
    RuleEvent,
)

_HTML_COMMENT = re.compile(r"(?s)<!--(.*?)-->")
_HIDDEN_STYLE = re.compile(
    r"(?is)<[^>]+(?:style\s*=\s*[\"'][^\"']*"
    r"(?:display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0)[^\"']*[\"'])"
    r"[^>]*>(.*?)</[^>]+>"
)
_INTERNAL_BLOCK = re.compile(
    r"(?is)\[BEGIN\s+INTERNAL\s+INSTRUCTIONS?\](.*?)\[END\s+INTERNAL\s+INSTRUCTIONS?\]"
)
_MODEL_ONLY_LINE = re.compile(
    r"(?im)^(?:MODEL[- ]ONLY|INTERNAL(?:\s+ONLY)?(?:\s+INSTRUCTION)?|SYSTEM\s*MESSAGE|"
    r"给模型的(?:内部)?(?:指令|消息)|仅模型可见|用户不可见|"
    r"DO\s+NOT\s+(?:SHOW|DISPLAY)\s+TO\s+(?:THE\s+)?USER)\s*[:：]\s*(.+)$"
)


def _inner_has_control_payload(inner: str) -> re.Match[str] | None:
    for _rule_id, _rationale, pattern in _PATTERNS:
        match = pattern.search(inner)
        if match is not None:
            return match
    return None


def find_hidden_regions(text: str) -> list[tuple[int, int]]:
    regions: list[tuple[int, int]] = []
    for pattern in (_HTML_COMMENT, _HIDDEN_STYLE, _INTERNAL_BLOCK, _MODEL_ONLY_LINE):
        for match in pattern.finditer(text):
            regions.append(match.span())
    return regions


def find_hidden_events(item: DetectionInput) -> list[RuleEvent]:
    events: list[RuleEvent] = []
    carriers: list[tuple[str, int, int, str, int]] = []
    for rule_id, pattern in (
        ("hi.html_comment", _HTML_COMMENT),
        ("hi.hidden_style", _HIDDEN_STYLE),
        ("hi.internal_block", _INTERNAL_BLOCK),
        ("hi.model_only_container", _MODEL_ONLY_LINE),
    ):
        for match in pattern.finditer(item.text):
            inner = match.group(1)
            inner_start = match.start(1)
            carriers.append((rule_id, match.start(), match.end(), inner, inner_start))

    for rule_id, carrier_start, carrier_end, inner, inner_start in carriers:
        if is_hard_negative_context(item.text, carrier_start, carrier_end):
            continue
        payload = _inner_has_control_payload(inner)
        if payload is None:
            continue
        start = inner_start + payload.start()
        end = inner_start + payload.end()
        events.append(
            RuleEvent(
                rule_id=rule_id,
                mechanism=Mechanism.HIDDEN_INSTRUCTION,
                event_class=EventClass.MECHANISM,
                confidence=Confidence.HIGH,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                span_start=start,
                span_end=end,
                excerpt=item.text[start:end],
                rationale=(
                    "structurally hidden control payload: concealment carrier "
                    "contains an explicit model-control instruction"
                ),
            )
        )
        if len(events) >= 8:
            break
    return events
