import json, hashlib
from collections import Counter
from _common import ROOT
from zhiyu.parser.chunker import Chunker
from zhiyu.models.document import DocumentRecord
import yaml
from zhiyu.datasets.template_similarity import build_template_groups, load_benchmark_audit_config

def score(counts, n, target_n, target_labels, members):
    member_c = Counter(m.get("original_label") for m in members)
    label_score = 0
    for lab, k in member_c.items():
        remaining = target_labels.get(lab, 0) - counts.get(lab, 0)
        label_score += min(k, max(0, remaining))
        label_score -= max(0, k - max(0, remaining))
    remaining_n = target_n - n
    size_score = min(len(members), max(0, remaining_n)) - max(0, len(members) - max(0, remaining_n))
    return (label_score, size_score)

def assign_group_splits(records, ngram_size, threshold, tune_target_ratio):
    components, _ = build_template_groups(records, ngram_size, threshold)
    groups = {
        hashlib.sha256("|".join(sorted(x["document_id"] for x in members)).encode()).hexdigest()[:16]: members
        for members in components
    }
    ordered = sorted(groups.items(), key=lambda x: x[0])
    n_total = len(records)
    tune_target_n = round(n_total * tune_target_ratio)
    gen_target_n = n_total - tune_target_n
    count = Counter(r.get("original_label") for r in records)
    tune_target = {lab: round(c * tune_target_ratio) for lab, c in count.items()}
    gen_target = {lab: count[lab] - tune_target[lab] for lab in count}
    tune_counts, gen_counts = Counter(), Counter()
    tune_n = gen_n = 0
    out = []
    for gid, members in ordered:
        tune_score = score(tune_counts, tune_n, tune_target_n, tune_target, members)
        gen_score = score(gen_counts, gen_n, gen_target_n, gen_target, members)
        if gen_score > tune_score:
            assigned = "development_generalization"
            gen_n += len(members)
            gen_counts.update(m.get("original_label") for m in members)
        else:
            assigned = "development_tune"
            tune_n += len(members)
            tune_counts.update(m.get("original_label") for m in members)
        out.extend({
            "document_id": r["document_id"],
            "original_label": r.get("original_label"),
            "group_id": gid,
            "assigned_split": assigned,
        } for r in members)
    return out

def main():
    cfg = load_benchmark_audit_config(ROOT / "configs/benchmark_audit.yaml")
    source = ROOT / "datasets/processed/trusted_provenance/benchmark_documents.jsonl"
    rows = [json.loads(x) for x in source.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = assign_group_splits(rows, cfg["ngram_size"], cfg["near_template_threshold"], cfg["tune_target_ratio"])
    path = ROOT / "datasets/manifests/development_group_split.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assignments = {x["document_id"]: x["assigned_split"] for x in out}
    config = yaml.safe_load((ROOT / "configs/chunking.yaml").read_text())
    chunker = Chunker(**config)
    for split in ("development_tune", "development_generalization"):
        selected = [r for r in rows if assignments[r["document_id"]] == split]
        chunks = []
        for r in selected:
            d = DocumentRecord(r["document_id"], "trusted_provenance", "development", "", "", ".txt", "", r["benchmark_text"], len(r["benchmark_text"]), "BenchmarkAdapter", "1.0", r.get("metadata", {}), [])
            chunks.extend(chunker.chunk(d))
        folder = ROOT / "datasets/processed/trusted_provenance"
        folder.joinpath(f"benchmark_{split.split('_')[-1]}_documents.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in selected), encoding="utf-8")
        folder.joinpath(f"benchmark_{split.split('_')[-1]}_chunks.jsonl").write_text("".join(json.dumps(c.__dict__, ensure_ascii=False) + "\n" for c in chunks), encoding="utf-8")
    print(Counter(x["assigned_split"] for x in out))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
