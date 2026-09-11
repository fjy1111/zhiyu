"""Build only the two explicitly allowed development splits."""
import json
from collections import Counter
from dataclasses import asdict
from _common import ROOT, MANIFESTS, write_json
from zhiyu.dataset import build_records

def main():
    documents, chunks = build_records(ROOT)
    output = ROOT / "datasets/processed/trusted_provenance"
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in [("development_documents", documents), ("development_chunks", chunks)]:
        target = output / f"{name}.jsonl"
        # Build fully in memory before replacing either previous output.
        target.write_text("".join(json.dumps(asdict(row), ensure_ascii=False) + "\n"
                                  for row in rows), encoding="utf-8")
    summary = {"documents": len(documents), "chunks": len(chunks),
               "splits": dict(Counter(d.source_split for d in documents)),
               "original_labels": dict(Counter(d.metadata["original_label"] for d in documents))}
    write_json(MANIFESTS / "development_corpus_summary.json", summary)
    print(json.dumps(summary))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

