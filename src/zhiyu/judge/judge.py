from __future__ import annotations
import json
from zhiyu.factual.provider import FactualProvider, FactualProviderError
from zhiyu.judge.prompt import JUDGE_SYSTEM
from zhiyu.judge.validate import InvalidJudgeOutput, parse_assessment
from zhiyu.models.judge import AnalysisStatusRecord, Component, DocumentEvidence, StatusKind, UnifiedRiskAssessment


class UnifiedJudge:
    def __init__(self, provider: FactualProvider):
        self.provider = provider

    def assess(self, doc: DocumentEvidence) -> tuple[AnalysisStatusRecord, UnifiedRiskAssessment | None]:
        try:
            raw = self.provider.complete(JUDGE_SYSTEM, json.dumps(doc.to_runtime_dict(), ensure_ascii=False))
            assessment = parse_assessment(raw, doc)
        except FactualProviderError as exc:
            return AnalysisStatusRecord(Component.UNIFIED_JUDGE, StatusKind.ERROR, True, error_code=exc.code), None
        except InvalidJudgeOutput:
            return AnalysisStatusRecord(Component.UNIFIED_JUDGE, StatusKind.INVALID_OUTPUT, True, error_code="INVALID_OUTPUT"), None
        return AnalysisStatusRecord(Component.UNIFIED_JUDGE, StatusKind.OK, True), assessment
