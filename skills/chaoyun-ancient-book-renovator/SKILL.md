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

## Text correctness before acceptance

For G3.5 proofs, and whenever feedback reports wrong, unrecognized or semantically incoherent text, require [字形、校读与语义复核](references/text-semantics-review.md). Inspect every text region in the declared scope, not only OCR-flagged words. Separate visible source glyphs, evidence-backed reading corrections and contextual meaning. Protect domain terms during script conversion; restore cross-column/page reading before interpretation. A legible source typo stays in the evidence layer, and restoring a glyph does not resolve its uncertain meaning. Review the actual corrected PDF in a separate execution, with substantive findings bound to the current text, PDF and unified uncertainty ledger. New G3.5 acceptance uses proof schema 1.1; a high-impact unresolved meaning blocks acceptance. Do not silently upgrade historical sample approvals.

## Editorial truth before packaging

For fixed recitations, talismans, form-bearing lettering, rare glyphs, or feedback that important original words were lost, apply [原文、白话、图像与生僻字处理](references/text-image-and-rare-glyph-policy.md). Classify function before script conversion: modernize explanations, retain fixed original wording as body text with separate narration, and preserve form-bearing glyphs within figures. Record source-supported figure/recitation/action relations during reconstruction and reading design; adjacency alone is not a pairing. Distinguish unknown readings, missing font coverage and genuinely damaged characters; keep legible unidentified glyphs rather than replacing them with blanks. This policy supplements workflow 1.10 without changing schemas or accepting historical books.

When evidence still cannot establish a character or recitation, follow [原字保形、残形与缺损兜底](references/glyph-fallback-and-acceptance.md). Preserve actual shapes and surviving fragments inline, distinguish missing spans, and verify copy order as well as appearance. Report source preservation and complete recitation restorability separately. Bind user acceptance to the agreed version and scope without closing unresolved readings or promoting a trial to formal publication.

For a full ordinary-reader edition, introduction, table of contents, glossary, and figure guidance are semantic deliverables. Design them from whole-book understanding before bulk translation; complete their prose against accepted translations. Read [references/reader-production.md](references/reader-production.md) for workflow 1.8 ownership, sample-first handoffs, actual reading sessions, and final-reader cut. It retains the 1.6 uncertainty requirements; share the representative chapter rather than producing two separate pilots. For a selected-page illustration sample, use the bounded route below; do not force whole-book front matter or glossary fields into a few-page sample.

Treat AI-authored material as a high-risk editorial layer, not harmless packaging. Every introduction, transition, term explanation, example, caption, and reading instruction must remove a specific reader obstacle, use plain language, and identify its source basis or editorial status. Correct but empty prose, field-shaped introductions, circular definitions, generic praise, repeated summaries, and internal workflow language fail the reader gate.

Organize the reading layer from the reader's point of view using `增、删、改、整`: add only what resolves a comprehension barrier, remove clutter from the continuous path without deleting source evidence, rewrite into natural modern Chinese without changing accepted meaning, and reorganize navigation while preserving source order separately.

- The introduction must state what kind of surviving book this is, distinguish title attribution from demonstrated authorship, and disclose compilation or layering when the evidence shows it.
- Reconstruct the source hierarchy from printed contents pages, running titles,卷次,篇名, and physical-page evidence. Never infer printed page numbers from PDF offsets without a verified mapping.
- Preserve a source-faithful contents view separately from editor-created reading guidance. Label every editor-created introduction or regrouping.
- Build the glossary from terms actually used in this book. Record the first source occurrence and give the contextual meaning; mark opaque terms instead of filling them with generic domain definitions.
- Do not accept a one-line label as a sufficient explanation of a core term. Require plain meaning, book-specific use, an exact source occurrence, an example, related concepts, and likely beginner confusion.
- Give each content-bearing figure a specific reading route. A repeated generic caption is not figure guidance.
- Do not allow model verdicts, repair queues, candidate text, pipeline states, or internal validation language into the reader layer.

For full-book ordinary-reader work, write `50-edited/editorial-report.json` using [references/editorial-evidence-contract.md](references/editorial-evidence-contract.md). The report is auditable evidence for these decisions; it does not replace human semantic review.

## Illustrated reader samples and project reports

