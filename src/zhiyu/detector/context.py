"""Local quotation / educational context checks for Phase 2 HIGH gating."""
from __future__ import annotations
import re

_EDU = re.compile(
    r"(?is)"
    r"(?:for\s+example|e\.g\.|such\s+as|often\s+contains?|may\s+contain|"
    r"typical(?:ly)?\s+(?:includes?|contains?)|example\s+(?:payload|attack|phrase)|"
    r"prompt\s+injection(?:\s+attacks?)?.{0,40}(?:contain|include|use|look)|"
    r"described\s+as|quoted\s+as|known\s+as|"
    r"例如|比如|如[：:]|常见(?:于|的)|攻击者(?:可能|常|会)?|"
    r"示例|样例|教学|论文|这类攻击|提示注入(?:攻击)?.{0,20}(?:常常|通常|可能|包含|使用))"
)

_PAIRS = (
    ('"', '"'),
    ("'", "'"),
    ("“", "”"),
    ("‘", "’"),
    ("「", "」"),
    ("『", "』"),
)


def in_quotes(text: str, start: int, end: int) -> bool:
    left = text[:start]
    right = text[end:]
    for open_ch, close_ch in _PAIRS:
        if open_ch == close_ch:
            if left.count(open_ch) % 2 == 1 and close_ch in right[:80]:
                return True
        elif left.rfind(open_ch) > left.rfind(close_ch) and close_ch in right[:80]:
            return True
    return False


def in_fenced_code(text: str, start: int) -> bool:
    before = text[:start]
    return before.count("```") % 2 == 1


def in_inline_code(text: str, start: int, end: int) -> bool:
    if text[:start].count("`") % 2 == 1 and "`" in text[end:end + 80]:
        return True
    return False


def educational_prefix(text: str, start: int) -> bool:
    window = text[max(0, start - 160):start]
    return _EDU.search(window) is not None


def is_hard_negative_context(text: str, start: int, end: int) -> bool:
    """True when a control-looking span is being discussed, quoted, or shown as an example."""
    if educational_prefix(text, start):
        return True
    quoted = in_quotes(text, start, end)
    coded = in_fenced_code(text, start) or in_inline_code(text, start, end)
    if quoted and _EDU.search(text[max(0, start - 200):end + 40]):
        return True
    if coded and educational_prefix(text, start):
        return True
    if coded:
        # A code fence/literal by itself is not a live instruction.
        return True
    return False
