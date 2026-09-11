"""Remove confirmed benchmark construction artifacts while preserving payload."""
from dataclasses import dataclass, field
import re

@dataclass
class BenchmarkDocumentRecord:
    document_id: str
    parsed_text: str
    benchmark_text: str
    original_label: str | None
    transformations: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

_SAMPLE = re.compile(r"(?m)^\s*(?:sample\s*id|样本编号|文档编号)\s*[:：].*\n?")
_NOTES = re.compile(r"(?m)^\s*说明[：:].*(?:测试提示注入|校园知识库|可信来源|非官方整理|冲突裁决).*(?:\n|$)")
_HIDDEN = re.compile(r"(?m)^\s*隐藏内容\s*[：:]\s?")
_TEMP = re.compile(r"（临时调整版）|\(临时调整版\)")
_HN_NOTE = re.compile(r"(?m)^\s*说明：这是同学整理摘要，已附官方链接，仅用于帮助快速阅读，不修改原始事实。\s*\n?")

def adapt(document) -> BenchmarkDocumentRecord:
    text = document.text
    transformations = []
    def sub(pattern, value, typ, source):
        updated, count = pattern.subn(value, source)
        if count: transformations.append({"type": typ, "count": count})
        return updated
    benchmark = sub(_SAMPLE, "", "REMOVE_SAMPLE_ID", text)
    benchmark = sub(_NOTES, "", "REMOVE_DATASET_NOTE", benchmark)
    benchmark = sub(_HIDDEN, "", "REMOVE_HIDDEN_PREFIX", benchmark)
    benchmark = sub(_TEMP, "", "REMOVE_TEMPORARY_MARKER", benchmark)
    benchmark = sub(_HN_NOTE, "", "REMOVE_HARD_NEGATIVE_DATASET_NOTE", benchmark)
    return BenchmarkDocumentRecord(document.document_id, text, benchmark,
        document.metadata.get("original_label"), transformations, dict(document.metadata))
