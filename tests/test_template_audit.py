from pathlib import Path
from zhiyu.datasets.template_similarity import (
    build_template_groups, load_benchmark_audit_config, template_fingerprint,
)
from audit_template_similarity import audit_template_records

ROOT = Path(__file__).resolve().parents[1]
BASE = "alpha common template " * 5

def test_load_repo_yaml():
    cfg = load_benchmark_audit_config(ROOT / "configs/benchmark_audit.yaml")
    assert cfg["ngram_size"] == 5
    assert abs(cfg["near_template_threshold"] - 0.80) < 1e-9
    assert abs(cfg["tune_target_ratio"] - 0.70) < 1e-9

def test_connected_groups_use_build_template_groups_not_exact_fingerprint():
    rows = [
        {"path": "demo_set/a.txt", "text": BASE},
        {"path": "demo_set/b.txt", "text": BASE + " B"},
        {"path": "dev_set/c.txt", "text": BASE + " C"},
        {"path": "dev_set/d.txt", "text": "zzzz " * 20},
    ]
    assert len({template_fingerprint(r["text"]) for r in rows}) == 4
    report = audit_template_records(rows, 5, 0.8)
    groups, pairs = build_template_groups([{"text": r["text"]} for r in rows], 5, 0.8)
    assert report["connected_template_groups"] == len(groups) == 2
    assert report["exact_skeleton_overlap_groups"] == 0
    clustered = [c for c in report["template_clusters"] if len(c["paths"]) == 3][0]
    assert set(clustered["paths"]) == {"demo_set/a.txt", "demo_set/b.txt", "dev_set/c.txt"}
    assert report["cross_split_template_overlap"] == 1
    assert len(report["near_template_pairs"]) == len(pairs) == 3
