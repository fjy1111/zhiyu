import json
from _common import ROOT
from zhiyu.datasets.template_similarity import (
    build_template_groups,
    load_benchmark_audit_config,
    template_fingerprint,
)


def _normalize_text(text):
    return " ".join(text.split())


def validate_group_records(tune_rows, gen_rows, ngram_size, threshold):
    tune_rows = list(tune_rows)
    gen_rows = list(gen_rows)
    all_rows = tune_rows + gen_rows
    groups, pairs = build_template_groups(all_rows, ngram_size, threshold)
    tune_ids = {row["document_id"] for row in tune_rows}
    gen_ids = {row["document_id"] for row in gen_rows}
    split_of = ["tune"] * len(tune_rows) + ["gen"] * len(gen_rows)
    connected = 0
    for group in groups:
        ids = {row["document_id"] for row in group}
        if (ids & tune_ids) and (ids & gen_ids):
            connected += 1
    near = sum(1 for left, right, _score in pairs if split_of[left] != split_of[right])
    result = {
        "documents": len(all_rows),
        "document_id_overlap": len(tune_ids & gen_ids),
        "exact_text_overlap": len(
            {row["benchmark_text"] for row in tune_rows}
            & {row["benchmark_text"] for row in gen_rows}
        ),
        "normalized_exact_overlap": len(
            {_normalize_text(row["benchmark_text"]) for row in tune_rows}
            & {_normalize_text(row["benchmark_text"]) for row in gen_rows}
        ),
        "exact_template_fingerprint_overlap": len(
            {template_fingerprint(row["benchmark_text"]) for row in tune_rows}
            & {template_fingerprint(row["benchmark_text"]) for row in gen_rows}
        ),
        "near_template_pair_overlap": near,
        "connected_template_group_overlap": connected,
    }
    result["pass"] = all(value == 0 for key, value in result.items() if key.endswith("overlap"))
    return result


def main():
    cfg = load_benchmark_audit_config(ROOT / "configs/benchmark_audit.yaml")
    folder = ROOT / "datasets/processed/trusted_provenance"
    tune = [json.loads(line) for line in (folder / "benchmark_tune_documents.jsonl").read_text(encoding="utf-8").splitlines()]
    gen = [json.loads(line) for line in (folder / "benchmark_generalization_documents.jsonl").read_text(encoding="utf-8").splitlines()]
    result = validate_group_records(tune, gen, cfg["ngram_size"], cfg["near_template_threshold"])
    (ROOT / "datasets/manifests/development_group_split_validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
