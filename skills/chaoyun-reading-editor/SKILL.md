---
name: chaoyun-reading-editor
description: Edit an accepted modern Chinese rendering into a coherent contemporary reading edition with clear hierarchy, notes, terminology, figures, and reader aids. Use after faithful modernization; do not change source meaning, hide uncertainty, or mix newly authored explanations into translated source text.
---

# 超云今读编辑

Transform an accurate modern rendering into a book that contemporary readers can follow.

The reader, not the pipeline, is the organizing point of view. Every editorial action follows `增、删、改、整`: add what removes a real comprehension barrier, remove reader-hostile clutter from the continuous path without erasing source evidence, rewrite for natural modern understanding without changing meaning, and reorganize navigation while preserving recoverable source order.

## Establish the edition

For a selected-page “配图＋现代白话文／作者口吻” sample, use the controller's [illustrated reader sample route](../chaoyun-ancient-book-renovator/references/illustrated-reader-samples.md). Preserve source-bearing commentary and meaning, integrate necessary first-use explanations into prose, and keep correction records and illustration provenance in the evidence package. Do not add reader-visible audit notes, exercises, a formal introduction or a glossary merely to fill full-book fields. The full-book production and gate requirements below remain applicable when the requested scope is a book.

For full-book ordinary-reader production, use [design/sample/full-edition modes](../chaoyun-ancient-book-renovator/references/reader-production.md). Consume whole-book understanding before writing `50-edited/editorial-plan.md`: introduction narrative, chapter connections, prerequisites, first explanations, actual examples, figures and lookup material. Draft pending reader outcomes. Design precedes full translation; consult the translator on meaning.

Own the mandatory [whole-book illustration plan](../chaoyun-ancient-book-renovator/references/whole-book-illustration-plan.md) in design mode: write `50-edited/illustration-plan.md` after book understanding and before sample production. Use the source inventory and source-reconstructor/modernizer findings to decide chapter needs, figure coverage, visual conventions, precise versus generated content and representative trials. Record actual representative-page findings in `50-edited/sample/illustration-review.md`, using the sample's independent reviewer. Bind both files in production-plan schema `1.1` before scaling. No-illustration decisions still need source-based reasons, not manufactured decorative figures.

Make a real sample with introduction, connected prose, representative terms and a figure where applicable. Hand it to reader-experience-reviser sample mode before scaling. Use its accepted quality and explanation methods, not repeated sentence templates. Full-edition mode uses accepted translations and this plan.

Scripts may render authored prose, preserve source mapping and derive counts; they must not generate comprehension answers, reviewer identities or semantic success. Write a coherent introduction first, then index its coverage. Nine dimensions do not require nine short paragraphs. Glossary examples must actually explain a source passage or a labeled editorial illustration; a quote plus “understand in context” is unfinished work.

Assume AI-authored prose is the likeliest source of reader hostility. For every introduction, transition, glossary explanation, example, caption and reading instruction, identify the exact obstacle it solves and its source basis. If it only announces structure, praises the book, repeats nearby prose, exposes a data field, or replaces one unexplained term with another, rewrite it or leave it out. Preserve a richer guide/process edition when useful, but do not force that material into the final reader path.

Record target reader, reading goal, reading level, modernization depth, annotation density, and whether the output is reading-only or source-comparison. If the user asks for ordinary people to read directly, optimize for interested non-specialists: retain necessary domain terminology, explain it on first occurrence, and do not assume prior training.

## Editing work

For fixed wording, figure lettering and hard characters, apply [text/image and rare-glyph policy](../chaoyun-ancient-book-renovator/references/text-image-and-rare-glyph-policy.md). Keep original recitations in typeset body text and narration separate; keep form-bearing glyphs inside figures. Group symbols, original wording and procedural context only by evidenced links. Do not replace a full chant with its meaning, remove it as an editorial note, or rasterize the whole passage to hide unresolved glyphs. Preserve clear unidentified glyphs with faithful single-glyph insets when needed, and disclose real copy/search limitations. Check semantic details as well as block coverage.

