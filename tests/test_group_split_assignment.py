from collections import Counter, defaultdict
from build_group_split import assign_group_splits

PADS = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel"]

def make_records():
    rows = []
    for name in PADS[:4]:
        rows.append({"document_id": "p-" + name, "original_label": "poison",
                     "benchmark_text": (name + "-poison-") * 25})
    for name in PADS[4:]:
        rows.append({"document_id": "n-" + name, "original_label": "normal",
                     "benchmark_text": (name + "-normal-") * 25})
    return rows

def test_groups_are_never_split():
    out = assign_group_splits(make_records(), 5, 0.8, 0.5)
    by = defaultdict(set)
    for row in out:
        by[row["group_id"]].add(row["assigned_split"])
    assert all(len(v) == 1 for v in by.values())
    assert {r["assigned_split"] for r in out} <= {"development_tune", "development_generalization"}

def test_stratified_assignment_does_not_put_all_poison_in_one_split():
    out = assign_group_splits(make_records(), 5, 0.8, 0.5)
    by = defaultdict(Counter)
    for row in out:
        by[row["assigned_split"]][row["original_label"]] += 1
    for split in ("development_tune", "development_generalization"):
        assert by[split]["poison"] > 0
        assert by[split]["normal"] > 0

def test_assignment_is_deterministic():
    a = assign_group_splits(make_records(), 5, 0.8, 0.5)
    b = assign_group_splits(make_records(), 5, 0.8, 0.5)
    assert a == b
