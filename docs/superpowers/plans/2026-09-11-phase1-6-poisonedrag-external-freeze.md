# Phase 1.6 PoisonedRAG External Benchmark Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze official PoisonedRAG nq / hotpotqa / msmarco adv-targeted JSON as an external evaluation-only benchmark, with provenance, a lossless adapter, Detector isolation, and honest validation.

**Architecture:** Keep datasets/raw/trusted_provenance untouched. Store PoisonedRAG under datasets/external_frozen/poisonedrag/. Adapter expands each adv_texts item into one evaluator record. DetectionInput is unchanged; a converter copies only text. DatasetPolicy never lists PoisonedRAG as development.

**Tech Stack:** Python 3.10+, pytest, PyYAML, git sparse clone, existing zhiyu.models.detection.DetectionInput.

**Spec:** User Phase 1.6 request plus AGENTS.md. Upstream JSON shape: object keyed by case id; each value has id, question, correct answer, incorrect answer, adv_texts. LICENSE is MIT.

## Global Constraints

- Do not modify datasets/raw/ (trusted_provenance).
- Do not download or commit the full PoisonedRAG repo or BEIR corpus.
- Do not regenerate poisoning data.
- PoisonedRAG is external_frozen evaluation only. Never write it into development_tune or development_generalization.
- Do not use it to write rules, tune prompts/thresholds, pick models, or patch failed samples.
- Do not implement Detector, Rule, LLM, Evidence Retrieval, Judge, RAG, frontend, or training.
- Do not change DetectionInput security boundary.
- Do not guess extra attack types from text. attack_family is the constant KNOWLEDGE_CORRUPTION.
- Do not edit upstream JSON bytes to make tests pass.
- Do not git commit or push inside a Task. Controller makes one stage-end commit.
- Work in D:/Projects/知御/zhiyu on main.
- TDD for Tasks 1-4: RED then GREEN then REFACTOR.

## Paths

datasets/external_frozen/poisonedrag/raw/{nq,hotpotqa,msmarco}.json
datasets/external_frozen/poisonedrag/SOURCE.md
datasets/external_frozen/poisonedrag/SOURCE_LICENSE
datasets/external_frozen/poisonedrag/processed/{nq,hotpotqa,msmarco,poisonedrag_external}.jsonl
datasets/manifests/poisonedrag_provenance.json
datasets/manifests/poisonedrag_validation.json

Upstream copy only: results/adv_targeted_results/{nq,hotpotqa,msmarco}.json and LICENSE.

## Shared interfaces

DATASETS = ("nq", "hotpotqa", "msmarco")
ATTACK_FAMILY = "KNOWLEDGE_CORRUPTION"
UPSTREAM_URL = "https://github.com/sleeepeer/PoisonedRAG.git"
external_sample_id(dataset, case_id, index) -> "poisonedrag:{dataset}:{case_id}:{index}"
expand_case(dataset, case_id, case) -> list[dict]  # ValueError on malformed; no silent skip
to_detection_input(record) -> DetectionInput  # only id + text
Evaluator record keys: external_sample_id, upstream_dataset, upstream_case_id, adv_text_index, text, question, correct_answer, target_answer, source=poisonedrag, attack_family=KNOWLEDGE_CORRUPTION, upstream_metadata


---

### Task 1: Freeze upstream files and provenance

