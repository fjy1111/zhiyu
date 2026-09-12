"""Claim extraction with deterministic unique binding. No factuality regex."""
from __future__ import annotations
import hashlib
import json
from zhiyu.models.detection import DetectionInput
from zhiyu.models.factual import (
    MAX_CLAIM_EXCERPT,
    MAX_CLAIMS,
    MAX_NORMALIZED_CLAIM,
    AtomicClaim,
    ClaimExtractionResult,
    ClaimStatus,
)
from zhiyu.semantic.binding import bind_unique_excerpt


class InvalidClaimOutput(ValueError):
    pass


def _claim_id(document_id: str, chunk_id: str, start: int, end: int) -> str:
    payload = f"{document_id}|{chunk_id}|{start}|{end}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_claim_payload(raw: str) -> tuple[str, list[dict]]:
    text = raw.strip()
    if text.startswith("```"):
        raise InvalidClaimOutput("markdown fence is not allowed")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidClaimOutput("json decode failed") from exc
    if not isinstance(payload, dict):
        raise InvalidClaimOutput("payload must be an object")
    status = payload.get("status")
    claims = payload.get("claims")
    if status not in {"OK", "NO_CLAIM"}:
        raise InvalidClaimOutput("invalid status")
    if not isinstance(claims, list):
        raise InvalidClaimOutput("claims must be a list")
    if status == "NO_CLAIM":
        if claims:
            raise InvalidClaimOutput("NO_CLAIM must have empty claims")
        return status, []
    if not (1 <= len(claims) <= MAX_CLAIMS):
        raise InvalidClaimOutput("OK claims must contain 1 to MAX_CLAIMS items")
    return status, claims


def materialize_claims(item: DetectionInput, raw: str) -> tuple[AtomicClaim, ...]:
    status, rows = parse_claim_payload(raw)
    if status == "NO_CLAIM":
        return ()
    allowed = {"excerpt", "normalized_claim", "claim_type", "rationale"}
    claims: list[AtomicClaim] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) - allowed:
            raise InvalidClaimOutput("invalid claim draft")
        excerpt = row.get("excerpt")
        normalized = row.get("normalized_claim")
        if not isinstance(excerpt, str) or not isinstance(normalized, str):
            raise InvalidClaimOutput("excerpt and normalized_claim must be strings")
        if not excerpt or not normalized:
            raise InvalidClaimOutput("excerpt and normalized_claim required")
        if len(excerpt) > MAX_CLAIM_EXCERPT or len(normalized) > MAX_NORMALIZED_CLAIM:
            raise InvalidClaimOutput("claim field too long")
        bound = bind_unique_excerpt(item.text, excerpt)
        if bound is None:
            raise InvalidClaimOutput("excerpt failed unique bind")
        start, end = bound
        claim_type = row.get("claim_type")
        if claim_type is not None and not isinstance(claim_type, str):
            raise InvalidClaimOutput("claim_type must be string or null")
        claims.append(AtomicClaim(
            claim_id=_claim_id(item.document_id, item.chunk_id, start, end),
            document_id=item.document_id,
            chunk_id=item.chunk_id,
            span_start=start,
            span_end=end,
            excerpt=excerpt,
            normalized_claim=normalized,
            claim_type=claim_type,
        ))
    return tuple(claims)
