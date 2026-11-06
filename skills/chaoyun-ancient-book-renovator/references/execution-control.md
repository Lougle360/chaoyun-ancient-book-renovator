# Focused execution and review protocol

This is the authoritative scheduling and reader-pass contract for new ordinary-reader production. Data workflow remains 1.10. **focused-v1** changes the review schedule, not the obligation to preserve source fidelity, complete reader understanding, uncertainty evidence or final PDF quality.

## Explicit activation and legacy boundary

New ordinary-reader workspaces created by init_workspace.py declare book.review_protocol = "focused-v1". Their 50-edited/review-policy.json declares protocol = "focused-v1", minimum_full_passes = 1, required_stable_passes = 1 and required_methods containing manuscript_reader, source_fidelity and final_pdf_reader. Higher explicitly locked counts remain enforceable; do not add them by habit.

Before the first semantic review, diagnose book.layout_proof_applicability = {required: boolean, reason: nonempty source-grounded explanation}, lock edition scope and run lock_acceptance_policy.py. The new lock binds the protocol, review-policy bytes, applicability decision and actual validation code. Missing/mismatched/unknown protocols or locks cannot activate the lower pass count. Production-plan 1.1 is mandatory for focused-v1.

Unmarked legacy books retain their three-full-pass/two-stable contract. Installing the Skill does not change book files, old approvals or official PDFs. Modified validator code can make old locks fail on a new run: preserve and use the matching prior Skill snapshot for a legacy run, or explicitly adopt focused-v1 in an isolated new edition before fresh acceptance. Preserve old locks and reviews; never refresh them to make changed policy appear historically approved. Reuse dependency-valid source assets and work, not incompatible passing judgments.

## Five stages, no extra ceremony

1. Diagnose, reconstruct and normalize reliable source; apply the real uncertainty route and conditional G3.5 proof.
2. Understand/design the book, reading units and illustrations; validate one shared representative sample.
3. Produce chapter batches, perform necessary editing/targeted repairs, prepare all final text and trial layout, then freeze.
4. Obtain independent full source fidelity and one complete independent final reader acceptance; recheck active uncertainty decisions with the same valid source evidence where compatible.
5. Inspect the actual candidate PDF once sequentially for all visual/reader checks, then use the guarded installer and report actual results.

A role is not an agent count. One producer may own compatible stage roles. An independent reviewer may combine compatible checks, but must preserve blind reader answers before seeing source comparison/expected answers and must not certify its own production. Each conclusion has its required evidence; shared execution does not merge away the different quality purposes.

There is no mandatory separate whole-book diagnostic read, fixed second/third full read, duplicate pilot per role, or second model task just to save a transcript. Extra diagnosis is driven by observed risk. One actual PDF inspection may supply both page-layout and sequential-reader records. Do not repeat full mechanical gates solely because a new agent or reporting task began. The installer still executes both existing publication gates at final promotion.

## Freeze, actual coverage and corrections

Before review, complete title/credits, preface, body, captions, glossary, notes, source anchors, assets and navigation inputs. Keep execution notes and status metadata outside the manuscript. Run preflight_review.py WORKSPACE --through edited after the relevant inputs are complete and when they change; unchanged evidence can be reused. not_yet is not approval.

Freeze the package during review; queue edits. The final full read covers every chapter and front/back matter in meaningful contiguous units, with actual questions, answers, assessments and retained provenance. Store real full passes in 50-edited/review-history/full-passes/. Each focused-v1 record has:
- review_mode: full_read;
- current manuscript_sha256 and acceptance_policy_lock_sha256 (the actual lock used during this reading);
- actual nonempty producer_run_id and reviewer_run_id, distinct from each other; producer_run_id matches the acceptance report’s hash-bound producer execution record, and the last full pass matches its hash-bound reviewer execution record and reading_session IDs;
- status, findings, new_blocking_issues and open_blocking_issues;
- sections_covered with inclusive start_line/end_line and substantive evidence covering every manuscript line;
- transcript and transcript_sha256 bound to a real retained execution, containing the literal reviewer run ID and each recorded section-evidence observation. The last pass reuses the same actual provenance file/content already bound by reading_session; do not create a second transcript. Manuscript/source/input or execution-record files and same-content copies cannot serve as reading transcripts. Actor, run and current output bindings in the actual execution records must agree with the acceptance report.

