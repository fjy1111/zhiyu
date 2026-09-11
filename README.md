# 知御（ZhiYu）

面向 RAG 知识库的投毒检测与主动防御系统。

当前阶段：Phase 1，数据治理、统一文档模型与多格式解析基础设施。
当前 Phase 1 尚未实现任何投毒检测能力。阶段完成后停止并等待评审，未经明确要求不进入 Phase 2。

`datasets/raw/trusted_provenance/` 中保留的原始 `test_data/` 内容来自 GitHub 仓库 [rag-poisoning-detection-trusted-provenance](https://github.com/rodriguezrobertbfrkx6857-sudo/rag-poisoning-detection-trusted-provenance.git)。这些文件当前仅作为知御的外部研究/实验数据来源，并按原始目录层级只读保存。

后续项目核心检测方法由知御独立实现；本项目不将参考仓库的系统实现、`backend/` 或 `frontend/` 作为代码基础。

来源 commit：`53d18b99129920db58983a27b7da84f92f11eadf`，下载日期 2026-09-11，MIT License。
639 个原始数据文件保持原始层级，另有 SOURCE.md 和 SOURCE_LICENSE。

## 当前目录结构

```text
zhiyu/
├── pyproject.toml
├── configs/{dataset_policy.yaml,chunking.yaml}
├── src/zhiyu/
│   ├── models/document.py
│   ├── parser/
│   │   ├── base.py
│   │   ├── text_parser.py
│   │   ├── markdown_parser.py
│   │   ├── html_parser.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── document_parser.py
│   │   └── chunker.py
│   ├── dataset.py
│   └── detector/, evidence/, judge/, decision/, retrieval_guard/, rag/（仅占位）
├── datasets/
│   ├── raw/trusted_provenance/
│   ├── processed/trusted_provenance/
│   ├── manifests/
│   ├── self_generated/
│   └── blind/
├── scripts/
│   ├── inspect_dataset.py
│   ├── raw_integrity.py
│   ├── build_development_corpus.py
│   ├── run_parser_validation.py
│   ├── audit_dataset_splits.py
│   └── _common.py
├── tests/
└── backend/, frontend/, experiments/（占位）
```

## Dataset Policy

策略位于 `configs/dataset_policy.yaml`。代码同时校验固定白名单，配置扩大范围会报错。

| 用途 | Split |
|---|---|
| development | demo_set、dev_set |
| evaluation_only | stress_set |
| frozen_holdout | blind_test_set、third_party_blind_set、third_party_blind_process_validation_set |
| format_test | file_format_test |

原始名称保留，但留出数据标签已存在于仓库，因此称为 Frozen Holdout / 冻结留出集，
不称为真正独立的第三方盲测；真正独立盲测以后另行建设。
开发构建只读取 demo/dev 及各自 metadata JSON，不读取 all_metadata.json 或 blind_test_set_metadata.json。
原始 label 保存为 `metadata.original_label`，`metadata.attack_type` 为 null，不转换为 SAFE/POISON 或攻击分类。
其他原始辅助字段（包括 facts）保留在通用 metadata 中，parser 不依赖任何领域字段。

冻结/评估数据只用于文件计数、原始哈希、完整性检查。
泄漏审计按本阶段特别授权，临时提取标准化文本计算 SHA256，不输出正文、事实或独立标签字段；
JSON/CSV 不解析语义，只计算原始哈希。审计仅输出路径、哈希、相似度和统计。
近重复仅分析 demo/dev，使用字符 5-gram Jaccard，阈值 0.8；不据此调参或删除数据。
跨 split 完全重复为零不代表不存在模板泄漏，冻结/评估集近重复尚未评估。

## Parser 和 Chunk

统一调用：`from zhiyu.parser.document_parser import DocumentParser`，然后 `DocumentParser().parse(local_path)`。
支持 TXT、MD、HTML、PDF、DOCX；未知格式抛出 UnsupportedFormatError，损坏内容抛出 ParseError。
TXT/MD 支持 UTF-8 BOM，非法字节替换并警告，不猜测其他编码。Markdown 保留正文语法。
HTML 去除 script/style/head/template，不执行脚本、不加载资源，不模拟 CSS 布局。
PDF 按页提取文本，无文字时返回 NO_EXTRACTABLE_TEXT，不做 OCR。
DOCX 按正文顺序提取段落及表格（包括嵌套表格），不执行宏或外部链接。

规范化只统一换行、将连续三个以上换行压缩为两个、去除首尾空白。
Document ID 基于来源、split、相对路径及原始 SHA256。
Chunk offset 为标准化 document.text 的 Python Unicode 字符下标，end_char 为右开边界。
Chunk 文本严格等于 document.text[start_char:end_char]。
配置见 `configs/chunking.yaml`（1200 字符窗口、200 字符重叠、优先段落边界）。
纯空白窗口不输出，被跳过窗口两侧不承诺固定重叠。Chunk ID 基于文档 ID、下标、offset 和配置，无随机数。

## 安装和运行

声明兼容 Python 3.10+，当前实际验证环境为 Python 3.13.5 / Windows。
在项目根目录运行（PowerShell）：

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test]"
.venv/Scripts/python scripts/inspect_dataset.py
.venv/Scripts/python scripts/build_development_corpus.py
.venv/Scripts/python scripts/run_parser_validation.py
.venv/Scripts/python scripts/audit_dataset_splits.py
.venv/Scripts/python scripts/raw_integrity.py after
.venv/Scripts/python -m pytest -q
```

开发语料输出：

- `datasets/processed/trusted_provenance/development_documents.jsonl`
- `datasets/processed/trusted_provenance/development_chunks.jsonl`

验证与审计输出：

- `datasets/manifests/parser_validation.json`
- `datasets/manifests/split_leakage_audit.json`、`split_leakage_audit.md`
- `datasets/manifests/raw_snapshot_before.json`、`raw_snapshot_after.json`、`raw_integrity.json`

基线已在 Phase 1 开始时生成，脚本拒绝覆盖已有 before 快照。
after 比较相对路径与逐文件哈希，不同则非零退出；重命名体现为删除和新增。
所有标准化语料只写入 processed。raw 只读约束由代码和流程执行，尚未设置操作系统 ACL 或文档资源沙箱。
