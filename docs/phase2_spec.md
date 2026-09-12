# Phase 2 Specification — Core Detection Foundation

定位：Parser / Chunker 之后，Semantic / Evidence / Judge / RAG 之前。

目标：第一套可运行、可评估、尽量可泛化的 Rule-only baseline。

不是完整 Ingestion Security Pipeline，也不是最终 ZhiYu Judge。

Phase 2 决策一律标记为 `rule_only_baseline`。

---

## 1. Pipeline

```text
DetectionInput (per chunk)
  -> Rule Scanner
  -> RuleEvent[]
  -> Document Aggregator (same document_id)
  -> document-level DetectionResult
     SAFE / REVIEW / POISON
```

- Scanner 的原子输入始终是一条 `DetectionInput`。
- Scanner 只对当前 chunk 产出 `RuleEvent[]`，不给整篇文档下结论。
- Aggregator 只合并同一 `document_id` 的 `RuleEvent`。
- Aggregator 不重新扫描全文，不重新跑规则，不调用 LLM，不访问 Query、trusted KB 或 ground truth。

---

## 2. Input

`DetectionInput` 字段仅允许：

- `document_id`
- `chunk_id`
- `text`
- `runtime?`（仅允许 `request_id` / `file_format`）

Scanner 只能读取当前 chunk 的 `text` 和允许的 runtime 字段。

禁止进入 Detector：

- label
- attack type ground truth
- query
- answer / target_answer
- trusted facts
- 其他文档
- benchmark metadata
- split / sample id 作为检测特征

评估器可以持有 `original_label`，但不得把它传入 Scanner、Aggregator 或 `DetectionInput`。

检测文本使用防火墙安全的 chunk / `benchmark_text` 路径，不使用 evaluator metadata，也不把 `parsed_text` 中的构造捷径当作规则依据。

---

## 3. RuleEvent

Phase 2 只使用一种事件对象 `RuleEvent`。不为 Signal、BehaviorEvidence 或 RetrievalEvidence 建立并行结构。

字段：

- `rule_id`
- `mechanism`：`PROMPT_INJECTION` | `HIDDEN_INSTRUCTION` | `FACT_TAMPERING` | `KNOWLEDGE_CONFLICT` | `RETRIEVAL_HIJACKING`
- `event_class`：`MECHANISM` | `STATISTICAL`
- `confidence`：`LOW` | `MEDIUM` | `HIGH`
- `document_id`
- `chunk_id`
- `span_start`
- `span_end`
- `excerpt`
- `rationale`
- `measurement`：optional；仅 STATISTICAL 使用，形状为 `{name, value, threshold}`

约束：

- `span` 是相对当前 `DetectionInput.text` 的半开区间 `[start, end)`。
- `excerpt` 必须等于 `text[span_start:span_end]`，并保持短小可审计。
- chunk-global 统计也必须落到代表性 source span，不得把超长 chunk 整段塞进 `excerpt`。
- `rationale` 只描述攻击机制或统计异常。
- `rationale` 不得包含 dataset 名、样本 ID、ground truth、实体白名单等数据集特征。
- `STATISTICAL` 永远不能单独导致 `POISON`。
- 只有 `MECHANISM` + `HIGH` 才具有 `POISON` 资格。
- `confidence` 是离散等级，不使用伪精确概率。
- `RuleEvent` 本身不包含最终 decision。
- `RuleEvent` 不包含 LLM 输出、trusted evidence、query、answer、label 或跨文档信息。
- `MECHANISM` 事件的 `measurement` 必须为 `None`。
- 不新增 `qualified` 字段。HIGH 是否成立完全由 Scanner 负责。

枚举可以保留五类威胁，但 Phase 2 Rule Scanner 不要求实际覆盖五类。禁止为了“覆盖五类”在没有 trusted evidence 时硬写 `FACT_TAMPERING` / `KNOWLEDGE_CONFLICT` 事实判断规则。

---

## 4. Scanner 能力

### 4.1 PROMPT_INJECTION

可以产生 `event_class = MECHANISM`。

只有存在明确模型控制行为时，才允许 `confidence = HIGH`。

典型机制：

- 要求忽略 / 覆盖已有指令
- 要求替换 system / developer / user role
- 要求改变原任务目标
- 要求绕过已有规则或策略
- 明确指示后续模型执行与知识内容无关的控制行为

HIGH 必须指向明确 source span。

禁止仅因为出现某个关键词就 HIGH。单独出现 `ignore`、`system`、`instruction`、`role` 不构成攻击证据。必须结合局部结构判断它是否真的形成模型控制指令。

