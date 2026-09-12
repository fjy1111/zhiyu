# ZhiYu Phase 4 Completion Report

Factual Evidence Layer. No SAFE/REVIEW/POISON mapping. Not Phase 5.

Previous REAL LLM run is SUPERSEDED because runtime content_hash overlap/provenance was invalid. This replacement run was performed once after the deterministic hash/dedup fix. No prompt change. No generalization sample inspection.

## Implementation-fix commit

e326a181500e5d12ea75914ea2f419dfb90e7c6b

- content_hash := sha256(runtime detector-visible text) for references and candidates
- unique reference texts by content_hash (keep lexicographically smallest document_id)
- overlap audit recomputes hashes from runtime text

## Corpus

- source_reference_document_count: 54
- unique_reference_text_count: 8
- candidate tune documents: 54
- candidate generalization documents: 39
- overlap audit: pass, remaining_overlap_count=0
- Phase 2/3 frozen artifact hashes unchanged

## Tests

- pytest -q: 186 passed (before replacement eval)
- git diff --check: passed on implementation commit
- DeepSeek smoke: previously PASS; prompts unchanged

## Replacement official evaluation (REAL LLM, one run)

evaluation_code_commit: e326a181500e5d12ea75914ea2f419dfb90e7c6b
working_tree_tracked_clean: true

development_tune (54 docs): claims=108; extraction OK/INVALID/ERROR=36/5/13; pairwise SUPPORTS/CONTRADICTS/NOT_ENOUGH=27/17/232; FactualEvidence SUPPORTED/CONTRADICTORY/INSUFFICIENT=27/7/58; llm_calls=162

development_generalization (39 docs): claims=69; extraction OK/INVALID/ERROR=23/2/14; pairwise SUPPORTS/CONTRADICTS/NOT_ENOUGH=5/14/161; FactualEvidence SUPPORTED/CONTRADICTORY/INSUFFICIENT=5/8/47; llm_calls=108

ERROR/INVALID are analysis failures, not poison labels.

## Limits

- Phase 4 does not decide SAFE/REVIEW/POISON
- INSUFFICIENT_EVIDENCE != POISON
- Unique trusted texts are few after dedup (8)

STOP. Do not enter Phase 5.
