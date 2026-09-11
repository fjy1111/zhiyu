# 知御 Phase 1 完成报告

## A. 本阶段实现了什么

完成数据策略、raw 基线与终态 SHA256 比较、通用 DocumentRecord/ChunkRecord、
TXT/MD/HTML/PDF/DOCX 统一解析、确定性分块、开发语料构建、多格式实测、泄漏审计与 pytest。
parser 不依赖领域字段。原始标签仅保留为 original_label，attack_type 为 null。
无检测算法、LLM、RAG、向量库、前端或 FastAPI 实现。

## B. 新增/修改文件列表

修改：README.md、.gitignore、scripts/inspect_dataset.py（扫描错误时非零退出）。
新增源代码、配置、测试和生成产物完整列于 C；其中 scripts/inspect_dataset.py 和
datasets/manifests/trusted_provenance_inventory.json 为已存在文件，其余列出的 Phase 1 功能文件均为新增。
新增本报告 experiments/phase1_completion_report.md。
新增安装环境 .venv、安装元信息 src/zhiyu.egg-info、测试缓存，均已忽略。

删除：.idea/.gitignore、misc.xml、modules.xml、workspace.xml、zhiyu.iml、
inspectionProfiles/profiles_settings.xml、inspectionProfiles/Project_Default.xml。
删除旧 src/{parser,detector,evidence,judge,decision,retrieval_guard,rag}/.gitkeep 及对应空目录。
这些是 IDE 配置和初始化占位，未删除用户源代码；没有保留 IDE 配置备份，IDE 可重建配置。

## C. 最终目录树

省略 .venv、缓存、egg-info、原始 639 个文件及原有 .gitkeep；raw 内部目录完整保留。

```text
zhiyu/
├── README.md
├── .gitignore
├── pyproject.toml
├── configs/
│   ├── dataset_policy.yaml
│   └── chunking.yaml
├── src/zhiyu/
│   ├── __init__.py
│   ├── dataset.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── document.py
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── text_parser.py
│   │   ├── markdown_parser.py
│   │   ├── html_parser.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── document_parser.py
│   │   └── chunker.py
│   ├── detector/__init__.py
│   ├── evidence/__init__.py
│   ├── judge/__init__.py
│   ├── decision/__init__.py
│   ├── retrieval_guard/__init__.py
│   └── rag/__init__.py
├── scripts/
│   ├── _common.py
│   ├── inspect_dataset.py
│   ├── raw_integrity.py
│   ├── build_development_corpus.py
│   ├── run_parser_validation.py
│   └── audit_dataset_splits.py
├── tests/
│   ├── conftest.py
│   ├── test_document_models.py
│   ├── test_text_parser.py
│   ├── test_markdown_parser.py
│   ├── test_html_parser.py
│   ├── test_pdf_parser.py
│   ├── test_docx_parser.py
│   ├── test_document_parser.py
│   ├── test_chunker.py
│   ├── test_dataset_policy.py
│   ├── test_raw_integrity.py
│   └── test_phase1_artifacts.py
├── datasets/
│   ├── raw/trusted_provenance/
│   │   ├── demo_set/
│   │   ├── dev_set/
│   │   ├── stress_set/
│   │   ├── blind_test_set/
│   │   ├── file_format_test/
│   │   ├── metadata/
│   │   ├── qa_set/
│   │   ├── third_party_blind_set/
│   │   ├── third_party_blind_process_validation_set/
│   │   ├── SOURCE.md
│   │   └── SOURCE_LICENSE
│   ├── processed/trusted_provenance/
│   │   ├── development_documents.jsonl
│   │   └── development_chunks.jsonl
│   ├── manifests/
│   │   ├── trusted_provenance_inventory.json
│   │   ├── raw_snapshot_before.json
│   │   ├── raw_snapshot_after.json
│   │   ├── raw_integrity.json
│   │   ├── development_corpus_summary.json
│   │   ├── parser_validation.json
│   │   ├── split_leakage_audit.json
│   │   └── split_leakage_audit.md
│   ├── blind/
│   └── self_generated/
├── experiments/phase1_completion_report.md
├── backend/
└── frontend/
```

## D. 使用的第三方依赖

直接运行依赖实际版本：pypdf 6.18.0、python-docx 1.2.0、beautifulsoup4 4.15.0、PyYAML 6.0.3。
测试依赖 pytest 9.1.1；构建依赖 setuptools。
间接依赖包括 lxml、soupsieve、typing-extensions，以及 pytest 的 colorama、iniconfig、packaging、pluggy、pygments。
Python 3.13.5 / Windows 实测，pyproject 声明 Python >=3.10。pip check 通过。

## E. Development corpus