规则应尽量表达组合机制：control verb + instruction target + override / role / task relation。不要维护英文 jailbreak 黑名单 + 中文攻击短语黑名单作为主要实现。

### 4.2 HIDDEN_INSTRUCTION

Phase 2 只定义为：具有可核验结构伪装的模型控制指令。

不负责判断“表面像知识，实际上意图控制模型”。后者留给 Phase 3 Semantic Analyzer。

HIGH 必须同时满足：

- 存在可验证的隐藏 / 伪装载体
- 载体内部存在明确的模型控制 payload

载体例子：HTML / Markdown comment、明确标记为 model-only / internal instruction 的区域、明显隐藏的 metadata-like container。

“在代码块里”“在引用块里”“在普通注释里”本身都不能自动视为恶意。

如果只有可疑容器但没有明确控制 payload：最多 `MECHANISM + LOW/MEDIUM`，或不产生事件；不得 HIGH。

如果只有疑似控制语义，但需要理解整段上下文才能确认攻击意图：Phase 2 不判 POISON。

### 4.3 RETRIEVAL_HIJACKING

Phase 2 入库阶段没有 Query、Top-K、rank、retrieval score，因此不得声称 RETRIEVAL_HIJACKING 已被证实。

只允许通用 retrieval manipulation signals：

- abnormal repetition
- repeated phrase concentration
- n-gram dominance
- unusual token / term concentration
- obvious stuffing
- lexical concentration anomaly

这些事件统一输出为：

- `mechanism = RETRIEVAL_HIJACKING`
- `event_class = STATISTICAL`

`confidence` 可以是 LOW / MEDIUM / HIGH，但即使是 HIGH，`STATISTICAL + HIGH` 也不能单独导致 POISON。

Document Aggregator 对纯 RH 统计事件的最高决策是 `REVIEW`。

不允许因为 repetition 极高、keyword density 极高、或多个 statistical event 同时出现，就把文档升级为 POISON。

rationale 应使用类似：

- retrieval-manipulation signal detected
- abnormal repetition concentration
- possible retrieval stuffing

禁止写：retrieval hijacking confirmed。

Query-conditioned 的真正 RETRIEVAL_HIJACKING 判断留给后续 retrieval stage。Phase 2 只负责 ingestion-time suspicion。

### 4.4 Hard-negative / quotation context

引用、教学、安全研究语境的 hard-negative 处理必须发生在 Rule Scanner 产生 `MECHANISM + HIGH` 之前。

Aggregator 不重新读取 chunk，也不重新判断“这是攻击还是在讨论攻击”。

因此 `MECHANISM + HIGH` 表示：当前 source span 中存在一个明确、可执行意义上的模型控制机制，并且已经通过 Phase 2 能力范围内的 hard-negative / quotation context 检查。

下面这种正常知识文本不得产生 `PROMPT_INJECTION + MECHANISM + HIGH`：

> Prompt injection attacks may contain ‘ignore previous instructions’.

Scanner 应不产生事件，或降为 MEDIUM / LOW。绝不能让它以 HIGH 进入 Aggregator。

代码示例、安全论文引用、攻击教学说明、字符串字面量、引用攻击 payload，不能仅凭里面出现完整控制句就产生 HIGH。

---

## 5. Document Aggregator

Aggregator 只看同一 `document_id` 的 `RuleEvent[]`。

不新增独立 `qualified` 字段。HIGH 是否成立完全由 Scanner 负责。Aggregator 只按离散决策表执行：

- `PROMPT_INJECTION` 或 `HIDDEN_INSTRUCTION`
- `event_class == MECHANISM`
- `confidence == HIGH`

决策表：

**CASE 1**  RuleEvent 数量 = 0 → `SAFE`

**CASE 2**  存在事件，但不存在任何  
`mechanism ∈ {PROMPT_INJECTION, HIDDEN_INSTRUCTION}` 且 `event_class == MECHANISM` 且 `confidence == HIGH`  
→ `REVIEW`

包括：LOW/MEDIUM mechanism、任意 STATISTICAL、任意数量 RH statistical events、多个弱机制事件、弱机制 + 统计异常。全部只能 REVIEW。

**CASE 3**  至少存在 1 条  
`mechanism ∈ {PROMPT_INJECTION, HIDDEN_INSTRUCTION}` 且 `event_class == MECHANISM` 且 `confidence == HIGH`  
→ `POISON`

其他 LOW / MEDIUM / STATISTICAL 事件可以保留在结果中作为辅助说明，但不改变这个决策。

禁止分数累积：

