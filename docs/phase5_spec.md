# Phase 5 Specification — Unified Evidence Judge & Risk Decision

定位：Phase 2/3/4 正式证据之后，Protected RAG / Context Integrity / Web 之前。

目标：把已经存在的异构安全证据统一解释，并通过明确、可审计、非补偿的决策规则得到：

- `SAFE`
- `REVIEW`
- `POISON`

Phase 5 **不新增底层检测器**，不重新发现事实或攻击证据，不修改 Phase 2/3/4 冻结实现 / Prompt / reference corpus / retrieval。

继续遵守：

- Evidence First, Judgment Second
- UNKNOWN != POISON
- `INSUFFICIENT_EVIDENCE != POISON`
- `CONTRADICTORY != POISON` automatically
- `ERROR / INVALID_OUTPUT != SAFE`
- LLM 不得使用 ground truth、benchmark metadata、参数记忆补造事实、创造不存在的 evidence、Web、重新检索、修改上游输出

核心原则：

```text
LLM interprets evidence.
Program decides risk.
```

---

## 1. Pipeline

```text
Formal Evidence
  RuleEvent[]
  BehaviorEvidence[]
  FactualEvidence[]
  analysis status / failure signals
        ↓
Unified Evidence Judge
        ↓
validated UnifiedRiskAssessment
        ↓
Deterministic / non-compensatory Risk Decision Engine
        ↓
SAFE / REVIEW / POISON
```

Judge 是证据解释器，不是最终裁决器。Risk Engine 独占最终三档。

---

## 2. Judge inputs

只允许正式、已验证的 Phase 2/3/4 输出。

### 2.1 Allowed

**RuleEvent[]：** 冻结 Phase 2 对象原样保留。Phase 5 在 bundle 物化时为每条 RuleEvent 派生确定性 `rule_event_ref`（SHA256 of `document_id`, `chunk_id`, `rule_id`, `span_start`, `span_end`, `mechanism`, `event_class`, `confidence`）。不修改 Phase 2 schema。Judge 必须引用 `cited_rule_event_refs[]`，不得只靠可能重复的 `rule_id`。未知 / 重复 / 跨文档 ref → Judge `INVALID_OUTPUT`。原始 `rule_id` 仅用于解释与审计。

**BehaviorEvidence[]：** `evidence_id`, `intent`, `mechanism`, `confidence`, `document_id` / `chunk_id`, bound excerpt / span, `rationale`, `source_rule_ids`

**FactualEvidence[]：** `evidence_id`, `claim_id`, `claim_excerpt`, `normalized_claim`, `relation`, supporting / contradicting / insufficient reference ids, reference provenance / exact bound excerpts, `aggregation_reason`

**Analyzer status / failure signals：** `OK`, `SKIPPED`, `NO_CLAIM`, `NO_EVIDENCE`, `INVALID_OUTPUT`, `ERROR`

status 是分析可靠性信息，不是新的攻击证据。

### 2.2 Forbidden

`original_label`, `attack_type` GT, `metadata["facts"]`, expected/target answer, benchmark split / sample id, evaluator-only annotation, Web, 未检索知识库, 邻 chunk, candidate 全文重分析, trusted corpus 全文重检索, 模型记忆补事实, Phase 6 RAG 输出。

Judge 不能重新做 Phase 2/3/4。

### 2.3 No invented evidence

Judge 引用的 `rule_id` / behavior `evidence_id` / factual `evidence_id` / `reference_id` 必须全部来自当前输入。程序验证：未知 id、伪造 id、输入外引用一律非法。

声称“事实篡改”但无对应正式 `FactualEvidence`，不能成为 POISON 依据。
声称“隐式控制”但无对应 `BehaviorEvidence` / `RuleEvent`，不能成为 POISON 依据。

没有正式证据 → LLM 不能发明 POISON。

---

## 3. UnifiedRiskAssessment

Judge **禁止**输出：`SAFE`, `REVIEW`, `POISON`, `final_risk_level`, final risk score。

结构化评估：

```text
UnifiedRiskAssessment
  document_id
  cited_rule_event_refs[]
  cited_behavior_evidence_ids[]
  cited_factual_evidence_ids[]
  behavior_assessment: NONE | SUSPICIOUS | STRONG_CONTROL
  factual_assessment: NONE | SUPPORTED_ONLY | CONTRADICTION_PRESENT | INSUFFICIENT_OR_MIXED
  evidence_coherence: CONSISTENT | MIXED | CONFLICTING | INSUFFICIENT
  uncertainty: LOW | MEDIUM | HIGH
  analyzer_failures[]
  rationale
```

字段只解释已有证据，不是最终风险档。

Judge `ERROR` / `INVALID_OUTPUT` / 未知 evidence id / schema 非法 → 不能默认 SAFE。由 Risk Engine 按原始证据 + failure status 走 fail-safe 路径。

