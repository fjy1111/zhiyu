# 《知御 Phase 1.5 Final 完成报告》

本报告只记录本次实际运行输出。未开始 Phase 2，未实现 Detector、Rule、LLM 或 RAG。

## A. T1 Template audit

命令：`.venv/Scripts/python.exe scripts/audit_template_similarity.py`

`audit_template_records()` 调用公共 `build_template_groups()`，参数来自 `configs/benchmark_audit.yaml`（`ngram_size=5`，`near_template_threshold=0.80`）。

实际结果：

- exact_skeleton_overlap_groups: 62
- connected_template_groups: 63
- near_template_pairs: 3087
- cross_split_template_overlap: 42
- template_clusters: 63

扫描文件数：demo_set 30、dev_set 150、stress_set 140、blind_test_set 160、third_party_blind_set 64。

connected 与 exact 不再相等，说明 connected groups 不是 fingerprint 桶的复制。

## B. T2 Group-aware split

命令：`.venv/Scripts/python.exe scripts/build_group_split.py`

输出：`Counter({'development_tune': 123, 'development_generalization': 57})`

- documents: 180
- groups: 23
- 无 group 跨 split
- development_tune 123（68.3%）：normal 57、poison 30、conflict 24、hard_negative 12
- development_generalization 57（31.7%）：normal 24、poison 15、conflict 12、hard_negative 6
- 两个 split 都包含全部四个 label

参数来自 yaml：`tune_target_ratio=0.70`。未按 frozen 数据调参。

## C. T3 Independent validator

命令：`.venv/Scripts/python.exe scripts/validate_group_split.py`

独立读取 tune/gen JSONL，再次调用 `build_template_groups()`，未把 builder 的 group_id 当验证依据。

```
{'documents': 180, 'document_id_overlap': 0, 'exact_text_overlap': 0, 'normalized_exact_overlap': 0, 'exact_template_fingerprint_overlap': 0, 'near_template_pair_overlap': 0, 'connected_template_group_overlap': 0, 'pass': True}
```

`datasets/manifests/development_group_split_validation.json` 与上次内容相同（仍为全 0 / pass true），但本次是重新计算后的结果。

## D. T4 Long document chunk tests

`tests/test_long_document_chunking.py` 从 `configs/chunking.yaml` 读取 chunk_size/overlap，覆盖中文约 2×、英文约 5×、中英混合约 10×、多段落长文本。未修改 Chunker。

## E. pytest

命令：`.venv/Scripts/python.exe -m pytest -q`

```
65 passed in 1.19s
```

0 failed，0 skipped。

## F. Raw integrity

命令：`.venv/Scripts/python.exe scripts/raw_integrity.py after`

```
{"before_files": 641, "after_files": 641, "modified": [], "deleted": [], "added": [], "pass": true}
```

未修改 `datasets/raw/`。

## G. 跨领域泛化结论

**NO。** trusted_provenance 仍主要是校园领域；本次审计 connected-group 跨原始 split overlap 为 42。修复评测基础设施不会创造新的跨域数据。

## H. 未开始 Phase 2

未实现安全 Detector、LLM、RAG、Rule Scanner 或前端。

## Git

commit / push 结果在提交完成后于对话中报告；本文件不填写尚未产生的 commit hash。
