# G3.5 原版式简体校订 PDF 审核

## 版本与时机

这是文字规范化之后的独立中间版本，名称为“原版式简体校订版”。保留原书版式与内容关系，一般说明文字使用校订后的简体字；固定原文和构形字迹按[保护范围](text-image-and-rare-glyph-policy.md)保留原形。它不承担白话翻译。原扫描、原始 OCR、校订稿、现代白话读者版分别保留。

用户要求还原原版式，或处理复杂竖排／图文混排中文扫描件时，总控必须启用本关卡。先选覆盖复杂页型的代表页，在批量套用方法之前审核；若交付的是整份原版式校订 PDF，则逐页审核该交付范围。普通纯文本提取及无此需求的旧工作空间不自动迁移。日本语材料先做语言分流，不套用中文繁简转换。

在 `book.json` 登记 `layout_proof_review`，含 `required: true` 与当前版本 `record` 路径。不得通过删除此配置绕过已要求的审核。此为 workflow 1.10 的专项审核扩展，不自动修改既有阶段的通过状态。

## 交付与实际审查

- 将带版本号的 PDF 放在 `60-publication/supplements/`。比较页左侧为原扫描、右侧为校订稿，保持可比比例与清晰页码；可附独立校订页。不要把不同裁切或缩放造成的视觉差别误报为排版差别。
- 逐页建立原页—源块—PDF 页对应。正文、图题、页眉、版心、小注、图旁文字均须核对；遗漏、重复、错列、断句或跨页错接均应退回。
- 逐幅登记图片，包括同一个源块内的子图。核对位置、大小比例、方向、边界、相互关系及内容，不能只核对图片文件数量。阴阳符号、黑白点数、卦爻、方位、连线分别复核。AI 重绘须标明其性质，不替换底本证据，也不能因更精美而获得忠实性通过。
- 文本按原列序、区域边界、行列间距复位。同一语义区域统一字体与字号，小注可使用另一组统一字号。禁止逐字按 OCR 墨迹框拉伸或自适应字号。检测实际 PDF 字体对象并目检；仅保存坐标不能声称“像素级还原”。换字、字体或图形后的可测偏差必须如实记录。
- 简体化覆盖适用的一般正文、图名、说明性图内标签与旁注；固定诵读原文、符箓及有构形作用的题字属于保护项，不做一刀切转换。逐项记录保护范围及依据，不能据此整页免审。生成图中的字须逐字检查，不能只验证可提取的活字；识别不了的小字进入疑点记录。
- 用上下文、专名、术语表、底本与可靠平行文进行智能纠错。例如有依据地将“伏义”校订为“伏羲”，不能全局替换“义”。每项实质校订记录位置、原文、校订文、依据、置信度与审核状态。原始识别层不覆盖，未定字不靠常识补造。
- 渲染并实际查看每一张比较页、独立页。记录字号、缺字、裁切、重叠、图文间距、嵌入字体、检索文字顺序等发现。不能把程序生成的页数或模板式“通过”当作真实审查。

## 必经文字与语义复核

执行[字形、校读与语义复核](text-semantics-review.md)，分别确认“原字是否抄对、校改是否有据、完整句段是否读通”。全部区域都要审，不能只检查OCR疑字。原字清楚但语义未定时，保留原字和未决校记；据证修底本讹字只进入校读层。另一次真实执行复审最终文字与PDF，结果绑定统一疑点账本。排版、字体和图片检查通过不能代替此项。

## 记录合同（schema 1.1）

每版保存 `90-audit/layout-proof/<version>/review.json`。所有文件引用为 `{path, sha256}`；一般使用工作空间相对路径。只有外部字体、原始 OCR 和渲染依赖允许绝对输入路径，原 PDF 位置由 intake 清单决定。

必需字段：

