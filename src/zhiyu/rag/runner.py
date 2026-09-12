from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from zhiyu.models.rag import (
    BuiltIndexes,
    EvaluatorRecord,
    GenerationOutcome,
    GenerationStatus,
    GeneratorConfig,
    RuntimeQuery,
)
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.evaluate import evaluate_system
from zhiyu.rag.firewall import QueryFirewallError
from zhiyu.rag.generate import SharedGenerator, run_protected_path, run_vanilla_path
from zhiyu.rag.retriever import SharedRetriever

CIC_VERSION = "phase6.cic.v1"


@dataclass
class RunnerResult:
    outcomes: dict
    replay: list[dict]
    provenance: dict
    generator: SharedGenerator


def _replay_row(path: str, query: RuntimeQuery, retrieval, outcome: GenerationOutcome) -> dict:
    row = {
        "query_id": query.query_id,
        "path": path,
        "retrieval_status": retrieval.status.value,
        "hit_chunk_ids": [hit.chunk_id for hit in retrieval.hits],
        "hit_document_ids": [hit.document_id for hit in retrieval.hits],
        "generation_status": outcome.status.value,
        "answer": outcome.answer,
        "error_code": outcome.error_code,
    }
    if outcome.cic is not None:
        row["cic"] = outcome.cic.to_runtime_dict()
    return row


class Phase6Runner:
    def __init__(self, indexes: BuiltIndexes, retriever: SharedRetriever, generator: SharedGenerator, cic: ContextIntegrityChecker, provenance: dict | None = None):
        if indexes.vanilla.config is not indexes.protected.config:
            raise ValueError("Vanilla/Protected must share retriever config")
        if retriever.config != indexes.config:
            raise ValueError("runner retriever config mismatch")
        self.indexes = indexes
        self.retriever = retriever
        self.generator = generator
        self.cic = cic
        self.provenance = {
            "evaluation_code_commit": None,
            "runtime_sha256": None,
            "evaluator_sha256": None,
            "phase5_bundle_sha256": None,
            "retriever": {"method": indexes.config.method, "k": indexes.config.k},
            "generator": {
                "model": generator.config.model,
                "temperature": generator.config.temperature,
                "max_tokens": generator.config.max_tokens,
            },
            "cic_version": CIC_VERSION,
        }
        if provenance:
            self.provenance.update(provenance)

    def run(self, queries: tuple[RuntimeQuery, ...] | list[RuntimeQuery]) -> RunnerResult:
        for query in queries:
            if isinstance(query, EvaluatorRecord) or not isinstance(query, RuntimeQuery):
                raise QueryFirewallError("runner accepts RuntimeQuery only")
        outcomes = {"vanilla": {}, "protected": {}}
        replay: list[dict] = []
        for query in queries:
            vanilla_retrieval = self.retriever.retrieve(query, self.indexes.vanilla)
            vanilla_outcome = run_vanilla_path(query, vanilla_retrieval, self.generator)
            outcomes["vanilla"][query.query_id] = vanilla_outcome
            replay.append(_replay_row("vanilla", query, vanilla_retrieval, vanilla_outcome))
            protected_retrieval = self.retriever.retrieve(query, self.indexes.protected)
            protected_outcome = run_protected_path(query, protected_retrieval, self.generator, self.cic)
            outcomes["protected"][query.query_id] = protected_outcome
            replay.append(_replay_row("protected", query, protected_retrieval, protected_outcome))
        return RunnerResult(outcomes, replay, dict(self.provenance), self.generator)

    def write_replay(self, path: Path, result: RunnerResult) -> Path:
        path = Path(path)
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in result.replay), encoding="utf-8")
        return path


def metrics_from_replay(replay_path: Path, records, generator_config: GeneratorConfig) -> dict:
    rows = [json.loads(line) for line in Path(replay_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    systems = {"vanilla": {}, "protected": {}}
    for row in rows:
        systems[row["path"]][row["query_id"]] = GenerationOutcome(
            GenerationStatus(row["generation_status"]),
            row.get("answer"),
            generator_config,
            error_code=row.get("error_code"),
        )
    return evaluate_system(records, systems)
