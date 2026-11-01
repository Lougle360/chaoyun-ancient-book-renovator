# Normalization policy

Classify each operation as `script_conversion`, `variant_mapping`, `punctuation`, `segmentation`, `whitespace`, `terminology`, or `editorial_exception`.

Each change record contains `block_id`, source span, before, after, operation, rule or evidence, confidence, and reviewer state.

## Safe defaults

- Apply [functional text/image classification](../../chaoyun-ancient-book-renovator/references/text-image-and-rare-glyph-policy.md) before t2s or variant mapping. Preserve fixed recitation strings and form-bearing lettering in the reading layer as well as the source layer; the general simplified-text default does not override these protected spans. Mixed paragraphs require span-level decisions.
- Convert common traditional characters only when the target word and domain meaning are unambiguous.
- Keep rare names, place names, book titles, calendrical terms, technical glyphs, and variant forms until a terminology decision exists.
- Add punctuation conservatively. When punctuation materially changes parsing, keep alternatives in the ledger.
- Japanese old/new character conversion occurs only inside text already classified as Japanese and follows a Japanese route.
- Preserve original quotations in the source layer even when ordinary quotations receive normalized typography. Fixed recitations retain original forms in the reader text, with separate explanatory narration; do not silently regularize them to familiar formulas.

## Contextual correction and semantic return

Keep three separate values where relevant: visible source glyph, current reading, proposed emendation. A clearly printed error remains in the source record; a supported emendation uses `editorial_exception` with the actual parallel witness and its location, not `script_conversion`. Faithful transcription corrections return to source reconstruction and keep the old snapshot.

Build term protection by occurrence/phrase and domain meaning, not global character replacement. In the reviewed fengshui sample, 乾 is a trigram/direction name and must survive t2s; this does not make every 干 a 乾. Check negation, choices, numbers and technical terms after conversion: mistaken 弃→并 changes meaning despite producing familiar words.

Column boundaries are not sentence boundaries. Restore 爬／沙、云／衢、出人／右 and stacked note labels before deciding punctuation. Historical省写 and names need evidence, not expansion to a modern-looking form. If all glyphs are legible but the phrase remains opaque, route it to the unified uncertainty ledger, preserve its context, and do not invent a paraphrase. Use [text/semantics review](../../chaoyun-ancient-book-renovator/references/text-semantics-review.md) for the final scope, independent review and acceptance contract.