180 documents，180 chunks；demo_set 30、dev_set 150。
原始标签分布：normal 81、poison 45、conflict 36、hard_negative 18。
无 evaluation/frozen 文档进入开发语料。测试监控文件读取，确认构建未打开这些 split 或聚合 metadata。
当前文档较短，默认配置下均只产生一个 Chunk；多窗口 overlap 由单元测试覆盖。

## F. Parser Validation

| 格式 | 成功 | 失败 |
|---|---:|---:|
| TXT | 1 | 0 |
| DOCX | 6 | 0 |
| HTML | 10 | 0 |
| MD | 10 | 0 |
| PDF | 6 | 0 |
| 合计 | 33 | 0 |

warnings：0；empty_text：0。
实际格式测试覆盖 file_format_test/documents 全部 32 个文件，加 demo_set 一个 TXT。
另有独立空白 PDF 测试确认无文本时发出 NO_EXTRACTABLE_TEXT、不进行 OCR；
DOCX 表格提取及 HTML script/style 去除、禁止联网行为均有测试。

## G. 数据泄漏审计

原始 SHA256 重复：31 组，涉及 81 文件，71 对。
标准化文本 SHA256 重复：34 组，74 对。
跨 split 原始重复：0 对；跨 split 标准化重复：0 对；
development 对 evaluation/frozen 标准化重复：0 对。
development 内原始重复和标准化重复均为 0 对。
统计“对”为组内两两组合，不能与重复组数混用。

审计覆盖 7 个 split，共 633 文件：demo 30、dev 150、stress 140、blind 160、
third_party_blind_set 64、third_party_blind_process_validation_set 57、format_test 32。
metadata 5 文件和 qa_set 1 文件不属于这 7 个 split，不读取其标签/事实；raw 完整性检查仍覆盖它们。
非文档 JSON/CSV 仅计算原始哈希，标准化哈希为 null；空正文不计入标准化重复。

近重复：仅 demo/dev，以字符 5-gram Jaccard >=0.8 得到 369 对，存在开发语料模板相似风险。
未对 evaluation/frozen 计算近重复特征，因此不能判断其模板独立性。
报告只保存相对路径、哈希、相似度、统计，不输出冻结正文或额外标签/事实字段。
路径保留源文件命名，包括源目录名；未由路径推断攻击类型。没有删除或修正重复文件。

## H. Raw Integrity

before 文件数 641，after 文件数 641。
modified 0，deleted 0，added 0，重命名 0。最终 PASS。
快照包含 639 原始数据文件及来源说明、许可证；相对路径到 SHA256 的完整映射前后相等。
原始数据内容、名称、标签、目录归属均未修改。

## I. pytest

40 passed，0 failed，0 skipped。实际执行：
inspect_dataset.py、build_development_corpus.py、run_parser_validation.py、audit_dataset_splits.py、
raw_integrity.py after、python -m pytest -q，均成功；运行解释器为项目 .venv/Scripts/python。

## J. 当前已知问题

- 未在 Python 3.10 上实测，依赖为版本范围，未生成锁文件。
- HTML 静态文本提取不模拟 CSS 可见性；DOCX 当前聚焦正文段落和表格，不承诺页眉、文本框等全部对象。
- 无 OCR；非 UTF-8 字节采用替换和警告，可能丢失字符，不自动猜测编码。
- 未实现资源限制/隔离进程，不能据此宣称可安全处理任意超大或恶意压缩文档。
- raw 为代码/流程层只读，未配置系统 ACL；通用 parser 本身不绑定数据策略，数据集入口由 DatasetPolicy 管控。
- 全空白窗口被跳过时，两侧输出 Chunk 不承诺固定 overlap；offset 和非空正文覆盖仍正确。
- 冻结/评估近重复未分析；完全重复为零不足以证明泛化能力或数据独立性。
- 开发元数据中的 facts 保留在通用 metadata；后续检测输入需明确排除真值字段，避免特权信息泄漏。
- 测试中的实际产物验证需要先执行构建、验证、审计脚本，README 已按此顺序列出。

## K. Phase 2 前建议评审者重点检查

检查 DatasetPolicy 的白名单和元数据读取边界、是否需要更强访问隔离；
检查规范化与 Chunk offset 的语义、空白窗口及段落边界行为；
检查文档解析的资源限制及格式覆盖边界；
检查原始标签保留策略与 facts 等真值字段是否会进入未来检测流程；
重点评审开发集 369 对近重复与后续独立评估方案，不以零跨 split 完全重复推断泛化能力。
复核 raw 快照相等及三份实验产物与测试结果。

## L. 阶段声明

未开始 Phase 2。代码与实验已停止在 Phase 1，等待另一个评审者审查。

