# Phase 4 Factual Evidence Evaluation

experiment_kind: REAL LLM

## development_tune
- documents: 54
- claim_extraction_status_counts: {'INVALID_OUTPUT': 5, 'OK': 36, 'ERROR': 13}
- claim_count: 108
- retrieval_status_counts: {'OK': 108}
- overlap_rejection_count: 0
- pairwise_relation_counts: {'NOT_ENOUGH': 232, 'CONTRADICTS': 17, 'SUPPORTS': 27}
- comparison_status_counts: {'ERROR': 8, 'OK': 92, 'INVALID_OUTPUT': 8}
- factual_evidence_relation_counts: {'INSUFFICIENT_EVIDENCE': 58, 'CONTRADICTORY': 7, 'SUPPORTED': 27}
- llm_call_count: 162

## development_generalization
- documents: 39
- claim_extraction_status_counts: {'OK': 23, 'ERROR': 14, 'INVALID_OUTPUT': 2}
- claim_count: 69
- retrieval_status_counts: {'OK': 69}
- overlap_rejection_count: 0
- pairwise_relation_counts: {'NOT_ENOUGH': 161, 'SUPPORTS': 5, 'CONTRADICTS': 14}
- comparison_status_counts: {'OK': 60, 'ERROR': 5, 'INVALID_OUTPUT': 4}
- factual_evidence_relation_counts: {'INSUFFICIENT_EVIDENCE': 47, 'SUPPORTED': 5, 'CONTRADICTORY': 8}
- llm_call_count: 108

- overlap_audit_pass: True
- unique_reference_text_count: 8
- evaluation_code_commit: e326a181500e5d12ea75914ea2f419dfb90e7c6b
