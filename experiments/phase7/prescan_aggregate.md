# Phase 7 Demo Prescan Aggregate

Real DeepSeek prescan. No reruns. No prompt/rule/threshold tuning.

- model: deepseek-flash
- base_url: https://api.deepseek.com
- documents: 38/38
- provider_calls_this_run: {'semantic': 32, 'factual': 81, 'judge': 32}

## SAFE / REVIEW / POISON by intended mechanism
- FACT_TAMPERING: REVIEW=5
- HARD_NEGATIVE: REVIEW=2
- HIDDEN_INSTRUCTION: POISON=3
- KNOWLEDGE_CONFLICT: REVIEW=4
- PROMPT_INJECTION: POISON=3
- RETRIEVAL_HIJACKING: REVIEW=4
- SAFE: REVIEW=17

## SAFE / REVIEW / POISON by intended role
- ATTACK: POISON=6, REVIEW=9
- CONFLICT: REVIEW=4
- HARD_NEGATIVE: REVIEW=2
- SAFE: REVIEW=17

## Attack samples non-SAFE
- 15/15

## SAFE/HARD_NEGATIVE remaining SAFE
- 0/19

## Demo suitability
- GOOD_DEMO: SAFE/HARD_NEGATIVE+SAFE; ATTACK+POISON; CONFLICT+REVIEW
- USABLE_WITH_REVIEW: SAFE/HARD_NEGATIVE+REVIEW; ATTACK+REVIEW; CONFLICT+POISON
- NOT_SUITABLE: SAFE/HARD_NEGATIVE+POISON; ATTACK+SAFE; CONFLICT+SAFE
- GOOD_DEMO: 10
- USABLE_WITH_REVIEW: 28
- NOT_SUITABLE: 0

## ERROR / INVALID_OUTPUT
- judge_status: INVALID_OUTPUT=27, OK=11
- docs_with_component_ERROR: 8
- docs_with_component_INVALID_OUTPUT: 5
- docs_with_provider_errors_invalid: 13
- provider_errors_invalid_sum: 14

## Artifact paths
- experiments/phase7/prescan_final.json
- experiments/phase7/prescan_checkpoint.jsonl
- experiments/phase7/prescan_aggregate.json
- experiments/phase7/prescan_aggregate.md
