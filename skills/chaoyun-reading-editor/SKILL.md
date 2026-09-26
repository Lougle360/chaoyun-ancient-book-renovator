---
name: chaoyun-reading-editor
description: Edit an accepted modern Chinese rendering into a coherent contemporary reading edition with clear hierarchy, notes, terminology, figures, and reader aids. Use after faithful modernization; do not change source meaning, hide uncertainty, or mix newly authored explanations into translated source text.
---

# 超云今读编辑

Transform an accurate modern rendering into a book that contemporary readers can follow.

## Establish the edition

Record target reader, reading goal, reading level, modernization depth, annotation density, and whether the output is reading-only or source-comparison. If the user asks for ordinary people to read directly, optimize for interested non-specialists: retain necessary domain terminology, explain it on first occurrence, and do not assume prior training.

## Editing work

1. Preserve every source `block_id` in `50-edited/blocks.jsonl` while allowing display-level paragraph grouping with contributing IDs.
2. Build coherent book, volume, chapter, section, note, figure, and table hierarchy.
3. Improve sentence length, transitions, and paragraphing only within the accepted meaning.
4. Add a front-of-book reading map when the original structure is unfamiliar, and give each major chapter a concise introduction stating its question, key concepts, and reading route.
5. Create reader aids—first-use term notes, historical context, cross-references, examples, and practical observation checklists where appropriate—as explicitly labeled editorial content.
6. Keep figures and captions near the relevant passage. Maintain stable numbering and alt text, and explain what to inspect and in what order when the image is necessary to understand the text.
7. Attribute traditional causal, predictive, medical, or fortune claims as source/traditional views. Separate them from observable descriptions without deleting or endorsing them.
8. Move repetitive catalogues or case lists to clearly named reference sections only when this improves continuous reading; preserve source order and provenance.
9. Apply a terminology and name consistency pass, generate a complete glossary, then generate `50-edited/modern-reading.md`.

Use [references/editorial-policy.md](references/editorial-policy.md) for boundaries and labeling.

## Gate

Pass when the declared target reader can follow the book without specialist prerequisites, hierarchy and references are coherent, all content IDs are accounted for, and editorial additions are visibly distinct from translated source content. OCR corruption or missing evidence returns to reconstruction. Fluency never overrides semantic fidelity.
