# Quality gates

Workflow 1.10 additionally requires [reading-unit evidence](reader-units.md) before bulk modernization, exact rendering locations after editing, and both bindings at publication. All 1.9 gates below continue to apply.

## G0 Intake integrity

- Source opens and its SHA-256, byte size, page count, and filename are recorded.
- Encryption, corruption, missing pages, duplicates, and excluded pages are accounted for.
- Included, excluded, blank/noncontent, and unreadable page counts reconcile exactly to the physical PDF page count.
- `delivery_mode` is explicit. Source identity and `source_pdf_pages` are verified against the actual intake PDF, not a report total. Every physical page has at least one block record, including a reasoned placeholder for blank, excluded or unreadable pages.
- The source is never overwritten.

## G1 Diagnosis

- Every page has a route and layout/language classification.
- Every distinct page family has a representative verification sample.
- Known unsupported content is recorded before bulk processing.
- Workflow 1.9 locks `edition-scope.json`: every source component has a declared destination, and source-bearing exclusions preserve explicit user authorization.

## G2 Faithful source

- Every logical page and content block is accounted for.
- Reading order, headings, notes, images, captions, and tables are checked against page images.
- OCR uncertainties remain visible; fluent inference is not accepted as transcription evidence.
- Raw uncertainty candidates have stable IDs and preserve source-image evidence; they are not yet treated as reader-facing defects.
- Each block has a source component, structural role, real region and reading order. An annotated or multi-register page cannot pass as one catch-all body block.
- For unresolved glyphs, apply [source-shape fallback](glyph-fallback-and-acceptance.md): distinguish identity, sound and meaning; retain real residual strokes as well as clear unidentified shapes. Check existing character mappings too, not only blanks. A placeholder must not erase available source shape or imply an unsupported gap length.

## G2.5 Uncertainty adjudication

- Every raw candidate belongs to exactly one active adjudication; repeated reports may be grouped without deleting their IDs.
- A revised adjudication supersedes an inactive historical decision; every candidate has exactly one active decision and open issue IDs remain stable.
- Each decision is classified as confirmed, noncontent, structural, duplicate, or materially open, with explicit reader impact.
- Confirmed source corrections include before/after text and evidence. Meaning alone is not sufficient to repair a glyph.
- The reader-facing ledger is regenerated from `open_material` decisions only and contains no resolved stamp, variant, cross-page, semantic-comment, or duplicate record.
- Candidate count, adjudicated count, and material-open count are reported separately.
- Preserving a glyph or repairing its display/copy behavior does not close an unresolved character, pronunciation or meaning. Record those conclusions separately and retain the stable open issue; user acceptance of a disclosed limitation is not evidence that the reading was resolved.
- Active closure requires located file evidence, checked/not-applicable decisions across six impact scopes, an independently executed bound review, and replayable applied changes where corrected. A duplicate must resolve to a closed canonical candidate. Evidence failure blocks the gate even when the projected open count is zero.
- A representative real chapter trial precedes scale-up; final publication independently rechecks every active decision against the frozen manuscript. Both artifacts are checked by `project_open_items.py --check --publication`; self-tests cannot count as an actual trial.

## G3 Normalization

- Each changed character, punctuation insertion, merge, or split is traceable.
- Script conversion and variant normalization do not change claims or translate the prose.
- Names, dates, measurements, quotations, and technical terms receive stricter review.
- Verify conversion in context (e.g. the trigram 乾 remains 乾). Source glyphs, documented emendations and semantic uncertainty remain separate; a readable source error must not become a fabricated OCR correction.
- Apply [functional text/image protection](text-image-and-rare-glyph-policy.md) before conversion: fixed originals pass through verbatim; form-bearing lettering stays in the figure. Record span-level exceptions and separate font coverage, unknown readings and damaged source evidence.

## G3.5 Original-layout simplified proof PDF

