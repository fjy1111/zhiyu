# AGENTS.md

# 知御（ZhiYu）项目开发规范

## 1. 项目定位

项目名称：

知御（ZhiYu）

项目目标：

构建面向 RAG 知识库的投毒检测与主动防御系统。

当前项目强调：

- RAG 知识投毒检测
- 机制级安全证据
- 可解释风险裁决
- 泛化能力
- 数据泄漏控制
- 可复现实验
- 工程完整性

禁止为了提高当前 Benchmark 分数而牺牲泛化能力。

---

## 2. 开发工作流

本项目使用：

- Codex：负责实现
- Superpowers：负责规划、TDD、代码审查与验证工作流
- ChatGPT：阶段结束后进行外部代码评审

所有非简单代码修改应遵循：

1. 理解任务
2. 制定小任务计划
3. 测试先行
4. 最小实现
5. Spec Review
6. Code Quality Review
7. 集成测试
8. Verification
9. Commit
10. Push
11. 停止并等待外部评审

不得：

“实现完成后自己宣布阶段通过并自动进入下一阶段”。

未经用户明确批准：

不得进入下一 Phase。

---

## 3. Superpowers 使用原则

涉及多步骤开发时，应优先使用：

- writing-plans
- test-driven-development
- subagent-driven-development
- requesting-code-review
- verification-before-completion

出现 Bug、测试异常或实现与预期不符时：

使用：

- systematic-debugging

禁止：

在没有确定根因的情况下连续堆补丁。

---

## 4. 小任务原则

避免一次实现大量独立功能。

一个任务应尽可能只解决一个明确问题。

推荐：

Task 1
→ test
→ implementation
→ review

Task 2
→ test
→ implementation
→ review

而不是：

一次同时实现 5～10 个独立模块。

如果一个任务包含多个彼此独立的子系统：

必须先拆分。

---

## 5. TDD 原则

新的行为和 Bug 修复原则上必须：

RED
→ GREEN
→ REFACTOR

即：

1. 先写能够证明需求的测试
2. 确认测试在旧实现上失败
3. 编写最小实现
4. 确认测试通过
5. 再进行重构

禁止：

先写实现，再写一个只会验证当前实现的弱测试。

测试必须验证：

“需求是否满足”

而不是：

“代码是否按照当前写法运行”。

---

## 6. 禁止虚假验收

严禁：

- 硬编码 PASS
- 硬编码 overlap = 0
- 手工修改实验 JSON 结果
- 为了报告数字修改输出
- 测试脚本默认相信生成脚本
- 报告声称实现了源码中不存在的功能

Validator 应尽可能：

独立读取最终产物并重新计算结果。

完成报告中的技术结论必须能够从当前仓库代码重新运行得到。

---

## 7. 数据集总原则

`datasets/raw/`

视为不可修改区域。

严禁：

- 修改 raw 文件
- 删除 raw 文件
- 重命名 raw 文件
- 为了测试通过修正 raw 内容

所有数据转换必须写到：

`datasets/processed/`

Raw integrity 在相关阶段结束时必须验证。

---

## 8. 数据泄漏原则

未来 Detector 不得访问 Benchmark Ground Truth。

禁止输入：

- original_label
- label
- attack_type ground truth
- is_poison
- expected_answer
- facts 真值
- source_split
- 由文件路径泄漏的类别
- Benchmark 私有 metadata

正式 Detector 应通过明确的：

`DetectionInput`

接口获取输入。

禁止 arbitrary metadata 直接传入 Detector。

---

## 9. Dataset Split 使用纪律

当前数据使用规则：

### development_tune

允许：

- 开发
- 调 Prompt
- 调通用阈值
- 调攻击机制规则

### development_generalization

只用于阶段性泛化评估。

禁止：

根据某一个错误样本新增专门规则。

### stress_set

Evaluation only。

### frozen_holdout

最终评估前不得用于调参。

### external benchmark

用于跨数据集、跨领域泛化测试。

### independent blind set

最终比赛前另行构建。

---

## 10. 泛化优先原则

本项目不得重复过去：

“效果差
→ 补一个领域规则
→ 再测试
→ 再补规则”

的开发方式。

任何新规则必须回答：

“它描述的是哪一种攻击机制？”

允许：

- instruction override
- role hijacking
- hidden instruction
- abnormal repetition
- retrieval stuffing

禁止：

- 针对校园领域关键词
- 针对某个人名
- 针对某个学校
- 针对某个具体测试文件
- 针对某个 Benchmark 特定句子
- 针对某个实体字段补丁

如果不能解释为通用攻击机制：

不要加入 Detector。

---

## 11. Unknown 不等于 Poison

必须坚持：

UNKNOWN != POISON

可信知识库没有证据时：

不得仅因为缺少证据就判定为投毒。

系统必须允许：

- SAFE
- REVIEW / UNKNOWN
- POISON

事实真实性与攻击风险必须区分。

---

