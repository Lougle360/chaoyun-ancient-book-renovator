# Quality gates

## G0 Intake integrity

- Source opens and its SHA-256, byte size, page count, and filename are recorded.
- Encryption, corruption, missing pages, duplicates, and excluded pages are accounted for.
- Included, excluded, blank/noncontent, and unreadable page counts reconcile exactly to the physical PDF page count.
- The source is never overwritten.

## G1 Diagnosis

- Every page has a route and layout/language classification.
- Every distinct page family has a representative verification sample.
- Known unsupported content is recorded before bulk processing.

## G2 Faithful source

- Every logical page and content block is accounted for.
- Reading order, headings, notes, images, captions, and tables are checked against page images.
- OCR uncertainties remain visible; fluent inference is not accepted as transcription evidence.
- Raw uncertainty candidates have stable IDs and preserve source-image evidence; they are not yet treated as reader-facing defects.

## G2.5 Uncertainty adjudication

- Every raw candidate belongs to exactly one adjudication; repeated reports may be grouped without deleting their IDs.
- Each decision is classified as confirmed, noncontent, structural, duplicate, or materially open, with explicit reader impact.
- Confirmed source corrections include before/after text and evidence. Meaning alone is not sufficient to repair a glyph.
- The reader-facing ledger is regenerated from `open_material` decisions only and contains no resolved stamp, variant, cross-page, semantic-comment, or duplicate record.
- Candidate count, adjudicated count, and material-open count are reported separately.

## G3 Normalization

- Each changed character, punctuation insertion, merge, or split is traceable.
- Script conversion and variant normalization do not change claims or translate the prose.
- Names, dates, measurements, quotations, and technical terms receive stricter review.

## G4 Modernization

- Every source content block has a modernized record or an explicit disposition.
- Classical Chinese, modern Japanese, classical Japanese, and kanbun use the correct route.
- The modern text adds no unsupported fact, causal claim, or certainty.
- High-risk blocks receive an independent comparison or enter the uncertainty ledger.

## G5 Reading edit

- Editorial additions are labeled and are not mixed into translated source text.
- Chapter hierarchy, terminology, cross-references, figures, and notes remain coherent.
- Readability improvements preserve the accepted meaning.
- For an ordinary-reader edition, the book includes a reading route, chapter guidance, first-use term explanations, figure-reading guidance, and a complete glossary where applicable.
- Traditional causal or predictive claims are attributed as historical/source claims and remain distinct from directly observable descriptions.
- OCR corruption, missing text, and uncertain reading order are returned to reconstruction rather than polished into fluent prose.

## G6 Publication

- Markdown image references resolve and no source-absolute paths leak into the package.
- Both reading edition and source-comparison edition are generated when source evidence permits.
- PDF fonts embed correctly; headings, TOC, page breaks, images, and Chinese/Japanese glyphs render.
- The quality report lists coverage, grade, models/tools, cost, unresolved items, and limitations.
- The declared release path is checked for locks before generation. A temporary PDF is validated before atomic replacement; a lock may block replacement but must not create a second ambiguous official release.
- The release includes the declared cover, copyright/credits page, author/editor/producer credits, clickable TOC, and PDF bookmarks.
- `release_filename` exists, matches the declared book title and edition label, and is the single unambiguous official PDF.
- Link targets and local assets are validated programmatically. Every rendered page is inspected for short and medium books; long books receive full anomaly checks and stratified visual inspection.

## Grade rule

Grade A requires all gates passed and no material unresolved item. Grade B allows bounded ledger items that do not undermine ordinary reading. Grade C covers drafts with material ambiguity. Grade D means the source cannot responsibly support the requested result.
