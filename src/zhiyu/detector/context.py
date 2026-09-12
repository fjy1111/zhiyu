"""Local quotation / educational context checks for Phase 2 HIGH gating."""
from __future__ import annotations
import re

_EDU = re.compile(
    r"(?is)"
    r"(?:for\s+example|e\.g\.|such\s+as|often\s+contains?|may\s+contain|"
    r"may\s+(?:ask|tell|instruct|require)|attackers?\s+may|"
    r"typical(?:ly)?\s+(?:includes?|contains?)|example\s+(?:payload|attack|phrase)|"
    r"prompt\s+injection(?:\s+attacks?)?.{0,40}(?:contain|include|use|look)|"
    r"described\s+as|quoted\s+as|known\s+as|quoted\s+payload|"
    r"the\s+phrase|this\s+phrase|threat\s+taxonomy|taxonomy|"
    r"appears\s+in|documentation|security\s+tutorial|known\s+payload|"
    r"例如|比如|如[：:]|常见(?:于|的)|攻击者(?:可能|常|会)?(?:要求|让|使用)?|"
    r"示例|样例|教学|论文|说明|这类攻击|提示注入(?:攻击)?.{0,20}(?:常常|通常|可能|包含|使用)|"
    r"威胁分类|攻击分类|该短语|这句话|引用(?:如下|说明)?|如下引文|攻击引用)"
)

_DISCUSS = re.compile(
    r"(?is)"
    r"(?:the\s+phrase|this\s+phrase|quoted\s+payload|payload\s*[:：]|"
    r"threat\s+taxonomy|taxonomy|appears\s+in|documentation|"
    r"known\s+payload|example\s+payload|security\s+tutorial|"
    r"attackers?\s+may|may\s+(?:ask|tell|instruct|contain|require)|"
    r"该短语|这句话|威胁分类|攻击分类|引用(?:如下|说明)|如下引文|"
    r"攻击引用|研究说明|如下所示|攻击说明)"
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


def _window(text: str, start: int, end: int) -> str:
    return text[max(0, start - 180):min(len(text), end + 100)]


def is_hard_negative_context(text: str, start: int, end: int) -> bool:
    """True when a control-looking span is discussed, quoted as an example, or documented."""
    if educational_prefix(text, start):
        return True
    quoted = in_quotes(text, start, end)
    coded = in_fenced_code(text, start) or in_inline_code(text, start, end)
    discussing = _DISCUSS.search(_window(text, start, end)) is not None
    if quoted and discussing:
        return True
    if coded and discussing:
        return True
    return False