**Files:**
- Create: scripts/import_poisonedrag_raw.py
- Create: tests/test_poisonedrag_import.py
- Create by running import once: datasets/external_frozen/poisonedrag/raw/*.json, SOURCE.md, SOURCE_LICENSE, datasets/manifests/poisonedrag_provenance.json

**Interfaces:**
- Consumes: https://github.com/sleeepeer/PoisonedRAG.git
- Produces: byte-identical copies of three JSON files plus LICENSE; provenance JSON

- [ ] **Step 1: Write failing tests**

tests/test_poisonedrag_import.py must import copy_frozen_files, write_provenance, REQUIRED_FILES from import_poisonedrag_raw.

test_copy_is_byte_identical_and_records_sha256(tmp_path): seed fake upstream results/adv_targeted_results/{nq,hotpotqa,msmarco}.json plus LICENSE; copy_frozen_files(src, dest); assert dest/raw files equal original bytes; result[name] sha256/bytes/cases match; SOURCE_LICENSE copied.

test_copy_refuses_overwrite(tmp_path): second copy_frozen_files raises FileExistsError.

Seed nq.json with two cases so cases==2.

- [ ] **Step 2: Run RED**

Run: .venv/Scripts/python.exe -m pytest tests/test_poisonedrag_import.py -q
Expected: missing copy_frozen_files.

- [ ] **Step 3: Minimal implementation**

REQUIRED_FILES = ("nq.json", "hotpotqa.json", "msmarco.json")
copy_frozen_files(upstream_root, dest_root) copies those files into dest_root/raw/ as raw bytes, copies LICENSE to dest_root/SOURCE_LICENSE, returns per-file {sha256, bytes, cases} where cases=len(json.loads). Refuse if any dest raw file exists.

write_provenance writes JSON: upstream_repository_url, upstream_commit, downloaded_at, license=MIT License, files map.

main():
1. Sparse-clone into a temp dir: git clone --filter=blob:none --sparse URL; git sparse-checkout set LICENSE results/adv_targeted_results
2. git rev-parse HEAD
3. copy into datasets/external_frozen/poisonedrag/
4. Write SOURCE.md (URL, commit, date Asia/Shanghai, MIT, three files) and datasets/manifests/poisonedrag_provenance.json
5. Delete the temp clone
6. Do not copy any other upstream path

- [ ] **Step 4: GREEN tests then freeze real files**

Unit tests PASS. Then run python scripts/import_poisonedrag_raw.py once. Do not modify JSON content.

- [ ] **Step 5: Do not commit**


### Task 2: PoisonedRAG adapter

**Files:**
- Create: src/zhiyu/datasets/poisonedrag_adapter.py
- Create: scripts/build_poisonedrag_external.py
- Create: tests/test_poisonedrag_adapter.py

**Interfaces:**
- Consumes: raw JSON object of cases
- Produces: expand_case, expand_dataset, external_sample_id, processed JSONL

- [ ] **Step 1: Write failing tests**

```python
# tests/test_poisonedrag_adapter.py
import json
import pytest
from zhiyu.datasets.poisonedrag_adapter import expand_case, expand_dataset, external_sample_id

CASE = {
    "id": "c1",
    "question": "Q?",
    "correct answer": "yes",
    "incorrect answer": "no",
    "adv_texts": ["p0", "p1", "p2"],
    "extra": "keep",
}

def test_expands_each_adv_text():
    rows = expand_case("nq", "c1", CASE)
    assert [r["adv_text_index"] for r in rows] == [0, 1, 2]
    assert [r["text"] for r in rows] == ["p0", "p1", "p2"]
    assert all(r["question"] == "Q?" and r["correct_answer"] == "yes" and r["target_answer"] == "no" for r in rows)
    assert all(r["source"] == "poisonedrag" and r["attack_family"] == "KNOWLEDGE_CORRUPTION" for r in rows)
    assert all(r["upstream_metadata"]["extra"] == "keep" for r in rows)

def test_external_sample_id_is_deterministic():
    a = expand_case("nq", "c1", CASE)
    b = expand_case("nq", "c1", CASE)
    assert [r["external_sample_id"] for r in a] == [r["external_sample_id"] for r in b]
    assert a[1]["external_sample_id"] == external_sample_id("nq", "c1", 1) == "poisonedrag:nq:c1:1"

def test_malformed_case_fails_loudly():
    with pytest.raises(ValueError):
        expand_case("nq", "c1", {"id": "c1", "question": "Q?"})

def test_rebuild_is_deterministic():
    data = {"c1": CASE, "c0": {**CASE, "id": "c0"}}
    assert expand_dataset("nq", data) == expand_dataset("nq", data)
```

- [ ] **Step 2: RED** — pytest tests/test_poisonedrag_adapter.py -q

- [ ] **Step 3: Minimal implementation**

Required fields: question, correct answer, incorrect answer, adv_texts (list). upstream_case_id = case.get("id") or case_id. Non-list adv_texts or non-str items raise ValueError. Empty strings are kept.

expand_dataset sorts case ids then concatenates expand_case.

build_poisonedrag_external.py reads the three raw files, writes four JSONL files (nq, hotpotqa, msmarco, poisonedrag_external) with json.dumps(record, ensure_ascii=False)+newline. Unified file concatenates nq, hotpotqa, msmarco in that order. Do not write into datasets/processed/trusted_provenance/. No LLM. Do not change raw.

- [ ] **Step 4: GREEN**
- [ ] **Step 5: Do not commit**


### Task 3: Isolation and DetectionInput leakage protection

**Files:**
- Modify: configs/dataset_policy.yaml
- Modify: src/zhiyu/dataset.py
- Modify: tests/test_dataset_policy.py
- Modify: tests/test_detection_input.py
- Modify: docs/experiment_protocol.md
- Modify: src/zhiyu/datasets/poisonedrag_adapter.py (to_detection_input)

**Interfaces:**
- to_detection_input(record) -> DetectionInput
- dataset_policy.yaml external_frozen: [poisonedrag]

- [ ] **Step 1: Write failing tests**

Add to tests/test_detection_input.py:

```python
@pytest.mark.parametrize("kwargs", [
    {"question": "q"},
    {"correct_answer": "a"},
    {"target_answer": "b"},
    {"ground_truth": "g"},
])
def test_detection_input_rejects_poisonedrag_evaluator_fields(kwargs):
    with pytest.raises(TypeError):
        DetectionInput("d", "c", "text only", **kwargs)

def test_to_detection_input_strips_evaluator_fields():
    from zhiyu.datasets.poisonedrag_adapter import to_detection_input, expand_case
    row = expand_case("nq", "c1", {
        "id": "c1", "question": "Q?", "correct answer": "yes",
        "incorrect answer": "no", "adv_texts": ["payload"],
    })[0]
    value = to_detection_input(row)
    dumped = value.to_dict()
    assert dumped["text"] == "payload"
    for key in ("question", "correct_answer", "target_answer", "correct answer",
                "incorrect answer", "upstream_dataset", "attack_family",
                "original_label", "is_poison", "expected_answer"):
        assert key not in dumped
        assert key not in json.dumps(dumped)
```

Add to tests/test_dataset_policy.py:

```python
def test_poisonedrag_is_not_a_development_split():
    policy = DatasetPolicy(ROOT)
    assert "poisonedrag" not in policy.config["development"]
    assert policy.config["external_frozen"] == ["poisonedrag"]
    with pytest.raises(PermissionError):
        list(policy.files("poisonedrag"))

def test_build_records_does_not_read_external_frozen(monkeypatch):
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert "external_frozen" not in str(path).replace("\\", "/")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    documents, _ = build_records(ROOT)
    assert {d.source_split for d in documents} == {"demo_set", "dev_set"}
```

- [ ] **Step 2: RED** — pytest tests/test_detection_input.py tests/test_dataset_policy.py -q

- [ ] **Step 3: Minimal implementation**

Do not add fields to DetectionInput or RuntimeContext.

to_detection_input(record) returns DetectionInput(record["external_sample_id"], record["external_sample_id"], record["text"]).

dataset_policy.yaml add:
external_frozen:
  - poisonedrag

DatasetPolicy must require config["external_frozen"] == ["poisonedrag"] and must not add poisonedrag to files() allowed splits.

docs/experiment_protocol.md must state:
1. PoisonedRAG = external_frozen
2. Phase 2 must not change rules from this set's failures
3. Do not browse failed samples case-by-case during development
4. Aggregate metrics only unless the user explicitly approves error analysis
5. Final reports must separate internal generalization vs external cross-dataset generalization

- [ ] **Step 4: GREEN**
- [ ] **Step 5: Do not commit**


### Task 4: Validator, trusted_provenance raw integrity, Data Card

**Files:**
- Create: scripts/validate_poisonedrag_external.py
- Create: tests/test_poisonedrag_validation.py
- Modify: datasets/DATA_CARD.md

**Interfaces:**
- validate(root) -> dict written to datasets/manifests/poisonedrag_validation.json

- [ ] **Step 1: Write failing tests**

```python
# tests/test_poisonedrag_validation.py
from pathlib import Path
from validate_poisonedrag_external import validate
ROOT = Path(__file__).resolve().parents[1]

def test_validator_counts_match_independent_recompute():
    result = validate(ROOT)
    assert result["raw_file_count"] == 3
    assert result["raw_unmodified"] is True
    assert result["duplicate_sample_ids"] == 0
    assert result["processed_rebuild_matches"] is True
    assert result["pass"] is True
    assert result["samples_total"] == sum(result["samples_by_dataset"].values())
    assert set(result["samples_by_dataset"]) == {"nq", "hotpotqa", "msmarco"}
    for row in result["files"]:
        assert row["sha256"] == row["provenance_sha256"]

def test_empty_text_is_reported_not_dropped():
    result = validate(ROOT)
    assert "empty_text" in result
```

- [ ] **Step 2: RED**

- [ ] **Step 3: Implementation**

Validator independently:
1. Hashes current raw files; compares to poisonedrag_provenance.json
2. Reloads raw JSON, re-runs expand_dataset, compares to processed JSONL records
3. Counts cases, samples, per-dataset samples, duplicate ids, empty text
4. Confirms every processed row traces to upstream case id + adv_text_index whose text equals adv_texts[index]
5. pass requires: 3 raw files, sha256 match, duplicate ids 0, rebuild match, raw unmodified. Empty text does not fail pass; it is reported
6. Must not trust builder print output

Keep using existing python scripts/raw_integrity.py after for trusted_provenance.

Update datasets/DATA_CARD.md with a PoisonedRAG section:
- independent external source
- NQ / HotpotQA / MS MARCO
- distribution differs from campus trusted_provenance
- covers knowledge corruption / fact tampering
- does not prove Prompt Injection / Hidden Instruction / Retrieval Hijacking generalization
- currently mainly poison samples
- alone cannot prove cross-domain FPR
- still need external clean controls and a true independent blind set
Do not inflate claims.

- [ ] **Step 4: GREEN**
- [ ] **Step 5: Do not commit**

---

## Controller after Tasks 1-4

1. python scripts/import_poisonedrag_raw.py (skip if raw already frozen; do not overwrite)
2. python scripts/build_poisonedrag_external.py
3. python scripts/validate_poisonedrag_external.py
4. python scripts/raw_integrity.py after
5. pytest -q
6. git diff --check ; git diff ; git status
7. Write experiments/phase1_6_completion_report.md from real outputs (user sections A-M)
8. Final independent review
9. Commit message: phase 1.6: freeze poisonedrag external benchmark
10. git push origin main (no force)
11. STOP. Do not start Phase 2.
