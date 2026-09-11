# Phase 1.5 Final Benchmark Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Phase 1.5 evaluation infrastructure so template audit, group-aware split, independent validation, and long-document chunk tests are truthful.

**Architecture:** Keep the shared algorithm in `zhiyu.datasets.template_similarity.build_template_groups`. Scripts become thin IO wrappers that load `configs/benchmark_audit.yaml` and call testable functions. Validators recompute connected components from split JSONL files and never trust builder outputs.

**Tech Stack:** Python 3.10+, pytest, PyYAML, existing `zhiyu` package (`pythonpath = ["src", "scripts"]`).

**Spec:** User Phase 1.5 final request T1-T4 plus current `AGENTS.md` and `configs/benchmark_audit.yaml`.

## Global Constraints

- Do not modify `datasets/raw/`.
- Do not implement any Detector, Rule, LLM, or RAG.
- Do not hardcode experiment results.
- Do not hand-edit generated manifests; regenerate them with scripts.
- Validator must independently recompute; it must not treat builder group IDs as ground truth.
- Config values must come from `configs/benchmark_audit.yaml` / `configs/chunking.yaml`, not scattered literals.
- Do not tune parameters against frozen/evaluation data.
- Do not enter Phase 2.
- Do not git commit or git push inside a Task. The controller makes one stage-end commit after verification.
- Work in `D:\Projects\知御\zhiyu` on branch `main`.
- TDD for Tasks 1-3: RED (watch fail) then GREEN then REFACTOR. Task 4 adds regression tests for existing Chunker; if they pass immediately, do not change Chunker.

## File map

- Modify: `src/zhiyu/datasets/template_similarity.py` — add `load_benchmark_audit_config`
- Modify: `scripts/audit_template_similarity.py` — connected components via `build_template_groups`, yaml params
- Modify: `scripts/build_group_split.py` — deterministic group-aware stratified assignment
- Modify: `scripts/validate_group_split.py` — independent connected-component overlap
- Modify: `tests/test_phase1_5r2_audits.py` or Create: `tests/test_template_audit.py`
- Create: `tests/test_group_split_assignment.py`
- Create: `tests/test_validate_group_split.py`
- Modify: `tests/test_long_document_chunking.py`
- Do not modify Python detector/evidence/judge/rag packages, datasets/raw, or experiment JSON by hand

## Shared interfaces

```python
def load_benchmark_audit_config(path) -> dict:
    # keys: ngram_size:int, near_template_threshold:float, tune_target_ratio:float

def audit_template_records(rows, ngram_size: int, threshold: float) -> dict:
    # rows: list[{"path": str, "text": str}]
    # returns at least:
    # exact_skeleton_overlap_groups: int
    # near_template_pairs: list[{"paths":[str,str], "similarity": float}]
    # connected_template_groups: int
    # cross_split_template_overlap: int
    # template_clusters: list[{"cluster_id": str, "paths": list[str]}]

def assign_group_splits(records, ngram_size: int, threshold: float, tune_target_ratio: float) -> list[dict]:
    # records: list[{"document_id","original_label","benchmark_text"}]
    # each output row: {document_id, original_label, group_id, assigned_split}
    # assigned_split in {"development_tune","development_generalization"}

def validate_group_records(tune_rows, gen_rows, ngram_size: int, threshold: float) -> dict:
    # independently rebuilds connected components
    # connected_template_group_overlap counts components with members in BOTH splits
    # must not set connected_template_group_overlap equal to fingerprint-set intersection
```

### Assignment algorithm (Task 2, copy verbatim)

1. `components, _ = build_template_groups(records, ngram_size, threshold)`.
2. `group_id = sha256("|".join(sorted(document_id for each member)).encode()).hexdigest()[:16]`.
3. Sort groups by `group_id` ascending. Never split a group.
4. `tune_target_n = round(n_total * tune_target_ratio)`; `gen_target_n = n_total - tune_target_n`.
5. For each label `lab`: `tune_target[lab] = round(count[lab] * tune_target_ratio)`; `gen_target[lab] = count[lab] - tune_target[lab]`.
6. Greedy: for each group, score each split (higher is better):

```python
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
```

7. Assign to the split with the higher score. If equal, `development_tune`.
8. Update that split's counts and size.

---

### Task 1: Template audit uses connected components and yaml

**Files:**
- Modify: `src/zhiyu/datasets/template_similarity.py`
- Modify: `scripts/audit_template_similarity.py`
- Create: `tests/test_template_audit.py`

