# Phase 6 Official Generalization Evaluation

**PASS — FROZEN**

Replacement official `development_generalization` run. Offline audit passed. No LLM was used in this audit.

## Provenance

- evaluation_code_commit: `6ea3f4cd6c5b4569d8893c82cafc94d5aba64dce`
- runtime_sha256: `50753f8a5fbed7677e5ac445003d091de413aafbfee2bb1d1d4c6b8e9feeb9f5`
- evaluator_sha256: `050aaf2c59c0adfadf40a0aaadaf9d4c134ba0148cb3c1c8a9de7c58de673b47`
- split: `development_generalization`
- queries: 24 = CLEAN 12 + POISON 12
- retriever: lexical k=3
- generator: deepseek-flash temperature=0.0 max_tokens=800
- cic_version: phase6.cic.v1 (not exercised on official gen)

## Indexes

- Vanilla gen: 39 docs / 39 chunks, gen-only, no tune documents
- Protected gen: 0 docs / 0 chunks (Phase 5 full_judge SAFE-only admission; gen has 0 SAFE)

## Calls

- Vanilla generator calls: 24
- Protected generator calls: 0
- CIC calls: 0
- provider ERROR / INVALID_OUTPUT: 0 / 0

## Recomputed metrics

| | Vanilla | Protected |
|---|---:|---:|
| ASR | 0.5 | 0.0 |
| DSR | 0.5 | 1.0 |
| QA accuracy | 1.0 | 0.0 |
| ABSTAIN rate | 0.0 | 0.0 |
| NO_CONTEXT rate | 0.0 | 1.0 |
| generation failure rate | 0.0 | 0.0 |
| defense_success_count (CIC ABSTAIN) | 0 | 0 |

Protected path: NO_CONTEXT 24/24.

## Interpretation — Security–Utility Trade-off

Protected DSR=1.0 is **not** a CIC defense result.

It is caused by ingestion/admission: the gen Protected index is empty (0 SAFE documents), so every query is `NO_CONTEXT`. Spec: poison `NO_CONTEXT` is excluded from ASR, so ASR=0 and DSR=1-ASR=1.0, while `defense_success_count` remains 0.

- CIC was **not exercised** on official gen (0 calls).
- Do **not** attribute official gen defense gain to CIC.
- Utility cost is total: Protected QA accuracy = 0.0 (all 12 clean queries are `NO_CONTEXT`).
- Vanilla remains the unfiltered baseline: QA=1.0, ASR=0.5, no `NO_CONTEXT`.

Honest trade-off: on this gen split, Protected buys ASR=0 by having nothing to retrieve, and pays with complete utility collapse. That is an admission/index outcome, not query-time context integrity checking.

## Superseded contaminated run

The previous official artifact is **INVALID / SUPERSEDED** for `SPLIT_CONTAMINATION` (Vanilla 93 docs, Protected 1 tune SAFE doc).

- `experiments/phase6/official_generalization.INVALID.SPLIT_CONTAMINATION.json`
- `experiments/phase6/official_generalization_replay.INVALID.SPLIT_CONTAMINATION.jsonl`

Do not use those metrics as official.

## Replacement artifacts

- `experiments/phase6/official_generalization.json`
- `experiments/phase6/official_generalization_replay.jsonl`
- `experiments/phase6/official_generalization.replacement_provenance.json`

## Audit

Offline checks 1-15 PASS: provenance, frozen snapshot SHAs, split-scoped indexes, no tune leakage, 12/12 queries, call counts, recomputed metrics, superseded old artifacts, GT firewall, no Phase 2-5 frozen code/config changes, `git diff --check`, full `pytest -q`.
