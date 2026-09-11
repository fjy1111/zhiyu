import json
from pathlib import Path

def test_benchmark_outputs():
    root=Path(__file__).resolve().parents[1]; rows=[json.loads(x) for x in (root/'datasets/processed/trusted_provenance/benchmark_documents.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==180 and all('parsed_text' in r and 'benchmark_text' in r for r in rows)
