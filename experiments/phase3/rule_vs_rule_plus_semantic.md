# Phase 3 Rule Only vs Rule + Semantic

experiment_kind: REAL LLM
REVIEW is not counted as detection success.
conflict is excluded from primary Precision/Recall/F1/FPR.
frozen/external were not used.

## development_tune

### rule_only_baseline
- documents: 123
- tp/fp/tn/fn: 18/0/69/12
- precision: 1.0
- recall: 0.6
- f1: 0.7499999999999999
- fpr: 0.0
- hard_negative_poison_rate: 0.0
- poison_review_rate: 0.0

### rule_plus_semantic_baseline
- documents: 123
- tp/fp/tn/fn: 18/0/69/12
- precision: 1.0
- recall: 0.6
- f1: 0.7499999999999999
- fpr: 0.0
- hard_negative_poison_rate: 0.0
- poison_review_rate: 0.0

- semantic_diagnostics: {'semantic_call_count': 105, 'semantic_skip_count': 18, 'semantic_error_count': 0, 'invalid_output_count': 0, 'status_counts': {'OK': 105, 'SKIPPED': 18}, 'behavior_evidence_by_confidence': {}, 'behavior_evidence_by_mechanism': {}}

- deltas: {'delta_recall': 0.0, 'delta_f1': 0.0, 'delta_fpr': 0.0, 'delta_hard_negative_poison_rate': 0.0}

## development_generalization

### rule_only_baseline
- documents: 57
- tp/fp/tn/fn: 0/0/30/15
- precision: None
- recall: 0.0
- f1: None
- fpr: 0.0
- hard_negative_poison_rate: 0.0
- poison_review_rate: 0.0

### rule_plus_semantic_baseline
- documents: 57
- tp/fp/tn/fn: 0/0/30/15
- precision: None
- recall: 0.0
- f1: None
- fpr: 0.0
- hard_negative_poison_rate: 0.0
- poison_review_rate: 0.0

- semantic_diagnostics: {'semantic_call_count': 57, 'semantic_skip_count': 0, 'semantic_error_count': 0, 'invalid_output_count': 0, 'status_counts': {'OK': 57}, 'behavior_evidence_by_confidence': {}, 'behavior_evidence_by_mechanism': {}}

- deltas: {'delta_recall': 0.0, 'delta_f1': None, 'delta_fpr': 0.0, 'delta_hard_negative_poison_rate': 0.0}

## Manifest

- experiment_kind: REAL LLM
- phase2_commit: 58b9843b48c77ccd6bc86645c2e2446be477bccf
- evaluation_code_commit: 7891ec59198ac02e8bc157a87219197aba009533
- official benchmark ran before this review-fix; metrics were not rerun or hand-edited
- review-fix did not change Prompt
