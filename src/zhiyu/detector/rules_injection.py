"""Mechanism-level explicit instruction-control rules."""
from __future__ import annotations
import re
from zhiyu.detector.context import is_hard_negative_context
from zhiyu.models.detection import (
    Confidence,
    DetectionInput,
    EventClass,
    Mechanism,
    RuleEvent,
)

_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "pi.instruction_override.en",
        "instruction-override mechanism: control verb targeting prior/system instructions",
        re.compile(
            r"(?is)(?:please\s+)?(?:ignore|disregard|forget|override|discard)\b"
            r".{0,48}?\b(?:previous|prior|above|all|earlier|original|preceding|any)\b"
            r".{0,32}?\b(?:instructions?|prompts?|rules?|policies|policy|guidelines?|system\s*prompt)"
        ),
    ),
    (
        "pi.instruction_override.en_system",
        "instruction-override mechanism: control verb targeting system/developer prompt",
        re.compile(
            r"(?is)(?:ignore|disregard|override|forget)\b.{0,24}?\b(?:the\s+)?"
            r"(?:system|developer)\s+(?:prompt|instructions?|message|rules?)"
        ),
    ),
    (
        "pi.instruction_override.zh",
        "instruction-override mechanism: control verb targeting prior/system instructions",
        re.compile(
            r"(?:请)?(?:忽略|无视|忘掉|不要(?:再)?(?:遵守|理会|执行|听从)|覆盖|作废)"
            r".{0,24}?(?:以上|之前|先前|原有|已有|前面|上面|所有)"
            r".{0,16}?(?:指令|提示|规则|约束|系统提示|设定)"
        ),
    ),
    (
        "pi.instruction_override.zh_system",
        "instruction-override mechanism: control verb targeting system/developer prompt",
        re.compile(
            r"(?:忽略|无视|覆盖|作废|不要遵守).{0,12}?(?:系统提示|开发者指令|原始指令|原有指令)"
        ),
    ),
    (
        "pi.role_manipulation.en",
        "role-manipulation mechanism: force a new unconstrained/system identity",
        re.compile(
            r"(?is)(?:you\s+are\s+now|from\s+now\s+on(?:\s+you\s+are)?|your\s+new\s+role\s+is|"
            r"act\s+as\s+(?:my\s+)?|pretend\s+(?:to\s+be|you\s+are))\s*.{0,40}?"
            r"(?:system(?:\s+prompt|\s+administrator)?|developer|unrestricted|"
            r"jailbroken|without\s+(?:any\s+)?restrictions|no\s+(?:safety\s+)?rules)"
        ),
    ),
    (
        "pi.role_manipulation.zh",
        "role-manipulation mechanism: force a new unconstrained/system identity",
        re.compile(
            r"(?:你现在是|从现在起你是|你的新角色是|扮演).{0,24}?"
            r"(?:系统(?:提示|管理员)?|开发者|无限制|越狱|不受(?:任何)?约束)"
        ),
    ),
    (
        "pi.task_hijack.en",
        "task-hijacking mechanism: replace the original task with attacker-specified control",
        re.compile(
            r"(?is)(?:your\s+(?:new\s+)?task\s+is(?:\s+now)?|"
            r"do\s+not\s+answer\s+the\s+(?:original|user|previous)\s+question|"
            r"abandon\s+(?:the\s+)?(?:original|previous)\s+task|"
            r"instead\s*,\s*(?:you\s+must|output|print|follow))"
        ),
    ),
    (
        "pi.task_hijack.zh",
        "task-hijacking mechanism: replace the original task with attacker-specified control",
        re.compile(
            r"(?:你的新任务是|不要(?:再)?回答(?:原来的|用户的|之前的|原)问题|"
            r"放弃原(?:来的)?任务|改为执行(?:以下|下列)?|只(?:执行|听从)(?:本|此)(?:文件|指令))"
        ),
    ),
    (
        "pi.policy_bypass.en",
        "policy-bypass mechanism: disable or evade existing safety constraints",
        re.compile(
            r"(?is)(?:bypass|disable|turn\s+off)\s+.{0,24}?"
            r"(?:safety|filter|guardrail|content\s+policy|restrictions)"
        ),
    ),
    (
        "pi.policy_bypass.zh",
        "policy-bypass mechanism: disable or evade existing safety constraints",
        re.compile(
            r"(?:绕过|关闭|无视).{0,12}?(?:安全策略|安全限制|内容过滤|防护规则|安全过滤)"
        ),
    ),
)


def _event(item: DetectionInput, rule_id: str, rationale: str, start: int, end: int) -> RuleEvent | None:
    if is_hard_negative_context(item.text, start, end):
        return None
    excerpt = item.text[start:end]
    return RuleEvent(
        rule_id=rule_id,
        mechanism=Mechanism.PROMPT_INJECTION,
        event_class=EventClass.MECHANISM,
        confidence=Confidence.HIGH,
        document_id=item.document_id,
        chunk_id=item.chunk_id,
        span_start=start,
        span_end=end,
        excerpt=excerpt,
        rationale=rationale,
    )


def find_injection_events(item: DetectionInput, skip_spans: tuple[tuple[int, int], ...] = ()) -> list[RuleEvent]:
    events: list[RuleEvent] = []
    seen: set[tuple[str, int, int]] = set()
    for rule_id, rationale, pattern in _PATTERNS:
        for match in pattern.finditer(item.text):
            start, end = match.span()
            if any(start >= skip_start and end <= skip_end for skip_start, skip_end in skip_spans):
                continue
            key = (rule_id, start, end)
            if key in seen:
                continue
            seen.add(key)
            event = _event(item, rule_id, rationale, start, end)
            if event is not None:
                events.append(event)
            if len(events) >= 12:
                return events
    return events
