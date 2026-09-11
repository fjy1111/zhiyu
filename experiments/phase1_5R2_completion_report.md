# 《知御 Phase 1.5R2 完成报告》

## A. label shortcut 新算法

`audit_label_shortcuts.py` 仅读取 development。token 按文档去重，统计各 label document count、其他 label document count、总覆盖和 concentration；`label_exclusive_tokens` 只包含只在一个 label 出现的 token。固定行先 trim/压缩空白，字段前缀取冒号前文本，同样统计 label counts、total documents 和 concentration。

## B. Raw 与 Benchmark 统计

| 输入 | high-frequency | concentrated (>=0.8) | exclusive | fixed-line | field-prefix |
|---|---:|---:|---:|---:|---:|
| parsed raw | 100 | 209 | 209 | 255 | 15 |
| benchmark | 100 | 17 | 17 | 61 | 12 |

普通跨标签词没有被标为 exclusive。完整 token、line、prefix 统计在 `label_shortcut_audit_raw.json` 和 `label_shortcut_audit_benchmark.json`。

## C–F. Template 结果

统一公共 API 位于 `src/zhiyu/datasets/template_similarity.py`，提供 normalize_template、template_fingerprint、character_ngrams、jaccard_similarity 和 build_template_groups。配置位于 `configs/benchmark_audit.yaml`（n=5、threshold=0.80、目标 0.70）。

实际审计：exact template groups 62；near-template pairs 3087；connected template groups 62。每个 connected group 由 union-find 按 near-template 边生成并输出 cluster_id/paths；冻结/评估报告没有正文、事实或标签。

cross-original-split connected-group overlap 为 42 组，说明各原始 split 存在共享模板，不能视为跨域独立数据。

## G–H. Group-aware stratification

`build_group_split.py` 调用公共 `build_template_groups()`，先建立 connected groups，再用确定性 greedy objective 将完整 group 放入 tune 或 generalization：目标是先保持 group isolation，再降低 generalization 各 label 覆盖缺口、比例偏差和总体尺寸偏差；不得拆 group。结果 tune 129、generalization 51，约 71.7%/28.3%。

标签分布：tune 为 normal 54、poison 40、conflict 22、hard_negative 13；generalization 为 normal 27、poison 5、conflict 14、hard_negative 5。

## I–J. 独立 Validator

Validator 独立读取 `benchmark_tune_documents.jsonl` 与 `benchmark_generalization_documents.jsonl`，合并后再次调用公共 `build_template_groups()`，并重新计算 document_id、exact text、normalized text、exact fingerprint、near-template pair、connected component overlap。结果分别为 0、0、0、0、0、0，PASS；没有读取构建脚本的分组结果作为验证依据。

## K. Long document tests

中英混合、多段落长文测试覆盖约 2×、5×、10× chunk_size 的规模要求，验证 chunk 数、offset、source slice equality、非空、确定性及 paragraph-boundary 下的真实 overlap 契约，均通过。

## L. DetectionInput regression tests

`DetectionInput` 只接受强类型 `RuntimeContext`，任意 dict 以及包含 original_label、facts、expected_answer、attack_type、is_poison、metadata 的 runtime 均拒绝。负面泄漏测试通过。

## M. Raw integrity

before/after 均 641 个文件；modified 0、deleted 0、added 0、renamed 0，PASS。raw 样本内容、名称和目录归属未修改。

## N. pytest

55 passed，0 failed，0 skipped。所有要求脚本均已实际运行成功。

## O. 跨领域泛化结论

**NO**。trusted_provenance 仍主要是校园领域，存在人工标签捷径、模板化和 42 组跨原始 split 模板重叠；修复分组和审计不会创造新的跨域数据。需要外部 Benchmark 和真正 independent blind set。

## P. 未开始 Phase 2

明确未开始 Phase 2，未实现安全 Detector、LLM、RAG、Rule Scanner 或前端。

## Git

commit 和 push 信息在提交完成后通过聊天报告；报告不写入本次 commit 的自身 hash。
