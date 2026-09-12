from zhiyu.eval.phase5 import in_scope_failure, summarize
from zhiyu.models.judge import Ablation, AnalysisStatusRecord, Component, DocumentEvidence, StatusKind


def _st(component, status, chunk="c0"):
    return AnalysisStatusRecord(component, status, attempted=True, chunk_id=chunk)


def _doc(statuses):
    return DocumentEvidence("d", ("c0",), (), (), (), tuple(statuses))


def test_in_scope_failure_uses_expected_execution_plan_only():
    doc = _doc((
        _st(Component.RULE, StatusKind.OK),
        _st(Component.SEMANTIC, StatusKind.ERROR, chunk="c0"),
        _st(Component.FACTUAL_CLAIM, StatusKind.INVALID_OUTPUT),
        _st(Component.FACTUAL_COMPARE, StatusKind.ERROR),
    ))
    assert in_scope_failure(doc, Ablation.RULE_ONLY) is False
    assert in_scope_failure(doc, Ablation.RULE_SEMANTIC) is True
    assert in_scope_failure(doc, Ablation.FULL_EVIDENCE) is True
    assert in_scope_failure(doc, Ablation.FULL_JUDGE) is True


def test_in_scope_failure_counts_judge_only_when_in_plan():
    doc = _doc((
        _st(Component.RULE, StatusKind.OK),
        _st(Component.SEMANTIC, StatusKind.OK),
        _st(Component.FACTUAL_CLAIM, StatusKind.OK),
    ))
    judge = AnalysisStatusRecord(Component.UNIFIED_JUDGE, StatusKind.INVALID_OUTPUT, True)
    assert in_scope_failure(doc, Ablation.FULL_EVIDENCE, extra_statuses=(judge,)) is False
    assert in_scope_failure(doc, Ablation.FULL_JUDGE, extra_statuses=(judge,)) is True
    assert in_scope_failure(doc, Ablation.RULE_ONLY, extra_statuses=(judge,)) is False


def test_unsafe_safe_on_failure_ignores_out_of_scope_failures():
    rows = [{
        "original_label": "normal",
        "decision": "SAFE",
        "poison_gate_refs": [],
        "unexpected_missing": [],
        "had_failure": False,
    }]
    payload = summarize(rows, include_details=False)
    assert payload["unsafe_safe_on_failure_count"] == 0
    rows[0]["had_failure"] = True
    assert summarize(rows, include_details=False)["unsafe_safe_on_failure_count"] == 1
