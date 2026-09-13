# Phase 5 Unified Judge Evaluation

same frozen bundle for all ablations

## rule_only_baseline
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 75, 'REVIEW': 0, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 57

## rule_plus_semantic_baseline
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 46, 'REVIEW': 29, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 28

## full_evidence_no_judge
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 2, 'REVIEW': 73, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 0

## full_judge
- primary: {'tp': 18, 'fp': 0, 'tn': 33, 'fn': 27, 'precision': 1.0, 'recall': 0.4, 'f1': 0.5714285714285715, 'fpr': 0.0}
- decisions: {'SAFE': 0, 'REVIEW': 75, 'POISON': 18}
- judge_only_poison_count: 0
- unsafe_safe_on_failure_count: 0

- transitions: {'SAFE->REVIEW': 2}