**Interfaces:**
- Consumes: `build_template_groups(records, n, threshold) -> (groups, pairs)`
- Produces: `load_benchmark_audit_config(path)`, `audit_template_records(rows, ngram_size, threshold)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_template_audit.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_template_audit.py -q`
Expected: FAIL because `load_benchmark_audit_config` is missing and/or `audit_template_records` still treats exact fingerprint buckets as connected groups (current `connected_template_groups == exact_skeleton_overlap_groups`).

- [ ] **Step 3: Write minimal implementation**

Add to `src/zhiyu/datasets/template_similarity.py`:

```python
from pathlib import Path
import yaml

def load_benchmark_audit_config(path):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {
        "ngram_size": int(data["ngram_size"]),
        "near_template_threshold": float(data["near_template_threshold"]),
        "tune_target_ratio": float(data["tune_target_ratio"]),
    }
```

Rewrite `scripts/audit_template_similarity.py` so `audit_template_records` calls `build_template_groups(rows, ngram_size, threshold)`, counts exact fingerprint groups with size>1 separately, sets `connected_template_groups` to the number of union-find components, sets `template_clusters` from those components, sets `near_template_pairs` from returned pairs (paths + similarity), and sets `cross_split_template_overlap` to the number of connected components whose paths have more than one first path segment. `main()` loads yaml via `load_benchmark_audit_config(ROOT/"configs/benchmark_audit.yaml")` and must not hardcode `5` or `0.8`. Keep scanning the same raw splits through `DatasetPolicy` as today.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_template_audit.py -q`
Expected: PASS

- [ ] **Step 5: Do not commit**

Leave the working tree dirty. Do not `git commit` or `git push`.

---

### Task 2: Deterministic group-aware stratified assignment

**Files:**
- Modify: `scripts/build_group_split.py`
- Create: `tests/test_group_split_assignment.py`

**Interfaces:**
- Consumes: `build_template_groups`, `load_benchmark_audit_config`
- Produces: `assign_group_splits(records, ngram_size, threshold, tune_target_ratio)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_group_split_assignment.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_group_split_assignment.py -q`
Expected: FAIL. Current builder fills `development_tune` by sorted `group_id` until the size target; with eight singleton groups and target 0.5 it can place all poison in one split. `assign_group_splits` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement `assign_group_splits` in `scripts/build_group_split.py` using the assignment algorithm above. `main()` must load yaml (`ngram_size`, `near_template_threshold`, `tune_target_ratio`) and call `assign_group_splits`. Do not hardcode `5`, `0.8`, or `0.7`. Keep writing the same output files as today (`development_group_split.json` and the four processed JSONL files). Do not run `main()` against frozen data for tuning. Do not modify `datasets/raw/`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_group_split_assignment.py tests/test_group_split.py -q`
Expected: `test_group_split_assignment.py` PASS. `test_group_split.py` may still read the old manifest; do not hand-edit that manifest. If it fails only because artifacts are stale, leave regeneration to the controller after all tasks.

- [ ] **Step 5: Do not commit**

---

### Task 3: Validator recomputes connected-component overlap

**Files:**
- Modify: `scripts/validate_group_split.py`
- Create: `tests/test_validate_group_split.py`

**Interfaces:**
- Consumes: `build_template_groups`, `load_benchmark_audit_config`
- Produces: `validate_group_records(tune_rows, gen_rows, ngram_size, threshold)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_validate_group_split.py
from zhiyu.datasets.template_similarity import template_fingerprint
from validate_group_split import validate_group_records

BASE = "shared campus notice template body for students and faculty " * 12

def test_connected_overlap_is_not_fingerprint_overlap():
    tune = [{"document_id": "t1", "benchmark_text": BASE + " AAA"}]
    gen = [{"document_id": "g1", "benchmark_text": BASE + " BBB"}]
    assert template_fingerprint(tune[0]["benchmark_text"]) != template_fingerprint(gen[0]["benchmark_text"])
    result = validate_group_records(tune, gen, 5, 0.8)
    assert result["exact_template_fingerprint_overlap"] == 0
    assert result["connected_template_group_overlap"] == 1
    assert result["pass"] is False

def test_separated_unrelated_templates_have_zero_connected_overlap():
    tune = [{"document_id": "t1", "benchmark_text": ("alpha-poison-") * 25}]
    gen = [{"document_id": "g1", "benchmark_text": ("hotel-normal-") * 25}]
    result = validate_group_records(tune, gen, 5, 0.8)
    assert result["connected_template_group_overlap"] == 0
    assert result["exact_template_fingerprint_overlap"] == 0
    assert result["pass"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validate_group_split.py -q`
