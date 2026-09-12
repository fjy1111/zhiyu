# Phase 4 Specification — Factual Evidence Layer

定位：Phase 3 Semantic Behavior Layer 之后，Unified Judge / Final Risk Engine / Protected RAG 之前。

目标：对当前 candidate chunk 中的原子事实主张，与独立冻结的 Trusted Reference Corpus 做可审计比较，只产出事实关系证据。

Phase 4 只回答：

> 当前文档中的事实主张，与独立可信证据之间是什么关系？

关系仅允许：

- `SUPPORTED`
- `CONTRADICTORY`
- `INSUFFICIENT_EVIDENCE`

**Phase 4 不输出 `SAFE / REVIEW / POISON`。**

继续遵守：

- Evidence First, Judgment Second
- UNKNOWN != POISON
- `INSUFFICIENT_EVIDENCE != POISON`
- LLM 不得凭参数记忆判断外部事实
- ground truth 不得进入 Detector

---

## 1. Pipeline

```text
Candidate DetectionInput (current chunk)
  -> Claim Extractor
  -> ClaimExtractionResult
        AtomicClaim[] | NO_CLAIM | INVALID_OUTPUT | ERROR
  -> per AtomicClaim Trusted Evidence Retrieval
        (frozen Trusted Reference Corpus only)
  -> overlap filter (id / path / hash)
  -> EvidenceRetrievalResult
        OK | NO_EVIDENCE | ERROR
  -> one LLM comparison call per AtomicClaim (at most TOP_K references)
  -> pairwise validation
  -> deterministic claim-level aggregation
  -> FactualEvidence
```

Comparer 不得直接吃 Claim Draft 或未通过 overlap filter 的命中。

---

## 2. Trusted Reference Corpus

Phase 4 使用 **独立、冻结** 的 Trusted Reference Corpus。Candidate Corpus 与 Trusted Reference Corpus 在逻辑和文件层面分离。

### 2.1 V1 construction

V1 从 source trusted-provenance 语料中，**确定性**划出一份 reference-only 子集：仅包含 canonical normal / trusted 文档。

这些文档 **只** 进入 Trusted Reference Corpus：

- 必须从所有 candidate pool 中移除（development_tune、development_generalization、以及任何 Phase 4 candidate evaluation pool）
- candidate 与 reference 必须按 path / `document_id` / content hash 分离
- reference 文本必须像 candidate `benchmark_text` 一样剥离 benchmark construction artifacts
- **不得**把 `qa_set` expected answers 当作 trusted evidence
- **不得**把 `metadata["facts"]` 当作 runtime evidence
- 选择过程必须确定性，并在 Phase 4 正式评测前冻结
- 生成 manifest + SHA256 + overlap audit
- 正式评测开始后，不得因为 FN/FP 再补充或调换 reference

这在真实部署中对应：管理员预先固化的官方参考文档集，而不是运行时从候选库里投票出来的“真值”。

### 2.2 Runtime isolation

1. “trusted” 身份必须在 Detector 运行前确定，不能由当前 candidate 的 label 或评测结果动态决定。
2. 普通 untrusted KB 的多数意见不是真值。`untrusted KB majority != trusted evidence`。
3. V1 不做实时 Web search。
4. 任一 candidate：
   - 不能成为自己的 trusted reference
   - 不能把同一 candidate evaluation pool 中的其他 candidate 当 trusted gold
   - 与 candidate 来自同一原始文件或相同 content hash 的文本不得进入其 reference evidence
5. overlap audit 必须检查 `document_id` / path / hash 的直接重叠；正式评测要求 overlap = 0。

### 2.3 Detector-visible vs evaluator-only

Detector 只允许读取：

- 当前 candidate 中抽取的 claim
- 从 Trusted Reference Corpus 检索出的 reference **原文**
- retrieval / 审计所需 provenance：`reference_id` / source path / content hash / retrieval score

Detector 绝对禁止读取：

- `original_label`
- `attack_type` ground truth
- `metadata["facts"]`
- `target_answer`
- `qa_set` expected answers
- evaluator-only annotation
- split name 等 benchmark 信息

`metadata["facts"]` 与 expected answers 只允许 evaluator 使用。

Factual conclusion 必须来自：

```text
candidate claim excerpt (+ retrieval-oriented normalized_claim)
  ↔ retrieved trusted source text
```

而不是 LLM 参数记忆。

---

## 3. Claim extraction

只在 **当前 candidate chunk** 内抽取原子事实主张。

### 3.1 输入

Claim Extractor 只读取：

- `DetectionInput.document_id`
- `DetectionInput.chunk_id`
- `DetectionInput.text`