For original-layout reconstruction and Chinese scans with complex diagrams/columns, apply [layout-proof-review.md](layout-proof-review.md). This is a distinct intermediate edition after G3, with source comparison, unchanged source evidence, eligible simplified text/labels plus documented protected originals, contextual correction records, complete figure inventory, original placement and uniform font sizes within each semantic region. Review every PDF page against its source; “beautiful”, selectable text and matching bounding boxes do not prove fidelity.

Register the versioned record in `book.json.layout_proof_review`. `validate_layout_proof.py WORKSPACE` must pass before scaling and is rechecked at modernization, editing and both publication gates. Pending or returned proof, missing review evidence and stale PDF/input/render hashes block acceptance. Changes require a new version and fresh review, not refreshed hashes on an old verdict. See the contract for sample versus complete scope. Legacy unrelated workspaces without this extension are not automatically migrated or approved.

New proof acceptance requires schema 1.1 and [text/semantics review](text-semantics-review.md): all source regions, visible glyphs, source-versus-reading separation, contextual terms, complete reading order, meaning and final artifact are independently inspected. The unified ledger must validate; an open reading cannot be reported as verified, internal audit-only disclosure is insufficient, and high-impact meaning uncertainty blocks acceptance. Font size or selectable text checks do not substitute for this content review.

## G4 Modernization

For ordinary-reader work, first pass workflow 1.8 `book_understood`, `reader_designed` and `sample_accepted` under [reader-production.md](reader-production.md). The understanding brief explains the whole source; the design places prerequisites/examples; a separate actual sample reader tests the method. Only sample translation is permitted before these prerequisites. Their validator checks bindings and task evidence, never grants semantic acceptance. Existing 1.6 uncertainty trial requirements remain in force and use the same chapter where possible.

New full-book production also requires the [whole-book illustration plan](whole-book-illustration-plan.md): `illustration-plan.md` completes the design-stage check, and representative figure review in `sample/illustration-review.md` completes the figure portion of the sample check. Bind both under production-plan schema `1.1` before bulk translation/illustration. Inspect their substance, source coverage and unresolved risks; file existence and hashes alone do not pass these checks. Workflow `1.10` retains `reader_units_built` between design and sample acceptance. A justified no-illustration result is allowed; an unexplained missing source figure is not.

- Every source content block has a modernized record or an explicit disposition.
- A translated/retained record requires nonempty stage text. Stage ID equality alone cannot certify transcription or translation completion.
- Classical Chinese, modern Japanese, classical Japanese, and kanbun use the correct route.
- The modern text adds no unsupported fact, causal claim, or certainty.
- High-risk blocks receive an independent comparison or enter the uncertainty ledger.
- Fixed recitations remain body text with separate narration; compare their literal characters, not only summarized meaning. Confirm source-backed figure/chant/action links and unresolved boundaries under [the text/image policy](text-image-and-rare-glyph-policy.md). Counts and copied text alone do not certify this check.

## G5 Reading edit

- Editorial additions are labeled and are not mixed into translated source text.
- Chapter hierarchy, terminology, cross-references, figures, and notes remain coherent.
- Readability improvements preserve the accepted meaning.
- For an ordinary-reader edition, the book includes a reading route, chapter guidance, first-use term explanations, figure-reading guidance, and a complete glossary where applicable.
- Traditional causal or predictive claims are attributed as historical/source claims and remain distinct from directly observable descriptions.
- OCR corruption, missing text, and uncertain reading order are returned to reconstruction rather than polished into fluent prose.
- `editorial-report.json` records the evidence used for the book-nature statement, source contents reconstruction, contextual glossary, content-figure guidance, and semantic status.
- `reader-aids.json` supplies item-level introduction and glossary evidence. The whole-book reader revision ledger and acceptance report pass independently, and all derived counts match `editorial-report.json`.
- Printed page numbers are not mapped to physical PDF pages by offset assumption; the mapping is verified against page images or explicit page records.
- Reader text contains no model verdicts, candidate fields, repair-queue text, pipeline states, or internal validation messages.

## G5.5 Whole-book reader revision