## 12. Evidence First, Judgment Second

知御核心设计原则：

先产生证据，
再进行判断。

不同攻击可以使用不同证据：

### 行为型攻击

例如：

Prompt Injection
Hidden Instruction

证据：

- 原文 suspicious span
- instruction intent
- rule event

### 事实型攻击

例如：

Fact Tampering
Knowledge Conflict

证据：

- Claim
- Trusted Evidence
- entailment / contradiction

### 检索操纵型

例如：

Retrieval Hijacking

证据：

- repetition statistics
- keyword density
- retrieval-related features

LLM 不应凭空创造安全证据。

---

## 13. LLM 使用原则

LLM 应主要负责：

- 语义分析
- Claim 提取
- Intent 分析
- Evidence-based Judgment
- Attack Attribution
- Explanation

禁止让 LLM：

仅凭自身记忆决定外部事实真假。

事实型判断应允许：

SUPPORTED
CONTRADICTORY
INSUFFICIENT_EVIDENCE

证据不足时允许拒判。

---

## 14. 长上下文原则

禁止默认把：

完整大文件
+
大量知识库内容

一次性发送给 LLM。

优先：

Document
→ Chunk
→ Candidate Analysis
→ Claim
→ Top-K Evidence
→ Judge
→ Structured Aggregation

文件级最终风险优先由结构化结果聚合。

---

## 15. 当前安全攻击体系

当前计划支持的主要机制：

- PROMPT_INJECTION
- HIDDEN_INSTRUCTION
- FACT_TAMPERING
- KNOWLEDGE_CONFLICT
- RETRIEVAL_HIJACKING

不得仅为了增加项目规模自行添加大量类别。

新增攻击类型必须先经过用户确认。

---

## 16. 检测阶段设计纪律

入库阶段关注：

Document-level Security

未来检索阶段关注：

Context-level Security

禁止简单地：

入库 Rule + LLM

然后 Retriever 后再原样跑一次：

Rule + LLM

检索阶段如果实现，必须解决不同问题，例如：

- 多 Chunk 冲突
- Query-conditioned context integrity
- context dominance
- context inconsistency

---

## 17. 代码设计原则

优先：

- 小模块
- 明确接口
- 类型明确
- 确定性行为
- 可测试
- 可消融
- 可复现

避免：

- God class
- 巨型函数
- 隐式全局状态
- 无约束 dict
- Magic constants
- 数据集特定逻辑混入通用模块

配置参数应放到：

`configs/`

而不是散落硬编码。

---

## 18. 实验原则

所有实验必须：

- 可重复运行
- 固定输入 split
- 保存配置
- 保存指标
- 保存 commit 信息（适合时）
- 区分开发和最终测试

重点指标包括：

- Precision
- Recall
- F1
- FPR
- ASR
- Defense Success Rate
- QA Accuracy

任何实验数值必须来自真实运行。

不得使用示例值冒充实验结果。

---

## 19. 完成前 Verification

任何任务声称：

- completed
- fixed
- PASS
- all tests passed

之前必须实际运行对应验证命令。

必须查看真实输出。

不能因为：

“代码看起来正确”

就宣布完成。

---

## 20. Code Review

较重要任务完成后必须至少进行：

### Spec Review

检查：

是否真的满足用户需求。

### Code Quality Review

检查：

- 逻辑正确性
- 测试质量
- 边界条件
- 重复代码
- 硬编码
- 泄漏
- 可维护性

Implementer 自己的检查不能完全替代独立 Reviewer。

如果 Superpowers 支持 subagent reviewer：

优先使用独立 reviewer。

---

## 21. Git 纪律

阶段任务完成并验证后：

检查：

`git diff`

`git status`

禁止提交：

- `.env`
- API Key
- token
- 密钥
- `.venv`
- IDE 缓存
- Python cache
- 临时文件

禁止：

- force push
- 擅自 rebase 已发布 main
- 擅自删除历史 commit

项目远程仓库：

https://github.com/fjy1111/zhiyu.git

默认：

main

只有阶段任务完成、测试通过后才允许 push。

---

## 22. 阶段边界

Codex 只完成当前用户明确指定的阶段。

即使：

“下一阶段很自然”

也不得自动继续。

阶段结束：

1. 完成验证
2. Commit
3. Push
4. 输出简短报告
5. STOP

等待外部评审。

---

## 23. 不追求无意义复杂度

每新增一个模块必须回答：

1. 它解决什么新的安全问题？
2. 与已有模块有什么区别？
3. 是否真正提升检测、防御或可解释性？
4. 能否通过实验验证？
5. 是否值得增加复杂度？

如果无法回答：

不要实现。

---

## 24. 当前项目优先级

优先级从高到低：

1. 泛化能力
2. 检测正确性
3. 实验可信度
4. 数据隔离
5. 可解释性
6. 工程稳定性
7. 性能
8. UI 完整度

不得为了页面效果牺牲前面的核心质量。