# Publication package

## Required files

- `modern-reading.md`
- one official `<book-title>·<edition-label>.pdf` declared by `book.json.release_filename` or `quality-report.json.publication.pdf`
- `quality-report.json`
- `quality-report.md`
- all referenced local assets

Create `source-comparison.md` and `source-comparison.pdf` when source text is sufficiently recovered. Do not create an empty comparison edition merely to satisfy a template.

`modern-reading.pdf` may be retained as an internal canonical alias, but the package must identify exactly one reader-facing release PDF. Superseded drafts belong in an archive or carry an unmistakable draft label.

## PDF requirements

- Embedded CJK fonts cover simplified/traditional Chinese, Japanese, punctuation, and rare glyphs used by the book.
- Searchable/selectable text is preferred; page images remain available for evidence.
- TOC targets, bookmarks, headings, page numbers, running headers, figures, tables, notes, and links render correctly.
- The cover, copyright/credits page, author/editor/producer credits, and edition label agree with `book.json`.
- Chinese cover typography is checked character by character. A hybrid cover may use generated art with programmatically typeset title/credits when this gives more reliable text.
- Avoid widows/orphans, clipped glyphs, stretched images, missing characters, and blank overflow pages.
- Inspect rendered pages from each layout family, not only the first page.

## Quality report

Record source identity, tools/models and versions, physical source-page accounting, reader-PDF page count, page/block coverage, sampling method, TOC link and bookmark results, rendered-page inspection count, error findings, uncertainty counts by severity, cost, grade, limitations, and the exact official output path. Structural audit and semantic audit must be reported separately.
