---
name: chaoyun-ancient-book-renovator
description: Renovate complex book PDFs into traceable modern Chinese Markdown and reader-facing PDFs, with faithful source reconstruction, figure restoration and independent content and publication review. Use for scanned, classical, vertical, annotated or mixed-layout books; not simple text extraction.
metadata:
  version: "1.11.0"
  workflow-schema: "1.10"
  review-protocol: "focused-v1"
---

# 超云古书翻新

Produce a complete, understandable edition with preserved source evidence. New ordinary-reader work uses workflow **1.10** with the explicitly locked **focused-v1** review protocol. It replaces the fixed three-full-read/two-stable schedule with one complete independent final-manuscript acceptance plus source fidelity and final-PDF inspection. Read [execution-control.md](references/execution-control.md) for the exact contract, reuse and legacy boundary.

## Essential quality boundaries

- Keep original PDFs, page images/crops, source text, coordinates and uncertainty immutable. Every source-bearing block has a traceable destination; never silently drop difficult commentary or invent missing text.
- Set delivery_mode explicitly: ordinary_reader, source_comparison or evidence_archive. Modern ebook requests default to a continuous modern-Chinese reader edition with usable explanations and figures.
- Content figures require [source-figure-restoration.md](references/source-figure-restoration.md). Never enlarge OCR thumbnails into final figures, call cropping/contrast alone restoration, or overwrite originals. Numbers, directions, dots, trigrams, labels and connections use deterministic drawing. Retain real glyph shapes/residual strokes without generative guessed strokes. Inspect every final figure in its actual PDF.
- Fixed recitations retain original wording as body text with separate explanation; form-bearing lettering stays in figures. Unknown identity, sound, meaning, font coverage and source damage are separate findings. User acceptance of preservation does not close an unresolved reading or raise its grade.
- Production cannot approve itself. Preserve actual reader answers before comparison with source or expected conclusions. Scripts may calculate bindings and aggregate real findings; they may not generate comprehension answers, reviewer identities or passing judgments.

## Five production stages

### 1. Diagnose and establish reliable source

Record exact book/input identity, physical page accounting, edition mode, target reader and official filename. Resume from the first unmet requirement, reusing dependency-valid evidence; do not recreate diagnosis, understanding or samples solely because a chat restarted.

For a new isolated workspace, use scripts/init_workspace.py with the requested edition label and target reader. It initializes focused-v1 only for ordinary_reader. Do not convert an existing book by changing a version string.

Use $chaoyun-pdf-diagnoser, $chaoyun-source-reconstructor and $chaoyun-text-normalizer as successive responsibilities; these are not three mandatory agents. Account for every page/block, real structural roles, reading order, complete tables and figures. Validate the source stage immediately. Preserve character/punctuation changes without paraphrasing at the normalization layer.

Lock edition-scope.json and the actual review policy before the first semantic review with scripts/lock_acceptance_policy.py. Diagnose and record book.layout_proof_applicability = {required: boolean, reason: source-grounded explanation}; never invent a not-applicable reason. Original-layout reconstruction and complex Chinese columns/diagrams require [G3.5 source-paired proof](references/layout-proof-review.md) and [text/semantics review](references/text-semantics-review.md). Use representative page families before scaling; produce a complete intermediate edition only when its declared delivery scope requires one. Sample approval never stands for whole-book source coverage.

Use $chaoyun-uncertainty-adjudicator for real candidates, located evidence, replayable corrections, independent closure checks and retained material-open items. Reuse stable IDs and canonical duplicate relationships; do not manufacture doubts or redo valid decisions to fill a form.

### 2. Design the book and prove one representative sample

$chaoyun-classical-modernizer understands the whole reliable source; $chaoyun-reading-editor designs chapter relationships, reading units, prerequisite explanations, terminology, source destinations and figure routes. These responsibilities may be delivered in one production assignment, with the required artifacts derived from the same evidence.

Use [reader-production](references/reader-production.md), [reader-units](references/reader-units.md) and the [illustration plan](references/whole-book-illustration-plan.md). Preserve source hierarchy separately from editorial organization; verify printed page numbers rather than infer an offset.

Carry one shared representative chapter through source/uncertainty, modernization, figure and layout trials. Use a separate sample-reader execution without answer keys; retain real responses and assessments. Keep distinct conclusions in their required records, but do not duplicate the trial. Expand only for uncovered risks or demonstrated method failure. A justified no-illustration finding is valid.

Before bulk work, resolve method-level blockers and validate reviewed reading units, production-plan schema 1.1, representative figure review where applicable and the uncertainty --pilot gate. A standalone selected-page request instead follows [illustrated-reader-samples](references/illustrated-reader-samples.md); it does not need fictitious whole-book approval.

### 3. Produce chapters, edit once and prepare final inputs

Translate and edit complete chapters or adjacent reading units. One producer may perform both roles in sequence; retain meaning and evidence boundaries. Separate workers only for independent regions or required independent review, never concurrent writes to the canonical manuscript/ledger.

