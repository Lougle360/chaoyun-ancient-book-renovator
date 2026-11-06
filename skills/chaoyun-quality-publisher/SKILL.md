---
name: chaoyun-quality-publisher
description: Independently audit a traceable modern reading edition and publish validated Markdown and PDF packages with source comparison, embedded fonts, resolved assets, and a quality report. Use after editing or when an existing book workspace needs final acceptance; do not certify content from file existence or structural checks alone.
---

# 超云品质出版

Treat audit and rendering as separate gates. A beautiful PDF is not evidence of accurate transcription or translation.

Use the controller’s [execution protocol](../chaoyun-ancient-book-renovator/references/execution-control.md): focused-v1 defaults to one complete stable final-manuscript reader acceptance, independent fidelity and final-PDF inspection; legacy books retain their locked schedule. Trial layout, fonts, anchors and navigation before freeze. Renderer-only fixes keep byte-identical accepted text. One actual sequential PDF inspection may supply visual, figure, navigation and continuity records; separate forms do not require repeated full PDF reads.

For a bounded illustrated sample, use [illustrated-reader-samples.md](../chaoyun-ancient-book-renovator/references/illustrated-reader-samples.md): inspect every delivered page, source-to-reader coverage and declared omissions; verify precise symbols in the actual PDF; bind an actual separate reader/source review to the current files. Report sample acceptance only. Do not create whole-book approvals or relax the full-book gates below. For an explicitly requested case report or Feishu publication, use [iteration-report-and-feishu.md](../chaoyun-ancient-book-renovator/references/iteration-report-and-feishu.md); cloud readback proves transfer, not semantic acceptance.

## Audit

When applicable, audit [original wording, image roles and rare glyphs](../chaoyun-ancient-book-renovator/references/text-image-and-rare-glyph-policy.md) separately from fluent meaning and counts. Compare fixed passages character by character in the actual Markdown/PDF, including headings, repeated words and continuations; check narration boundaries, source-supported symbol/action links, protected lettering and single-glyph fallbacks. Whole-chant images or hidden OCR alone do not meet the body-text requirement. A fully accounted block list does not prove complete meaning, and blanks do not prove characters were repaired.

For unresolved glyphs, use [glyph fallback and version acceptance](../chaoyun-ancient-book-renovator/references/glyph-fallback-and-acceptance.md). Check real source/crop/PDF fidelity, preserved aspect and placement, then extract or copy entire surrounding sequences to verify order and repetition. Inline image positions and `ActualText` presence alone do not prove correct reading order. Keep source preservation and complete recitation restorability as separate conclusions. Bind user acceptance to the agreed version, hashes, scope and disclosed limitations; freeze accepted artifacts without closing unresolved readings or promoting a scoped trial to formal release.

For ordinary-reader release require [workflow 1.8 prerequisites](../chaoyun-ancient-book-renovator/references/reader-production.md) and reader acceptance schema 1.2 with actual reading-session provenance plus final-reader-cut evidence. Preserve all 1.6 uncertainty gates. Report integrity, fidelity, comprehension and PDF proof separately, including model/human review type. Inspect provenance: distinct filenames/role labels do not prove independent execution, and mechanical success cannot assign semantic grade.

For new full-book work, require production-plan schema `1.1` and the [whole-book illustration plan and representative-figure review](../chaoyun-ancient-book-renovator/references/whole-book-illustration-plan.md). Compare the final figure inventory and actual PDF with the accepted plan, including recorded changes and source-image coverage. A source-grounded no-illustration decision is valid. Legacy schema `1.0` validation does not satisfy this new requirement; preserve historical releases and assess fresh evidence before a new release.

1. Verify source hash, page coverage, block identity across stages, dispositions, asset references, and uncertainty-ledger coverage.
2. Verify complete source-to-reader fidelity evidence and exact dependencies. Reuse valid independent findings instead of repeating identical comparison; inspect changed/high-risk material or evidence gaps and expand for systematic errors. A statistical sample cannot replace full required fidelity coverage.
3. Check names, dates, quantities, terminology, quotations, captions, tables, and Japanese/classical-language routes.
4. Confirm editor-created content is labeled and does not masquerade as source text.
5. For ordinary-reader editions, validate item-level `50-edited/reader-aids.json` against source blocks and the final publication Markdown; require `$chaoyun-reader-experience-reviser` acceptance and its revision ledger; then audit the derived `50-edited/editorial-report.json`: book nature and attribution, introduction coverage, whole-book reader review, contextual glossary coverage, figure-specific guidance, pipeline-language scan, and high-impact uncertainty count. Never accept self-reported counts in place of entries and evidence.
6. Assign grade A–D with explicit evidence and limitations.
7. Require the uncertainty Skill's `--check --publication` gate: no unsupported closure, no duplicate masking an open main issue, a content-bound final-manuscript recheck, and a passing real chapter-trial record. Neither a zero open count nor an old source-stage verdict substitutes for this gate.