- LOW + LOW + LOW → MEDIUM
- MEDIUM + MEDIUM → HIGH
- STATISTICAL × N → POISON
- 多个不同 rule_id 命中 → 自动增加风险等级

Phase 2 不做数值加权总分。Aggregator 是离散决策矩阵，不是 scoring model。

一条 `MECHANISM + HIGH` 的 `PROMPT_INJECTION` 或结构型 `HIDDEN_INSTRUCTION` 即足够导致 POISON。不要求两条独立 HIGH。

Aggregator 禁止：

- 重新读取 chunk text
- 重新跑 regex
- 判断语义
- 调 LLM
- 查 trusted evidence
- 看 query
- 看 ground truth
- 计算加权风险总分

决策语义：

- `SAFE`：没有 Rule Scanner 发现的风险信号。
- `REVIEW`：发现可疑或异常信号，但证据不足以证明明确入库攻击机制。
- `POISON`：至少存在一个由 Scanner 给出的、可定位的显式模型控制攻击机制（`PI/HI + MECHANISM + HIGH`）。

这是 rule-only baseline decision，不是未来 Full ZhiYu Judge 的最终决策语义。

---

## 6. DetectionResult

文档级稳定接口，至少包含：

- `document_id`
- `decision`：`SAFE` | `REVIEW` | `POISON`
- `decision_kind`：`rule_only_baseline`
- `rule_events`：该文档全部 `RuleEvent`

必须可追溯：document decision → RuleEvent → chunk_id → source span / excerpt。

不含 ground truth、query、LLM 原文或加权总分。

---

## 7. Rule Legality Policy

Phase 2 只允许机制级规则。合法规则必须描述攻击者正在做什么，而不是数据长什么样。

### Allowed rule families

1. Instruction Override
2. Role Manipulation
3. Task Hijacking
4. Policy / Constraint Bypass
5. Structurally Hidden Control Payload
6. Retrieval Manipulation Statistics（仅 STATISTICAL，最高 REVIEW）

中文和英文都可以支持，但不要把英文 jailbreak phrase blacklist + 中文攻击短语 blacklist 作为主要实现。

### Forbidden

以下规则一经发现，默认视为数据集过拟合，应删除或重构：

1. Domain-specific entities（学校、校区、地点、部门、课程、人物、产品等，除非该实体本身就是安全协议语义的一部分）
2. Sample-specific strings（样本原句、轻微改写、失败样本独有短语、benchmark 高频模板片段）
3. Dataset metadata shortcuts（sample id、filename pattern、label、split name、attack type GT、construction note、source dataset name）
4. Template recognition（“长得像 poison 样本”、固定开头/结尾、人工生成模板、某种语料风格）
5. Generalization leakage（根据 generalization 单样本补 regex / 关键词 / 阈值 / 优先级）
6. frozen / external 用于开发

### development_tune policy

development_tune 可以查看失败样本、做错误分类、分析缺失的攻击机制、查看 FP / FN 原因。

禁止：看到某个失败样本，就把它的原句、实体、模板或近似表达写进规则。

允许：通过失败样本发现某个尚未覆盖的通用攻击机制，独立定义该机制，用多个不同表达和正常反例验证，再决定是否加入规则。

每个新增规则必须通过：

1. 这条规则描述的是什么攻击机制？
2. 如果换成金融、医疗、CTI、技术文档等未见领域，这条规则仍然合理吗？
3. 如果完全删除当前失败样本，我们仍然有理由设计这条规则吗？
4. 有没有正常文本可能出现同样表面词语？如果有，规则是否有足够上下文约束避免误报？

任意一问无法合理回答：不得加入规则。

每个 Rule Family 至少同时包含 positive、paraphrased positive、negative、hard-negative tests。尤其要测试关键词出现但不是攻击，例如安全文档讨论 Prompt Injection。

---

## 8. Evaluation

必须明确区分 “POISON 检出能力” 和 “REVIEW 分流行为”。禁止把 REVIEW 合并进阳性来刷 Recall。

### Primary binary detection metric

预测侧只有 `decision == POISON` 才算 `predicted_positive = True`。SAFE 和 REVIEW 都算 False。

主指标：Precision、Recall、F1、FPR。衡量的是 Rule-only baseline 是否能真正给出高置信 POISON。

### Ground-truth mapping

现有 `original_label` 不直接等于 SAFE / REVIEW / POISON。

- positive ground truth：`original_label == poison`
- negative ground truth：`original_label == normal` 或 `hard_negative`
- `original_label == conflict`：不并入主 binary correctness，只报告 decision distribution

不得为了计算漂亮 F1，强行把 conflict 映射成 poison 或 normal。

