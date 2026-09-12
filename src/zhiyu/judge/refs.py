from __future__ import annotations
import hashlib
from zhiyu.models.detection import RuleEvent
from zhiyu.models.judge import RULE_EVENT_REF_VERSION


def rule_event_ref(event: RuleEvent) -> str:
    payload = "|".join([
        RULE_EVENT_REF_VERSION,
        event.document_id,
        event.chunk_id,
        event.rule_id,
        str(event.span_start),
        str(event.span_end),
        event.mechanism.value,
        event.event_class.value,
        event.confidence.value,
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
