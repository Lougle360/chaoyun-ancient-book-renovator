---
name: chaoyun-quality-publisher
description: Independently audit a traceable modern reading edition and publish validated Markdown and PDF packages with source comparison, embedded fonts, resolved assets, and a quality report. Use after editing or when an existing book workspace needs final acceptance; do not certify content from file existence or structural checks alone.
---

# 超云品质出版

Treat audit and rendering as separate gates. A beautiful PDF is not evidence of accurate transcription or translation.

## Audit

1. Verify source hash, page coverage, block identity across stages, dispositions, asset references, and uncertainty-ledger coverage.
2. Compare high-risk and statistically distributed samples against source page images and accepted translations. Expand review when systematic errors appear.
3. Check names, dates, quantities, terminology, quotations, captions, tables, and Japanese/classical-language routes.
4. Confirm editor-created content is labeled and does not masquerade as source text.
5. Assign grade A–D with explicit evidence and limitations.

Hard publication failures include unresolved literal HTML/XML tags in rendered text, internal pipeline messages presented to readers, OCR garbage treated as prose, repeated sentinel page IDs, broken page-to-block links, low-confidence fragments accepted as high-confidence without image evidence, or incomplete page-level visual coverage claimed as a full scan conversion. Stop and return the edition to the responsible stage instead of decorating these defects with an uncertainty box.

Use [references/publication-package.md](references/publication-package.md) for output and visual requirements.

## Publish

- Produce `60-publication/modern-reading.md` and one official reader PDF named from `book.json.release_filename`, normally `<原书名>·<版本名>.pdf`. A `modern-reading.pdf` internal alias is optional and must not be presented as a second final edition.
- Produce source-comparison Markdown/PDF when evidence supports it.
- Use relative asset paths in Markdown and embed suitable CJK fonts in PDF.
- Include a formal cover, copyright/credits page, supplied author/editor/producer lines, and appropriate reader-use notes. For generated covers, intentionally choose either a full-image cover with verified Chinese typography or an image background with programmatically typeset text; inspect every cover character.
- Verify clickable TOC targets, PDF bookmarks, heading levels, page breaks, figures, captions, tables, footnotes, links, selectable text, and rendered pages.
- Inspect every rendered page for short books and all anomaly pages plus stratified samples for long books. Blank overflow pages, raw markup, orphan fragments, unexplained crops, and pages with extreme whitespace are defects, not stylistic choices.
- Keep exactly one unambiguous official release artifact in the publication root. Archive or clearly label superseded drafts. If a file lock forces a versioned working filename, restore the declared official name before delivery.
- Write `90-audit/quality-report.json` and a human-readable quality report.

Run the deterministic package audit:

```shell
python scripts/audit_publication.py book-workspace
```

## Gate

Do not report completion until required outputs are nonempty, the package audit passes against the declared official PDF, semantic gates are evidenced, source-page accounting reconciles, and unresolved items fit the declared grade. Report the single official release file and remaining limitations.