For full-book ordinary-reader work, complete the mandatory [whole-book illustration plan](references/whole-book-illustration-plan.md) in `reader_designed`, after whole-book understanding and before sample production. Save `50-edited/illustration-plan.md`; validate representative figure types in actual sample pages and save `50-edited/sample/illustration-review.md`. New production plans use schema `1.1` and bind both files before bulk work. Books needing no illustrations document that decision instead of generating filler. Standalone selected-page samples retain their bounded route.

When the user asks for “配图＋现代白话文”, “作者口吻”, “不需要批注”, or a new sample following that accepted direction, read [references/illustrated-reader-samples.md](references/illustrated-reader-samples.md). Treat this as a reading profile within `ordinary_reader`, not a new workflow schema or automatic acceptance grade.

- Express the source's ideas directly in natural modern Chinese. Preserve conditions, distinctions and source attribution at an appropriate edition level; keep production notes and collation out of the continuous reading path. Source commentary carrying meaning is still content.
- Use generated illustrations for natural forms and concepts; control exact numbers, labels, directions, connections and symbols separately. Verify the actual PDF, not only rendering inputs. Reuse suitable assets with provenance and fresh in-context review.
- A selected-page sample keeps source, manuscript, mappings, declared omissions, artwork and independent review in an isolated package. Its conclusion binds only the reviewed scope and bytes. It neither requires fictitious whole-book records nor bypasses any previously required source/layout review or full-book gate.
- “缺乏的先跳过” applies only when authorized in the current context: record the precise omitted portions and their effect on completeness. An unresolved central meaning cannot be hidden behind a fluent, apparently complete account.

For an iteration report or an explicitly requested cloud publication, read [references/iteration-report-and-feishu.md](references/iteration-report-and-feishu.md). Report actual versions and corrections; use an installed Feishu CLI when requested/available, upload local images, then read back content and resources. Writing a report or updating this Skill does not itself authorize publishing, sending messages, or changing sharing permissions.

## Define the edition before processing

Choose and record one primary delivery mode before bulk work begins:

- **Evidence archive:** optimized for faithful recovery, provenance, and later research.
- **Source-comparison edition:** source text and modern text remain visibly paired.
- **Ordinary-reader modern edition:** a complete contemporary book that a non-specialist can read directly.

When the user asks for “普通人可以直接阅读” or equivalent, use the ordinary-reader modern edition. Do not substitute OCR text, a source comparison, or a lightly punctuated transcript for that deliverable. Read [references/modern-reading-edition.md](references/modern-reading-edition.md) and [references/delivery-and-rework.md](references/delivery-and-rework.md). Record explicit `delivery_mode`, `target_reader`, `edition_label`, and `release_filename` in `book.json`; display wording never selects a gate.

Workflow 1.9 also requires `10-diagnosis/edition-scope.json` before production. Inventory main text, commentary, prefaces, figures, tables and paratext as source components. For a complete ordinary-reader white-language edition, main text, commentary and prefaces remain required in the reader release unless the user explicitly authorizes a named exclusion. Preserve the user's actual words and time of that decision. A producer may not redefine a difficult component as “process only”, “core text only” or “supplement” to obtain a pass.

## Run the suite — book production

1. Establish the input PDF, output root, delivery mode, intended reader, modernization depth, and whether paid model calls are authorized. Preserve the source PDF. Record the physical PDF page count and classify every page as included content, front/back matter, blank/noncontent, excluded with reason, or unreadable.
2. Initialize a new isolated workspace:

   ```shell
   python scripts/init_workspace.py input.pdf output-directory --edition-label 现代白话版 --target-reader 现代普通读者
   ```

