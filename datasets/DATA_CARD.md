# trusted_provenance Data Card

来源是 `rag-poisoning-detection-trusted-provenance` 的 `test_data`，commit `53d18b99129920db58983a27b7da84f92f11eadf`。数据主要是校园领域，包含明显的人工构造和模板化特征；development 存在较多近重复，原始文本存在 label shortcut。

Phase 1.5 的 Benchmark Adapter 去除了已确认的样本编号、数据集说明、人工字段前缀和临时 marker，同时保留 parsed_text、攻击 payload 和事实文本。Frozen Holdout 不等价于真正独立的第三方盲测；该数据不能单独证明跨领域泛化。

后续必须增加外部 Benchmark，并建设真正 independent blind set。此数据卡不代表任何检测性能结论。
