"""Expand frozen PoisonedRAG raw JSON into evaluator JSONL records."""
from __future__ import annotations

import json
from pathlib import Path

from zhiyu.datasets.poisonedrag_adapter import DATASETS, expand_dataset

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "datasets" / "external_frozen" / "poisonedrag" / "raw"
PROCESSED_DIR = ROOT / "datasets" / "external_frozen" / "poisonedrag" / "processed"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in rows),
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    if PROCESSED_DIR.resolve() == (ROOT / "datasets" / "processed" / "trusted_provenance").resolve():
        raise RuntimeError("Refusing to write PoisonedRAG into trusted_provenance")

    unified: list[dict] = []
    counts: dict[str, int] = {}
    for dataset in DATASETS:
        raw_path = RAW_DIR / f"{dataset}.json"
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        rows = expand_dataset(dataset, data)
        _write_jsonl(PROCESSED_DIR / f"{dataset}.jsonl", rows)
        unified.extend(rows)
        counts[dataset] = len(rows)
    _write_jsonl(PROCESSED_DIR / "poisonedrag_external.jsonl", unified)
    counts["poisonedrag_external"] = len(unified)
    print(json.dumps(counts, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
