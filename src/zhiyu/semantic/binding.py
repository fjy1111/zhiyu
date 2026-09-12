"""Exact unique source binding. No fuzzy match, no occurrence hint."""
from __future__ import annotations
from zhiyu.models.semantic import MAX_EXCERPT


def bind_unique_excerpt(text: str, excerpt: str) -> tuple[int, int] | None:
    if not excerpt or len(excerpt) > MAX_EXCERPT:
        return None
    start = text.find(excerpt)
    if start < 0:
        return None
    if text.find(excerpt, start + 1) >= 0:
        return None
    end = start + len(excerpt)
    if text[start:end] != excerpt:
        return None
    return start, end