真实 poison 且 prediction = REVIEW：主指标记 FN，同时记录 `poison_review_rate`。

### Auxiliary triage metrics

至少报告：

- review_rate_overall
- review_rate_normal
- review_rate_hard_negative
- review_rate_poison
- safe_rate_normal
- safe_rate_hard_negative
- safe_rate_poison
- poison_rate_normal
- poison_rate_hard_negative

尤其关注 `hard_negative_poison_rate`。

### Conflict reporting

只报告 `conflict_safe_rate`、`conflict_review_rate`、`conflict_poison_rate`。不要计算 conflict 准确率。Phase 2 没有 trusted factual evidence；大量 conflict 不应被规则直接 POISON。Detector 不得因 “conflict” 这个 ground-truth label 被特殊处理。

### Diagnostics

辅助报告：event count by mechanism / event_class / confidence、document decisions by split、POISON trigger rule families。不得只给一个总 F1。

### Split policy

- `development_tune`：允许聚合指标、FP / FN 明细、rule debugging。
- `development_generalization`：只允许聚合指标和分机制/分标签聚合统计。禁止根据单样本失败修改规则。
- frozen / external：Phase 2 不使用。

### No score threshold

Phase 2 不设 `F1 >= X` 或 `Recall >= X` 才通过。低 Recall 可以诚实接受。虚假高 Recall 不可以。

如果 evaluator 中已经存在合法的 evaluator-only attack family metadata，可以额外报告 scope-aligned recall，但只能作为辅助诊断，不得替代 all-poison Recall。如果当前数据没有可靠 attack family metadata，不要人工猜测或重新标注来制造该指标。

---

## 9. Hard Stop

只要以下条件全部满足，Phase 2 必须立即结束：

1. 主链路可运行：DetectionInput → Rule Scanner → RuleEvent[] → Document Aggregator → document-level DetectionResult。

2. Phase 2 已实现当前明确允许的三类能力：PROMPT_INJECTION 的显式机制规则；HIDDEN_INSTRUCTION 的结构隐藏规则；RETRIEVAL_HIJACKING 的统计异常信号。不要求覆盖 FACT_TAMPERING 和 KNOWLEDGE_CONFLICT。

3. 测试覆盖至少包括：positive；paraphrased positive；negative；quoted / educational hard-negative；statistical RH cases；aggregation decision matrix；DetectionInput ground-truth firewall。

4. 数据边界正确：development_tune 允许明细调试；development_generalization 只允许聚合评估；frozen / external 完全不使用。

5. evaluation runner 可重复运行，并真实输出：Precision、Recall、F1、FPR、REVIEW-related auxiliary metrics、hard-negative poison rate、conflict decision distribution、rule/event diagnostics。

6. 所有实验数字由程序生成。即使 Recall 很低，也必须如实报告。

7. 没有 dataset-specific patch。

8. 没有为了提高分数继续增加第二轮规则族。

9. Phase 2 中没有实现：LLM Semantic Analyzer；Behavior Evidence Layer；Trusted Factual Evidence；Evidence-grounded Judge；Query-conditioned RH；Protected RAG；Context Integrity Checker；Web Frontend。

10. 相关 tests 和 verification 通过。

一旦以上 10 条全部满足：

- PHASE 2 COMPLETE
- 更新简洁 completion report
- commit
- push
- STOP

禁止：

- 因 Recall 低继续补规则
- 因还能想到新 regex 继续开发
- 自动进入 Phase 3
- 自动新增 Phase 2R / 2R2
- 重新打开 Phase 1.6

低 Recall 是 Phase 2 baseline 的实验结果，不是继续扩张 Phase 2 的理由。

---

## 10. Phase boundary

Phase 2 不做：

- LLM Semantic Analyzer
- Behavior Evidence Layer
- Trusted Factual Evidence
- FACT_TAMPERING 完整判断
- KNOWLEDGE_CONFLICT 完整判断
- Evidence-grounded unified Judge
- Final unified Risk Engine
- Query-conditioned RETRIEVAL_HIJACKING
- Protected RAG
- Context Integrity Checker
- Web Frontend
- External Benchmark / Phase 1.6

Phase 3 只解决 Rule-only baseline 无法可靠处理的隐式行为语义：

- LLM Semantic Analyzer
- Behavior Evidence
- 隐式控制意图判断
- 接到现有 DetectionInput / RuleEvent / DetectionResult / document aggregation 接口上

Phase 2 必须继续能独立运行，作为 Rule Only ablation。

Phase 3 不得把剩余整条 Ingestion Pipeline 做完。
