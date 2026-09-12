# Phase 5 Replacement Unified Judge Evaluation

frozen replacement bundle

## rule_only_baseline
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 75, 'REVIEW': 0, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 0

## rule_plus_semantic_baseline
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 46, 'REVIEW': 29, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 0

## full_evidence_no_judge
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 4, 'REVIEW': 71, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 0

## full_judge
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 1, 'REVIEW': 74, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 0

- judge_call_count: 93
- judge_status_counts: {'OK': 22, 'INVALID_OUTPUT': 71, 'ERROR': 0}
- transitions: {'SAFE->REVIEW': 3}
