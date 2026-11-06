---
name: chaoyun-reader-experience-reviser
description: Read a complete modernized book as an ordinary reader, diagnose whole-book comprehension failures, and apply traceable additions, removals from the reading path, rewrites, and reorganizations. Use after the first reading edition and again when a publication candidate needs reader-experience proofing; do not repair OCR or silently change source meaning.
---

# 超云全书读者审编

Read the book from cover to glossary as the declared reader, not as the pipeline that produced it. Separate the first audit pass from the revision pass so that editing does not hide the original reader problem.

Use the controller’s [execution protocol](../chaoyun-ancient-book-renovator/references/execution-control.md). Focused-v1 defaults to one actual complete stable independent final acceptance; unmarked legacy work retains three-full-pass/two-stable requirements. Do not add a mandatory diagnostic full read. Prepare/clean the manuscript first, diagnose observed risks, and deliver answers, findings, transcript and bindings together. Changed manuscript bytes still need fresh full acceptance. Formal focused publication checks actual full coverage automatically; local/hash-only checks never satisfy it.

## Modes

- **Sample mode:** follow [the production contract](../chaoyun-ancient-book-renovator/references/reader-production.md) before full production. Obtain actual unaided answers in a separate invocation before source comparison. Method failures return to understanding/design. Sample acceptance does not certify the book.

- **Manuscript mode:** independently inspect the complete manuscript, preserve understanding and obstacles, and return edits to their producer. This may supply final acceptance when the already-clean frozen manuscript needs no change.
- **Final-reader mode:** accept the compact final output with complete meaningful-unit coverage and actual reading evidence. Preserve process snapshot and final-cut checks; focused-v1 does not require another independent full read solely because manuscript mode is renamed final-reader mode.
- **Proof mode:** run on the publication candidate when pagination, figure placement, navigation, or rendered context may change the reading experience. Return content defects to manuscript mode and visual defects to `$chaoyun-quality-publisher`.

## Workflow

1. Prepare the clean candidate and immutable input snapshot. In actual full acceptance, finish reading and record answers before editing or seeing source answers. Check introduction promises, prerequisites, navigation, continuity, terminology, examples, figures, repetition, source/editor distinction and closure. Targeted pre-freeze diagnosis inspects its declared scope and cannot be labeled full acceptance.
2. Record every obstacle in `50-edited/reader-review.json`. A statement such as “reads well” is not evidence; identify where the reader stops, guesses, backtracks, or loses the argument.
3. Create append-only `50-edited/reader-revision-ledger.jsonl` records using exactly one operation:
   - `add`: supply evidence-based context, explanation, example, transition, route, or caution.
   - `delete_from_reading_path`: remove repetition or pipeline clutter from continuous reading while preserving source material and a destination or provenance reference.
   - `rewrite`: clarify archaic syntax, vague reference, overloaded sentences, or terminology without changing accepted meaning.
   - `reorganize`: improve sequence, hierarchy, cross-reference, or figure placement while retaining a recoverable source order.
4. Route OCR, missing-source, translation, attribution, or meaning uncertainty back to the responsible Skill and create an uncertainty candidate. Do not solve an evidence problem through fluent editing.
5. Apply accepted revisions to the reading layer, update `reader-aids.json` when the introduction or glossary changes, and preserve contributing `block_id` values.
6. Preserve the reviewed information-rich input as an immutable process snapshot. Make the final-reader cut without deleting source-bearing content: remove or move guide fields, internal reports, repeated scaffolding and AI prose that solves no demonstrated reader obstacle. Audit introductions, transitions, term explanations, examples, captions and figure notes for plain language, source basis and reading burden.
7. Complete the locked protocol: focused-v1 defaults to one complete stable full read of the exact final manuscript; unmarked legacy work retains three complete passes and two stable final passes. Bind real current full-pass evidence to manuscript, policy lock, actual producer/reviewer executions and transcript, with full_read mode and complete line coverage. Preserve actual unit/task answers and core-term checks; scripts cannot create answers or verdicts. Produce reader-acceptance 1.2 and final_reader_cut from actual final evidence.
8. Run `scripts/validate_reader_revision.py <workspace>`. Publication remains blocked until it passes.

Read [references/reader-revision-contract.md](references/reader-revision-contract.md) before creating review or revision records.

Do not mechanically add a preface, summary, example or correction to every section. A zero-edit cycle may pass with complete real evidence, and an unchanged valid full read is reusable. Extra full reads need changed final bytes, a concrete defect or stricter locked policy. Stop after two no-progress cycles on the same blocker or an authorized budget limit; preserve the draft and exact missing evidence.

## Boundaries

- Apply [text/image and rare-glyph policy](../chaoyun-ancient-book-renovator/references/text-image-and-rare-glyph-policy.md) when fixed originals or symbols occur. Do not remove a chant as untranslated clutter, merge its narration into the quoted words, or rewrite its repeated words for fluency. Test whether readers can distinguish original wording, explanation, symbol and action order. A clear unidentified glyph is not a blank; return glyph questions to reconstruction/adjudication.
- For [glyph fallbacks](../chaoyun-ancient-book-renovator/references/glyph-fallback-and-acceptance.md), test whether readers recognize original shapes, residual fragments and editorial gap markers without mistaking them for complete restored words. Judge ordinary comprehension and the ability to reproduce the entire recitation separately; preservation alone does not establish pronunciation. Report actual copying limitations where they affect use.
- Do not edit `20-source`, repair unreadable glyphs, or turn an uncertain translation into a confident sentence.
- Do not delete source-bearing material merely because it is difficult. Move it to a labeled reference path when continuous reading benefits, and keep provenance.
- Do not add generic background, decorative examples, or praise that answers no reader problem.
- Do not let the same pass both create and certify its own revision. The final regression reviewer differs from the revision producer.

## Gate

Pass when all required reading dimensions have evidence-based regression verdicts, every applied change replays exactly between frozen snapshots, no unresolved reader issue remains from any cycle, the acceptance hash and section evidence match the final manuscript, and medium/high semantic-risk changes have active evidence-backed confirmation in the unified uncertainty lifecycle. Deterministic validation cannot certify that a reader truly understands; report that limit and retain the actual comprehension review.

For workflow 1.10, use [reading-unit checks](../chaoyun-ancient-book-renovator/references/reader-units.md). Full acceptance tests chapter meaning, commentary ownership, continued sentences, first-use concepts and unnecessary AI prose. Preserve answers and failures; source/structure failures return upstream. Follow the explicit protocol rather than assuming all books use the legacy three/two schedule.
