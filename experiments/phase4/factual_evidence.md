# Phase 4 Factual Evidence Evaluation

experiment_kind: REAL LLM

## development_tune
- documents: 81
- claim_extraction_status_counts: {'OK': 54, 'INVALID_OUTPUT': 13, 'ERROR': 14}
- claim_count: 162
- retrieval_status_counts: {'OK': 162}
- overlap_rejection_count: 0
- pairwise_relation_counts: {'NOT_ENOUGH': 161, 'CONTRADICTS': 76, 'SUPPORTS': 243}
- comparison_status_counts: {'OK': 160, 'INVALID_OUTPUT': 2}
- factual_evidence_relation_counts: {'INSUFFICIENT_EVIDENCE': 52, 'CONTRADICTORY': 27, 'SUPPORTED': 81}
- llm_call_count: 243

## development_generalization
- documents: 45
- claim_extraction_status_counts: {'OK': 23, 'ERROR': 15, 'INVALID_OUTPUT': 7}
- claim_count: 69
- retrieval_status_counts: {'OK': 69}
- overlap_rejection_count: 0
- pairwise_relation_counts: {'NOT_ENOUGH': 112, 'SUPPORTS': 21, 'CONTRADICTS': 68}
- comparison_status_counts: {'OK': 67, 'INVALID_OUTPUT': 2}
- factual_evidence_relation_counts: {'INSUFFICIENT_EVIDENCE': 37, 'SUPPORTED': 7, 'CONTRADICTORY': 23}
- llm_call_count: 114

- overlap_audit_pass: True
- reference_count: 54
