# ZhiYu Experiment Protocol

`development_tune` 可用于调整通用攻击机制规则、Prompt 和阈值；`development_generalization` 仅阶段性评估，禁止根据单个错误案例补规则；`stress_set` 为 evaluation only；Frozen Holdout 在最终评估前不调参；external benchmark 用于跨数据集泛化，independent blind 用于比赛最终测试。

新增规则必须描述攻击机制，不得针对校园词汇、单一 entity、单个文档、测试句子或 benchmark 文件名。Phase 1.5 不实现任何检测规则。
