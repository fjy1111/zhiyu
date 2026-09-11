# third_party_blind_set

该目录用于放置第三方盲测样本。

当前目录包含 60 份候选盲测流程验证样本，位于：

```text
documents/
metadata.csv
```

这些样本由当前工程生成，只用于验证“第三方盲测目录、标签登记、评估报告更新”的流程，不能写作真实第三方测试结果。正式提交前如能请老师或同学提供未知样本，应替换或新增到 `documents/`，并在 `metadata.csv` 中登记真实标签。

执行流程见：

```text
docs/第三方盲测执行说明.md
docs/第三方盲测样本征集说明.md
```

发给第三方填写时，建议使用：

```text
third_party_labels_template.csv
```

回收后再复制并改名为：

```text
third_party_labels_filled.csv
```

不要在没有真实第三方标签时提前创建 `third_party_labels_filled.csv`。