禁止读取 label、attack_type、`metadata["facts"]`、trusted reference、其他 candidate、邻 chunk、全文、split / benchmark metadata。

Claim Extraction **不得提前看到** trusted evidence。

### 3.2 什么算 claim（extractor 语义约束）

必须是可外部核验的原子事实，例如：时间、地点、数值、身份/归属、规则/规定内容、状态/事件是否发生。

禁止：Prompt Injection / 模型控制指令、意见/偏好/情绪、建议、纯修辞、无法核验的价值判断、整段 chunk、多个事实揉成一个复合 claim。

不得为当前校园数据集设计固定字段。Claim schema 必须跨领域通用。

**Claim 的事实性、原子性、最小规范化是 semantic extractor 的约束，不是确定性规则层的工作。** 不得为此编写 regex / keyword 规则去判断“像不像事实”或“是否原子”。

每 chunk 最多 `MAX_CLAIMS = 3`。禁止把整个 chunk 当一个 claim。

### 3.3 ClaimDraft

LLM 只输出 draft：

- `excerpt`：当前 chunk 的短原文
- `normalized_claim`：面向检索的最小规范化，不得加入原文中不存在的新事实
- `claim_type`：optional generic category
- `rationale`：optional

`normalized_claim` **不是 evidence，也不是 ground truth**。它只用于 retrieval 查询。Comparer 必须同时收到 **原始绑定 excerpt** 和 `normalized_claim`。单独的 `normalized_claim` 永远不能生成 `FactualEvidence`。

LLM 不生成 `claim_id`、offset、SAFE/REVIEW/POISON。

### 3.4 Deterministic validator

确定性校验 **只** 负责：

- schema
- `MAX_CLAIMS`
- 长度限制
- 必填字段
- unique exact excerpt binding

不做事实性 / 原子性 / 领域关键词判定。

excerpt 必须在当前 chunk 中唯一出现：

- unique → 程序计算 `span_start` / `span_end`，并验证 `text[span:end] == excerpt`
- absent → `INVALID_OUTPUT`
- multiple → `INVALID_OUTPUT`

不做 fuzzy matching，不自动选 occurrence，不用模型猜 offset。

### 3.5 All-or-nothing

同一次 LLM response 中任一 claim 在确定性校验上失败：

```text
status = INVALID_OUTPUT
claims = []
```

不得部分接受。

### 3.6 ClaimExtractionResult

- `document_id`
- `chunk_id`
- `status`：`OK` | `NO_CLAIM` | `INVALID_OUTPUT` | `ERROR`
- `claims`：`AtomicClaim[]`
- `error_code`：optional

`NO_CLAIM`：模型明确判断当前 chunk 没有可核验事实主张。不是 ERROR，不是 POISON。

`INVALID_OUTPUT` / `ERROR` 不能假装成 `NO_CLAIM`。

### 3.7 AtomicClaim

只有通过确定性校验的 draft 才能生成：

- `claim_id`：程序确定性生成
- `document_id` / `chunk_id`
- `span_start` / `span_end`
- `excerpt`
- `normalized_claim`
- `claim_type`：optional

---

## 4. Trusted evidence retrieval

每个 `AtomicClaim` 单独检索一次。不做 chunk 级共享 evidence pool。

### 4.1 检索输入

只允许：

- `claim.normalized_claim`（查询）
- `claim.excerpt`（绑定原文，必须随 claim 传递）
- frozen Trusted Reference Corpus index

禁止读取 label、attack_type、`metadata["facts"]`、target_answer、qa_set expected answers、其他 candidate 的标签或 evaluator 信息。

### 4.2 检索空间

只允许 Trusted Reference Corpus。

不得检索：当前 candidate corpus、普通 untrusted KB、development_generalization candidate pool、frozen benchmark candidate pool、Web、LLM 参数记忆。

### 4.3 Overlap filter and abstention

V1：

- 固定小 `TOP_K`，**K = 3**
- **先**做 overlap filter
- 任一命中与当前 candidate 存在 same `document_id` / same source path / same content hash → 丢弃
- 过滤后若无 candidate 剩余 → `NO_EVIDENCE`

Phase 4 **不发明、不调参** 任意语义相似度阈值。弱相关 / 仅主题相关的命中留给 pairwise `NOT_ENOUGH`。

`retrieval_score` 只用于排序和审计，不是 factual truth。

不得：用 LLM 记忆补证据、猜测外部事实、因 candidate 看起来可疑就判 CONTRADICTORY、为避免空结果强行保留已被 overlap 过滤的命中。

### 4.4 EvidenceRetrievalResult