---

## 4. AnalysisStatusRecord

不修改 Phase 2/3/4 frozen evidence schema。Phase 5 使用轻量状态信封：

```text
AnalysisStatusRecord
  component: RULE | SEMANTIC | FACTUAL_CLAIM | FACTUAL_RETRIEVAL | FACTUAL_COMPARE | UNIFIED_JUDGE
  status: OK | SKIPPED | NO_CLAIM | NO_EVIDENCE | INVALID_OUTPUT | ERROR
  attempted: bool
  skip_reason: optional
  error_code: optional
```

只描述执行可靠性。

不能把 `None` / 缺失对象 / 调用链中断偷偷解释成 `SKIPPED`。

- **LEGITIMATE_NOT_RUN：** 有正式 status、合法 `skip_reason` 或 `NO_CLAIM`、prerequisite 可验证
- **UNEXPECTED_MISSING：** 应有结果却没有、status 缺失、无合法 skip_reason、pipeline 中断、contract 不完整 → **REVIEW**

---

## 5. Deterministic Risk Engine (non-compensatory)

V1 不使用加权分数。弱证据不能靠数量升级。固定优先级：

```text
1. Strong formal control evidence?     YES → POISON
2. Any suspicious / contradictory / insufficient evidence?  YES → REVIEW
3. Any ERROR / INVALID_OUTPUT / unexpected missing / invalid Judge?  YES → REVIEW
4. All required analyses completed or legitimately skipped,
   and no unresolved risk?             YES → SAFE
```

不得改变顺序。Judge 不能覆盖这些规则。SUPPORTED 不能抵消控制证据或分析失败。

### 5.1 POISON gate

任一正式强控制证据：

- RuleEvent：`mechanism ∈ {PROMPT_INJECTION, HIDDEN_INSTRUCTION}` 且 `event_class == MECHANISM` 且 `confidence == HIGH`
- 或 BehaviorEvidence：`intent == IMPLICIT_CONTROL` 且 `mechanism ∈ {PI, HI}` 且 `confidence == HIGH`

→ **POISON**（non-compensatory）

无论 Judge 是否 OK/ERROR/INVALID，都不能把已成立的强证据降级。其他 analyzer ERROR 也不能抵消。

禁止：MEDIUM 累积成 HIGH；STATISTICAL 堆成 POISON；CONTRADICTORY 单独 POISON；Judge 在无正式强控制证据时暗示 POISON。

`judge_only_poison_count` 必须为 0。

### 5.2 REVIEW gate

未触发 POISON 时，任一：

- 非 HIGH-MECHANISM 的风险 RuleEvent / STATISTICAL / LOW·MEDIUM mechanism
- LOW/MEDIUM `IMPLICIT_CONTROL`、`UNCERTAIN`、其他不足 POISON 的 suspicious BehaviorEvidence
- Factual `CONTRADICTORY` 或 `INSUFFICIENT_EVIDENCE`
- evidence coherence MIXED / CONFLICTING / 无法一致解释
- 本应执行且已尝试的组件 ERROR / INVALID_OUTPUT（Semantic、Claim、Retrieval、Compare、Judge）
- UNEXPECTED_MISSING

→ **REVIEW**

语义：不能自动 SAFE 放行；quarantine / manual review；不进入 SAFE-only KB。
`REVIEW != POISON`。failure != attack evidence。

### 5.3 Neutral statuses

本身不触发风险：

- Semantic `SKIPPED` 且 `skip_reason = RULE_HIGH_ALREADY_SUFFICIENT` 且 prerequisite Rule HIGH 实际存在（最终由 Rule HIGH 走 POISON）
- Phase 4 `NO_CLAIM`（不能单独 REVIEW）
- 合法 absence of FactualEvidence **仅当** `ClaimExtractionResult.status == NO_CLAIM`

`factual_evidence == []` 本身不能当安全。

Retrieval `NO_EVIDENCE` 已折叠为 `INSUFFICIENT_EVIDENCE` → REVIEW。UNKNOWN != SAFE。

### 5.4 SAFE gate

全部成立：

- 无 POISON gate
- 无 REVIEW-triggering evidence
- 无 CONTRADICTORY / INSUFFICIENT FactualEvidence
- 无 MIXED / CONFLICTING
- 应执行的 analyzer 均为 OK 或合法中性
- 无 ERROR / INVALID_OUTPUT / UNEXPECTED_MISSING
- Judge validation 正常完成
- 无未解决风险

允许存在：SUPPORTED FactualEvidence、NO_CLAIM、合法 SKIPPED。

SAFE = “计划中的安全分析已可靠完成，且没有留下未解决风险”，不是“没发现攻击”。

### 5.5 Factual contradiction policy

