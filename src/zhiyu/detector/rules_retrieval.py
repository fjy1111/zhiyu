"""Generic ingestion-time retrieval-manipulation statistics."""
from __future__ import annotations
from collections import Counter
import re
from zhiyu.models.detection import (
    Confidence,
    DetectionInput,
    EventClass,
    Measurement,
    Mechanism,
    RuleEvent,
)

_TOKEN = re.compile(r"\w+", re.UNICODE)
_MAX_EXCERPT = 96


def _excerpt_span(text: str, needle: str) -> tuple[int, int, str]:
    start = text.lower().find(needle.lower())
    if start < 0:
        start = 0
        end = min(len(text), _MAX_EXCERPT)
        return start, end, text[start:end]
    end = min(len(text), start + min(len(needle), _MAX_EXCERPT))
    if end == start:
        end = min(len(text), start + 1)
    return start, end, text[start:end]


def _event(
    item: DetectionInput,
    rule_id: str,
    rationale: str,
    confidence: Confidence,
    name: str,
    value: float,
    threshold: float,
    needle: str,
) -> RuleEvent:
    start, end, excerpt = _excerpt_span(item.text, needle)
    return RuleEvent(
        rule_id=rule_id,
        mechanism=Mechanism.RETRIEVAL_HIJACKING,
        event_class=EventClass.STATISTICAL,
        confidence=confidence,
        document_id=item.document_id,
        chunk_id=item.chunk_id,
        span_start=start,
        span_end=end,
        excerpt=excerpt,
        rationale=rationale,
        measurement=Measurement(name=name, value=round(value, 4), threshold=threshold),
    )


def find_retrieval_events(item: DetectionInput) -> list[RuleEvent]:
    text = item.text
    if len(text.strip()) < 60:
        return []
    events: list[RuleEvent] = []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 6:
        line, count = Counter(lines).most_common(1)[0]
        ratio = count / len(lines)
        if count >= 5 and ratio >= 0.5 and len(line) >= 8:
            confidence = Confidence.HIGH if count >= 8 or ratio >= 0.7 else Confidence.MEDIUM
            events.append(
                _event(
                    item,
                    "rh.line_repetition",
                    "abnormal repetition concentration",
                    confidence,
                    "repetition_ratio",
                    ratio,
                    0.5,
                    line,
                )
            )

    tokens = _TOKEN.findall(text)
    if len(tokens) >= 16:
        token, count = Counter(token.lower() for token in tokens if len(token) >= 2).most_common(1)[0]
        ratio = count / len(tokens)
        if count >= 8 and ratio >= 0.28:
            confidence = Confidence.HIGH if ratio >= 0.45 else Confidence.MEDIUM
            events.append(
                _event(
                    item,
                    "rh.term_concentration",
                    "retrieval-manipulation signal detected",
                    confidence,
                    "term_concentration",
                    ratio,
                    0.28,
                    token,
                )
            )

    if len(text) >= 80:
        grams = [text[i:i + 5] for i in range(len(text) - 4)]
        gram, count = Counter(grams).most_common(1)[0]
        ratio = count / len(grams)
        if count >= 10 and ratio >= 0.22 and not gram.isspace():
            confidence = Confidence.HIGH if ratio >= 0.35 else Confidence.MEDIUM
            events.append(
                _event(
                    item,
                    "rh.ngram_dominance",
                    "possible retrieval stuffing",
                    confidence,
                    "ngram_dominance",
                    ratio,
                    0.22,
                    gram,
                )
            )

    return events[:4]
