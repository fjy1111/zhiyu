# 知御架构原则

涉及检测架构、证据设计、LLM 使用或入库/检索阶段职责修改时，必须先阅读本文件。本文件保存项目架构设计，不替代 `AGENTS.md` 中的 Agent 开发纪律。

## Evidence First, Judgment Second

知御核心设计原则：先产生证据，再进行判断。不同攻击可以使用不同证据。LLM 不应凭空创造安全证据。

### 行为型攻击

例如 Prompt Injection、Hidden Instruction。

证据：

- 原文 suspicious span
- instruction intent
- rule event

### 事实型攻击

例如 Fact Tampering、Knowledge Conflict。

证据：

- Claim
- Trusted Evidence
- entailment / contradiction

### 检索操纵型

例如 Retrieval Hijacking。

证据：

- repetition statistics
- keyword density
- retrieval-related features

## LLM 使用原则

LLM 应主要负责：

- 语义分析
- Claim 提取
- Intent 分析
- Evidence-based Judgment
- Attack Attribution
- Explanation

禁止让 LLM 仅凭自身记忆决定外部事实真假。

事实型判断应允许：

- SUPPORTED
- CONTRADICTORY
- INSUFFICIENT_EVIDENCE

证据不足时允许拒判。

## 长上下文原则

禁止默认把完整大文件和大量知识库内容一次性发送给 LLM。

优先：

Document → Chunk → Candidate Analysis → Claim → Top-K Evidence → Judge → Structured Aggregation

文件级最终风险优先由结构化结果聚合。

## 当前安全攻击体系

当前计划支持的主要机制：

- PROMPT_INJECTION
- HIDDEN_INSTRUCTION
- FACT_TAMPERING
- KNOWLEDGE_CONFLICT
- RETRIEVAL_HIJACKING

不得仅为了增加项目规模自行添加大量类别。新增攻击类型必须先经过用户确认。

## Document-level / Context-level Security

入库阶段关注 Document-level Security。未来检索阶段关注 Context-level Security。

禁止简单地在入库阶段跑 Rule + LLM，然后在 Retriever 后再原样跑一次 Rule + LLM。

检索阶段如果实现，必须解决不同问题，例如：

- 多 Chunk 冲突
- Query-conditioned context integrity
- context dominance
- context inconsistency
