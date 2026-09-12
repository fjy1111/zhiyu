# ZhiYu Phase 2 Completion Report

Rule-only baseline. Not a full ingestion pipeline. Not Phase 3.

## Changed

- `docs/phase2_spec.md`: frozen Phase 2 specification
- `src/zhiyu/models/detection.py`: RuleEvent / DetectionResult / enums
- `src/zhiyu/detector/`: Rule Scanner (PI explicit, HI structural, RH statistical)
- `src/zhiyu/decision/aggregator.py`: discrete SAFE/REVIEW/POISON table
- `src/zhiyu/eval/phase2.py` and `scripts/evaluate_phase2.py`: evaluator-only metrics
- tests: positive / paraphrase / negative / quoted hard-negative / RH / aggregator / firewall
- generated: `experiments/phase2/rule_only_baseline.json`, `experiments/phase2/rule_only_baseline.md`

Spec-correctness follow-up (not Phase 2R): tighter HIGH qualification, code-fence no longer auto-benign, plus generic retrieval-context override and protected-instruction exfiltration mechanisms. No sample-specific patches. No generalization-set inspection.

## Tests

```text
.venv/Scripts/python -m pytest -q tests/test_phase2_scanner.py tests/test_phase2_aggregator.py tests/test_phase2_firewall.py tests/test_phase2_eval.py
.venv/Scripts/python -m pytest -q
.venv/Scripts/python scripts/evaluate_phase2.py
git diff --check
```

Results:

- targeted Phase 2 tests: passed
- full pytest: 132 passed
- git diff --check: passed
- raw data: unmodified
- frozen/external: unused
- ground truth: not passed into DetectionInput / Scanner / Aggregator

## Evaluation (program-generated)

Primary metric counts only `decision == POISON` as positive. REVIEW is not detection success. conflict is excluded from Precision/Recall/F1/FPR.

development_tune (123 docs): tp/fp/tn/fn = 18/0/69/12; precision=1.0; recall=0.6; f1=0.75; fpr=0.0; hard_negative_poison_rate=0.0; conflict_poison_rate=0.0.

development_generalization (57 docs): tp/fp/tn/fn = 0/0/30/15; precision=null; recall=0.0; f1=null; fpr=0.0; hard_negative_poison_rate=0.0; conflict_poison_rate=0.0.

No second-round rules were added after seeing remaining FNs.

## Known limits

- Phase 2 only catches explicit instruction-control and structural hiding, plus RH statistical REVIEW signals.
- FACT_TAMPERING / KNOWLEDGE_CONFLICT / semantic hidden intent are out of scope.
- No LLM, no trusted evidence, no Judge, no RAG, no Context Integrity Checker, no Web.

## Hard Stop

Phase 2 complete. STOP. Do not enter Phase 3.