`CONTRADICTORY != POISON automatically`。可能是旧版本、普通错误、多来源冲突、非恶意修改或真投毒。V1 无独立“恶意篡改意图”证据，故 CONTRADICTORY → REVIEW，阻断自动入库，但不无证据推断恶意。

---

## 6. Decision granularity and expected execution

Phase 5 最终决策是 **DOCUMENT-LEVEL**。

一条 `Phase5EvidenceBundle` 记录对应一个 candidate document，包含其全部 expected chunks 的正式证据与状态。

### 6.1 ExpectedExecutionPlan

至少记录：

- `document_id`
- `expected_chunk_ids`

对每个 expected chunk，必须能判定哪些组件应当执行，哪些是合法不必执行。

`UNEXPECTED_MISSING` = expected execution − actual formal result/status。

禁止从 `None` / 缺失数据推断 `SKIPPED`。

依赖（在该 ablation 期望该层时）：

- 每个 candidate chunk 都应有 Rule scan
- 每个 candidate chunk 都应有 Semantic analysis，除非冻结合法 skip 且 prerequisite 可验证
- 每个 candidate chunk 都应有 Factual Claim Extraction
- `ClaimExtraction == NO_CLAIM` → retrieval/comparison 不期望
- `ClaimExtraction == OK` → 每个 AtomicClaim 期望 retrieval
- Comparison 仅当 `Retrieval == OK` 时期望
- `NO_EVIDENCE` 按冻结 Phase 4 合法产生 `INSUFFICIENT_EVIDENCE`

### 6.2 Ablation-aware expected components

- `rule_only_baseline`：只期望 RULE
- `rule_plus_semantic_baseline`：RULE + SEMANTIC
- `full_evidence_no_judge`：RULE + SEMANTIC + FACTUAL；Judge 故意不期望
- `full_judge`：RULE + SEMANTIC + FACTUAL + UNIFIED_JUDGE

ablation 中故意省略的组件不得记为 `UNEXPECTED_MISSING`。

## 7. EvidenceBundle materialization

在 ablation 评测之前物化一次 `Phase5EvidenceBundle`。

使用：同一 Phase 4 derived candidate view + 冻结 Phase 2/3/4 实现与配置。

一次生成全部所需正式证据/状态，然后 commit/freeze bundle 并记录 SHA256。

四路 ablation 必须消费同一冻结 bundle。不得为每个 ablation 分别重跑 Phase 2/3/4，以免上游 LLM 随机性污染消融并重复消耗 API。

bundle 可含 per-document 机器可读执行证据；禁止人工/逐样本 generalization 错误检查；报告只做聚合。

Evaluator labels 分开存储，不得进入 runtime EvidenceBundle。

Bundle 不得含：`original_label`、`attack_type`、`facts`、expected answers、evaluator annotations、暴露给 Judge 的 split 字段。

### 7.1 Phase 4 evidence boundary

消费冻结 `FactualEvidence` 原样。不重开 trusted corpus，不重检索，不给 Phase 5 补充新事实证据。

Judge 可消费已有字段：`claim_excerpt`、`normalized_claim`、`relation`、supporting/contradicting/insufficient ids、已有 `reference_provenance`、`aggregation_reason`、`rationale`。

若冻结 `FactualEvidence` 中没有 exact trusted reference excerpt，Phase 5 不得仅为 Judge 解释去拉取。

### 7.2 Cost / provenance

EvidenceBundle 物化是一次受控生成，不是 ablation 重跑。

记录：`evidence_bundle_build_commit`、candidate snapshot SHA256、bundle SHA256、Phase 2/3/4 frozen commit 与 model/prompt/reference/config、execution-plan version、RuleEvent-ref derivation version。

bundle 冻结后，不得因 Phase 5 指标重新生成。

official `full_judge` 评测只新增 Phase 5 所需 Judge 调用。禁止根据 generalization 样本调 Prompt。

## 8. Evaluation

目标不是调高 Recall，而是证明：三路证据可统一消费；决策可审计可复现；failure/uncertainty 不会错误 SAFE；Judge 不会凭空 POISON；ablation 公平。

### 8.1 Same candidate set

不得把历史 Phase 2/3/4 官方数字直接横向比（candidate pool 不同）。

V1 统一 candidate view = 当前合法 Phase 4 derived view：

- development_tune: 54 docs
- development_generalization: 39 docs

所有 ablation 在同一 set 上重跑冻结的 Phase 2/3 逻辑。不得改 Phase 2 rules、Phase 3 prompt、Phase 4 prompt/corpus/retrieval/aggregation。

### 8.2 Frozen Phase5EvidenceBundle

正式评测前冻结每条 candidate：

- RuleEvent[] + Rule status
- BehaviorEvidence[] + Semantic status
- FactualEvidence[] + Phase 4 component statuses
- candidate document/chunk identity

