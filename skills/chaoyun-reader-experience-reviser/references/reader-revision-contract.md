# Whole-book reader revision contract

## Reader review

Create `50-edited/reader-review.json` before editing:

```json
{
  "schema_version": "1.0",
  "cycle_id": "RC0003",
  "mode": "manuscript",
  "input_sha256": "...",
  "target_reader": "现代普通读者",
  "reviewer": "reader-audit-model-or-person",
  "dimensions": {
    "introduction_promise": {"verdict": "needs_revision", "findings": ["The introduction promises a method not explained later."]},
    "prerequisites": {"verdict": "passed", "findings": []},
    "navigation": {"verdict": "passed", "findings": []},
    "continuity": {"verdict": "passed", "findings": []},
    "terminology": {"verdict": "needs_revision", "findings": ["A core term appears before explanation."]},
    "examples_and_figures": {"verdict": "passed", "findings": []},
    "redundancy_and_pacing": {"verdict": "passed", "findings": []},
    "source_editor_trust": {"verdict": "passed", "findings": []},
    "closure_and_lookup": {"verdict": "passed", "findings": []}
  },
  "glossary_samples": [
    {"term": "示例术语", "plain_enough": true, "context_specific": true, "example_helpful": true, "issue": null}
  ],
  "blocking_issues": ["RR000001"]
}
```

Every dimension is reviewed even when no defect is found. Findings identify a reader obstacle and location or concept; generic approval text is not a finding. Sample at least the lesser of ten glossary entries or all entries. When there are ten or fewer core terms, sample every core term. A sampled entry passes only when its plain definition, book-specific context, and example are useful to the declared reader.

## Revision ledger

`50-edited/reader-revision-ledger.jsonl` is append-only across unlimited cycles:

```json
{
  "schema_version": "1.0",
  "event_id": "RRE000002",
  "revision_id": "RR000001",
  "cycle_id": "RC0003",
  "operation": "add",
  "reader_problem": "The core term is used before the reader can understand it.",
  "block_ids": ["P000080-B003"],
  "section": "卷三·点穴歌",
  "before": "...",
  "after": "...",
  "preservation": null,
  "evidence": ["P000080-B003"],
  "semantic_risk": "low",
  "uncertainty_candidate_id": null,
  "status": "applied",
  "rationale": "Adds a first-use explanation without changing the translated claim."
}
```

Rules:

- `event_id` is unique. The same `revision_id` may appear in later appended events as its status moves from proposed to applied, rejected, or returned.
- `operation` is `add`, `delete_from_reading_path`, `rewrite`, or `reorganize`.
- `status` is `proposed`, `applied`, `rejected`, or `returned_to_responsible_stage`.
- Applied `add`, `rewrite`, and `reorganize` records contain distinct before/after state. Applied deletion records name where the source material remains available in `preservation`.
- Every record names the reader problem, evidence, and affected blocks or section.
- A medium/high semantic-risk change has an `uncertainty_candidate_id` and is adjudicated before publication.

## Acceptance report

After a fresh regression read, create `50-edited/reader-acceptance-report.json`:

```json
{
  "schema_version": "1.0",
  "cycle_id": "RC0003",
  "mode": "manuscript",
  "producer": "revision-producer",
  "reviewer": "different-regression-reviewer",
  "status": "passed",
  "output_sha256": "...",
  "regression_review": "passed",
  "blocking_issues": [],
  "counts": {"add": 1, "delete_from_reading_path": 0, "rewrite": 0, "reorganize": 0}
}
```

The output hash matches `50-edited/modern-reading.md`. Counts are derived from the latest event for each revision in the accepted cycle. The producer and regression reviewer differ. A new later cycle supersedes acceptance; publication uses the latest cycle represented in the ledger and acceptance report.
