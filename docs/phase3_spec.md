# Phase 3 Specification — Semantic Behavior Layer

定位：Phase 2 Rule-only baseline 之后，Trusted Factual Evidence / Judge / RAG 之前。

目标：补上 Rule-only 无法可靠理解的隐式模型控制语义，并形成可复现消融：

```text
Rule Only
vs
Rule + Semantic
```

不是完整 Ingestion Security Pipeline，也不是最终 ZhiYu Judge。

Phase 2 必须保持完全可独立运行。Phase 3 不得修改 Phase 2 Rule Scanner、Aggregator 或已有 `rule_only_baseline` 实验结果。

---

## 1. North Star

Phase 3 只回答：

> 这段文本是否在试图控制后续模型行为？

LLM 是 Semantic Analyzer，不是 Universal Truth Oracle。不得判断外部事实真伪。

继续遵守：

- Evidence First, Judgment Second
- UNKNOWN != POISON
- LLM 不得发明 evidence

主要针对：`PROMPT_INJECTION`、`HIDDEN_INSTRUCTION`。

---

## 2. Pipeline

```text
DetectionInput (per chunk)
  -> Phase 2 Rule Scanner                 # unchanged
  -> RuleEvent[]
  -> Semantic invocation gate
        |-- SKIPPED if PI/HI MECHANISM+HIGH already exists
        |-- else Semantic Analyzer (real LLM or test mock)
  -> SemanticObservationDraft[]
  -> all-or-nothing schema + consistency + exact source binding
  -> SemanticAnalysisResult
  -> Document Aggregator (rule_plus_semantic_baseline)
        RuleEvent[] + SemanticAnalysisResult[]
  -> document-level SAFE / REVIEW / POISON
```

Rule Only 路径继续：

```text
DetectionInput -> Rule Scanner -> RuleEvent[] -> Phase 2 Aggregator
-> decision_kind = rule_only_baseline
```

Document-level Rule + Semantic Aggregator 只接收：

- `RuleEvent[]`
- `SemanticAnalysisResult[]`

不得直接使用 `SemanticObservationDraft` 做决策。

---

## 3. Input boundary

不要修改现有 `DetectionInput` schema。它仍然只有：

- `document_id`
- `chunk_id`
- `text`
- `runtime?`（仅 `request_id` / `file_format`）

Phase 3 新增独立输入：

```text
SemanticAnalysisInput
  - detection_input: DetectionInput
  - rule_events: RuleEvent[]
```

约束：

- 一次只分析一个 chunk
- `rule_events` 只能来自同一 `document_id` + 同一 `chunk_id`
- 允许 `rule_events = []`，以便将来 Semantic Only 与 Rule + Semantic 共用同一 Analyzer
- 不得传入邻 chunk、全文、其他文档、document-level Rule-only decision

允许读取：

- 当前 chunk `text`
- 当前 chunk `RuleEvent` 的 `rule_id` / `mechanism` / `event_class` / `confidence` / span / `excerpt` / `rationale` / `measurement?`

RuleEvent 只是 machine-generated observations，可能不完整或只是弱信号。不得因为已标记某 mechanism 就机械复述。

绝对禁止进入 Semantic Analyzer：

- original label
- attack type ground truth
- query
- answer / target_answer
- trusted facts / trusted KB
- neighboring chunks / full document / other documents
- document-level SAFE / REVIEW / POISON
- split name、sample id 特征、benchmark metadata、evaluator-only metadata

禁止循环偏置：先把文档结论告诉 LLM，再让它“证明”该结论。

Prompt 必须说明：已有 RuleEvent 只是确定性观察，可能不完整或不确定；必须依据当前 source text 本身分析。禁止 “Rule Scanner says PROMPT_INJECTION, please confirm it.”

---

## 4. LLM invocation gate

若当前 chunk 已存在：

- `mechanism ∈ {PROMPT_INJECTION, HIDDEN_INSTRUCTION}`
- `event_class == MECHANISM`
- `confidence == HIGH`

则默认 **SKIP Semantic Analyzer**，不调用 LLM。

返回：

```text
status = SKIPPED
skip_reason = RULE_HIGH_ALREADY_SUFFICIENT
behavior_evidence = []
```

这不是把 RuleEvent 当 ground truth，而是避免对已有强、可定位、经过 hard-negative qualification 的案例重复消费模型。

主要应运行 Semantic Analyzer 的情况：