The minimum final pass must be passed with no new/open blocker. The existing reader-acceptance 1.2 task/answer, section, glossary, edit-chain and execution-record requirements remain. A local/hash-only/inherited check cannot count as full_read. Both formal publication gates automatically enforce focused-v1 coverage through validate_integrity; preflight --final-pass-set is optional early diagnosis.

Keep failed or superseded full passes with their historical cycle and local checks in limited-regressions/. Do not delete failed answers or put old-hash records into the current pass set. A diagnostic full read counts only if its complete evidence already applies to the exact final package; no relabeling or invented new run.

| Change | Required work |
|---|---|
| No relevant input changed | Reuse evidence. No new reviewer to repeat the verdict. |
| Local defect found before final acceptance | Repair and review affected passage plus dependent terms, figures and claims; finish one complete final acceptance after freeze. |
| Systematic meaning/order failure | Return upstream and expand the affected inspection; fix the method before another final full read. |
| Manuscript bytes changed after acceptance | Old acceptance is stale. Targeted checks diagnose the edit; the new exact final manuscript still requires one complete acceptance (or its higher locked count). |
| Only renderer typography/pagination changed | Keep byte-identical manuscript acceptance; regenerate and inspect the actual final PDF, figures and navigation. |
| Audit-only metadata changed outside the manuscript | Check its real dependencies; do not invent another full read if manuscript acceptance stays valid. |

The protocol does not implement semantic-hash normalization or incremental composition of old chapter answers into a fake new full read. Prevent cheap metadata edits from triggering expensive reacceptance by placing them correctly before freeze.

## Compact handoffs and one checkpoint

Produce whole chapters or adjacent reading units. Keep one resumable checkpoint in the existing execution log: book/workspace, accepted evidence/input hashes, current batch, blockers, pending edits, next action, usage window and authorized budget. Update it at batch completion/handoff, not per field/page.

Pass only the book/workspace, immutable input and hash, task scope, applicable Skill/reference, necessary source/figure evidence, output paths and stop condition. For regression add the exact diff and affected dependencies. Do not fork unrelated books' long history. Never assign concurrent writers to the canonical manuscript or ledger.

The reviewer returns actual answers, findings, transcript and bindings together. Deterministic scripts prepare pending inventories, compute hashes/counts and aggregate true results; they never author comprehension or passing judgments.

## Measured budget and stop conditions

Use scripts/measure_run_cost.py with every explicit producer/reviewer session and the actual book time window. For example:

~~~shell
python scripts/measure_run_cost.py \
  --session 'THREAD_ID=/absolute/path/to/session.jsonl' \
  --start '2026-11-06T10:00:00+08:00' \
  --budget-tokens 300000 \
  --output /absolute/path/to/book/90-audit/current-usage.json
~~~

300000 is an example, not a default authorization. Budget units are noncached input + output; cached input is separate and reasoning is already in output. Explicit thread filtering and response deduplication do not discover unlisted agents or automatically attribute every call to a task. Image/external costs may need separate records. This is a scoped diagnostic, not an account bill; elapsed wall time is not pure computing time or the sum of parallel agent durations.

Check cumulative use at batch completion and before another semantic reviewer or candidate build. Exit 2 means the explicit budget is reached: stop dependent work. Unknown/malformed usage is not zero. The CLI does not interrupt running agents or guarantee no within-batch overrun; the coordinator must size work within authorization and enforce checkpoints.

Without a hard user limit, base a labeled planning threshold on actual sample usage and remaining work; do not promise minutes or a saving percentage. On overrun, inspect whether the work progressed and revise the plan before another full run. Stop an affected loop after two cycles on the same blockers without new evidence/progress. Existing authorization persists; routine updates do not require the user to say “continue”. Seek a new decision only for a real scope/budget expansion.
