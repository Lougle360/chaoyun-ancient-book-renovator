---
name: chaoyun-ancient-book-renovator
description: Renovate book-like PDFs into traceable modern Chinese Markdown and polished reader-facing PDFs. Use for complex scanned books, classical Chinese, traditional Chinese, Japanese, vertical text, annotations, or mixed layouts that require diagnosis, faithful reconstruction, modernization, editing, and quality gates; do not use for a simple one-off text extraction.
---

# 超云古书翻新skill

Turn a recoverable book PDF into a modern reading edition without losing the evidentiary link to the source.

## Non-negotiable model

Maintain two separate layers:

- **Evidence layer:** page images, layout coordinates, faithful source text, uncertainty, and provenance.
- **Reading layer:** normalized text, modern Chinese, editorial additions, Markdown, and PDF.

Never replace the evidence layer with a translation or fluent rewrite. Every modernized content block must resolve to a stable source `block_id`. Do not invent missing text from context. Mark unrecoverable content explicitly.

## Define the edition before processing

Choose and record one primary delivery mode before bulk work begins:

- **Evidence archive:** optimized for faithful recovery, provenance, and later research.
- **Source-comparison edition:** source text and modern text remain visibly paired.
- **Ordinary-reader modern edition:** a complete contemporary book that a non-specialist can read directly.

When the user asks for “普通人可以直接阅读” or equivalent, use the ordinary-reader modern edition. Do not substitute OCR text, a source comparison, or a lightly punctuated transcript for that deliverable. Read [references/modern-reading-edition.md](references/modern-reading-edition.md) and record `target_reader`, `edition_label`, and `release_filename` in `book.json`.

## Run the suite

1. Establish the input PDF, output root, delivery mode, intended reader, modernization depth, and whether paid model calls are authorized. Preserve the source PDF. Record the physical PDF page count and classify every page as included content, front/back matter, blank/noncontent, excluded with reason, or unreadable.
2. Initialize a new isolated workspace:

   ```shell
   python scripts/init_workspace.py input.pdf output-directory --edition-label 现代白话版 --target-reader 现代普通读者
   ```

3. Use `$chaoyun-pdf-diagnoser` to create the book profile and page-level route map. Read [references/routing.md](references/routing.md) when layouts or languages are mixed.
4. Use `$chaoyun-source-reconstructor` to create the faithful source Markdown and page/block records. Do not proceed if source coverage or reading order fails its gate.
5. Use `$chaoyun-text-normalizer` for script conversion, variant-character policy, punctuation, and segmentation. This stage must not paraphrase.
6. Use `$chaoyun-classical-modernizer` for classical Chinese-to-modern Chinese and Japanese-to-modern Chinese. Route mixed-language blocks separately.
7. Use `$chaoyun-reading-editor` to build the declared reader edition, including its reading route, chapter guidance, first-use terminology, figure guidance, and glossary where appropriate, while keeping editor-created material explicitly labeled.
8. Use `$chaoyun-quality-publisher` for independent semantic checks, formal front matter, official release naming, package audit, and Markdown/PDF production.
9. Run the deterministic contract validator:

   ```shell
   python scripts/validate_workspace.py output-directory --stage publication
   ```

10. Report the achieved grade, source-page accounting, reader-facing PDF page count, unresolved items, and the single official release path. Never call a run complete merely because files exist.

For scan-heavy books, do not publish a full-book reading edition until every included source page has page-level visual evidence or an explicit `unreadable` / `noncontent` disposition. Text-only judging against inherited OCR is not an independent semantic check. The contract validator and publication auditor must both exit successfully; a hand-written `passed_with_ledger` state cannot override either failure.

## State and stopping rules

- Stages are `intake`, `diagnosis`, `source`, `normalized`, `modernized`, `edited`, and `publication`.
- A later stage may start only after the preceding gate is `passed` or explicitly `passed_with_ledger`.
- Use append-only audit records and preserve stage outputs; do not rewrite earlier evidence in place.
- Support resume from the last completed stage. A retry must not duplicate accepted records.
- Before a paid full-book run, estimate pages/cost and obtain authorization. A representative sample is not authorization for the full corpus.
- Keep samples and full-book artifacts in visibly different paths and filenames. A sample may validate routing and quality, but it is never proof that the complete book was converted. Never label a partial, C-grade, or validation-failing artifact as `完整版`, `final`, or publication-ready.
- Stop on corrupt/encrypted input, missing pages, materially ambiguous reading order, systematic language misclassification, or budget exhaustion. Record the exact blocker.

## Completion grades

- **A — publication-ready:** all gates pass, all content blocks are accounted for, and no high-risk uncertainty remains.
- **B — readable with ledger:** the edition is usable, with bounded uncertainties fully listed and linked to source evidence.
- **C — assisted draft:** substantial uncertainties or layout/translation risks remain; do not present as publication-ready.
- **D — unrecoverable:** source evidence is insufficient for a responsible conversion.

Use [references/data-contract.md](references/data-contract.md) for files and record fields. Use [references/quality-gates.md](references/quality-gates.md) before advancing a stage or declaring completion.