3. Use `$chaoyun-pdf-diagnoser` to create the book profile and page-level route map. Read [references/routing.md](references/routing.md) when layouts or languages are mixed. Before scaling the route to the full book, take a representative real chapter through reconstruction, modernization, reader editing and the complete uncertainty loop. Preserve trial snapshots and actual blind-review results, cost and time in `90-audit/pilot-review.json`; require the uncertainty Skill's `--pilot` gate. A trial is not full-book acceptance and does not authorize additional paid scope.
4. Use `$chaoyun-source-reconstructor` to create the faithful source Markdown and page/block records. Run `validate_workspace.py WORKSPACE --stage source` immediately; workflow 1.9 checks structural roles, real block coordinates, reading order and edition-scope components here, not only at publication. Do not proceed if source coverage or reading order fails its gate.
5. Run `$chaoyun-uncertainty-adjudicator` at the source-reconstruction checkpoint. Discovery → registration → assignment → evidence → decision → actual correction → impact review → separate fidelity/reader review → closure or retention is mandatory. It is one unified lifecycle, not fixed first/second lists. Preserve stable candidate and reopened issue identities; closed duplicates must follow their canonical issue.
6. Use `$chaoyun-text-normalizer` for script conversion, variant-character policy, punctuation, and segmentation. This stage must not paraphrase. For an original-layout reconstruction or a Chinese scan with complex diagrams/columns, require **G3.5 原版式简体校订 PDF 审核** under [references/layout-proof-review.md](references/layout-proof-review.md). Produce a separately versioned, source-paired PDF after normalization and before scaling the method. Register `book.json.layout_proof_review` and review actual rendered pages; a generated PDF or a successful mechanical check does not approve it. A representative sample approves only the method and those pages.
7. For ordinary readers, invoke `$chaoyun-classical-modernizer` understanding mode and `$chaoyun-reading-editor` design mode. Finish the whole-book illustration plan during design, including source-figure coverage, chapter needs, visual conventions and representative trials. Then translate/edit a representative sample and use `$chaoyun-reader-experience-reviser` sample mode with an actual separate reviewer; integrate figure verification into that sample and retain its illustration-review record. Do not give the reviewer expected answers. Resolve method-level obstacles and validate production-plan schema 1.1 bindings before bulk work. Other delivery modes skip reader-specific prerequisites.
8. Complete full translation using the settled context and term meanings, routing mixed languages separately. Use reading-editor full-edition mode for the entire book, including final credits, introduction, original preface, body, guidance, glossary and appendices. Label additions and retain source identities. Preserve this information-rich guide/process manuscript as an immutable process edition; it is useful evidence, not automatically the reader release.
9. Reader-experience-reviser performs actual full-manuscript review, necessary correction and regression reading. Then make the final-reader cut: remove or move guide fields, audit language, redundant explanation and other non-reading matter without deleting source-bearing content; preserve the process edition and a traceable finalization record. Re-read the exact final reader manuscript chapter by chapter. Preserve substantive answers and source comparisons. Systematic failure returns to understanding/design; repeated patch-and-certify cycles are not the normal production method.
10. Run `$chaoyun-uncertainty-adjudicator` at every checkpoint that generated new OCR, translation, terminology, structural, reader-edit, or proof concerns. There is no fixed cycle count, subject to budget/no-progress stops. Preserve complete candidate/decision history. Before publication, independently check every active adjudication against the final manuscript, write `uncertainty-release-review.json`, and run `--check --publication`. The reader-facing ledger contains only current `open_material` decisions; an empty projection never substitutes for closure evidence.
11. Before semantic review begins, run `scripts/lock_acceptance_policy.py WORKSPACE`. The lock binds the edition scope and validator hashes. Any later change to scope or acceptance code invalidates downstream approval and requires a fresh lock plus fresh review. Freeze the complete accepted manuscript and complete the independent source-to-reader fidelity review. Use `$chaoyun-quality-publisher` to render a separate candidate, inspect every ordinary-reader PDF page and navigation target, and run both candidate gates. Only the guarded installer may then back up and atomically replace the official PDF. Do not add new prose after acceptance without returning it for review.
12. Run the deterministic contract validator:

   ```shell
   python scripts/validate_workspace.py output-directory --stage publication
   ```

13. Report the achieved grade, source-page accounting, reader-facing PDF page count, uncertainty cycles, raw candidate count, adjudicated count, material unresolved count, reader revision count, and the single official release path. Never call a run complete merely because files exist.

For scan-heavy books, do not publish a full-book reading edition until every included source page has page-level visual evidence or an explicit `unreadable` / `noncontent` disposition. Text-only judging against inherited OCR is not an independent semantic check. The contract validator and publication auditor must both exit successfully; a hand-written `passed_with_ledger` state cannot override either failure.