For remaining unknowns, apply [glyph fallback and inline layout](../chaoyun-ancient-book-renovator/references/glyph-fallback-and-acceptance.md): retain true residual forms, use a consistent regional font size/baseline without stretching fragments, and keep surrounding words as body text. Carry stable glyph references and honest alt/copy fallbacks into Markdown and PDF; explain necessary uncertainty markers briefly in the reading path. Hand complete surrounding sequences to publication for copy-order checks, not just an image count.

1. Preserve every source `block_id` in `50-edited/blocks.jsonl` while allowing display-level paragraph grouping with contributing IDs. Maintain `50-edited/source-reader-map.jsonl`: exactly one row per source block, with its component, destination, reader heading and an exact reader quote or an explicit preserved non-reading destination. Hidden comments and aggregated anchors are not mapping evidence.
2. Build coherent book, volume, chapter, section, note, figure, and table hierarchy.
3. Improve sentence length, transitions, and paragraphing only within the accepted meaning.
4. Add a reading map or chapter introduction only where it resolves an actual reader obstacle. Keep full chapter-design reasoning in the process edition; do not mechanically print it in the final edition.
5. Create reader aids—first-use term notes, historical context, cross-references, examples, and practical observation checklists where appropriate—as explicitly labeled editorial content.
6. Keep figures and captions near the relevant passage. Maintain stable numbering and alt text, and explain what to inspect and in what order when the image is necessary to understand the text.
7. Attribute traditional causal, predictive, medical, or fortune claims as source/traditional views. Separate them from observable descriptions without deleting or endorsing them.
8. Move repetitive catalogues or case lists to clearly named reference sections only when this improves continuous reading; preserve source order and provenance.
9. Treat the book introduction as a substantive reader deliverable. Explain the surviving work, intended reader, reader value, contents and relationships, distinctive features, textual context, reading routes, limitations, and what this edition changed. A production note or generic praise is not an introduction.
10. Build a term inventory from this book, then write tiered glossary entries. Core terms require a plain definition, contextual definition, exact first source occurrence, usage example, related concepts, and common-confusion guidance. Do not publish one-line labels that send the reader back to the unexplained text.
11. Generate `50-edited/reader-aids.json`, then render `50-edited/modern-reading.md`. Derive `editorial-report.json` counts from the structured reader aids; never type success counts independently.
12. Assemble final cover/credits wording and all reader-facing sections before full-reader review. Maintain the book-specific `50-edited/delivery-contract.json` outcomes using the controller's `references/delivery-and-rework.md`. Preserve this complete information-rich draft as the process edition, then hand it to `$chaoyun-reader-experience-reviser` for the final-reader cut and full regression; do not certify it from the same production pass. A large cut requires issue-level revision rows with before/after evidence; one catch-all `rewrite` record cannot account for a book-scale deletion.

Use [references/editorial-policy.md](references/editorial-policy.md) for boundaries and labeling.
For full-book ordinary-reader production, read and enforce [references/reader-value-contract.md](references/reader-value-contract.md), then run:

```shell
python scripts/validate_reader_value.py book-workspace
```

## Gate

Pass this production stage when the introduction and glossary have verifiable book-specific evidence, hierarchy and references are coherent, all content IDs are accounted for, and editorial additions are visibly distinct from translated source content. Whole-book reader acceptance belongs to `$chaoyun-reader-experience-reviser`; OCR corruption or missing evidence returns to reconstruction. Fluency never overrides semantic fidelity.

For workflow 1.10, build and freeze [reader units](../chaoyun-ancient-book-renovator/references/reader-units.md) in design mode and produce their exact manuscript locations in full-edition mode. Both source text and old commentary become natural modern prose. Use visual hierarchy instead of repeated source-role labels. Chapter introductions and glossary fields are process evidence; print only prose that resolves an actual reader obstacle.
