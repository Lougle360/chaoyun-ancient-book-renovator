#!/usr/bin/env python3
"""Synthetic behavior tests only; fixtures are never actual book acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True

from pypdf import PdfWriter
from preflight_review import inspect_workspace, run_check
from test_reader_production import fixture_plan
from validate_integrity import validate as formal_integrity, validator_paths
from validate_production_plan import ILLUSTRATION_BINDINGS

SCRIPT = Path(__file__).with_name("preflight_review.py")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False), encoding="utf-8")


def snapshot(root):
    return {p.relative_to(root).as_posix(): (digest(p), p.stat().st_mtime_ns, p.stat().st_size)
            for p in root.rglob("*") if p.is_file()}


def fixture(root, full=False):
    """Minimal text-only 1.10 records with explicitly synthetic evidence."""
    write(root, "book.json", {"book_id": "fixture", "delivery_mode": "ordinary_reader",
                              "workflow_schema_version": "1.10", "source_pdf_pages": 1})
    state = {"book_id": "fixture", "current_stage": "source", "stages": {}}
    write(root, "run-state.json", state)
    source_pdf = root / "00-intake/source.pdf"
    source_pdf.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(source_pdf)
    write(root, "00-intake/source-manifest.json", {"source_path": str(source_pdf), "source_sha256": digest(source_pdf)})
    rows = [dict(schema_version="1.0", book_id="fixture", page_id="P000001", block_id=f"P000001-B00{i}",
                 source_page=1, block_type=kind, source_text=text, normalized_text=text, modern_text=text,
                 disposition="retained", component_id="C", structural_role=kind, bbox=[0, i, 50, i + 1], reading_order=i)
            for i, (kind, text) in enumerate([("heading", "试验篇"), ("body", "合成材料不代表实际审核。")], 1)]
    write(root, "20-source/blocks.jsonl", "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    write(root, "10-diagnosis/edition-scope.json", {
        "status": "locked", "locked_at": "SYNTHETIC-TEST", "delivery_mode": "ordinary_reader",
        "completeness_claim": "full_source_content", "user_requirement": "SYNTHETIC TEST ONLY",
        "source_components": [{"component_id": "C", "kind": "main_text", "planned_destination": "final_reader", "required_in_release": True}],
    })
    write(root, "90-audit/acceptance-policy-lock.json", {
        "policy_version": "1.10", "edition_scope_sha256": digest(root / "10-diagnosis/edition-scope.json"),
        "validators": {name: digest(path) for name, path in validator_paths().items()},
    })
    if not full:
        return rows
    for stage in ("30-normalized", "40-modernized", "50-edited"):
        write(root, stage + "/blocks.jsonl", "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
    write(root, "90-audit/synthetic-structure.md", "SYNTHETIC STRUCTURE TEST; NOT REAL REVIEW.\n")
    evidence = {"file": "90-audit/synthetic-structure.md", "sha256": digest(root / "90-audit/synthetic-structure.md"), "reason": "Synthetic test evidence"}
    units = {"schema_version": "1.0", "status": "reviewed", "source_sha256": digest(root / "20-source/blocks.jsonl"),
             "review_evidence": evidence, "continuations": [], "units": [
                 {"unit_id": f"U{i}", "kind": kind, "source_blocks": [row["block_id"]], "source_pages": [1],
                  "destination": "final_reader", "decision_evidence": evidence}
                 for i, (row, kind) in enumerate(zip(rows, ("heading", "main_text")), 1)]}
    write(root, "50-edited/reader-units.json", units)
    plan = fixture_plan(root)
    plan["schema_version"] = "1.1"
    for relative in ILLUSTRATION_BINDINGS:
        write(root, relative, "SYNTHETIC TEST: no figures in the source fixture.\n")
    for relative in [*ILLUSTRATION_BINDINGS, "50-edited/reader-units.json"]:
        plan["bindings"][relative] = digest(root / relative)
    write(root, "50-edited/production-plan.json", plan)
    manuscript = "# 正文\n<!-- source:P000001-B001 -->\n试验篇\n<!-- source:P000001-B002 -->\n合成材料不代表实际审核。\n"
    write(root, "50-edited/modern-reading.md", manuscript)
    write(root, "50-edited/source-reader-map.jsonl", "".join(json.dumps({
        "block_id": row["block_id"], "component_id": "C", "reader_heading": "正文", "reader_quote": row["source_text"],
        "status": "reviewed", "review_evidence": "SYNTHETIC TEST ONLY",
    }, ensure_ascii=False) + "\n" for row in rows))
    write(root, "50-edited/reader-unit-rendering.json", {
        "units_sha256": digest(root / "50-edited/reader-units.json"), "manuscript_sha256": digest(root / "50-edited/modern-reading.md"),
        "units": [{"unit_id": "U1", "start_line": 2, "end_line": 3, "quote": "试验篇"},
                  {"unit_id": "U2", "start_line": 4, "end_line": 5, "quote": "合成材料不代表实际审核。"}],
    })
    state.update(current_stage="edited", stages={name: {"status": "passed"} for name in (
        "book_understood", "reader_designed", "reader_units_built", "sample_accepted")})
    write(root, "run-state.json", state)
    return rows


def fixture_final_passes(root):
    """Three explicit synthetic full-read declarations, never real review evidence."""
    write(root, "50-edited/review-policy.json", {"minimum_full_passes": 3, "required_stable_passes": 2})
    manuscript = root / "50-edited/modern-reading.md"
    paths = []
    for number in range(1, 4):
        transcript = f"50-edited/review-history/full-passes/pass-{number}.md"
        write(root, transcript, f"SYNTHETIC FULL-READ FIXTURE {number}; NOT ACTUAL REVIEW.\n")
        record = {
            "reviewer_run_id": f"synthetic-full-read-{number}", "review_mode": "full_read", "status": "passed",
            "manuscript_sha256": digest(manuscript), "findings": [], "new_blocking_issues": [], "open_blocking_issues": [],
            "transcript": transcript, "transcript_sha256": digest(root / transcript), "sections_covered": [
                {"start_line": 1, "end_line": 3, "evidence": "SYNTHETIC coverage of title and opening source anchor."},
                {"start_line": 4, "end_line": 5, "evidence": "SYNTHETIC coverage of final source anchor and sentence."},
            ],
        }
        relative = f"50-edited/review-history/full-passes/pass-{number}.json"
        write(root, relative, record)
        paths.append(root / relative)
    return paths


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chaoyun-preflight-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_future_stages_are_not_missing_errors(self):
        fixture(self.root)
        report = inspect_workspace(self.root)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["checks"]["source"]["readiness"], "ready")
        self.assertEqual(report["checks"]["normalized"]["readiness"], "not_yet")
        self.assertEqual(report["checks"]["reader_units"]["readiness"], "not_yet")
        required = inspect_workspace(self.root, through="edited")
        self.assertEqual(required["checks"]["normalized"]["readiness"], "error")
        self.assertTrue(any("missing 30-normalized/blocks.jsonl" in x["message"] for x in required["issues"]))

    def test_full_preflight_is_read_only_and_cannot_replace_formal_gate(self):
        fixture(self.root, full=True)
        before = snapshot(self.root)
        report = inspect_workspace(self.root)
        self.assertEqual(report["issues"], [])
        self.assertTrue(all(x["readiness"] == "ready" for x in report["checks"].values()))
        self.assertEqual(report["semantic_review"], "not_assessed")
        self.assertEqual(report["publication_approval"], "not_assessed")
        # A policy lock and mechanically complete inputs still do not supply actual review.
        self.assertTrue(any("review-policy.json" in x for x in formal_integrity(self.root)))
        self.assertEqual(snapshot(self.root), before)

    def test_independent_errors_are_collected_and_duplicates_are_linked(self):
        rows = fixture(self.root, full=True)
        rows[1].pop("bbox")
        write(self.root, "20-source/blocks.jsonl", "".join(json.dumps(x) + "\n" for x in rows))
        rows[0]["book_id"] = "wrong-book"
        write(self.root, "30-normalized/blocks.jsonl", "".join(json.dumps(x) + "\n" for x in rows))
        manuscript = self.root / "50-edited/modern-reading.md"
        manuscript.write_text(manuscript.read_text().replace("<!-- source:P000001-B002 -->", ""), encoding="utf-8")
        mapping = self.root / "50-edited/source-reader-map.jsonl"
        mapping.write_text(mapping.read_text().replace("合成材料不代表实际审核。", "nonexistent quote"), encoding="utf-8")
        report = inspect_workspace(self.root)
        messages = [x["message"] for x in report["issues"]]
        for fragment in ("lacks structural fields", "wrong book_id", "production dependency changed", "source binding is stale", "not located in its declared section", "missing final-reader source anchor"):
            self.assertTrue(any(fragment in x for x in messages), fragment)
        structural = [x for x in report["issues"] if "lacks structural fields" in x["message"]]
        self.assertEqual(len(structural), 1)
        self.assertEqual(set(structural[0]["checks"]), {"source", "normalized", "modernized", "edited"})

    def test_malformed_record_does_not_abort_batch(self):
        fixture(self.root, full=True)
        write(self.root, "20-source/blocks.jsonl", '{"block_id": []}\n')
        write(self.root, "50-edited/production-plan.json", "invalid json\n")
        other = self.root / "other-book"
        fixture(other)
        before = snapshot(self.root)
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), str(other)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        result = json.loads(proc.stdout)
        self.assertEqual(len(result["workspaces"]), 2)
        self.assertTrue(result["workspaces"][0]["issues"])
        self.assertEqual(result["workspaces"][1]["issues"], [])
        self.assertEqual(snapshot(self.root), before)

    def test_known_progress_cannot_hide_missing_artifacts(self):
        fixture(self.root)
        write(self.root, "run-state.json", {"book_id": "fixture", "current_stage": "intake", "stages": {"edited": {"status": "passed"}}})
        report = inspect_workspace(self.root)
        self.assertEqual(report["observed_through"], "edited")
        self.assertEqual(report["checks"]["edited"]["readiness"], "error")

    def test_malformed_metadata_is_reported_without_stopping_other_checks(self):
        fixture(self.root)
        write(self.root, "book.json", {"delivery_mode": [], "book_id": ["bad"]})
        write(self.root, "run-state.json", {"stages": {"source": {"status": []}}})
        report = inspect_workspace(self.root)
        messages = [x["message"] for x in report["issues"]]
        self.assertTrue(any("requires explicit delivery_mode" in x for x in messages))
        self.assertTrue(any("status must be a string" in x for x in messages))
        self.assertEqual(report["checks"]["source"]["readiness"], "error")

    def test_non_object_metadata_does_not_abort_later_workspaces(self):
        roots = []
        for name in ("book.json", "run-state.json"):
            for value in ([], None, "not an object"):
                root = self.root / f"invalid-{len(roots)}"
                fixture(root)
                write(root, name, json.dumps(value))
                roots.append(root)
        good = self.root / "valid-last"
        fixture(good)
        roots.append(good)
        before = snapshot(self.root)
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, roots)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        reports = json.loads(proc.stdout)["workspaces"]
        self.assertEqual(len(reports), len(roots))
        for report in reports[:-1]:
            self.assertEqual(report["checks"]["metadata"]["readiness"], "error")
            self.assertEqual(report["checks"]["source"]["readiness"], "error")
            self.assertTrue(any("expected object" in issue["message"] for issue in report["issues"]))
        self.assertEqual(reports[-1]["issues"], [])
        self.assertEqual(snapshot(self.root), before)

    def test_legacy_reader_units_are_not_silently_migrated(self):
        fixture(self.root)
        path = self.root / "book.json"
        book = json.loads(path.read_text())
        book["workflow_schema_version"] = "1.9"
        write(self.root, "book.json", book)
        lock_path = self.root / "90-audit/acceptance-policy-lock.json"
        lock = json.loads(lock_path.read_text())
        lock["policy_version"] = "1.9"
        write(self.root, "90-audit/acceptance-policy-lock.json", lock)
        before = snapshot(self.root)
        report = inspect_workspace(self.root)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["checks"]["reader_units"]["readiness"], "not_applicable")
        self.assertEqual(snapshot(self.root), before)

    def test_policy_lock_is_required_and_current_before_source_review(self):
        fixture(self.root)
        lock_path = self.root / "90-audit/acceptance-policy-lock.json"
        original = lock_path.read_bytes()
        lock_path.unlink()
        missing = inspect_workspace(self.root, through="source")
        self.assertEqual(missing["checks"]["acceptance_policy_lock"]["readiness"], "error")
        self.assertTrue(any("requires a frozen acceptance-policy-lock.json" in x["message"] for x in missing["issues"]))
        lock = json.loads(original)
        lock["validators"]["controller/validate_integrity.py"] = "stale"
        write(self.root, "90-audit/acceptance-policy-lock.json", lock)
        stale_validator = inspect_workspace(self.root)
        self.assertTrue(any("acceptance policy changed after review began" in x["message"] for x in stale_validator["issues"]))
        lock_path.write_bytes(original)
        scope = self.root / "10-diagnosis/edition-scope.json"
        scope.write_bytes(scope.read_bytes() + b"\n")
        stale_scope = inspect_workspace(self.root)
        self.assertTrue(any("does not match the frozen edition scope" in x["message"] for x in stale_scope["issues"]))

    def test_source_request_requires_lock_but_intake_and_legacy_do_not(self):
        fixture(self.root)
        (self.root / "90-audit/acceptance-policy-lock.json").unlink()
        source_path = self.root / "20-source/blocks.jsonl"
        source = source_path.read_bytes()
        source_path.unlink()
        write(self.root, "run-state.json", {"book_id": "fixture", "current_stage": "intake", "stages": {}})
        intake = inspect_workspace(self.root)
        self.assertEqual(intake["checks"]["acceptance_policy_lock"]["readiness"], "not_yet")
        requested = inspect_workspace(self.root, through="source")
        self.assertEqual(requested["checks"]["acceptance_policy_lock"]["readiness"], "error")
        source_path.write_bytes(source)
        book = json.loads((self.root / "book.json").read_text())
        for version, mode in (("1.8", "ordinary_reader"), ("1.10", "evidence_archive"), ("1.10", "source_comparison")):
            book.update(workflow_schema_version=version, delivery_mode=mode)
            write(self.root, "book.json", book)
            legacy = inspect_workspace(self.root)
            self.assertEqual(legacy["checks"]["acceptance_policy_lock"]["readiness"], "not_applicable")
            self.assertEqual(legacy["issues"], [])

    def test_opt_in_final_set_rejects_two_full_passes_plus_local_regression(self):
        fixture(self.root, full=True)
        paths = fixture_final_passes(self.root)
        record = json.loads(paths[-1].read_text())
        record["review_mode"] = "limited_regression"
        paths[-1].write_text(json.dumps(record), encoding="utf-8")
        before = snapshot(self.root)
        default = inspect_workspace(self.root)
        self.assertEqual(default["issues"], [])
        self.assertEqual(len(default["checks"]), 11)
        self.assertNotIn("final_pass_set", default["checks"])
        strict = inspect_workspace(self.root, final_pass_set=True)
        self.assertEqual(strict["checks"]["final_pass_set"]["readiness"], "error")
        self.assertTrue(any("must declare review_mode=full_read" in x["message"] for x in strict["issues"]))
        self.assertEqual(snapshot(self.root), before)

    def test_opt_in_three_bound_full_declarations_with_complete_coverage(self):
        fixture(self.root, full=True)
        fixture_final_passes(self.root)
        before = snapshot(self.root)
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), "--through", "edited", "--final-pass-set"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)["workspaces"][0]
        self.assertEqual(report["checks"]["final_pass_set"]["readiness"], "ready")
        self.assertEqual(report["semantic_review"], "not_assessed")
        self.assertEqual(report["publication_approval"], "not_assessed")
        self.assertEqual(snapshot(self.root), before)

    def test_opt_in_final_set_rejects_gaps_unverifiable_ranges_and_empty_evidence(self):
        fixture(self.root, full=True)
        paths = fixture_final_passes(self.root)
        original = paths[-1].read_text()
        for variant in ("gap", "chapter_names", "empty_evidence", "inherited_section"):
            with self.subTest(variant=variant):
                record = json.loads(original)
                if variant == "gap":
                    record["sections_covered"][-1]["end_line"] = 4
                elif variant == "chapter_names":
                    record["sections_covered"] = ["opening", "body"]
                elif variant == "empty_evidence":
                    record["sections_covered"][-1]["evidence"] = "   "
                else:
                    record["sections_covered"][-1]["new_full_section_read_this_run"] = False
                paths[-1].write_text(json.dumps(record), encoding="utf-8")
                report = inspect_workspace(self.root, final_pass_set=True)
                self.assertEqual(report["checks"]["final_pass_set"]["readiness"], "error")
                self.assertTrue(any("does not cover every manuscript line" in x["message"] for x in report["issues"]))

    def test_opt_in_final_set_keeps_original_count_stability_and_binding_checks(self):
        fixture(self.root, full=True)
        paths = fixture_final_passes(self.root)
        original = paths[-1].read_text()
        for variant, fragment in (("too_few", "complete reader passes are insufficient"),
                                  ("unstable", "final stable reader passes"), ("stale", "is stale")):
            with self.subTest(variant=variant):
                record = json.loads(original)
                if variant == "too_few":
                    paths[-1].unlink()
                else:
                    if variant == "unstable":
                        record["open_blocking_issues"] = ["SYNTHETIC unresolved issue"]
                    else:
                        record["manuscript_sha256"] = "stale"
                    paths[-1].write_text(json.dumps(record), encoding="utf-8")
                report = inspect_workspace(self.root, final_pass_set=True)
                self.assertEqual(report["checks"]["final_pass_set"]["readiness"], "error")
                self.assertTrue(any(fragment in x["message"] for x in report["issues"]))
                paths[-1].write_text(original, encoding="utf-8")

    def test_worker_blocks_accidental_writes(self):
        target = self.root / "must-not-exist.txt"
        code = "from preflight_review import readonly_guard; from pathlib import Path; import sys; readonly_guard(); Path(sys.argv[1]).write_text('changed')"
        proc = subprocess.run([sys.executable, "-B", "-c", code, str(target)], cwd=SCRIPT.parent, capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("read-only worker blocked a file write", proc.stderr)
        self.assertFalse(target.exists())

    def test_timeout_is_an_error_not_readiness(self):
        with mock.patch("preflight_review.subprocess.run", side_effect=subprocess.TimeoutExpired("synthetic", 1)):
            result = run_check(self.root, "source", 1)
        self.assertTrue(any("exceeded 1s" in x for x in result["errors"]))


if __name__ == "__main__":
    unittest.main()
