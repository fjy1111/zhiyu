import json
from zhiyu.judge.refs import rule_event_ref
from zhiyu.models.detection import Confidence, EventClass, Mechanism, RuleEvent
from zhiyu.models.judge import AnalysisStatusRecord, Component, DocumentEvidence, RuleEventRecord, StatusKind


def test_runtime_bundle_has_no_gt():
    event = RuleEvent(
        "pi.instruction_override.en", Mechanism.PROMPT_INJECTION, EventClass.MECHANISM,
        Confidence.HIGH, "d", "c0", 0, 5, "xxxxx", "override",
    )
    doc = DocumentEvidence(
        "d", ("c0",), (RuleEventRecord(rule_event_ref(event), event),), (), (),
        (AnalysisStatusRecord(Component.RULE, StatusKind.OK, True, chunk_id="c0"),),
    )
    dumped = json.dumps(doc.to_runtime_dict())
    for forbidden in ("original_label", "attack_type", "facts", "target_answer", "split"):
        assert forbidden not in dumped
