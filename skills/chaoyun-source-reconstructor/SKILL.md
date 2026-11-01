---
name: chaoyun-source-reconstructor
description: Reconstruct faithful, traceable source Markdown and page/block data from complex book PDFs while preserving layout evidence, images, notes, and uncertainty. Use after PDF diagnosis when OCR or layout recovery is needed; do not translate, simplify, paraphrase, or silently repair unreadable source text.
---

# 超云原貌重建

Create the evidentiary source edition that all later stages depend on.

## Workflow

1. Read the diagnosis profile and honor its page-level routes. If none exists, diagnose first.
2. Render or preserve page images at sufficient resolution for later verification. Keep source page numbering separate from logical numbering.
3. Extract or OCR regions with coordinates, block type, language hint, and reading-order index. Use multiple passes only where diagnosis shows a concrete benefit.
4. Reconstruct headings, body, notes, captions, tables, figures, and cross-page paragraphs according to visible evidence.
5. Assign stable `page_id` and `block_id` values. Every block records `component_id`, `structural_role`, `bbox`, and page-local `reading_order`. Write `20-source/blocks.jsonl` before producing `20-source/source.md`.
6. Compare representative and high-risk pages against source images. Put uncertain glyphs, reading order, and damaged regions into the audit ledger.

Follow [references/reconstruction-policy.md](references/reconstruction-policy.md).

When fixed recitations, form-bearing lettering or rare glyphs occur, use [text/image and rare-glyph policy](../chaoyun-ancient-book-renovator/references/text-image-and-rare-glyph-policy.md). Identify protected spans before normalization; separate recited wording, procedural text and embedded notes using visible boundaries and continuations. Record figure/chant/action links only where supported, including absent or unresolved links. Preserve clear unidentified glyphs with located source evidence; font failure, uncertain reading and physical damage are different problems. An image of a whole legible chant is evidence, not a substitute for its reader-facing body text.

If identification remains unresolved, own the source assets and mapping under [glyph fallback](../chaoyun-ancient-book-renovator/references/glyph-fallback-and-acceptance.md). Preserve actual residual strokes, source context, crop coordinates and hashes; do not generate missing strokes or force inseparable forms into single characters. Recheck inherited character mappings as well as blanks, and hand off glyph identity, pronunciation and meaning as separate states.

## Hard boundaries

- Preserve original characters, wording, claims, mistakes, and historical forms at this stage.
- A clearly visible but semantically odd glyph is not missing text. Restore the actual glyph rather than □ or a fluent guess; any emendation of a source typo belongs in the reading layer with its witness. Distinguish a transcription repair from an unresolved meaning question in the same phrase.
- Do not use semantic plausibility as proof of an unreadable glyph.
- Do not collapse marginalia or commentary into the main text without explicit structural evidence.
- Keep source coordinates and stable block IDs when repairing reading order. Similar x coordinates do not decide which stacked segment comes first; inspect the column and join complete phrases, including split labels such as 发／挥／曰.
- Do not represent an annotated or multi-register page as one catch-all `body` block. Separate visible main text, commentary, headings, running matter and other regions before modernization.
- Preserve figures and complex tables as images when a structured transcription cannot be verified.
- Remove repeated headers or page numbers only after demonstrating the repetition pattern.

## Gate

Pass only when all included pages and blocks are accounted for, reading order is supported, assets resolve, and uncertain material is linked to page evidence. Every included physical page must use its real non-sentinel page ID; repeated placeholders such as `p000` are a hard failure. Join cross-page sentences before modernization or preserve an explicit continuation link; do not translate isolated line fragments as complete prose. Structural validity alone is not OCR accuracy.

For workflow 1.10 ordinary-reader work, follow [reading-unit ownership](../chaoyun-ancient-book-renovator/references/reader-units.md). Supply source-backed commentary targets and continuation links to the editor. Inspect page boundaries and identify chapter/book notes separately from passage notes; do not attach by nearest-neighbor text alone.

For original-layout proofs or text-error feedback, hand off to [字形、校读与语义复核](../chaoyun-ancient-book-renovator/references/text-semantics-review.md). Check source fidelity across the entire declared sample, including text the OCR did not flag; readable glyphs alone do not certify meaning.