Workflow 1.8 requires reader review/acceptance 1.2: meaningful contiguous units, actual task/answer/assessment files and provenance, with task links from each unit and core glossary sample. It additionally binds an immutable process-edition snapshot and the six final-reader-cut checks. Repeated generic answers are not section-specific evidence. Old acceptance cannot be upgraded by altering a schema field. Full coverage is preserved without requiring a fake comprehension report for each small heading. The 1.1 mechanics below remain applicable except for the upgraded acceptance version and reading-unit boundaries.

- `$chaoyun-reader-experience-reviser` reads the complete manuscript before editing, records reader obstacles across all nine dimensions, and applies traceable `add`, `delete_from_reading_path`, `rewrite`, or `reorganize` operations.
- Deletion from the reading path preserves source material and provenance. Medium/high semantic-risk revisions enter the unified uncertainty lifecycle.
- A fresh regression reviewer differs from the revision producer. The acceptance hash matches the final manuscript, no proposed or returned revision remains unresolved, and glossary sampling passes.
- Reader schema 1.1 requires real input/output snapshots and replayable edits, evidenced closure across every cycle, complete section-level comprehension records, all core terms rechecked, and separate production/review execution records. See the reader-revision contract; strings naming different reviewers alone do not prove independent review.
- Workflow 1.9 requires at least three complete passes of the exact manuscript and two stable final passes with no new or open blocker. Each pass binds a real transcript and distinct execution record. Large cuts require issue-level revision rows, not one catch-all rewrite.

## G6 Publication

- Markdown image references resolve and no source-absolute paths leak into the package.
- Both reading edition and source-comparison edition are generated when source evidence permits.
- PDF fonts embed correctly; headings, TOC, page breaks, images, and Chinese/Japanese glyphs render.
- Where source glyphs are embedded, verify source/asset fidelity, actual PDF placement and the full copied sequence including surrounding text and repeated occurrences under [glyph fallback and acceptance](glyph-fallback-and-acceptance.md). Appearance and ID counts alone do not prove copy order. Disclose unsupported copying; do not hide guessed readings in the text layer. Record source preservation and complete recitation restorability separately.
- The quality report lists coverage, grade, models/tools, cost, unresolved items, and limitations.
- The declared release path is checked for locks before generation. A temporary PDF is validated before atomic replacement; a lock may block replacement but must not create a second ambiguous official release.
- Grade A requires zero active material items. Grade B rejects every active high-impact item. The quality report's candidate, adjudication, active-decision, and open counts must match the ledgers.
- For ordinary-reader editions, `editorial-report.json` must pass its contract and its high-impact count must match the adjudication ledger. Structural and visual success cannot upgrade a semantically blocked edition.
- The release includes the declared cover, copyright/credits page, author/editor/producer credits, clickable TOC, and PDF bookmarks.
- `release_filename` exists, matches the declared book title and edition label, and is the single unambiguous official PDF.
- Link targets and local assets are validated programmatically. Every ordinary-reader PDF page is inspected regardless of book length; other delivery modes declare their inspection scope.
- Candidate promotion runs both gates before replacing the official PDF. Book-specific outcomes and source-to-reader fidelity evidence are required; see [delivery-and-rework.md](delivery-and-rework.md).
- For ordinary-reader editions, the release manifest binds manuscript, publication Markdown, assets, PDF and page images; source fidelity and actual reader comprehension still require substantive review.
- Workflow 1.9 freezes validator hashes before semantic review. It requires page roles, page-specific layout findings, visible page numbers, TOC page labels, preserved list/glossary hierarchy and a sequential final-PDF reader review.

Record a user's version acceptance with their words, the agreed scope, timestamp, exact artifact hashes and disclosed limitations. Freeze accepted files and synchronize the project status; later changes need new evidence. A scoped trial acceptance is valid within its agreed scope but does not promote grades, close unresolved readings or satisfy missing formal-publication gates.

## Grade rule

Grade A requires all gates passed and no material unresolved item. Grade B allows bounded low/medium ledger items that do not undermine ordinary reading and permits no high-impact open item. Grade C covers drafts with material ambiguity, any active high-impact item, or an incomplete semantic/editorial contract. Grade D means the source cannot responsibly support the requested result.
