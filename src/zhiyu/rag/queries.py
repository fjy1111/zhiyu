from __future__ import annotations
import hashlib
import json
from pathlib import Path
from zhiyu.models.rag import EvaluatorKind, EvaluatorRecord, RuntimeQuery
from zhiyu.rag.firewall import parse_runtime_query, snapshot_sha256


def build_query_id(query_text: str) -> str:
    return hashlib.sha256(query_text.encode("utf-8")).hexdigest()


def dump_runtime_snapshot(path: Path, queries: tuple[RuntimeQuery, ...] | list[RuntimeQuery]) -> Path:
    path = Path(path)
    ordered = sorted(queries, key=lambda item: item.query_id)
    rows = [item.to_runtime_dict() for item in ordered]
    for row in rows:
        parse_runtime_query(row)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return path


def dump_evaluator_snapshot(path: Path, records: tuple[EvaluatorRecord, ...] | list[EvaluatorRecord]) -> Path:
    path = Path(path)
    ordered = sorted(records, key=lambda item: item.query_id)
    path.write_text("".join(json.dumps(item.to_evaluator_dict(), ensure_ascii=False) + "\n" for item in ordered), encoding="utf-8")
    return path


def load_runtime_snapshot(path: Path) -> tuple[RuntimeQuery, ...]:
    queries = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        queries.append(parse_runtime_query(json.loads(line)))
    return tuple(queries)


def load_evaluator_snapshot(path: Path) -> tuple[EvaluatorRecord, ...]:
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        records.append(EvaluatorRecord(
            row["query_id"],
            EvaluatorKind(row["kind"]),
            gold_answer=row.get("gold_answer"),
            attack_success_criteria=row.get("attack_success_criteria"),
            attack_target=row.get("attack_target"),
        ))
    return tuple(records)


def snapshot_pair_hashes(runtime_path: Path, evaluator_path: Path) -> dict[str, str]:
    runtime_rows = [json.loads(line) for line in Path(runtime_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    evaluator_rows = [json.loads(line) for line in Path(evaluator_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in runtime_rows:
        parse_runtime_query(row)
    return {
        "runtime_sha256": snapshot_sha256({"rows": runtime_rows}),
        "evaluator_sha256": snapshot_sha256({"rows": evaluator_rows}),
    }
