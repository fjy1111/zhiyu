# 《知御 Phase 1.5R 完成报告》

1. 已修复原 Phase 1.5 的 label shortcut 审计、固定行模板/字段前缀空结果、hard_negative 说明未移除、三套 template fingerprint 不统一、仅 exact hash 分组、group split 验证硬编码和 DetectionInput 可接收任意 runtime 字典等问题。

2. hard_negative 人工说明“这是同学整理摘要……”已从 benchmark_text 消失；新增 `REMOVE_HARD_NEGATIVE_DATASET_NOTE`，转换只依赖文本，不读取 original_label。parsed_text 保持不变，事实文本保留。

3. Raw/Benchmark 最强 shortcut：Raw 中样本编号覆盖 180/180，已确认数据集说明 162/180，隐藏字段前缀 9 次，临时 marker 66 次；Benchmark 中上述人工模式为 0。标签高频、集中和 exclusive token、固定行模板、字段前缀统计见两个 JSON 审计文件；普通跨标签词没有被标为 exclusive。

4. 统一 `src/zhiyu/datasets/template_similarity.py`，统一规范化 sample ID、URL、email、日期、时间、电话、连续数字和空白。exact template groups：62。

5. development n=5 字符 n-gram、阈值 0.80，使用 connected components 合并 near-template pairs；审计共 369 对近模板关系，connected template groups 的分组由同一模块生成。

6. 重新分组为 development_tune 129、development_generalization 51。标签分布：tune normal 54、poison 40、conflict 22、hard_negative 13；generalization normal 27、poison 5、conflict 14、hard_negative 5。分组未拆分，比例约 71.7/28.3。

7. Validator 独立读取 `benchmark_tune_documents.jsonl` 和 `benchmark_generalization_documents.jsonl`，重新计算 document_id、exact benchmark_text、normalized text、exact fingerprint、near-template pair、connected group 六项 overlap，不信任构建 manifest。结果全部 0，PASS。

8. DetectionInput 现在只接受强类型 RuntimeContext（request_id、file_format），任意 dict 及包含 original_label、facts、expected_answer、attack_type、is_poison、metadata 的 runtime 均被 TypeError 拒绝；负面测试通过。

9. 长文测试覆盖中英混合多段文本，产生多个 Chunk，offset、source slice、非空、确定性和 overlap 通过；既有 fixture 与新增测试共 52 项。

10. Raw integrity：before/after 均 641；modified 0、deleted 0、added 0、renamed 0，PASS。

11. pytest：52 passed、0 failed、0 skipped。已实际运行 build_development_corpus、build_benchmark_corpus、audit_label_shortcuts、audit_template_similarity、build_group_split、validate_group_split、raw_integrity.py after、pytest -q。

12. trusted_provenance 是否足以证明跨领域泛化：**NO**。数据主要是校园领域，仍有明显模板化和跨 split template overlap；修复隔离机制不等于新增跨域数据。仍需外部 Benchmark 和真正 independent blind set。

13. 当前已知问题：近模板审计是确定性字符相似度，不是语义等价判断；冻结数据仍只输出审计所需路径、hash、cluster 和统计，不做近模板特征泄露到报告；Python 3.13.5 / Windows 已测，3.10 未实测；无 OCR、资源沙箱和系统 ACL。

14. **未开始 Phase 2。**

## Git

- branch: main
- commit: 待提交后填写
- remote: https://github.com/fjy1111/zhiyu.git
- push status: 待执行
- final git status: 待执行