不得含 label / attack_type / facts / expected answer / split name inside Judge input / evaluator annotation。

记录：dataset snapshot SHA256、Phase 2/3/4 frozen commit/config/prompt/model/reference hash、bundle SHA256。

official evaluation 开始后 bundle 不再修改。

`full_evidence_no_judge` 与 `full_judge` 必须消费同一 bundle。

### 8.3 Ablations

- **rule_only_baseline**：只消费 RuleEvent，冻结 Phase 2
- **rule_plus_semantic_baseline**：RuleEvent + BehaviorEvidence，冻结 Phase 3
- **full_evidence_no_judge**：三路证据 + statuses，不调 Judge，直接 Q2/Q3 门
- **full_judge**：同一 bundle + Judge → validated assessment → Risk Engine

### 8.4 Metrics

主阳性：`decision == POISON`。REVIEW 在 binary 中为 negative。GT：poison=positive；normal+hard_negative=negative；conflict 不进主 F1。

报告 TP/FP/FN/TN、Precision/Recall/F1/FPR。不设通过阈值。不得把 REVIEW 当 TP。

另报：overall/poison/normal/hard_negative/conflict review rates；`unsafe_auto_admission_rate`（poison 中 decision==SAFE）；`poison_non_safe_rate = (POISON+REVIEW)/poison`（只解释是否被自动放行）。

conflict 只报三档分布与 review/poison rate。CONTRADICTORY 通常应 REVIEW；若大量 POISON 只记录观察，不调 gate。

hard_negative_poison_rate 与 hard_negative_review_rate 分开。

### 8.5 Judge diagnostics

Judge OK/INVALID/ERROR；unknown/duplicate/invented citation rejection；uncertainty / coherence 分布。

full_evidence_no_judge vs full_judge：verdict agreement；SAFE↔REVIEW、REVIEW↔POISON 转移；Judge-added REVIEW。

`judge_only_poison_count == 0`。
`unsafe_safe_on_failure_count == 0`（无强 POISON 证据时，unresolved failure 不得 SAFE）。

这些是 correctness invariant，不是性能阈值。

### 8.6 Discipline

tune：可看聚合指标/错误类型/status 分布，禁止为指标改规则/prompt/gate/reference/threshold。
gen：只允许聚合；禁止单样本、FN/FP 文本、Judge failure 样本、case patch。
frozen/external：Phase 5 不使用，保持 DEFERRED。

Mock 仅测试。正式数字真实 DeepSeek。流程：mock/unit → 最小 Judge smoke → freeze prompt/schema/config → freeze EvidenceBundle → **恰好一次** official evaluation。因 correctness/provenance bug 无效须经 external review 后才允许一次 replacement。

记录：evaluation_code_commit、working tree clean、candidate/bundle SHA256、上游 frozen commits/configs、Judge prompt version、decision policy version、model/temperature/timeout/retries、timestamp、GT firewall。GT 只进 evaluator。

---

## 9. Hard Stop

1. UnifiedRiskAssessment schema 实现（`cited_rule_event_refs`）
1b. ExpectedExecutionPlan；UNEXPECTED_MISSING 由 expected − actual 计算
1c. Phase5-local deterministic `rule_event_ref` 派生（不改 Phase 2 schema）
1d. EvidenceBundle 一次物化，四路 ablation 共用
2. Judge evidence-ID validation 实现
3. Judge 不输出最终 verdict
4. deterministic non-compensatory Risk Engine 实现
5. Q2 POISON / REVIEW / SAFE gates 测试完整
6. Q3 ERROR / INVALID / SKIPPED / NO_CLAIM / UNEXPECTED_MISSING 路径测试完整
7. `judge_only_poison_count` invariant 可验证
8. `unsafe_safe_on_failure_count` invariant 可验证
9. GT firewall 通过
10. same-candidate ablation 实现
11. frozen Phase5EvidenceBundle 可复现
12. minimal real DeepSeek Judge smoke 通过
13. exactly one official Phase 5 evaluation 完成
14. full pytest -q 通过
15. git diff --check 通过
16. 未修改 Phase 2/3/4 frozen implementation
17. 未进入 Phase 6

全部成立：completion report → commit → push → STOP。

没有 F1/Recall/Precision 达标线。低 Recall、高 REVIEW、Judge 不提升 F1，只要 contract 正确、可复现、无泄漏，都不能成为 Phase 5R 或样本补丁的理由。

---

## 10. Not Phase 5

Protected KB、Retriever、Context Integrity Checker、Vanilla vs Protected RAG、QA generation、Web frontend、Dashboard、Phase 6。

---

## Final principle

Phase 5 证明的是：异构安全证据如何被可靠、可审计地统一裁决；不是如何把 benchmark Recall 调得最好看。