| 字段 | 内容 |
|---|---|
| `schema_version`, `book_id`, `version` | `1.1`、当前书 ID、非空且对应目录的版本 |
| `edition_kind` | `original_layout_simplified_proof` |
| `status` | `pending`、`changes_requested`、`accepted` |
| `validator_sha256` | 本次使用的 `validate_layout_proof.py` 的 SHA-256 |
| `text_semantics_policy_sha256`, `text_semantics_review` | 语义审核脚本哈希及实际内容审读JSON的文件绑定；格式见[专项合同](text-semantics-review.md)。未审核候选引用可为null，接受时必需。 |
| `scope` | `kind: sample/complete`、`source_pages: [物理页号]`、具体 `reason`；complete 覆盖输入 PDF 全部物理页，不能暗示整个原书已完成 |
| `source_pdf`, `pdf` | 原 PDF 与本版比较 PDF 的文件绑定 |
| `inputs` | 文件绑定列表，每项另有 `role`；至少含 `source_blocks`、`normalized_blocks`、`corrections`、`renderer`、`font`；使用的图片、配置、OCR、辅助脚本均绑定，不只绑定主渲染脚本 |
| `coverage` | 每源页一项：`source_page`、所有 `block_ids`、原页 `source_image` 文件绑定 |
| `figures` | 每幅／子图一项：唯一 `figure_id`、`block_id`、`source_page`、`source_bbox`、出现的 `pdf_pages`、实际 `asset` 文件绑定；坐标沿用源页像素，不是资产裁片坐标 |
| `pages` | 每 PDF 页一项：`pdf_page`、`role: comparison/standalone`、对应 `source_pages`、`render` 文件绑定、`checks` |
| `review` | 未审为 null；接受时记录 `reviewer`、`kind: user/human/model`、`reviewed_at`、本版 `pdf_sha256` 及真实审查记录 `evidence` 文件绑定 |

每页 `checks` 必须包含下列八项，每项为 `{status, findings}`：

1. `text_coverage`：正文与各类文字完整。
2. `figure_coverage`：子图清单完整，无缺图、多图或重复。
3. `layout_alignment`：原列序、位置、比例与边界复核。
4. `uniform_region_fonts`：同区固定字号、无逐字拉伸。
5. `simplified_body_and_labels`：适用的正文及说明性标签已简体化；固定原文与构形字迹的保护范围、原字保留及依据逐项复核。沿用字段名，不升级schema；发现记录不能只写“全部简体”或用整页不适用掩盖遗漏。
6. `contextual_corrections`：专名、术语、引文纠错、跨列接读、句意及疑点处理；须有独立内容审读记录支持，不能只声称已执行繁简转换。
7. `figure_semantics`：点数、方向、卦爻、连线与标签关系。
8. `pdf_readability`：实际渲染、字体、裁切与检索顺序。

检查状态为 `pending/passed/changes_requested/not_applicable`。通过或不适用必须有具体发现／理由。接受须八项均通过或有依据地不适用；未解决缺图、错字、错位不能记为通过。实际审查可以由人或独立模型执行；如用户要求亲自审核，只有明确的用户反馈能满足该要求。不得伪造审查会话，或把“这是重要审核点”理解为已接受质量。

## 校验、返工与边界

```shell
python scripts/validate_layout_proof.py WORKSPACE --allow-pending
python scripts/validate_layout_proof.py WORKSPACE
```

第一条只校验候选稿完整性，不能解锁后续流程。第二条要求真实审核；总控在扩展到批量前执行，并由 `validate_workspace.py` 的 modernized/edited/publication 阶段和出版审计再次执行。schema1.1还检查内容审读覆盖、独立执行、统一台账、当前PDF绑定、读者可见的未决披露，并拒绝高影响未决放行。它不证明语义真实或自动发现所有缺图。旧schema1.0记录只作历史保留；不得修改版本号／哈希将其升级为通过。

PDF、文字、图片、字体、排版参数或渲染脚本变化均使旧审核失效。保留旧记录，新建下一版本并设为 pending；禁止刷新旧哈希沿用旧结论。审核退回时记录具体页／区域和问题。样张通过只证明所审范围和方法，不能冒充全书通过；本关卡也不能替代后续白话忠实性、读者审读和正式出版校验。
