# 字形、校读与语义复核

这是 G3.5 的必经内容审核，也是处理“识别错了、认不出来、认对却读不通”反馈时的返工入口。适用于本次交付范围；样张不扩大为全书验收。复用统一疑点账本和既有阅读单元，不再建一套并行疑点系统。

## 三种判断分别作结论

| 判断 | 核对对象 | 可以怎样改 |
|---|---|---|
| 字形是否忠实 | 原页放大、坐标、原始OCR、原貌转写 | 只有实际字形证据能更正 `source_text`。原图可辨但文义不通，仍须照录，不能用□代替。 |
| 校读是否有据 | 原字、同书正文标题／卷次、图题／古注、平行正文、可信异本 | 底本讹字可在规范化阅读层有据校改；源层保留原字，以 `editorial_exception` 等明确标出校勘，不能冒充繁简转换。 |
| 全句是否读通 | 完整句段、跨列／跨页续文、注释归属、专业语境 | 字都认对仍可能错断、错接、误解术语。先恢复接读关系，再说明含义；无证不能靠“更通顺”填字、替字或添加确定含义。 |

字形已定、词义未定可同时成立。恢复“馬／水／換”的原字，只能关闭相应转写错误；“是否校乌／沐／鬼”的文义问题必须另行裁决。OCR置信度、多个同源识别文本一致、常见成语、熟悉人名和整齐七言均不是唯一校读的证据。

## 审核动作

1. 冻结本轮输入和前版：扫描、OCR、源块、读本、校订账、阅读单元、PDF。逐区审阅交付范围内的所有文字，包含未被OCR标低分的字、图题、图中文字、小注、页眉、卷次和目录。不得只审已染色的疑字。
2. 编辑前登记候选，保留 `page_id`、`block_id`、实际坐标、原字、当前读法、拟校、问题类别、责任阶段和冻结输入。继续用 uncertainty-adjudicator 的 schema 1.3 候选与 1.2 裁决；所有既有关闭要求仍适用。
3. 查原页同字写法、前后列／邻页、同书重复段落／标题／古注，必要时查可信异本。保存实际看过的扫描及位置，不以未经查看的链接或继承OCR充当旁证。不要把底本本身的讹字归咎于OCR。
4. 在繁简转换前建立本书的语境保护项，并在转换后复查命中处：人名、书名、卦名、干支、方位、数量、否定和取舍词。固定诵读原文与构形字迹另按[文字／图像处理规范](text-image-and-rare-glyph-policy.md)保护，不能因现代读者版而全部简化。例如卦名“乾”仍作乾；普通“乾燥”可作干燥。禁止全局 `干→乾` 或 `义→羲`。校订记录必须说明规则适用的词组和原文位置。
5. 将版面顺序与语义接读分别核验。几何框不变也可能读序错误；同列上段应先于下段。连接“爬／沙”“云／衢”“出人／右”和拆框的“发／挥／曰”。干支“未、巳、酉”须按所在句的领域语境审读，不能默认现代词义。保留省写序号或历史用词，释义放在编者说明中。
6. 每次改字检查是否引入新错误，尤其否定、取舍、数字、方位与专名。修正后通读完整句段，核对源文、规范文本、相关译文／术语／图注及最终PDF，不能只检查JSON已改变。阅读层的据义校改不得写回忠实源层。
7. 由另一次真实执行复审冻结的修订文字和最终PDF。保留实质意见、身份、run ID和文件哈希；只换审核者名字不算独立。首次方法试验按既有盲审要求进行；最终定点复审可以查看改字清单，但如实标为定点复审。
8. 更新统一账本，关闭有证据且已落地复审的项；恢复字形后仍不通的句子继续 `open_material`。高影响未决阻止内容验收；低／中影响项须评估能否限定并在阅读材料中明确披露，不能靠减少疑点数获得通过。