Hard publication failures include unresolved literal HTML/XML tags in rendered text, internal pipeline messages presented to readers, OCR garbage treated as prose, repeated sentinel page IDs, broken page-to-block links, low-confidence fragments accepted as high-confidence without image evidence, or incomplete page-level visual coverage claimed as a full scan conversion. Stop and return the edition to the responsible stage instead of decorating these defects with an uncertainty box.

Use [references/publication-package.md](references/publication-package.md) for output and visual requirements.

## Publish

- When original-layout proof is required, audit the separately versioned **原版式简体校订版** through [G3.5](../chaoyun-ancient-book-renovator/references/layout-proof-review.md). Check source-paired pages, every subfigure, region font sizes, eligible simplified labels, explicitly protected original wording/lettering and contextual corrections. Preserve the pending/returned/accepted status and bind review to the exact PDF and inputs. It is an intermediate edition; its approval does not replace final reader-edition acceptance.
- New G3.5 acceptance requires the schema 1.1 [text/semantics review](../chaoyun-ancient-book-renovator/references/text-semantics-review.md): separate actual review of all regions, source/reading separation, term protection, complete reading order, meaning and final PDF. Verify the canonical uncertainty ledger and reader-visible unresolved disclosures. High-impact unresolved meaning blocks acceptance even when layout, embedded fonts and image counts pass. Old approval cannot be promoted by updating a schema field or hash.
- Produce `60-publication/modern-reading.md` and one official reader PDF named from `book.json.release_filename`, normally `<原书名>·<版本名>.pdf`. A `modern-reading.pdf` internal alias is optional and must not be presented as a second final edition.
- Publish only the accepted `compact_final_reader` manuscript. Keep the guide/process edition in review history or supplements and label it as non-release; never let its metadata, field dumps or editorial scaffolding re-enter the official reader PDF during layout.
- Produce source-comparison Markdown/PDF under `60-publication/supplements/` when evidence supports it; do not place a second final-looking PDF beside the official reader PDF.
- Use relative asset paths in Markdown and embed suitable CJK fonts in PDF.
- Include a formal cover, copyright/credits page, supplied author/editor/producer lines, and appropriate reader-use notes. For generated covers, intentionally choose either a full-image cover with verified Chinese typography or an image background with programmatically typeset text; inspect every cover character.
- Verify clickable TOC targets, PDF bookmarks, heading levels, page breaks, figures, captions, tables, footnotes, links, selectable text, and rendered pages.
- For ordinary-reader editions, inspect every rendered page regardless of book length. Other declared modes may use full anomaly inspection and documented stratified sampling. Blank overflow pages, raw markup, orphan fragments, unexplained crops, and pages with extreme whitespace are defects, not stylistic choices.
- Use release-binding schema 1.1. Give every page a reader-facing role and separate findings for legibility, density, whitespace, hierarchy and continuity. Repeated boilerplate approval is invalid. Body and glossary pages require reviewed visible page numbers; TOC entries require visible page labels; Markdown lists and glossary emphasis must remain visible in the PDF.
- Read the candidate sequentially as a reader and write `90-audit/pdf-reader-review.json`, bound to the exact PDF hash. Record a concrete reader action and continuity judgment for every page. Pixel identity and text extraction cannot replace this pass.
- Keep exactly one unambiguous official release artifact in the publication root. Archive or clearly label superseded drafts. If a file lock forces a versioned working filename, restore the declared official name before delivery.
- Treat `book.json.release_filename` as canonical. `quality-report.json` must name the same file; a versioned fallback cannot pass the publication audit as the official release.
- Render under `60-publication/candidates/`, not the official path. Prepare and review candidate proofs, then install with `python scripts/install_official_pdf.py <workspace> <candidate.pdf> --expected-pages N`. The installer runs both gates against the candidate, requires grade A/B, backs up the previous official file, checks locks and uses atomic replacement. Failure leaves the previous release unchanged.
- Write `90-audit/quality-report.json` and a human-readable quality report.
- Prepare content-bound proof with scripts/prepare_release_proof.py and the actual candidate path; this creates pending observations, never approvals. Inspect pages and record findings. The guarded installer executes both final gates; call separate audits when diagnosing failures, not as another identical automatic pre-install chain. Never install an unaudited PDF to enable proof review.
- Keep publication Markdown byte-identical to the accepted complete manuscript, including final front matter. Freeze credits, cover text and reader-facing additions before acceptance. Asset references must resolve to identical content from both stages. If publication changes prose, return it to reader review instead of refreshing hashes to bypass it.

Run the deterministic package audit:

```shell
python scripts/audit_publication.py book-workspace
```

## Gate

Do not report completion until required outputs are nonempty, the package audit passes against the declared official PDF, semantic gates are evidenced, source-page accounting reconciles, and unresolved items fit the declared grade. Report the single official release file and remaining limitations.

For workflow 1.10, enforce [reading-unit rendering](../chaoyun-ancient-book-renovator/references/reader-units.md). Check every PDF page for distinguishable main text/commentary and understandable cross-page note continuation. A continuation page need not repeat the main passage. Record actual page-specific observations; scripts must not manufacture approvals from page counts or extracted first/last lines.
