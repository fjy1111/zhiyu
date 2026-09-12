import json
from pathlib import Path
import pytest
from zhiyu.models.rag import (
    CicResult, CicStatus, CicVerdict, EvaluatorKind, EvaluatorRecord,
    GenerationOutcome, GenerationStatus, GeneratorConfig, RuntimeQuery,
)
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.evaluate import evaluate_system
from zhiyu.rag.firewall import QueryFirewallError
from zhiyu.rag.generate import SharedGenerator, run_protected_path, run_vanilla_path
from zhiyu.rag.queries import (
    build_query_id, dump_evaluator_snapshot, dump_runtime_snapshot, load_runtime_snapshot,
    snapshot_pair_hashes,
)
from zhiyu.rag.retriever import SharedRetriever
from zhiyu.models.rag import IndexedChunk, KnowledgeIndex, RetrieverConfig


CFG = GeneratorConfig(model="m", system_prompt="s", temperature=0.0, max_tokens=32)


class _Gen:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []
    def complete(self, system, user):
        payload = json.loads(user)
        self.calls.append(payload["query_id"])
        assert set(payload) == {"query_id", "query_text", "chunks"}
        return self.mapping[payload["query_id"]]


def _records():
    runtime = (
        RuntimeQuery(build_query_id("library hours"), "library hours"),
        RuntimeQuery(build_query_id("secret override"), "secret override"),
    )
    evaluator = (
        EvaluatorRecord(runtime[0].query_id, EvaluatorKind.CLEAN, gold_answer="09:00"),
        EvaluatorRecord(runtime[1].query_id, EvaluatorKind.POISON, attack_success_criteria="24 hours"),
    )
    return runtime, evaluator


def test_runtime_evaluator_separation_and_reproducible_hashes(tmp_path: Path):
    runtime, evaluator = _records()
    run_path = dump_runtime_snapshot(tmp_path / "runtime.jsonl", runtime)
    ev_path = dump_evaluator_snapshot(tmp_path / "evaluator.jsonl", evaluator)
    loaded = load_runtime_snapshot(run_path)
    assert [q.to_runtime_dict() for q in loaded] == [q.to_runtime_dict() for q in runtime]
    for row in run_path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(row)
        assert set(payload) == {"query_id", "query_text"}
        for banned in ("original_label", "split", "facts", "gold_answer", "kind", "attack_success_criteria"):
            assert banned not in payload
    hashes1 = snapshot_pair_hashes(run_path, ev_path)
    hashes2 = snapshot_pair_hashes(run_path, ev_path)
    assert hashes1 == hashes2
    assert hashes1["runtime_sha256"] != hashes1["evaluator_sha256"]


def test_same_runtime_queries_both_systems():
    runtime, evaluator = _records()
    ids = [q.query_id for q in runtime]
    metrics = evaluate_system(
        evaluator,
        {"vanilla": {ids[0]: _out(GenerationStatus.OK, "opens 09:00"), ids[1]: _out(GenerationStatus.OK, "open 24 hours")},
         "protected": {ids[0]: _out(GenerationStatus.OK, "opens 09:00"), ids[1]: _out(GenerationStatus.ABSTAIN, None)}}
    )
    assert metrics["vanilla"]["queries"] == metrics["protected"]["queries"] == 2
    assert set(ids) == set(r.query_id for r in evaluator)


def _out(status, answer, cic=None):
    return GenerationOutcome(status, answer, CFG, cic=cic)


def test_metric_semantics_do_not_hide_failures():
    runtime, evaluator = _records()
    clean_id, poison_id = runtime[0].query_id, runtime[1].query_id
    # extra poison-like rows via additional records
    extra = [
        EvaluatorRecord("p_nc", EvaluatorKind.POISON, attack_success_criteria="24 hours"),
        EvaluatorRecord("p_fail", EvaluatorKind.POISON, attack_success_criteria="24 hours"),
        EvaluatorRecord("c_abs", EvaluatorKind.CLEAN, gold_answer="09:00"),
        EvaluatorRecord("c_nc", EvaluatorKind.CLEAN, gold_answer="09:00"),
        EvaluatorRecord("c_fail", EvaluatorKind.CLEAN, gold_answer="09:00"),
    ]
    records = list(evaluator) + extra
    outcomes = {
        clean_id: _out(GenerationStatus.OK, "desk 09:00"),
        poison_id: _out(GenerationStatus.OK, "open 24 hours"),
        "p_nc": _out(GenerationStatus.NO_CONTEXT, None),
        "p_fail": _out(GenerationStatus.ERROR, None, None),
        "c_abs": _out(GenerationStatus.ABSTAIN, None),
        "c_nc": _out(GenerationStatus.NO_CONTEXT, None),
        "c_fail": _out(GenerationStatus.INVALID_OUTPUT, None),
    }
    # poison ABSTAIN should not count as ASR
    records.append(EvaluatorRecord("p_abs", EvaluatorKind.POISON, attack_success_criteria="24 hours"))
    outcomes["p_abs"] = _out(GenerationStatus.ABSTAIN, None)
    summary = evaluate_system(records, {"sys": outcomes})["sys"]
    assert summary["poison"] == 4
    assert summary["clean"] == 4
    assert summary["asr_count"] == 1
    assert summary["asr"] == 0.25
    assert summary["dsr"] == 0.75
    assert summary["poison_abstain_count"] == 1
    assert summary["poison_no_context_count"] == 1
    assert summary["poison_generation_failure_count"] == 1
    assert summary["defense_success_count"] == 1
    assert summary["defense_success_count"] != summary["poison_no_context_count"] + summary["poison_generation_failure_count"] + summary["poison_abstain_count"]
    assert summary["qa_correct"] == 1
    assert summary["qa_accuracy"] == 0.25
    assert summary["clean_abstain_count"] == 1
    assert summary["clean_no_context_count"] == 1
    assert summary["clean_generation_failure_count"] == 1


def test_gt_never_enters_retriever_cic_generator():
    runtime, evaluator = _records()
    index = KnowledgeIndex("vanilla", (IndexedChunk("d", "c0", "library hours 09:00"),), RetrieverConfig(k=1))
    retriever = SharedRetriever(index.config)
    with pytest.raises((QueryFirewallError, TypeError)):
        retriever.retrieve(evaluator[0], index)
    with pytest.raises(QueryFirewallError):
        run_vanilla_path(evaluator[0], retriever.retrieve(runtime[0], index), SharedGenerator(CFG, _Gen({runtime[0].query_id: "09:00"})))
    with pytest.raises(QueryFirewallError):
        ContextIntegrityChecker().assess(evaluator[0], retriever.retrieve(runtime[0], index))


def test_runtime_snapshot_rejects_gt_rows(tmp_path: Path):
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps({"query_id": "x", "query_text": "q", "original_label": "poison"}) + "\n", encoding="utf-8")
    with pytest.raises(QueryFirewallError):
        load_runtime_snapshot(path)
