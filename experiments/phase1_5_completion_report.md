# 《知御 Phase 1.5 完成报告》

## A. 实现内容

完成数据集资格审计、Dataset Adapter 双文本模型、DetectionInput 泄漏隔离、标签捷径审计、模板相似性审计、group-aware development split、长文本 Chunk 验证及 Data Card/实验协议。
Adapter 仅移除已确认的人工 benchmark 构造痕迹，保留 payload 和 parsed_text。
未实现任何投毒检测规则、LLM、Evidence Retrieval、RAG、前端或模型训练。

## B. 新增/修改文件

新增：`src/zhiyu/datasets/__init__.py`、`trusted_provenance_adapter.py`、`src/zhiyu/models/detection.py`；
`scripts/build_benchmark_corpus.py`、`audit_label_shortcuts.py`、`audit_template_similarity.py`、
`build_group_split.py`、`validate_group_split.py`；
`datasets/DATA_CARD.md`、`docs/experiment_protocol.md`；
对应 manifests、processed benchmark JSONL 和 5 个新增测试文件。
修改：`README.md`、`.gitignore`、`scripts/inspect_dataset.py`及 Phase 1 配置/包文件。
删除：已确认的 IDE `.idea` 文件和旧顶层空包占位目录。
未修改 raw 文件；未新增模型或安全检测实现。

## C. Raw integrity

before 641，after 641；modified 0、deleted 0、added 0、renamed 0；PASS。
见 `datasets/manifests/raw_integrity.json`。

## D. Benchmark transformation 统计

documents_total 180，changed 180，unchanged 0；sample_id_removed 180，
dataset_note_removed 162，hidden_prefix_removed 9，temporary_marker_removed 66，
other transformations []。每条记录保留 transformations，输出见 `trusted_provenance_transform_audit.json`。

## E. Raw label shortcut 结果

仅分析 development 的 parsed_text，标签分布为 normal 81、poison 45、conflict 36、hard_negative 18。
脚本输出各标签高频 token、固定行模板和字段前缀统计；未访问 frozen/evaluation 标签。

## F. Benchmark label shortcut 结果

仅分析 development 的 benchmark_text，使用同一确定性 token 审计；Adapter 去除上述人工编号、说明行、隐藏字段名和临时 marker，未删除 payload 或事实。

## G. 去捷径前后对比

去除前：所有 180 篇含 benchmark 构造编号，162 篇含已确认说明行，9 篇含隐藏字段前缀，66 篇含临时 marker。
去除后：这些模式分别为 0；攻击正文和事实仍保留。未擅自加入其他 marker，`other_transformations` 为空。
详细结果见 `label_shortcut_audit_raw.json`、`label_shortcut_audit_benchmark.json` 和 `label_shortcut_audit.md`。

## H. Template similarity

对 demo、dev、stress、blind、third_party_blind_set 共 574 个可解析文档建立确定性 skeleton。
exact skeleton overlap groups 62；以路径、SHA256、cluster 信息输出，未输出冻结正文、标签或事实。

## I. Cross-split template overlap

cross-split template overlap 42 组。该结果说明多个 split 共享模板，不能将现有 frozen holdout 视为跨域独立证明。未用该结果删除样本或编写规则。

## J. development_tune

134 documents。标签分布：normal 54、poison 41、conflict 24、hard_negative 15。

## K. development_generalization

46 documents。标签分布：normal 27、poison 4、conflict 12、hard_negative 3。与 tune 共享 template group：0；比例约 74.4%/25.6%，未强行追求标签比例。

## L. Group isolation 验证

`validate_group_split.py` 通过：template group overlap 0、exact text overlap 0、normalized exact overlap 0。
tune/generalization 的 benchmark documents/chunks 已分别生成，Chunk 基于 benchmark_text 的新 offset。

## M. Long-document Chunk 验证

新增中英混合、多段落约 13,600 字符 fixture；产生多个 Chunk，offset、切片相等、非空、确定性和 200 字符 overlap 均通过测试。
既有 Chunk 配置为 1200/200，段落边界优先。

## N. pytest

46 passed，0 failed，0 skipped。实际运行 build_development_corpus、build_benchmark_corpus、
audit_label_shortcuts、audit_template_similarity、build_group_split、validate_group_split、
raw_integrity.py after 和 pytest -q 均成功。

## O. 当前数据是否足以证明跨领域泛化？

**NO。** 数据主要来自校园领域，存在人工标签捷径、模板化和 42 组跨 split skeleton 重叠；
现有 frozen holdout 也不是独立第三方盲测。需要外部 benchmark 和真正 independent blind set。

## P. 当前已知问题

Python 3.13.5 / Windows 已验证，Python 3.10 未实测；无 OCR、资源沙箱或系统 ACL。
skeleton 是无训练的正则化审计工具，不是语义等价判断。当前 tune/generalization 切分按严格 skeleton，
对未完全相同但高度相似的模板仍可能保守不足。开发 metadata 中 facts 仍保存在离线记录中，
未来 Detector 必须只接收 DetectionInput。未对 frozen/evaluation 计算近重复特征。

## Q. 阶段声明

**未开始 Phase 2。**

## Git

- branch: main
- commit: 待本报告提交后填写
- remote: https://github.com/fjy1111/zhiyu.git
- push status: 待执行
- final git status: 待执行