- `claim_id`
- `status`：`OK` | `NO_EVIDENCE` | `ERROR`
- `evidence_candidates`：`TrustedEvidenceCandidate[]`（最多 3 条）
- `error_code`：optional

`OK`：至少一个通过 overlap filter 的 trusted evidence candidate。
`NO_EVIDENCE`：检索正常完成，过滤后为空。
`ERROR`：index / provider / runtime 异常。ERROR 不能伪装成 `NO_EVIDENCE`。

`NO_EVIDENCE` 时该 claim 后续只能 `INSUFFICIENT_EVIDENCE`。

### 4.5 TrustedEvidenceCandidate

- `reference_id`
- `reference_document_id`
- `reference_path`
- `reference_content_hash`
- `retrieval_score`
- `span_start` / `span_end`
- `excerpt`

`excerpt` 必须是 Trusted Reference Corpus 中的真实原文片段。span 由程序基于 reference 原文确定，并验证 `reference_text[span_start:span_end] == excerpt`。

不得只保存 LLM 摘要、改写后的事实、或模型生成的 “reference statement”。

provenance 不能把 “official” 等字段直接推出 `SUPPORTED`。

### 4.6 检索算法

V1 可用通用 lexical / vector / hybrid retrieval。

禁止为当前校园数据：固定 topic 字典、固定字段名、固定实体规则、benchmark sample id / scenario / filename shortcut。

---

## 5. Claim ↔ evidence comparison

Phase 4 最终只生成 factual relation evidence，仍然不输出 `SAFE / REVIEW / POISON`。

### 5.1 Comparer 输入

对每个 AtomicClaim 只允许：

- 当前 `AtomicClaim`（**必须含绑定 excerpt**；`normalized_claim` 只作辅助，不能单独成证）
- 该 claim 对应的合法 `TrustedEvidenceCandidate[]`（≤ TOP_K）
- 每条 reference 的原文 excerpt
- 必要 provenance：`reference_id` / path / content hash / span / retrieval score

禁止读取 label、attack_type、`metadata["facts"]`、target_answer、qa_set expected answers、evaluator annotation、其他 candidate、其他 claim 的 evidence、Web、LLM 参数记忆、document-level decision。

必须依据 claim excerpt ↔ retrieved trusted source text。不得用模型记忆补充外部事实。

### 5.2 Cost-bounded pairwise comparison

逻辑上仍是 pairwise：每个 claim × 每条 reference 一条 relation。

V1 实现约束：

- **每个 AtomicClaim 只调用 1 次 LLM**
- 一次调用最多带入 `TOP_K=3` 条 evidence candidates
- 返回必须为每个 `reference_id` **恰好一条** relation

除非测试明确要求，否则不对每个 claim-reference pair 单独发 API。

`ReferenceComparisonDraft`：

- `reference_id`：必须属于当前 retrieval result
- `relation`：`SUPPORTS` | `CONTRADICTS` | `NOT_ENOUGH`
- `rationale`

LLM 不生成：FactualEvidence id、SAFE/REVIEW/POISON、risk score、新的 reference quote、新的 claim、外部事实。

程序校验：

- 每个返回的 `reference_id` 属于当前 retrieval result
- 无重复 `reference_id`
- 每个被比较的 reference 恰好有一条 pairwise result
- 非法引用 / 缺条 / 重复 → 该次 comparison `INVALID_OUTPUT`

### 5.3 Pairwise 定义

- **SUPPORTS**：reference 原文明确提供能够支持 AtomicClaim 的事实。
- **CONTRADICTS**：reference 原文明确给出与 AtomicClaim **不可同时成立** 的事实。
- **NOT_ENOUGH**：未涉及关键事实、仅主题相关、证据过模糊、无法确认支持或冲突。

“没有提到”绝不能等于 `CONTRADICTS`。弱相关命中走 `NOT_ENOUGH`，而不是在 retrieval 层用相似度阈值砍掉。

### 5.4 Claim-level deterministic aggregation

程序根据 pairwise relations 生成最终 relation。禁止多数投票、weighted voting、retrieval score voting。

| pairwise 情况 | claim-level relation |
|---|---|
| ≥1 SUPPORTS 且 0 CONTRADICTS | `SUPPORTED` |
| ≥1 CONTRADICTS 且 0 SUPPORTS | `CONTRADICTORY` |
| 同时存在 SUPPORTS 与 CONTRADICTS | `INSUFFICIENT_EVIDENCE` |
| 全部 NOT_ENOUGH | `INSUFFICIENT_EVIDENCE` |
| retrieval.status == NO_EVIDENCE | `INSUFFICIENT_EVIDENCE` |

trusted store 内部冲突时，Phase 4 不裁决哪个 source 更真，统一 `INSUFFICIENT_EVIDENCE`。

