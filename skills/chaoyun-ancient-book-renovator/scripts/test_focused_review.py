#!/usr/bin/env python3
"""Synthetic gate regressions only; these fixtures are never real book reviews."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

from preflight_review import check_final_pass_set
from test_preflight_review import fixture, fixture_final_passes, snapshot, write
from test_reader_production import fixture_session
from validate_integrity import sha256, validate, validate_policy_lock, validate_review_stability, validate_source, validator_paths

SCRIPTS = Path(__file__).resolve().parent
POLICY = "50-edited/review-policy.json"
LOCK = "90-audit/acceptance-policy-lock.json"
PASS = "50-edited/review-history/full-passes/pass-1.json"


def load(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def run_script(name, *args):
    return subprocess.run([sys.executable, "-B", str(SCRIPTS / name), *map(str, args)], capture_output=True, text=True)


def focused_fixture(root):
    fixture(root, full=True)
    book = load(root, "book.json")
    book.update(review_protocol="focused-v1", layout_proof_applicability={
        "required": False, "reason": "SYNTHETIC text-only test fixture, not a production diagnosis."})
    write(root, "book.json", book)
    write(root, POLICY, {"schema_version": "1.0", "protocol": "focused-v1", "minimum_full_passes": 1,
                         "required_stable_passes": 1,
                         "required_methods": ["manuscript_reader", "source_fidelity", "final_pdf_reader"]})
    # Only disposable synthetic fixture locks are replaced to exercise the real CLI.
    (root / LOCK).unlink()
    result = run_script("lock_acceptance_policy.py", root)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    manuscript = root / "50-edited/modern-reading.md"
    session = fixture_session(root, "50-edited/modern-reading.md")
    sections = [
        {"start_line": 1, "end_line": 3, "evidence": "SYNTHETIC observation of title and opening anchor."},
        {"start_line": 4, "end_line": 5, "evidence": "SYNTHETIC observation of final anchor and sentence."},
    ]
    provenance = root / session["provenance_file"]
    provenance.write_text(provenance.read_text(encoding="utf-8") + "\n" + "\n".join(section["evidence"] for section in sections), encoding="utf-8")
    session["provenance_sha256"] = sha256(provenance)
    acceptance = {"schema_version": "1.2", "reading_session": session, "output_sha256": sha256(manuscript)}
    for role in ("producer", "reviewer"):
        path = f"90-audit/synthetic-{role}.json"
        actor = f"SYNTHETIC {role} actor"
        write(root, path, {"actor": actor, "run_id": session[role + "_execution_id"], "output_sha256": sha256(manuscript)})
        acceptance.update({role: actor, role + "_record": path, role + "_record_sha256": sha256(root / path)})
    write(root, "50-edited/reader-acceptance-report.json", acceptance)
    write(root, PASS, {
        "producer_run_id": session["producer_execution_id"], "reviewer_run_id": session["reviewer_execution_id"],
        "review_mode": "full_read", "status": "passed", "manuscript_sha256": sha256(manuscript),
        "acceptance_policy_lock_sha256": sha256(root / LOCK),
        "findings": [], "new_blocking_issues": [], "open_blocking_issues": [],
        "transcript": session["provenance_file"], "transcript_sha256": session["provenance_sha256"], "sections_covered": sections,
    })


class FocusedReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chaoyun-focused-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        focused_fixture(self.root)

    def rejects(self, fragment):
        errors = validate(self.root)
        self.assertTrue(any(fragment in message for message in errors), errors)

    def mutate_record(self, **updates):
        record = load(self.root, PASS)
        record.update(updates)
        write(self.root, PASS, record)

    def test_one_complete_stable_independent_final_read_passes_formal_gate(self):
        before = snapshot(self.root)
        self.assertEqual(validate(self.root), [])
        self.assertEqual(check_final_pass_set(self.root), [])
        self.assertEqual(snapshot(self.root), before)

    def test_zero_passes_rejected(self):
        (self.root / PASS).unlink()
        self.rejects("insufficient: 0/1")

    def test_partial_and_hash_only_cannot_count_without_manual_preflight(self):
        original = load(self.root, PASS)
        for changes in ({"review_mode": "limited_regression"}, {"review_mode": "hash_only"},
                        {"partial": True}, {"partial": 1}, {"inherited": True}, {"hash_only": True},
                        {"new_full_section_read_this_run": False}, {"new_full_section_read_this_run": 0}):
            with self.subTest(changes=changes):
                write(self.root, PASS, {**original, **changes})
                self.assertTrue(validate(self.root))

    def test_full_coverage_requires_actual_ranges_and_nonempty_evidence(self):
        original = load(self.root, PASS)
        for variant in ("gap", "chapter_name", "empty_evidence", "partial_section", "inherited_section"):
            with self.subTest(variant=variant):
                record = json.loads(json.dumps(original))
                if variant == "gap":
                    record["sections_covered"][-1]["end_line"] = 4
                elif variant == "chapter_name":
                    record["sections_covered"] = ["SYNTHETIC chapter name"]
                elif variant == "empty_evidence":
                    record["sections_covered"][0]["evidence"] = "   "
                elif variant == "partial_section":
                    record["sections_covered"][0]["review_mode"] = "limited_regression"
                else:
                    record["sections_covered"][0]["new_full_section_read_this_run"] = False
                write(self.root, PASS, record)
                self.rejects("does not cover every manuscript line")

    def test_every_final_manuscript_byte_change_invalidates_the_read(self):
        manuscript = self.root / "50-edited/modern-reading.md"
        manuscript.write_bytes(manuscript.read_bytes() + b"\n")
        self.rejects("is stale")

    def test_nonempty_distinct_producer_and_reviewer_runs_required(self):
        original = load(self.root, PASS)
        for changes in ({"producer_run_id": ""}, {"producer_run_id": original["reviewer_run_id"]},
                        {"producer_run_id": " " + original["reviewer_run_id"] + " "},
                        {"reviewer_run_id": " "}, {"reviewer_run_id": []}):
            with self.subTest(changes=changes):
                write(self.root, PASS, {**original, **changes})
                self.assertTrue(validate(self.root))

    def test_self_reported_producer_cannot_hide_actual_producer_as_reviewer(self):
        actual_producer = load(self.root, PASS)["producer_run_id"]
        self.mutate_record(producer_run_id="unbound-different-run", reviewer_run_id=actual_producer)
        self.rejects("not independent of the bound actual producer run")

    def test_actual_execution_binding_cannot_be_missing_or_relabelled(self):
        path = self.root / "50-edited/reader-acceptance-report.json"
        original = path.read_bytes()
        path.unlink()
        self.rejects("actual execution binding")
        path.write_bytes(original)
        acceptance = load(self.root, "50-edited/reader-acceptance-report.json")
        for role in ("producer", "reviewer"):
            with self.subTest(role=role):
                altered = json.loads(original)
                altered["reading_session"][role + "_execution_id"] = "unbound-run"
                write(self.root, "50-edited/reader-acceptance-report.json", altered)
                self.rejects("execution differs from actual reading session")
        write(self.root, "50-edited/reader-acceptance-report.json", acceptance)
        producer = self.root / acceptance["producer_record"]
        producer.write_text("{}", encoding="utf-8")
        self.rejects("producer execution record hash mismatch")

    def test_final_full_read_is_the_actual_acceptance_reviewer(self):
        self.mutate_record(reviewer_run_id="some-other-reviewer")
        self.rejects("final complete reader pass must match the actual acceptance reviewer run")

    def test_transcript_cannot_be_input_source_execution_or_a_copy(self):
        write(self.root, "50-edited/review-history/RC0001/input.md", "SYNTHETIC input manuscript before edit.")
        write(self.root, "50-edited/reader-review.json", {"input_snapshot": "50-edited/review-history/RC0001/input.md"})
        targets = ["50-edited/modern-reading.md", "20-source/blocks.jsonl", "90-audit/synthetic-producer.json",
                   "50-edited/review-history/RC0001/input.md"]
        for relative in targets:
            for copied in (False, True):
                with self.subTest(relative=relative, copied=copied):
                    if copied:
                        path = self.root / "50-edited/copied-transcript.txt"
                        path.write_bytes((self.root / relative).read_bytes())
                        relative_transcript = path.relative_to(self.root).as_posix()
                    else:
                        path, relative_transcript = self.root / relative, relative
                    self.mutate_record(transcript=relative_transcript, transcript_sha256=sha256(path))
                    self.rejects("transcript reuses manuscript, source/input or execution content")

    def test_transcript_must_contain_its_run_and_claimed_section_evidence(self):
        record = load(self.root, PASS)
        path = self.root / record["transcript"]
        original = path.read_text(encoding="utf-8")
        for removed, expected in ((record["reviewer_run_id"], "transcript lacks its actual reviewer_run_id"),
                                  (record["sections_covered"][0]["evidence"], "section evidence is absent")):
            with self.subTest(removed=removed):
                path.write_text(original.replace(removed, ""), encoding="utf-8")
                self.mutate_record(transcript_sha256=sha256(path))
                self.rejects(expected)

    def test_transcript_binding_and_real_nonempty_text_remain_required(self):
        record = load(self.root, PASS)
        transcript = self.root / record["transcript"]
        transcript.write_text("changed synthetic transcript", encoding="utf-8")
        self.rejects("transcript binding is invalid")
        transcript.write_text("  \n", encoding="utf-8")
        self.mutate_record(transcript_sha256=sha256(transcript))
        self.rejects("nonempty actual transcript")

    def test_last_pass_must_be_stable(self):
        for changes in ({"status": "failed"}, {"new_blocking_issues": ["synthetic blocker"]},
                        {"open_blocking_issues": ["synthetic blocker"]}):
            with self.subTest(changes=changes):
                self.mutate_record(**changes)
                self.rejects("final stable reader passes")

    def test_missing_policy_or_lock_never_enables_one_pass(self):
        for relative in (POLICY, LOCK):
            with self.subTest(relative=relative):
                path = self.root / relative
                saved = path.read_bytes()
                path.unlink()
                self.assertTrue(validate(self.root))
                errors = []
                validate_review_stability(self.root, self.root / "50-edited/modern-reading.md", errors)
                self.assertTrue(errors)
                path.write_bytes(saved)

    def test_unknown_mismatched_and_malformed_profiles_fail_closed(self):
        original_book, original_policy = load(self.root, "book.json"), load(self.root, POLICY)
        cases = [({"review_protocol": "focused-v999"}, {}), ({}, {"protocol": "focused-v999"}),
                 ({"review_protocol": None}, {}), ({"workflow_schema_version": "1.9"}, {}),
                 ({"workflow_schema_version": "future"}, {}), ({"delivery_mode": "evidence_archive"}, {})]
        for book_changes, policy_changes in cases:
            with self.subTest(book=book_changes, policy=policy_changes):
                write(self.root, "book.json", {**original_book, **book_changes})
                write(self.root, POLICY, {**original_policy, **policy_changes})
                self.assertTrue(validate(self.root))
                self.assertTrue(validate_source(self.root))

    def test_focused_markers_cannot_reuse_a_legacy_or_incomplete_lock(self):
        original = load(self.root, LOCK)
        for field in ("review_protocol", "review_policy_sha256", "layout_proof_applicability"):
            with self.subTest(field=field):
                lock = dict(original)
                lock.pop(field)
                write(self.root, LOCK, lock)
                self.assertTrue(validate(self.root))
                errors = []
                validate_policy_lock(self.root, errors)
                self.assertTrue(errors)
                self.assertEqual(load(self.root, LOCK), lock)

    def test_invalid_focused_counts_cannot_be_locked(self):
        original = load(self.root, POLICY)
        (self.root / LOCK).unlink()
        for minimum, stable in ((0, 0), (1, 0), (1, 2), (True, True), (1, False)):
            with self.subTest(minimum=minimum, stable=stable):
                write(self.root, POLICY, {**original, "minimum_full_passes": minimum, "required_stable_passes": stable})
                result = run_script("lock_acceptance_policy.py", self.root)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.root / LOCK).exists())

    def test_policy_and_protocol_tampering_invalidate_lock(self):
        policy = load(self.root, POLICY)
        policy["minimum_full_passes"] = 2
        write(self.root, POLICY, policy)
        self.rejects("frozen review-policy.json")
        lock = load(self.root, LOCK)
        lock["review_protocol"] = "unknown"
        write(self.root, LOCK, lock)
        self.rejects("review protocol cannot be removed or changed")

    def test_removing_both_markers_cannot_downgrade_frozen_protocol(self):
        book, policy = load(self.root, "book.json"), load(self.root, POLICY)
        book.pop("review_protocol")
        policy.pop("protocol")
        policy.update(minimum_full_passes=3, required_stable_passes=2)
        write(self.root, "book.json", book)
        write(self.root, POLICY, policy)
        self.rejects("review protocol cannot be removed or changed")

    def test_existing_focused_lock_blocks_version_and_mode_skip_downgrades(self):
        original_book, original_policy = load(self.root, "book.json"), load(self.root, POLICY)
        (self.root / PASS).unlink()
        for change in ({"workflow_schema_version": "1.8"}, {"delivery_mode": "evidence_archive"},
                       {"delivery_mode": "source_comparison", "workflow_schema_version": "1.8"}):
            with self.subTest(change=change):
                book, policy = dict(original_book), dict(original_policy)
                book.pop("review_protocol")
                policy.pop("protocol")
                book.update(change)
                write(self.root, "book.json", book)
                write(self.root, POLICY, policy)
                for gate in (validate, validate_source, check_final_pass_set):
                    self.assertTrue(any("review protocol cannot be removed or changed" in error for error in gate(self.root)))

    def test_archiving_and_relocking_does_not_reauthorize_old_passes(self):
        old_pass = (self.root / PASS).read_bytes()
        policy = load(self.root, POLICY)
        policy["rule"] = "CHANGED SYNTHETIC REVIEW POLICY"
        write(self.root, POLICY, policy)
        self.rejects("frozen review-policy.json")
        (self.root / LOCK).rename(self.root / "90-audit/previous-policy-lock.json")
        result = run_script("lock_acceptance_policy.py", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / PASS).read_bytes(), old_pass)
        self.rejects("acceptance policy lock binding is stale or missing")

    def test_layout_applicability_is_explicit_and_frozen(self):
        original = load(self.root, "book.json")
        for value in (None, {"required": False, "reason": ""},
                      {"required": True, "reason": "Changed synthetic diagnosis"}):
            with self.subTest(value=value):
                write(self.root, "book.json", {**original, "layout_proof_applicability": value})
                self.rejects("layout_proof_applicability")

    def test_higher_frozen_count_is_not_silently_lowered(self):
        policy = load(self.root, POLICY)
        policy.update(minimum_full_passes=2, required_stable_passes=2)
        write(self.root, POLICY, policy)
        (self.root / LOCK).unlink()
        result = run_script("lock_acceptance_policy.py", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.rejects("insufficient: 1/2")

    def test_all_new_executable_policy_code_is_frozen_and_old_api_unchanged(self):
        legacy, focused = validator_paths(), validator_paths("focused-v1")
        self.assertEqual(len(legacy), 12)
        self.assertTrue(set(legacy).issubset(focused))
        expected = {f"controller/{name}" for name in (
            "validate_full_read.py", "init_workspace.py", "lock_acceptance_policy.py", "preflight_review.py")}
        self.assertEqual(set(focused) - set(legacy), expected)
        lock = load(self.root, LOCK)
        self.assertEqual(set(lock["validators"]), set(focused))
        lock["validators"]["controller/validate_full_read.py"] = "stale-code"
        write(self.root, LOCK, lock)
        self.rejects("acceptance policy changed after review began: controller/validate_full_read.py")

    def test_existing_lock_cannot_be_overwritten_or_refreshed(self):
        lock = self.root / LOCK
        before = lock.read_bytes()
        result = run_script("lock_acceptance_policy.py", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preserve or explicitly archive", result.stderr)
        self.assertEqual(lock.read_bytes(), before)

    def test_missing_required_review_methods_cannot_be_locked(self):
        policy = load(self.root, POLICY)
        policy["required_methods"] = ["manuscript_reader"]
        write(self.root, POLICY, policy)
        (self.root / LOCK).unlink()
        result = run_script("lock_acceptance_policy.py", self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_fidelity and final_pdf_reader", result.stderr)
        self.assertFalse((self.root / LOCK).exists())

    def test_legacy_workflow_keeps_three_full_and_two_stable_passes(self):
        legacy = self.root / "legacy"
        fixture(legacy, full=True)
        paths = fixture_final_passes(legacy)
        self.assertEqual(validate(legacy), [])
        paths[-1].unlink()
        self.assertTrue(any("insufficient: 2/3" in error for error in validate(legacy)))
        fixture_final_passes(legacy)
        record = load(legacy, "50-edited/review-history/full-passes/pass-2.json")
        record["open_blocking_issues"] = ["synthetic blocker in penultimate pass"]
        write(legacy, "50-edited/review-history/full-passes/pass-2.json", record)
        self.assertTrue(any("final stable reader passes" in error for error in validate(legacy)))
        policy = load(legacy, POLICY)
        policy.update(minimum_full_passes=1, required_stable_passes=1)
        write(legacy, POLICY, policy)
        self.assertTrue(any("at least three" in error for error in validate(legacy)))

    def test_init_only_sets_new_ordinary_reader_profile_and_does_not_migrate(self):
        source = self.root / "00-intake/source.pdf"
        for mode in ("ordinary_reader", "source_comparison", "evidence_archive"):
            with self.subTest(mode=mode):
                output = self.root / ("new-" + mode)
                result = run_script("init_workspace.py", source, output, "--delivery-mode", mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                book = load(output, "book.json")
                self.assertEqual(book["workflow_schema_version"], "1.10")
                self.assertNotIn("layout_proof_applicability", book)
                self.assertFalse((output / LOCK).exists())
                if mode == "ordinary_reader":
                    self.assertEqual(book["review_protocol"], "focused-v1")
                    policy = load(output, POLICY)
                    self.assertEqual((policy["protocol"], policy["minimum_full_passes"], policy["required_stable_passes"]),
                                     ("focused-v1", 1, 1))
                else:
                    self.assertNotIn("review_protocol", book)
                    self.assertFalse((output / POLICY).exists())
        before = snapshot(self.root)
        result = run_script("init_workspace.py", source, self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.root), before)


if __name__ == "__main__":
    unittest.main()
