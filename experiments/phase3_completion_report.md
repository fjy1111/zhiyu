# ZhiYu Phase 3 Completion Report

Semantic Behavior Layer. Not a full ingestion pipeline. Not Phase 4.

## Changed

- `docs/phase3_spec.md`: frozen Phase 3 specification
- `src/zhiyu/models/semantic.py`: SemanticAnalysisInput / Draft / BehaviorEvidence / SemanticAnalysisResult
- `src/zhiyu/semantic/`: gate, exact unique source binding, all-or-nothing validation, mock + DeepSeek providers
- `src/zhiyu/decision/semantic_aggregator.py`: rule_plus_semantic_baseline discrete table
- `src/zhiyu/detector/rule_plus_semantic.py`: Rule + Semantic pipeline (Phase 2 Rule Scanner unchanged)
- `scripts/smoke_phase3.py`, `scripts/evaluate_phase3.py`
- generated: `experiments/phase3/rule_vs_rule_plus_semantic.json`

## Tests

```text
.venv/Scripts/python -m pytest -q
.venv/Scripts/python scripts/smoke_phase3.py
.venv/Scripts/python scripts/evaluate_phase3.py
git diff --check
```

Results:

- full pytest: 159 passed
- DeepSeek smoke: PASS (benign=SAFE/OK, implicit=POISON/OK)
- git diff --check: passed after this report
- raw data: unmodified
- frozen/external: unused
- ground truth: not passed into Semantic Analyzer
- mock metrics: not used in experiments/phase3

## Official evaluation (REAL LLM)

Same DetectionInput, same splits, same Rule Scanner, same metrics. REVIEW is not detection success.

development_tune (123):

- Rule Only: tp/fp/tn/fn=18/0/69/12; precision=1.0; recall=0.6; f1=0.75; fpr=0.0; hard_negative_poison_rate=0.0
- Rule + Semantic: tp/fp/tn/fn=18/0/69/12; precision=1.0; recall=0.6; f1=0.75; fpr=0.0; hard_negative_poison_rate=0.0
- semantic_call_count=105; semantic_skip_count=18; semantic_error_count=0; invalid_output_count=0
- deltas: ΔRecall=0.0; ΔF1=0.0; ΔFPR=0.0; Δhard_negative_poison_rate=0.0

development_generalization (57):

- Rule Only: tp/fp/tn/fn=0/0/30/15; precision=null; recall=0.0; f1=null; fpr=0.0
- Rule + Semantic: identical
- semantic_call_count=57; skip/error/invalid=0
- ΔRecall=0.0

No second-round Prompt patch after seeing remaining FNs.

该正式 benchmark 运行于 review-fix 前，review-fix 未根据 benchmark 样本或指标修改 Prompt。

## Known limits

- Phase 3 only analyzes implicit/explicit model-control behavior on one chunk.
- This official run produced no BehaviorEvidence (LLM returned successful NO_CONTROL). Ablation therefore matches Rule Only.
- FACT_TAMPERING / KNOWLEDGE_CONFLICT / Judge / RAG / CIC / Web are out of scope.

## Hard Stop

Phase 3 complete. STOP. Do not enter Phase 4.