无旁证时，交付标明未决的版本稿及下一步缺少的证据；不要把猜读填入正文，也不要只染色不说明问题。对已有原版式PDF返工，另出带版本号的原扫对比稿，列出“原字／前版／本版／依据”和仍未解决的字词或句读。术语、接读、图题或图内字有改动后，重新渲染并复查实际成品。

## G3.5 schema 1.1 的机器记录

`review.json` 增加：

- `schema_version: "1.1"`；workflow仍为1.10，不重命名既有阶段。
- `text_semantics_policy_sha256`：`scripts/validate_text_semantics.py` 的实际哈希，与原 `validator_sha256` 一起绑定审核政策。
- `text_semantics_review`：实际内容审读JSON的 `{path, sha256}`，例如 `90-audit/layout-proof/V3/text-semantics.json`。未完成审核的候选可暂为null；`accepted` 必须具备。

内容审读JSON：

| 字段 | 要求 |
|---|---|
| `schema_version` | `1.0` |
| `proof_sha256` | 对最终证明材料调用 `validate_text_semantics.proof_digest(proof_record)`，绑定源PDF、最终PDF、全部输入、页／块／图覆盖、渲染和页检查。排除审核引用本身，避免循环哈希。 |
| `status` | `passed` 或 `changes_requested`；实际复核做完不等于内容通过。 |
| `producer`, `producer_run_id`, `reviewer`, `reviewer_run_id`, `reviewed_at` | 非空；制作人与审核人、两次执行ID均不同。 |
| `evidence` | 实际独立审读笔记／会话的文件绑定，不是自动生成的“已通过”占位报告。 |
| `ledger_bindings` | 以 `uncertainty-candidates.jsonl`、`uncertainty-adjudication.jsonl`、`uncertain-items.jsonl` 为键，各绑定对应 `90-audit/` 文件。零候选允许空JSONL，仍需文件与哈希；不人为制造疑点。 |
| `coverage` | 每源页一项 `{source_page, block_ids, findings}`；块清单等于G3.5该页全部源块，findings为实际逐页发现。 |
| `checks` | 下列六项各有 `{status, findings}`；status为 `passed/passed_with_ledger/changes_requested`。无某种文字或无改字时说明实际情况，不略过整类审查。 |
| `candidate_results` | 覆盖范围内每候选恰好一项，格式见下；计数从账本导出，不填写上次样张的数字。 |

六项检查：`glyph_fidelity`（字形），`source_reading_separation`（原字与校读分离），`contextual_terms`（术语和转换），`reading_order`（完整接读），`meaning_in_context`（句意与未决边界），`final_artifact`（最终文字及PDF实际复核）。

候选结果包含 `candidate_id`、`result: verified/disclosed_unresolved`、具体 `finding`、非空 `evidence` 列表。evidence使用既有located格式：文本 `{path, sha256, quote}` 或图像 `{path, sha256, region: [x0,y0,x1,y1]}`。`verified` 必须对应已关闭裁决；`open_material` 必须使用 `disclosed_unresolved`，并提供 `reader_disclosure` located引用，定位到 `30-normalized/`、`40-modernized/`、`50-edited/` 或 `60-publication/` 中实际交付阅读／校读材料的说明。仅内部审核文件不满足读者披露。

`validate_layout_proof.py` 自动调用此检查，并复用 `project_open_items` 验证疑点关闭和投影。正文、PDF、页检查或账本变化使旧绑定失效；不能只刷新哈希保留旧结论。校验能拒绝缺记录、漏项、过期引用、未决冒充解决和高影响未决放行，但不能替模型或人判断句意是否正确。

旧schema1.0记录保留为历史；不得改版本号、补字段或机械复制V2报告后宣称新验收。没有G3.5需求的旧工作空间不自动启用此关卡。新审核使用1.1，实际重新查看相关文字和PDF。

## 回归依据

更新纠错方法时，读[真实失败案例](text-semantics-regressions.md)。它们用来检查错误分类、证据层边界和接读判断，不是全局替换词典。脚本反例测试只证明合同能拒绝不合格状态；真实书稿仍需独立审读。