Complete all reader text together: title/credits, introduction, original preface, body, tables, notes, captions, glossary and appendices. Restore/redraw required figures from the canonical inventory. Use concrete book-specific explanations and preserve uncertain meaning. Keep an immutable information-rich process snapshot, then derive the clean compact_final_reader manuscript with traceable additions, removals from the reading path, rewrites and reorganizations. A clean manuscript may need no artificial revision.

Before semantic acceptance, run scripts/preflight_review.py WORKSPACE --through edited. Fix the collected relevant errors together; not_yet is not a pass. Trial fonts, source anchors, credits, glossary emphasis, asset routing, navigation and representative layout before text freeze. Keep execution notes and future status changes outside the manuscript. Reuse unchanged preflight evidence; rerun when its inputs/dependencies change.

There is no compulsory extra whole-book diagnostic reader pass. Use targeted diagnosis only where production or the sample revealed risk. Batch-repair those problems, check their dependencies and freeze manuscript bytes, mappings and assets.

### 4. Accept the frozen book by purpose

Require independent **source-to-reader fidelity** and **whole-book reader comprehension**. Fidelity covers source blocks, conditions, negations, quantities, terminology, tables and actual figures. The reader explains meaningful contiguous units, core concepts and figure reading using real tasks without answer keys. Both cover the complete applicable scope; sampled fidelity or a local regression cannot stand for full acceptance.

For focused-v1, one complete independent full read of the exact final manuscript, with no new/open blocker, satisfies the default reader-pass count. Do not add second/third full reads merely for a quota or rename diagnosis as another task. A diagnostic full read may count only if the exact final inputs and all required evidence already match. Compatible checks can share an assignment and artifacts, but preserve blind reader answers before source comparison, separate conclusions and independence from production.

On a defect, repair the affected text and connected terms/figures; return systematic source/meaning failures upstream. Before final freeze, use targeted regression instead of another diagnostic whole-book run. If the accepted manuscript bytes change, its acceptance is stale: the corrected final manuscript still requires one real complete acceptance, never a refreshed old hash or a local check labeled full_read. Extra full reading requires a concrete failure/changed input or a genuinely stricter locked policy.

Reviewers deliver answers, findings, execution provenance, full line coverage and bindings together. Current full passes declare full_read and distinct actual producer/reviewer executions. Focused-v1 coverage checks run automatically inside both publication gates; preflight --final-pass-set remains available for early diagnosis, not an additional mandatory approval.

Independently recheck active uncertainty decisions against the frozen output, preserve material-open disclosure, and complete the reader-acceptance 1.2, final-reader-cut and fidelity records from the same valid evidence. One source review may also provide the applicable uncertainty evidence; do not pay for identical source comparison twice.

### 5. Inspect and install the actual PDF

Use $chaoyun-quality-publisher and the PDF Skill with the settled layout. Render a separate candidate, not the official path. Inspect every final page sequentially and every content figure; combine visual, continuity, font, copy/search order, page labels, TOC/bookmarks and link observations in one actual PDF-review assignment. Reuse the observations in the required records instead of scheduling separate full PDF reads per form.

Renderer-only fixes preserve byte-identical manuscript acceptance; the changed final PDF still needs its own complete proof. Source-comparison supplements remain separate when evidence supports them.

Use the guarded installer after actual review. It runs the workspace publication validator and publication auditor against the candidate, then atomically replaces the one declared official PDF. Do not manually run the identical full gate chain immediately beforehand unless diagnosing a failure. Preserve source, previous releases and failed evidence; update book state, batch index and measured cost from actual results.

## References on demand

| Need | Read |
|---|---|
| Stage records, field details and gates | [data-contract](references/data-contract.md), [quality-gates](references/quality-gates.md), [delivery-and-rework](references/delivery-and-rework.md) |
| Reader edition and editorial evidence | [modern-reading-edition](references/modern-reading-edition.md), [editorial evidence](references/editorial-evidence-contract.md) |
| Mixed layouts/languages, protected text or rare glyphs | [routing](references/routing.md), [text/image policy](references/text-image-and-rare-glyph-policy.md), [glyph fallback](references/glyph-fallback-and-acceptance.md) |
| Explicitly requested iteration report or cloud publication | [iteration-report-and-feishu](references/iteration-report-and-feishu.md); local production does not authorize external publication |

## Cost, stopping and truthful completion

Measure book-scoped usage at batch boundaries and before another semantic review/candidate build using scripts/measure_run_cost.py. Use the existing authorized budget; missing logs are unknown, not zero. If no hard limit exists, use measured sample cost for a labeled planning estimate, not a promised time or saving. A role does not need a persistent agent, and a new task does not need unrelated books' history.

Stop the affected route after two cycles on the same blocker without new evidence/progress, or at an explicit budget limit. Continue only independent authorized work that can progress. Routine progress updates do not end the authorized job or require repeated permission.

Integrity, fidelity, comprehension and final-PDF requirements remain substantive gates. A = all required gates passed, no material uncertainty; B = passed with bounded low/medium limitations, no high-impact item; C = assisted draft/incomplete gates; D = inadequate evidence. A sample, test suite or user-scoped acceptance is not whole-book publication. Report exact book/version, source/reader page counts, actual review types, remaining limitations, measured usage scope and one official path.
