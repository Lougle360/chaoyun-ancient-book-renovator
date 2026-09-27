# 超云古书翻新skill

把扫描版古书 PDF 翻新成现代人可以直接阅读的高质量 Markdown 与正式 PDF。

它不是简单的 OCR 工具，而是一套面向复杂古书的完整出版工作流：先保存原书证据，再恢复文字与版面，随后完成繁简转换、古文或日文今译、普通读者编辑、术语解释、质量审计和正式出版。

## 适合处理什么

- 扫描版、影印版和图片型 PDF
- 繁体中文、文言文、日文、汉文训读或多语言混排
- 竖排、多栏、夹注、眉批、图版、表格等复杂版式
- 需要转换成现代白话文、但又不能丢失原文依据的古书
- 需要封面、版权页、跳转目录、PDF 书签和正式书名的出版型成品

普通的数字版 PDF 如果只需要提取文字，不必使用这套重型流程。

## 最终产物

标准工作空间会保留两层内容：

1. **证据层**：原 PDF、页面图像、忠实转录、版面位置、置信度、疑难记录和来源追踪。
2. **阅读层**：现代标点、简体规范、现代白话文、编者导读、章节说明、图解、术语表、Markdown 和正式 PDF。

当目标是“普通人可以直接阅读”时，默认生成现代白话读者版，并要求：

- 原 PDF 每一页都有明确去向，不以样章冒充全书；
- 专业术语首次出现时解释，书末保留完整术语表；
- 古代风水、医学、术数或吉凶判断使用“书中认为”“传统上认为”等历史归属表达；
- 正式 PDF 包含封面、版权页、作者与整理者、出品方、可点击目录和 PDF 书签；
- 成品使用 `<原书名>·<版本名>.pdf`，只保留一个明确的正式交付文件。

## Skill 结构

```text
chaoyun-ancient-book-renovator
└─ skills/
   ├─ chaoyun-ancient-book-renovator   # 总控与质量门
   ├─ chaoyun-pdf-diagnoser            # PDF 诊断和页面路由
   ├─ chaoyun-source-reconstructor      # 原书重建与证据记录
   ├─ chaoyun-uncertainty-adjudicator   # 疑点归并、裁决和读者影响分级
   ├─ chaoyun-text-normalizer           # 繁简、异体字、标点与分段
   ├─ chaoyun-classical-modernizer      # 文言文、日文到现代中文
   ├─ chaoyun-reading-editor            # 普通读者版编辑
   └─ chaoyun-quality-publisher         # 独立审计与正式出版
```

主调用名：

```text
$chaoyun-ancient-book-renovator
```

## 安装

将仓库中的八个 Skill 目录复制到 Codex Skill 目录：

```powershell
git clone https://github.com/Lougle360/chaoyun-ancient-book-renovator.git
cd chaoyun-ancient-book-renovator

$target = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Recurse -Force ".\skills\chaoyun-*" $target
```

重新打开 Codex 后即可发现这些 Skill。

## 使用方法

在 Codex 中提供古书 PDF，并调用：

```text
使用 $chaoyun-ancient-book-renovator，把这本古书翻新成普通人可以直接阅读的现代白话版。
保留原图和术语解释，生成 Markdown 与正式 PDF。
```

建议在任务开始时说明：

- 目标读者，例如风水爱好者、普通大众或研究人员；
- 需要现代白话版、原文对照版还是证据档案版；
- 是否保留原图、批注和异体字；
- 作者、整理者、出品方和版本名称；
- 是否授权使用付费 OCR、视觉模型或语言模型。

## 工作流程

```text
锁定原 PDF 与页数
        ↓
诊断语言、版式和页面类型
        ↓
逐页重建原文与图像证据
        ↓
归并并裁决识读疑点
        ↓
繁简、异体字、标点和结构规范
        ↓
文言文/日文转换为现代中文
        ↓
普通读者编辑、导读、图解和术语表
        ↓
再次裁决翻译与编辑疑点
        ↓
独立语义审计与结构审计
        ↓
正式 Markdown 和可阅读 PDF
```

## 质量等级

- **A — 可正式出版**：所有质量门通过，没有高风险疑难。
- **B — 可直接阅读，保留台账**：存在范围明确、不会破坏整体阅读的疑难项。
- **C — 辅助草稿**：仍有重要版式、识别或翻译风险，不得标成完整版。
- **D — 无法可靠恢复**：现有证据不足以负责任地完成转换。

样章只能验证技术路线，不能证明全书已经完成。扫描型古书达到 A/B 级前，必须完成逐页视觉证据覆盖或为每个无法处理的页面记录明确原因。

## 工作空间示例

```text
book-workspace/
├─ book.json
├─ run-state.json
├─ 00-intake/
├─ 10-diagnosis/
├─ 20-source/
├─ 30-normalized/
├─ 40-modernized/
├─ 50-edited/
├─ 60-publication/
│  ├─ modern-reading.md
│  └─ 原书名·现代白话版.pdf
└─ 90-audit/
   ├─ events.jsonl
   ├─ uncertainty-candidates.jsonl
   ├─ uncertainty-adjudication.jsonl
   ├─ uncertain-items.jsonl
   ├─ quality-report.json
   └─ quality-report.md
```

## 验证

总控 Skill 自带工作空间校验和自测：

```powershell
python .\skills\chaoyun-ancient-book-renovator\scripts\self_test.py
python .\skills\chaoyun-ancient-book-renovator\scripts\validate_workspace.py <book-workspace> --stage publication
python .\skills\chaoyun-uncertainty-adjudicator\scripts\project_open_items.py <book-workspace> --check
python .\skills\chaoyun-quality-publisher\scripts\audit_publication.py <book-workspace>
```

发布审计会检查正式 PDF、Markdown 资源、源页面覆盖、PDF 页数、目录链接、书签和质量报告。

## 设计原则

- 不用流畅改写覆盖原始证据。
- 不根据上下文虚构缺失文字。
- 不把技术检查通过等同于语义正确。
- 不把模型提出的每一条疑问都当成正文缺损；候选、裁决历史和读者可见未决项必须分开。
- 不把样章、局部结果或 C 级草稿标为完整版。
- 付费全书处理前先估算成本并取得明确授权。
- 所有现代化内容都应能追溯到稳定的原书页面和内容块。

## 环境

- Python 3.10+
- `pypdf`
- 生成正式 PDF 时通常还需要 `reportlab`、CJK 字体以及可用的 PDF 渲染工具
- OCR、视觉模型和语言模型由实际任务环境决定，密钥不得写入仓库或书籍产物