## State and stopping rules

Workflow schema 1.6 adds evidence-bound doubt closure, canonical duplicate dependency, exact correction replay, six-scope impact checks, separate review execution, a representative chapter-trial gate and final-manuscript uncertainty recheck. It retains 1.5 delivery modes, content/fidelity bindings and guarded candidate promotion. Read the uncertainty, delivery/rework, reader-revision and publication contracts when upgrading a legacy workspace. Preserve old acceptance as history and perform fresh review; changing version numbers cannot upgrade a pass. Mechanical checks verify evidence integrity and recorded review, not semantic truth or that every possible doubt was found.

- Workflow 1.7 adds ordinary-reader stages `book_understood`, `reader_designed`, `sample_accepted` after `normalized` and before full `modernized`; the remaining stages are `edited`, `reader_revised`, `final_adjudicated`, `publication`, with existing intake/source stages unchanged. Reader acceptance is schema 1.2. Sample translation is allowed before full modernization. These additions retain all 1.6 uncertainty closure and trial requirements.
- Workflow 1.8 keeps those stages and adds a required dual-artifact finalization inside `reader_revised`: preserve the guide/process manuscript, derive a clean `compact_final_reader` manuscript, record the final-reader cut, and bind the final regression session to that exact output. A legacy 1.7 workspace may use the 1.8 contract only after fresh evidence is created; changing the version field alone grants nothing.
- Workflow 1.9 adds a locked edition-scope inventory, structural source roles, `source-reader-map.jsonl`, a frozen acceptance-policy hash, three or more complete reader passes with two stable final passes, and sequential PDF-reader evidence. Existing 1.8 approval is historical evidence only; it cannot be promoted by changing the version field.
- A later stage may start only after the preceding gate is `passed` or explicitly `passed_with_ledger`.
- Use append-only audit records and preserve stage outputs; do not rewrite earlier evidence in place.
- Support resume from the last completed stage. A retry must not duplicate accepted records.
- Migration and rebuild scripts must be idempotent. Read from an immutable source ledger, never from the projection they overwrite. Before accepting a migration, run it twice or verify that the second run refuses safely and leaves hashes/counts unchanged.
- Before a paid full-book run, estimate pages/cost and obtain authorization. A representative sample is not authorization for the full corpus.
- Keep samples and full-book artifacts in visibly different paths and filenames. A sample may validate routing and quality, but it is never proof that the complete book was converted. Never label a partial, C-grade, or validation-failing artifact as `完整版`, `final`, or publication-ready.
- Keep uncertainty candidates, adjudications, and reader-facing open items distinct. A resolved stamp, variant character, cross-page continuation, semantic comment, or duplicate must remain traceable in history but must not inflate the published uncertainty count.
- Stop on corrupt/encrypted input, missing pages, materially ambiguous reading order, systematic language misclassification, or budget exhaustion. Record the exact blocker.
- Stop a revision loop after two consecutive cycles on the same blockers with no new evidence or meaningful progress. Report the missing input and preserve the draft, rather than consuming unlimited budget or calling the loop successful.

## Completion grades

- **A — publication-ready:** all gates pass, all content blocks are accounted for, and no active material uncertainty remains.
- **B — readable with ledger:** the edition is usable, with bounded uncertainties fully listed and linked to source evidence, and no active high-impact item.
- **C — assisted draft:** substantial uncertainties or layout/translation risks remain; do not present as publication-ready.
- **D — unrecoverable:** source evidence is insufficient for a responsible conversion.

Use [references/data-contract.md](references/data-contract.md) for files and record fields. Use [references/quality-gates.md](references/quality-gates.md) before advancing a stage or declaring completion.

Workflow 1.10 requires [reading units](references/reader-units.md) before bulk modernization and binds them again at publication. Read that contract for ordinary-reader work. Keep the existing 1.9 fidelity, scope, uncertainty, reader and PDF gates. The added state reader_units_built sits after reader_designed and before sample_accepted. Establish commentary scope from evidence; passage, chapter, book, nested notes and source lacunae have different handling. Never force a note onto an invented passage. Complete meaningful pages/chapters per work session, save resumable evidence, and continue available work after status updates; only report verified progress or a real blocker.
