# ZhiYu Phase 4 Completion Report

Factual Evidence Layer. No SAFE/REVIEW/POISON mapping. Not Phase 5.

## Implementation

- Independent frozen Trusted Reference Corpus: 54 official-normal documents
- Derived Phase 4 candidate view (does not rewrite Phase 2/3 benchmark artifacts)
- Claim extraction + unique source binding
- Generic lexical retrieval TOP_K=3, overlap filter, no similarity threshold
- One LLM comparison call per claim
- Deterministic aggregation to FactualEvidence

## Reference corpus

- count: 54
- corpus_sha256: 62364b82b1481f08d47a681118f1d2f81f19fefe408ca873abab93f599bc76f3
- overlap audit: pass, remaining_overlap_count=0
- Phase 2/3 frozen artifact hashes unchanged

## Tests

- targeted Phase 4 tests passed
- pytest -q: 184 passed
- git diff --check: run at commit
- DeepSeek smoke: claim OK 1, compare OK 2

## Official evaluation (REAL LLM, one run)

development_tune (81 docs): claims=162; extraction OK/INVALID/ERROR=54/13/14; retrieval OK=162; pairwise SUPPORTS/CONTRADICTS/NOT_ENOUGH=243/76/161; FactualEvidence SUPPORTED/CONTRADICTORY/INSUFFICIENT=81/27/52; llm_calls=243

development_generalization (45 docs): claims=69; extraction OK/INVALID/ERROR=23/7/15; FactualEvidence SUPPORTED/CONTRADICTORY/INSUFFICIENT=7/23/37; llm_calls=114

ERROR/INVALID are analysis failures, not poison labels. No second run. No generalization sample inspection.

## Limits

- Phase 4 does not decide SAFE/REVIEW/POISON
- INSUFFICIENT_EVIDENCE != POISON
- Some extraction ERROR/INVALID occurred during the official run
- No Judge / RAG / Web

## Hard Stop

Phase 4 complete. STOP. Do not enter Phase 5.