### 5.5 Comparison failure

ComparisonResult status：`OK` | `INVALID_OUTPUT` | `ERROR`

`ERROR` / `INVALID_OUTPUT` 不能被解释成 SUPPORTED / CONTRADICTORY / INSUFFICIENT_EVIDENCE，也不能自动成为 POISON。后续 Judge 如何处理失败，不属于 Phase 4。

### 5.6 FactualEvidence

只有经过 AtomicClaim validation、trusted retrieval、pairwise comparison validation、deterministic aggregation 之后才能生成。单独 `normalized_claim` 不能创建该对象。

- `evidence_id`：程序确定性生成
- `claim_id`
- `document_id` / `chunk_id`
- `claim_excerpt` / `normalized_claim`
- `relation`：`SUPPORTED` | `CONTRADICTORY` | `INSUFFICIENT_EVIDENCE`
- `supporting_reference_ids[]`
- `contradicting_reference_ids[]`
- `insufficient_reference_ids[]`
- `reference_provenance[]`
- `rationale` / `aggregation_reason`

追溯链：

```text
FactualEvidence
  -> AtomicClaim.excerpt (bound)
  -> TrustedEvidenceCandidate
  -> trusted reference document
  -> exact excerpt/span
```

### 5.7 NO_EVIDENCE

```text
relation = INSUFFICIENT_EVIDENCE
supporting_reference_ids = []
contradicting_reference_ids = []
aggregation_reason = NO_TRUSTED_EVIDENCE
```

含义是“系统不知道”，不是“claim 是假的”。

---

## 6. Evaluation

Phase 4 是事实关系证据层，不是最终投毒检测器。**不得用 overall POISON Recall 作为 Phase 4 验收标准。**

Ground truth / `metadata["facts"]` / expected answers **只允许 evaluator 读取**，永远不能进入 Claim Extractor / Retriever / Comparer。

至少报告：

- claim extraction status counts
- claim count
- retrieval OK / NO_EVIDENCE / ERROR counts
- overlap rejection count
- pairwise SUPPORTS / CONTRADICTS / NOT_ENOUGH counts
- comparison OK / INVALID_OUTPUT / ERROR counts
- final FactualEvidence relation counts
- LLM call count
- reference corpus manifest / hash
- candidate/reference overlap audit（必须为 0）

开发顺序：先 deterministic fixtures / mocks。

真实 DeepSeek 只用于：

1. 最小 claim extraction smoke
2. 最小 comparison smoke
3. Prompt / config / reference corpus 冻结后的 **一次** 正式评测

禁止反复全量 benchmark Prompt tuning。禁止查看 `development_generalization` 单样本。

---

## 7. Hard Stop

以下全部成立则 Phase 4 必须立即结束：

1. 冻结 reference store + manifest + zero-overlap audit 存在
2. `ClaimExtractionResult` / `AtomicClaim` 已实现
3. exact source binding 已实现
4. retrieval result / `TrustedEvidenceCandidate` 已实现
5. pairwise comparison validation 已实现
6. deterministic relation aggregation 已实现
7. `FactualEvidence` 可追溯
8. mock / unit / integration tests 通过
9. 最小真实 DeepSeek smoke 通过
10. 正式 Phase 4 evaluation 可复现
11. ground truth 未进入 Detector
12. 未加入 Web / Judge / Risk Engine / RAG / Phase 5 代码

然后：completion report → commit → push → STOP。

低指标或大量 `INSUFFICIENT_EVIDENCE` 是实验发现，不是继续补 reference、调阈值或进入 Phase 4R 的理由。

---

## 8. Phase 4 must not do

- 根据 `CONTRADICTORY` 直接输出 `POISON`
- 根据 `SUPPORTED` 直接输出 `SAFE`
- 把多个 claim 合成 document risk
- Unified Judge / Final Risk Engine
- Query-conditioned Retrieval Hijacking
- Protected RAG / Context Integrity Checker / Web frontend
- 实时 Web search
- 使用 `metadata["facts"]` 或 qa_set expected answers 作为 Detector 证据
- 让 LLM 用参数记忆充当 trusted evidence
- 为事实性/原子性编写 regex 规则
- 为 Phase 4 调任意相似度阈值
- 按 FN/FP 动态增补 Trusted Reference Corpus

---

## Final principle

Phase 4 的产品是可审计的事实关系证据：

```text
bound claim excerpt ↔ Trusted Reference 原文
  -> SUPPORTED | CONTRADICTORY | INSUFFICIENT_EVIDENCE
```

证据不足和 trusted store 内部冲突都不是投毒结论。