- 没有 RuleEvent
- 只有 LOW / MEDIUM mechanism event
- 只有 STATISTICAL event
- 规则发现可疑 span，但无法确认控制意图
- Rule-only 结果不足以形成明确行为判断

Phase 3 不重新检测所有显式攻击。即使隐式意图可能跨 chunk，也不扩大到邻 chunk / 全文。单 chunk 证据不足时允许不确定，不得为 Recall 扩大上下文。

---

## 5. SemanticAnalysisResult

每个 chunk 的正式语义输出是：

```text
SemanticAnalysisResult
  - document_id
  - chunk_id
  - status: OK | SKIPPED | INVALID_OUTPUT | ERROR
  - skip_reason: optional
  - behavior_evidence: BehaviorEvidence[]
  - error_code: optional
```

状态不得混用：

- `OK + behavior_evidence=[]`：分析成功，没有攻击型 BehaviorEvidence（含成功的 `NO_CONTROL`）
- `SKIPPED`：因门控不必执行
- `INVALID_OUTPUT`：LLM 输出无法通过 all-or-nothing validation
- `ERROR`：调用失败 / 超时 / provider 异常

`ERROR` / `INVALID_OUTPUT` 不得自动当成 `NO_CONTROL` 或 `SAFE`，也不得当成 `POISON`。

---

## 6. LLM raw output

LLM 只输出 `SemanticObservationDraft[]`，使用严格 JSON + schema validation。禁止自由文本后再用 regex 猜意思。

每个 draft 字段：

- `intent`：`IMPLICIT_CONTROL` | `NO_CONTROL` | `UNCERTAIN`
- `mechanism`：`PROMPT_INJECTION` | `HIDDEN_INSTRUCTION` | `null`
- `confidence`：`LOW` | `MEDIUM` | `HIGH`
- `excerpt`：当前 `DetectionInput.text` 中的原文片段；`NO_CONTROL` 允许空 excerpt
- `rationale`：只解释 excerpt 中的模型控制意图；`NO_CONTROL` 可说明为何不是控制
- `source_rule_ids`：optional `list[str]`

LLM 不输出：

- `SAFE` / `REVIEW` / `POISON`
- document decision
- trusted facts / external evidence
- fabricated quote
- `evidence_id`
- `span_start` / `span_end`
- final risk score

一个 chunk 可有多个独立可疑 span，但必须设少量上限（最多 3 条），禁止把整段 chunk 当作超长 excerpt。

---

## 7. All-or-nothing validation and exact source binding

程序不信任 LLM offsets，也不做 occurrence hint。

Exact source binding 冻结为：

- excerpt 在当前 chunk text 中**唯一出现** → bind，`span_start` / `span_end` 由程序计算，并验证 `text[span:end] == excerpt`
- excerpt 不存在 → 该次 response `INVALID_OUTPUT`
- excerpt 多次出现 → 该次 response `INVALID_OUTPUT`

不做 fuzzy matching，不 normalize 后差不多匹配，不语义相似替代，不允许模型改写原句，不自动选择 occurrence，不增加 occurrence-hint 接口。

`NO_CONTROL` 的空 excerpt 不进入 source binding，也不生成 BehaviorEvidence。

严格 all-or-nothing：一次 LLM response 中，**任何一条 draft** 出现下列情况，则整个当前 chunk：

```text
status = INVALID_OUTPUT
behavior_evidence = []
```

触发条件：

- schema invalid
- excerpt 不存在（对需要 binding 的 draft）
- excerpt 无法唯一 source-bind
- intent / mechanism consistency invalid
- `source_rule_ids` 引用了本次输入中不存在的 `rule_id`
- excerpt 过长（超过当前 chunk 的合理短 span 上限，例如 240 字符）

不得部分接受同一次非法 LLM response。

`source_rule_ids` 只能引用本次 `SemanticAnalysisInput.rule_events` 中真实存在的 `rule_id`。非法引用使整次 response 无效，而不是静默丢弃。

一致性：

- `intent == NO_CONTROL` → `mechanism` 必须为 `null`；不生成攻击型 BehaviorEvidence
- `intent == UNCERTAIN` → mechanism 可为 PI / HI / null；excerpt 必须唯一 bind 后才能成为 BehaviorEvidence
- `intent == IMPLICIT_CONTROL` → mechanism 必须是 `PROMPT_INJECTION` 或 `HIDDEN_INSTRUCTION`；excerpt 必须唯一 bind