Expected: FAIL. Current validator sets `connected_template_group_overlap` to fingerprint-set intersection, so the first test sees `0` instead of `1`.

- [ ] **Step 3: Write minimal implementation**

`validate_group_records` must:
1. Concatenate tune+gen rows.
2. Call `build_template_groups(all_rows, ngram_size, threshold)` again. Do not read `development_group_split.json` for overlap.
3. `connected_template_group_overlap` = number of components whose `document_id`s appear in both splits.
4. Independently recompute document_id, exact text, normalized text, fingerprint, and near-template pair overlaps.
5. `near_template_pair_overlap` counts pairs returned by `build_template_groups` that cross splits (or equivalent independent pairwise Jaccard >= threshold).
6. `pass` is true only when every overlap field is 0.
7. `main()` reads the two processed JSONL files, loads yaml, writes `datasets/manifests/development_group_split_validation.json`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validate_group_split.py -q`
Expected: PASS

- [ ] **Step 5: Do not commit**

---

### Task 4: Four long-document chunk tests

**Files:**
- Modify: `tests/test_long_document_chunking.py`
- Do not modify `src/zhiyu/parser/chunker.py` unless a new test fails for a real offset bug

**Interfaces:**
- Consumes: `Chunker` and `configs/chunking.yaml`
- Produces: four tests (Chinese ~2x, English ~5x, mixed ~10x, multi-paragraph)

- [ ] **Step 1: Write the tests**

Replace/extend `tests/test_long_document_chunking.py`:

```python
import yaml
from pathlib import Path
from zhiyu.parser.chunker import Chunker

ROOT = Path(__file__).resolve().parents[1]

def load_chunker():
    cfg = yaml.safe_load((ROOT / "configs/chunking.yaml").read_text(encoding="utf-8"))
    return Chunker(**cfg), cfg["chunk_size_chars"], cfg["chunk_overlap_chars"]

def assert_chunks(doc, chunker, overlap, min_chunks):
    chunks = chunker.chunk(doc)
    assert chunks == chunker.chunk(doc)
    assert len(chunks) >= min_chunks
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
        assert c.text == doc.text[c.start_char:c.end_char]
        assert c.text.strip() and 0 < len(c.text) <= chunker.size
        if i and chunks[i-1].end_char > c.start_char:
            assert chunks[i-1].end_char - c.start_char == overlap

def test_chinese_about_2x_chunk_size(make_document):
    chunker, size, overlap = load_chunker()
    text = "中文内容验证。" * (2 * size // 7 + 3)
    assert abs(len(text) / size - 2) < 0.4
    assert_chunks(make_document(text), chunker, overlap, 2)

def test_english_about_5x_chunk_size(make_document):
    chunker, size, overlap = load_chunker()
    text = "English chunking verification text. " * (5 * size // 36 + 3)
    assert abs(len(text) / size - 5) < 0.4
    assert_chunks(make_document(text), chunker, overlap, 5)

def test_mixed_about_10x_chunk_size(make_document):
    chunker, size, overlap = load_chunker()
    text = "中文 English mix. " * (10 * size // 18 + 3)
    assert abs(len(text) / size - 10) < 0.5
    assert_chunks(make_document(text), chunker, overlap, 10)

def test_multiparagraph_long_text(make_document):
    chunker, size, overlap = load_chunker()
    paragraph = "第一段内容。" * 40 + "\n\n" + "Second paragraph content. " * 40
    text = (paragraph + "\n\n") * 8
    assert "\n\n" in text
    assert len(text) > 2 * size
    assert_chunks(make_document(text), chunker, overlap, 2)
```

Keep `test_long_bilingual_offsets` or delete it if fully superseded; do not leave duplicate weak tests that skip the four required cases.

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_long_document_chunking.py -q`
Expected: PASS on current Chunker if offsets already work. If FAIL for a real bug, fix only `chunker.py` enough to restore the offset/slice/overlap contract. Do not retune chunk_size from frozen data.

- [ ] **Step 3: Do not commit**

---

## Controller after Tasks 1-4

Only after every Task review is clean:

1. `python scripts/audit_template_similarity.py`
2. `python scripts/build_group_split.py`
3. `python scripts/validate_group_split.py`
4. `pytest -q`
5. `python scripts/raw_integrity.py after`
6. `git diff --check`
7. `git diff`
8. `git status`
9. Write `experiments/phase1_5_final_completion_report.md` from those real outputs only
10. One commit `phase 1.5 final: complete benchmark validation foundation` and `git push origin main`
11. STOP. Do not start Phase 2.
