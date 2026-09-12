from pathlib import Path
import pytest
from unittest.mock import Mock
from zhiyu.models.rag import GeneratorConfig, RetrieverConfig, RuntimeQuery
from zhiyu.rag.admission import build_indexes, load_candidate_chunks, load_frozen_decisions
from zhiyu.rag.cic import ContextIntegrityChecker, maybe_run_cic
from zhiyu.rag.generate import SharedGenerator, run_protected_path
from zhiyu.rag.queries import load_runtime_snapshot
from zhiyu.rag.retriever import NO_CONTEXT, SharedRetriever
ROOT = Path(__file__).resolve().parents[1]
CFG = RetrieverConfig(k=3)


def _split_indexes(split: str):
    chunks = load_candidate_chunks(ROOT, split=split)
    decisions = load_frozen_decisions(ROOT / "experiments/phase5/unified_judge_replacement_replay.jsonl")
    return build_indexes(chunks, decisions, CFG)


def test_omitted_split_keeps_combined_candidates():
    chunks = load_candidate_chunks(ROOT)
    assert len({chunk.document_id for chunk in chunks}) == 93
    assert len(chunks) == 93


def test_unknown_split_is_rejected():
    with pytest.raises(ValueError, match="unsupported Phase 6 split"):
        load_candidate_chunks(ROOT, split="frozen_holdout")


def test_tune_and_gen_indexes_are_disjoint():
    tune = _split_indexes("development_tune")
    gen = _split_indexes("development_generalization")
    assert tune.vanilla.document_ids.isdisjoint(gen.vanilla.document_ids)
    assert tune.protected.document_ids.isdisjoint(gen.protected.document_ids)


def test_gen_vanilla_and_protected_counts():
    gen = _split_indexes("development_generalization")
    assert len(gen.vanilla.document_ids) == 39
    assert len(gen.vanilla.chunks) == 39
    assert len(gen.protected.document_ids) == 0
    assert len(gen.protected.chunks) == 0


def test_tune_vanilla_and_protected_counts():
    tune = _split_indexes("development_tune")
    assert len(tune.vanilla.document_ids) == 54
    assert len(tune.vanilla.chunks) == 54
    assert len(tune.protected.document_ids) == 1
    assert len(tune.protected.chunks) == 1


def test_no_cross_split_hits_on_gen_index():
    gen = _split_indexes("development_generalization")
    tune = _split_indexes("development_tune")
    retriever = SharedRetriever(CFG)
    runtime = load_runtime_snapshot(ROOT / "datasets/processed/phase6/runtime_queries.jsonl")
    hit_docs = set()
    for query in runtime:
        result = retriever.retrieve(query, gen.vanilla)
        hit_docs.update(hit.document_id for hit in result.hits)
    assert hit_docs.isdisjoint(tune.vanilla.document_ids)
    assert hit_docs <= gen.vanilla.document_ids


def test_empty_protected_gen_is_no_context_without_cic_or_generator():
    gen = _split_indexes("development_generalization")
    retriever = SharedRetriever(CFG)
    query = RuntimeQuery("q", "开放时间是什么？")
    retrieval = retriever.retrieve(query, gen.protected)
    assert retrieval.status is NO_CONTEXT
    provider = Mock()
    cic = ContextIntegrityChecker(provider=provider)
    assert maybe_run_cic("protected", query, retrieval, cic) is None
    assert provider.complete.call_count == 0
    gen_provider = Mock()
    outcome = run_protected_path(
        query,
        retrieval,
        SharedGenerator(GeneratorConfig(model="m", system_prompt="s"), gen_provider),
        cic,
    )
    assert outcome.status.value == "NO_CONTEXT"
    assert gen_provider.complete.call_count == 0