Phase 3 Semantic Analyzer 不得把 `FACT_TAMPERING` / `KNOWLEDGE_CONFLICT` / `RETRIEVAL_HIJACKING` 作为语义行为结论。

---

## 8. Formal BehaviorEvidence

只有通过 all-or-nothing validation 和 exact source binding 的 candidate 才能进入 `SemanticAnalysisResult.behavior_evidence`。

字段：

- `evidence_id`：程序确定性生成，不得由 LLM 发明
- `document_id`
- `chunk_id`
- `intent`：`IMPLICIT_CONTROL` | `UNCERTAIN`
- `mechanism`：`PROMPT_INJECTION` | `HIDDEN_INSTRUCTION` | `null`
- `confidence`：`LOW` | `MEDIUM` | `HIGH`
- `span_start`
- `span_end`
- `excerpt`
- `rationale`
- `source_rule_ids`：optional `list[str]`

`NO_CONTROL` 不进入该列表。

`SemanticObservationDraft` 本身永远没有 POISON 权限。

流程：

```text
DetectionInput + RuleEvent[]
  -> gate / Semantic Analyzer
  -> SemanticObservationDraft[]
  -> all-or-nothing validation
  -> Exact Source Binding
  -> SemanticAnalysisResult
```

---

## 9. Rule + Semantic decision table

新增独立：

```text
decision_kind = rule_plus_semantic_baseline
```

Aggregator 输入仅为 `RuleEvent[]` + `SemanticAnalysisResult[]`。不使用加权总分，不把弱信号累加升格。

Semantic 只能通过 `SemanticAnalysisResult` 提供已验证 BehaviorEvidence，不能修改、删除或覆盖已有 RuleEvent，也不能把 Rule POISON 降为 SAFE / REVIEW。

文档级优先级：

**第一层**  任意 chunk 存在 PI/HI `MECHANISM + HIGH` RuleEvent → `POISON`
（与 Phase 2 完全一致；Semantic 无权降级。此时对应 chunk 的 semantic status 应为 `SKIPPED`，SKIPPED 本身不额外触发 REVIEW。）

**第二层**  任意 `SemanticAnalysisResult.behavior_evidence` 中存在：
`intent == IMPLICIT_CONTROL` 且 `mechanism ∈ {PI, HI}` 且 `confidence == HIGH` → `POISON`

**第三层**  存在任意：弱 RuleEvent、STATISTICAL RuleEvent、LOW/MEDIUM BehaviorEvidence、`intent == UNCERTAIN`、任一 chunk `status == ERROR`、任一 chunk `status == INVALID_OUTPUT` → `REVIEW`

包括：semantic `OK` 且无攻击型 BehaviorEvidence，但文档仍有 LOW/MEDIUM 或 STATISTICAL RuleEvent → 仍为 `REVIEW`。

**第四层**  无 RuleEvent，且所有实际执行的 semantic analysis 都是 `OK` 或因 Rule HIGH 产生的 `SKIPPED`，且没有攻击型 BehaviorEvidence，且没有 `UNCERTAIN` / `ERROR` / `INVALID_OUTPUT` → `SAFE`

典型：全部 chunk `OK` + 无 BehaviorEvidence + 无 RuleEvent → `SAFE`

Fail-closed：本应执行 Semantic Analyzer 却发生 `ERROR` 或 `INVALID_OUTPUT` → `REVIEW`。不得 SAFE，不得 POISON。

3 个 MEDIUM semantic ≠ HIGH。10 个 STATISTICAL ≠ POISON。

可追溯：

- document decision → RuleEvent
- document decision → `SemanticAnalysisResult` → BehaviorEvidence → excerpt → chunk_id → exact span
- `REVIEW` because ERROR / INVALID_OUTPUT → chunk_id → status（不得伪造成攻击 evidence）

---

## 10. Evaluation

必须并排比较 `rule_only_baseline` vs `rule_plus_semantic_baseline`。

两者必须使用：同一 `DetectionInput`、同一 development_tune 文档、同一 development_generalization 文档、同一 Phase 2 Rule Scanner、同一 ground-truth mapping、同一评测指标。

主指标与 Phase 2 相同：

- 只有 `decision == POISON` 为 predicted positive
- `REVIEW` 不算成功检出
- positive GT：`poison`；negative GT：`normal` / `hard_negative`
- `conflict` 不进主 Precision / Recall / F1，只报三档分布

报告 Precision / Recall / F1 / FPR，以及 `poison_review_rate`、`normal_review_rate`、`hard_negative_review_rate`、`hard_negative_poison_rate`、conflict 分布。

