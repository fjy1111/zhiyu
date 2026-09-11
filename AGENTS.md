# AGENTS.md

# 知御（ZhiYu）项目开发规范

知御目标是构建面向 RAG 知识库的投毒检测与主动防御系统，强调机制级证据、可解释风险裁决、泛化能力、数据泄漏控制、可复现实验和工程完整性。禁止为提高当前 Benchmark 分数牺牲泛化能力。

涉及检测架构、证据设计、LLM 使用或入库/检索阶段职责修改时，必须先阅读 [docs/architecture_principles.md](docs/architecture_principles.md)。该文件保存 Evidence First、证据类型、LLM 使用、长上下文、攻击类型体系，以及 Document-level / Context-level Security 的区别。

本项目由 Codex 实现，Superpowers 负责规划、TDD、审查与验证，ChatGPT 在阶段结束后做外部评审。多步骤开发优先使用 `writing-plans`、`test-driven-development`、`subagent-driven-development`、`requesting-code-review`、`verification-before-completion`。出现 Bug、测试异常或实现与预期不符时使用 `systematic-debugging`，禁止未定位根因就连续打补丁。

非简单代码修改遵循：理解任务 → 计划 → 测试先行 → 最小实现 → Spec Review → Code Quality Review → 集成测试 → Verification → Commit → Push → 停止并等待外部评审。其中 Commit / Push 仅在用户授权的整个阶段结束且 Verification 通过后执行，单个内部 Task 不得自行 push。

## 小任务开发

一次只解决一个明确问题。推荐：Task → test → implementation → review。包含多个独立子系统时必须先拆分，禁止一次实现大量独立模块。

优先：

- 小模块
- 明确接口
- 类型明确
- 确定性行为
- 可测试
- 可消融
- 可复现

避免 God class、巨型函数、隐式全局状态、无约束 dict、Magic constants，以及把数据集特定逻辑混入通用模块。配置放在 `configs/`。

新增模块必须能回答：

1. 解决什么新的安全问题
2. 与已有模块有何区别
3. 是否真正提升检测、防御或可解释性
4. 能否通过实验验证
5. 是否值得增加复杂度

无法回答则不要实现。

优先级：泛化能力 > 检测正确性 > 实验可信度 > 数据隔离 > 可解释性 > 工程稳定性 > 性能 > UI 完整度。不得为了页面效果牺牲前面的核心质量。

## TDD

新行为和 Bug 修复原则上必须 RED → GREEN → REFACTOR：

1. 先写能证明需求的测试
2. 确认测试在旧实现上失败
3. 编写最小实现
4. 确认测试通过
5. 再重构

禁止先写实现，再补只会验证当前写法的弱测试。测试验证需求是否满足，而不是代码是否按当前实现运行。

## Spec Review 与 Code Quality Review

较重要任务完成后至少做：

- Spec Review：是否满足用户需求
- Code Quality Review：逻辑、测试质量、边界、重复、硬编码、泄漏、可维护性

实现者自检不能替代独立 Reviewer。若 Superpowers 支持 subagent reviewer，优先使用。

## Verification before completion

声称 completed、fixed、PASS 或 all tests passed 之前，必须实际运行该任务对应的验证命令并查看真实输出。不能因为“代码看起来正确”就宣布完成。不得只跑标准清单。

阶段结束或准备 commit 前至少检查：

- 对应验证命令（代码任务通常包括 `pytest -q`）
- `git diff`（审查实际补丁，不能用 `--check` 代替）
- `git diff --check`
- `git status`

涉及 raw 数据的阶段结束时，额外运行仓库已有命令：

- `python scripts/raw_integrity.py after`

该命令由 `scripts/raw_integrity.py` 确认：读取 `datasets/manifests/raw_snapshot_before.json`，与当前 `datasets/raw/trusted_provenance` 哈希比较，写入 `datasets/manifests/raw_integrity.json`，不一致则非零退出。不要猜测其他 raw integrity 命令。

## 禁止虚假验收

严禁：

- 硬编码 PASS
- 硬编码 overlap = 0
- 手工修改实验 JSON 结果
- 为报告数字修改输出
- 测试脚本默认相信生成脚本
- 报告声称实现了源码中不存在的功能

Validator 应独立读取最终产物并重新计算。完成报告中的技术结论必须能从当前仓库代码重新运行得到。

实验必须可重复、固定输入 split、保存配置和指标，适合时保存 commit，并区分开发和最终测试。指标包括 Precision、Recall、F1、FPR、ASR、Defense Success Rate、QA Accuracy。任何实验数值必须来自真实运行，不得用示例值冒充。

## 数据与泄漏

`datasets/raw/` 不可修改。严禁修改、删除、重命名 raw 文件，或为测试通过修正 raw 内容。所有转换写入 `datasets/processed/`。

Detector 禁止访问 benchmark ground truth，包括：

- `original_label`
- `label`
- `attack_type` 真值
- `is_poison`
- `expected_answer`
- `facts` 真值
- `source_split`
- 由文件路径泄漏的类别
- Benchmark 私有 metadata

正式 Detector 只能通过 `DetectionInput` 获取输入，禁止把 arbitrary metadata 直接传入 Detector。

## Split 使用纪律

- `development_tune`：可开发、调 Prompt、调通用阈值、调攻击机制规则
- `development_generalization`：只用于阶段性泛化评估，禁止根据单个错误样本新增专门规则
- `stress_set`：evaluation only
- `frozen_holdout`：最终评估前不得调参
- external benchmark：跨数据集、跨领域泛化
- independent blind set：比赛前另行构建

禁止“效果差 → 补领域规则 → 再测试 → 再补规则”。禁止针对测试集、校园领域关键词、人名、学校、具体测试文件、Benchmark 特定句子或实体字段补规则。新规则必须描述通用攻击机制。允许的机制包括 instruction override、role hijacking、hidden instruction、abnormal repetition、retrieval stuffing。不能解释为通用攻击机制则不要加入 Detector。

## Unknown != Poison

必须坚持 `UNKNOWN != POISON`。可信知识库没有证据时，不得仅因缺少证据判定为投毒。系统必须允许 SAFE、REVIEW / UNKNOWN、POISON。事实真实性与攻击风险必须区分。

## 阶段边界与冲突

Codex 只完成用户明确指定的当前阶段。即使下一阶段看起来自然，也不得自动进入。不得在实现完成后自行宣布阶段通过。

如果当前用户任务与 `AGENTS.md` 或数据策略存在无法同时满足的冲突，停止并向用户报告冲突，不得自行猜测或选择其中一方继续。

## Git 与敏感信息

单个内部 Task 完成后不得自行 push。只有当前用户授权的整个阶段完成，且 Verification 全部通过，才允许 commit + push。禁止 force push、擅自 rebase 已发布 main、擅自删除历史 commit。

禁止提交 `.env`、API Key、token、密钥、`.venv`、IDE 缓存、Python cache、临时文件。远程仓库为 `https://github.com/fjy1111/zhiyu.git`，默认分支 `main`。

阶段结束顺序：完成验证 → Commit → Push → 输出简短报告 → STOP，等待外部评审。
