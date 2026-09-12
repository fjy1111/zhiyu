from __future__ import annotations
import hashlib
import json
from zhiyu.models.rag import RuntimeQuery

FORBIDDEN_RUNTIME_FIELDS = frozenset({
    "original_label", "attack_type", "is_poison", "label",
    "expected_answer", "target_answer", "correct_answer", "facts",
    "source_split", "split", "gold_answer", "attack_success_criteria",
    "kind", "CLEAN", "POISON",
})
RUNTIME_QUERY_KEYS = frozenset({"query_id", "query_text"})


class QueryFirewallError(ValueError):
    pass


def parse_runtime_query(payload: dict) -> RuntimeQuery:
    if not isinstance(payload, dict):
        raise QueryFirewallError("RuntimeQuery payload must be an object")
    extra = set(payload) - RUNTIME_QUERY_KEYS
    missing = RUNTIME_QUERY_KEYS - set(payload)
    if extra or missing:
        raise QueryFirewallError("RuntimeQuery must contain only query_id and query_text")
    for key in FORBIDDEN_RUNTIME_FIELDS:
        if key in payload:
            raise QueryFirewallError(f"GT field leaked into RuntimeQuery: {key}")
    return RuntimeQuery(str(payload["query_id"]), str(payload["query_text"]))


def snapshot_sha256(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
