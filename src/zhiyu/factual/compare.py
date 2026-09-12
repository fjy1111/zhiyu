from __future__ import annotations
import json
from zhiyu.models.factual import (
    AtomicClaim,
    ComparisonResult,
    ComparisonStatus,
    PairwiseComparison,
    PairwiseRelation,
    TrustedEvidenceCandidate,
)


class InvalidComparisonOutput(ValueError):
    pass


_REL = {item.value: item for item in PairwiseRelation}


def parse_comparisons(raw: str, expected_ids: set[str]) -> tuple[PairwiseComparison, ...]:
    text = raw.strip()
    if text.startswith("```"):
        raise InvalidComparisonOutput("markdown fence is not allowed")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidComparisonOutput("json decode failed") from exc
    rows = payload.get("comparisons") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise InvalidComparisonOutput("comparisons must be a list")
    seen: set[str] = set()
    pairs: list[PairwiseComparison] = []
    for row in rows:
        if not isinstance(row, dict):
            raise InvalidComparisonOutput("pair must be an object")
        ref = row.get("reference_id")
        rel = row.get("relation")
        rationale = row.get("rationale", "")
        if ref not in expected_ids:
            raise InvalidComparisonOutput("unknown reference_id")
        if ref in seen:
            raise InvalidComparisonOutput("duplicate reference_id")
        if rel not in _REL:
            raise InvalidComparisonOutput("invalid relation")
        if not isinstance(rationale, str):
            raise InvalidComparisonOutput("rationale must be a string")
        seen.add(ref)
        pairs.append(PairwiseComparison(ref, _REL[rel], rationale))
    if seen != expected_ids:
        raise InvalidComparisonOutput("missing reference result")
    return tuple(pairs)
