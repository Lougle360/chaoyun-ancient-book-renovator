---
name: chaoyun-text-normalizer
description: Normalize faithful historical text for modern reading through script conversion, variant-character handling, punctuation, segmentation, and terminology consistency with a complete change ledger. Use after source reconstruction; do not translate classical Chinese or Japanese, paraphrase meaning, or overwrite the faithful source layer.
---

# 超云古字通

Make the source legible at the character and sentence-boundary level while keeping meaning unchanged.

## Workflow

1. Read `20-source/blocks.jsonl`; preserve every `block_id` and `source_text`.
2. Select a declared target script, normally simplified Chinese for explanatory prose. Before conversion, classify protected spans under [text/image and rare-glyph policy](../chaoyun-ancient-book-renovator/references/text-image-and-rare-glyph-policy.md): fixed recitations retain original forms, and form-bearing figure lettering retains glyphs and placement. Preserve names and technical forms according to the project terminology file.
3. Apply script conversion only to eligible spans; pass protected originals through without script or variant replacement. Log verified variant mapping, punctuation, whitespace normalization, and conservative segmentation as distinct operations.
4. Write `30-normalized/blocks.jsonl`, `30-normalized/normalized.md`, and one `30-normalized/changes.jsonl` record per material change.
5. Review names, dates, quantities, citations, formulas, titles, and rare domain terms more strictly than ordinary prose.
6. For original-layout Chinese proofs, include eligible explanatory figure titles and labels in script conversion; explicitly exempt protected fixed wording and form-bearing talisman/inscription glyphs. Do not equate every in-image character with a replaceable label. Correct OCR by phrase and context with source or parallel-text evidence: e.g. a supported `伏义→伏羲` name correction is not a global `义→羲` substitution. Log before/after, location, basis and uncertainty; preserve raw OCR/source evidence. Hand the corrected text and ledger to [G3.5 原版式简体校订 PDF 审核](../chaoyun-ancient-book-renovator/references/layout-proof-review.md). Uncertain text stays marked rather than guessed.

Read [references/normalization-policy.md](references/normalization-policy.md) before handling variants, Japanese forms, or uncertain punctuation.

For unresolved source shapes, follow [glyph fallback](../chaoyun-ancient-book-renovator/references/glyph-fallback-and-acceptance.md). Carry stable glyph IDs, true residual forms and source-backed gap boundaries through normalization. Do not assign a guessed codepoint, replace surviving strokes with □, or treat a known character's unknown recitation sound as a missing character. Record any supported mapping change without discarding the original shape or uncertainty history.

For G3.5 or feedback about wrong meaning, also require [text/semantics review](../chaoyun-ancient-book-renovator/references/text-semantics-review.md). Protect contextual terms before conversion and inspect the converted occurrences afterwards (乾 as a trigram is not 干; this does not forbid 乾燥→干燥). Reconnect cross-column/page phrases before punctuation. Do not treat a source typo as an OCR error: keep the source glyph, log evidence-backed reading emendation separately, and retain unresolved meaning even after a glyph correction. Check every region, not only low-confidence OCR. Final acceptance needs a separate review of the actual normalized text and rendered PDF.

## Boundaries

- Traditional-to-simplified conversion is orthographic normalization, not translation.
- Classical Chinese-to-modern Chinese belongs to `$chaoyun-classical-modernizer`.
- Japanese kanji must not be converted through a Chinese dictionary before language routing.
- Do not silently replace a source error with the expected phrase. Record an editorial note or uncertainty instead.
- Preserve an unambiguous link from normalized text to the exact source string and operation list.

## Gate

Pass only when block identity and coverage match the source stage, every material change is logged, and no semantic paraphrase has entered normalized text.
