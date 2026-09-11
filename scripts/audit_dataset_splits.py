"""Hash-only held-out audit; no held-out metadata parsing or text serialization."""
import hashlib
import itertools
import json
import logging
from collections import Counter, defaultdict
from _common import ROOT, MANIFESTS, write_json
from zhiyu.dataset import DatasetPolicy, DEVELOPMENT, EVALUATION, FROZEN, FORMAT
from zhiyu.parser.document_parser import DocumentParser

def digest(data):
    return hashlib.sha256(data).hexdigest()

def groups(rows, key):
    buckets = defaultdict(list)
    for row in rows:
        if row.get(key) is not None:
            buckets[row[key]].append(row["path"])
    return [{"sha256": h, "paths": paths} for h, paths in sorted(buckets.items()) if len(paths) > 1]

def pair_count(groups_):
    return sum(len(g["paths"]) * (len(g["paths"]) - 1) // 2 for g in groups_)

def main():
    policy, parser = DatasetPolicy(ROOT), DocumentParser()
    rows, stats, development_texts = [], {}, {}
    # Suppress PDF library diagnostics: only explicit path/hash/statistics reach output.
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    for split in DEVELOPMENT + EVALUATION + FROZEN + FORMAT:
        paths = list(policy.files(split, "audit"))
        stats[split] = {"files": len(paths), "formats": dict(Counter(p.suffix.lower() for p in paths))}
        for path in paths:
            rel = path.relative_to(policy.raw).as_posix()
            row = {"path": rel, "sha256": digest(path.read_bytes()), "normalized_sha256": None}
            if path.suffix.lower() in parser.routes:
                try:
                    document = parser.parse(path, relative_path=rel)
                    # Only nonempty parsed normalized text is considered a text duplicate.
                    if document.text:
                        row["normalized_sha256"] = digest(document.text.encode("utf-8"))
                        if split in DEVELOPMENT:
                            development_texts[rel] = document.text
                    else:
                        row["empty_text"] = True
                    del document
                except Exception:
                    row["parse_failed"] = True
            rows.append(row)
    exact, normalized = groups(rows, "sha256"), groups(rows, "normalized_sha256")
    def split(path):
        return path.split("/")[0]
    cross = []
    for group in normalized:
        for a, b in itertools.combinations(group["paths"], 2):
            if split(a) != split(b):
                cross.append({"paths": [a, b], "sha256": group["sha256"]})
    dev_heldout = [p for p in cross if
                   any(split(x) in DEVELOPMENT for x in p["paths"]) and
                   any(split(x) in EVALUATION + FROZEN for x in p["paths"])]
    cross_exact = [{"paths": [a, b], "sha256": group["sha256"]}
                   for group in exact for a, b in itertools.combinations(group["paths"], 2)
                   if split(a) != split(b)]
    development_rows = [r for r in rows if split(r["path"]) in DEVELOPMENT]
    # Near-duplicate computation is intentionally restricted to development.
    # Frozen/evaluation permission permits hashes, not retained text features.
    features = {p: {t[i:i+5] for i in range(max(1, len(t)-4))}
                for p, t in development_texts.items()}
    near = []
    for a, b in itertools.combinations(sorted(features), 2):
        union = features[a] | features[b]
        similarity = len(features[a] & features[b]) / len(union) if union else 0
        if similarity >= 0.8:
            near.append({"paths": [a, b], "similarity": round(similarity, 6)})
    report = {
        "splits": stats, "files": rows,
        "exact_duplicate_groups": exact, "exact_duplicate_pairs": pair_count(exact),
        "normalized_duplicate_groups": normalized, "normalized_duplicate_pairs": pair_count(normalized),
        "cross_split_normalized_pairs": cross,
        "cross_split_exact_pairs": cross_exact,
        "development_vs_heldout_normalized_pairs": dev_heldout,
        "development_exact_duplicate_pairs": pair_count(groups(development_rows, "sha256")),
        "development_normalized_duplicate_pairs": pair_count(groups(development_rows, "normalized_sha256")),
        "near_duplicate": {"ngram_chars": 5, "threshold": 0.8,
                           "scope": list(DEVELOPMENT), "pairs": near},
        "parse_failures": sum(r.get("parse_failed", False) for r in rows),
    }
    write_json(MANIFESTS / "split_leakage_audit.json", report)
    lines = ["# Split leakage audit", "", "| Metric | Count |", "|---|---:|"]
    summary = {"exact_duplicate_groups": len(exact), "exact_duplicate_pairs": pair_count(exact),
               "normalized_duplicate_groups": len(normalized), "normalized_duplicate_pairs": pair_count(normalized),
               "cross_split_normalized_pairs": len(cross), "cross_split_exact_pairs": len(cross_exact), "development_vs_heldout_pairs": len(dev_heldout),
               "development_near_duplicate_pairs": len(near), "parse_failures": report["parse_failures"]}
    lines += [f"| {k} | {v} |" for k, v in summary.items()]
    lines += ["", "| Split | Files |", "|---|---:|"]
    lines += [f"| {k} | {v['files']} |" for k,v in stats.items()]
    lines += ["", "| Split | Format | Files |", "|---|---|---:|"]
    lines += [f"| {s} | {ext} | {n} |" for s, item in stats.items() for ext,n in item["formats"].items()]
    lines += ["", "| Path A | Path B | Similarity |", "|---|---|---:|"]
    lines += [f"| {p['paths'][0]} | {p['paths'][1]} | {p['similarity']} |" for p in near]
    lines += ["", "| SHA256 | Paths |", "|---|---|"]
    lines += [f"| {g['sha256']} | {' ; '.join(g['paths'])} |" for g in normalized]
    (MANIFESTS / "split_leakage_audit.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps(summary))
    return int(report["parse_failures"] > 0)

if __name__ == "__main__":
    raise SystemExit(main())