正式实验必须真实调用当前配置的 DeepSeek。mock 只用于单测 / schema / error-path / deterministic integration。mock 结果不得进入 `experiments/phase3/` 正式数字。报告必须区分 `REAL LLM` 与 `MOCK / TEST ONLY`。

正式评测前冻结：model name、base URL（不记录 Secret）、prompt version、schema version、temperature、max tokens、retry / timeout policy、Phase 2 commit / implementation version、evaluation dataset snapshot。API Key 永不写入报告。生成可追溯的 Phase 3 evaluation config / manifest。

成本硬约束：

- 开发优先 deterministic tests、手写语义用例、mock provider
- 真实 DeepSeek 只用于最小 smoke test 和最终正式 benchmark
- 禁止改一个 Prompt 就全量重跑、为调试反复跑完整 tune+gen、因单样本反复调用、自动循环 Prompt optimization
- 利用已冻结调用门控跳过 Rule HIGH
- 正式评测统计：`semantic_call_count` / `semantic_skip_count` / `semantic_error_count` / `invalid_output_count`

Prompt 只描述通用行为机制。允许基于机制定义、synthetic examples、tune 聚合错误类型做机制级修正。禁止把失败原句、dataset entity、benchmark phrase 写进 Prompt；禁止根据 generalization 单样本改 Prompt 或 confidence 规则。generalization 只允许聚合指标。

评测时序：先完成 schema / binding / mock tests / decision table / error handling / provider smoke test，全部通过后冻结 Prompt 和配置，然后 **只跑一次** 正式 tune + generalization 真实 DeepSeek benchmark。除非程序 Bug、API 配置错误、schema/parser Bug、source binding Bug，否则不得因指标不好重跑第二轮完整 benchmark。低 Recall 不是重跑理由。

正式结果必须同时输出两条路径的 P/R/F1/FPR 与 triage metrics，以及 ΔRecall / ΔF1 / ΔFPR / Δhard_negative_poison_rate。Semantic 没提升也必须如实报告。禁止只展示更好的路径。

额外诊断：call/skip/OK/SKIPPED/ERROR/INVALID_OUTPUT 计数；BehaviorEvidence 按 confidence / mechanism 计数。用于判断提升来自真实语义证据，还是来自大量 REVIEW / 调用失败。

---

## 11. Hard Stop

以下条件全部成立则 Phase 3 必须立即结束：

1. Phase 2 Rule Only 仍可独立运行
2. `SemanticAnalysisInput` 契约完成
3. `SemanticObservationDraft` structured output 完成
4. schema validation 完成
5. exact source binding 完成
6. `BehaviorEvidence` 契约完成
7. `SemanticAnalysisResult` 契约完成
8. `SKIPPED` / `OK` / `ERROR` / `INVALID_OUTPUT` 状态正确
9. Rule + Semantic 离散决策表完成
10. mock / deterministic tests 通过
11. 至少一次真实 DeepSeek smoke test 成功
12. 正式真实 LLM evaluation 可重跑
13. Rule Only vs Rule + Semantic 使用同一评测口径
14. development_generalization 没有逐样本调 Prompt
15. frozen / external 未使用
16. ground truth 未进入 Semantic Analyzer
17. 正式实验数字由程序生成
18. 没有为了 Recall 做第二轮 benchmark-specific Prompt patch
19. full tests + verification 通过

然后：completion report → commit → push → STOP。

即使 generalization 上 Rule Only Recall = 0%、Rule + Semantic Recall = 10% 或 0%，只要实现、实验和数据边界真实正确，Phase 3 都必须结束。低指标是实验发现，不是继续 Phase 3R / Prompt patch loop 的理由。

---

## 12. Phase 3 must not implement

- Trusted Factual Evidence
- FACT_TAMPERING 完整判断
- KNOWLEDGE_CONFLICT 完整判断
- Unified Evidence-grounded Judge
- Final Risk Engine
- Query-conditioned Retrieval Hijacking
- Protected RAG
- Context Integrity Checker
- Web Frontend
- Phase 1.6 External Benchmark

不要因为语义层需要接口，就把后续模块顺手实现。

---

## 13. LLM configuration

通过环境变量读取：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`

禁止打印、记录、写入代码 / 日志 / 测试 / 文档或 commit `.env`。

真实实验使用当前配置的 DeepSeek。测试允许 deterministic fake/mock，但 mock 不能作为正式实验结果。
