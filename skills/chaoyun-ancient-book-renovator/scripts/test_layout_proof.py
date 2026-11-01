#!/usr/bin/env python3
"""Synthetic gate regressions; these fixtures are NOT actual PDF acceptance."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter
import validate_layout_proof as gate
import validate_text_semantics as semantics


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class LayoutProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.record_path = self.root / "90-audit/layout-proof/T1/review.json"
        self.book = {"book_id": "fixture", "delivery_mode": "source_comparison", "source_pdf_pages": 1,
                     "layout_proof_review": {"required": True, "record": str(self.record_path.relative_to(self.root))}}
        write(self.root / "book.json", self.book)
        write(self.root / "run-state.json", {"book_id": "fixture", "stages": {}})
        for name in ("00-intake/source.pdf", "60-publication/supplements/proof-T1.pdf"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            writer = PdfWriter()
            writer.add_blank_page(width=200, height=300)
            writer.write(str(path))
        source = self.ref("00-intake/source.pdf")
        write(self.root / "00-intake/source-manifest.json", {"staged_source": str(self.root / source["path"]), "source_sha256": source["sha256"]})
        block = {"block_id": "P000001-B001", "source_page": 1, "block_type": "figure", "source_text": "獨水天眷"}
        inputs = []
        for role, name in (("source_blocks", "20-source/blocks.jsonl"), ("normalized_blocks", "30-normalized/blocks.jsonl"),
                           ("corrections", "30-normalized/changes.jsonl"), ("renderer", "scripts/render.py"), ("font", "assets/font.bin")):
            write(self.root / name, block if name.endswith("blocks.jsonl") else {"synthetic": role})
            inputs.append({"role": role, **self.ref(name)})
        # File content is explicitly synthetic; only bindings/coverage are tested.
        for name in ("source.png", "render.png", "figure.png", "review.txt"):
            (self.root / name).write_bytes(b"synthetic gate fixture, not visual review")
        pdf = self.ref("60-publication/supplements/proof-T1.pdf")
        self.record = {
            "schema_version": "1.1", "book_id": "fixture", "version": "T1",
            "edition_kind": "original_layout_simplified_proof", "status": "accepted",
            "validator_sha256": gate.sha(Path(gate.__file__)),
            "text_semantics_policy_sha256": gate.sha(Path(semantics.__file__)),
            "scope": {"kind": "sample", "source_pages": [1], "reason": "Synthetic regression only"},
            "source_pdf": source, "pdf": pdf, "inputs": inputs,
            "coverage": [{"source_page": 1, "block_ids": [block["block_id"]], "source_image": self.ref("source.png")}],
            "figures": [{"figure_id": "F1", "block_id": block["block_id"], "source_page": 1,
                         "source_bbox": [1, 1, 100, 100], "pdf_pages": [1], "asset": self.ref("figure.png")}],
            "pages": [{"pdf_page": 1, "role": "comparison", "source_pages": [1], "render": self.ref("render.png"),
                       "checks": {key: {"status": "passed", "findings": "Synthetic assertion: " + key} for key in gate.CHECKS}}],
            "review": {"reviewer": "fixture", "kind": "model", "reviewed_at": "synthetic", "pdf_sha256": pdf["sha256"], "evidence": self.ref("review.txt")},
        }
        self.semantic_path = self.root / "90-audit/layout-proof/T1/text-semantics.json"
        for name in semantics.LEDGERS:
            path = self.root / "90-audit" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("")
        self.semantic = {
            "schema_version": "1.0", "status": "passed",
            "producer": "synthetic-producer", "producer_run_id": "synthetic-production",
            "reviewer": "synthetic-reviewer", "reviewer_run_id": "synthetic-review",
            "reviewed_at": "synthetic-fixture-not-real-review", "evidence": self.ref("review.txt"),
            "coverage": [{"source_page": 1, "block_ids": [block["block_id"]], "findings": "Synthetic entire-page coverage"}],
            "checks": {key: {"status": "passed", "findings": "Synthetic assertion: " + key} for key in semantics.CHECKS},
            "candidate_results": [],
        }
        self.save_semantic()
        self.save()

    def ref(self, name):
        return {"path": name, "sha256": gate.sha(self.root / name)}

    def save(self):
        write(self.record_path, self.record)

    def save_semantic(self):
        self.semantic["proof_sha256"] = semantics.proof_digest(self.record)
        self.semantic["ledger_bindings"] = {name: self.ref("90-audit/" + name) for name in semantics.LEDGERS}
        write(self.semantic_path, self.semantic)
        self.record["text_semantics_review"] = self.ref(str(self.semantic_path.relative_to(self.root)))

    def add_open_candidate(self, impact="medium"):
        source_ref = {**self.ref("20-source/blocks.jsonl"), "quote": "獨水天眷"}
        candidate = {"schema_version": "1.3", "candidate_id": "UC1", "page_id": "P000001", "block_id": "P000001-B001",
                     "kind": "language", "excerpt": "獨水天眷", "reason": "Visible glyph does not establish meaning",
                     "severity": impact, "origin_stage": "normalized", "review_cycle": "RC1", "checkpoint": "proof",
                     "created_by": "synthetic", "created_at": "synthetic", "owner_stage": "normalized", "input_ref": source_ref}
        decision = {"schema_version": "1.2", "adjudication_id": "UA1", "candidate_ids": ["UC1"], "page_id": "P000001",
                    "block_id": "P000001-B001", "active": True, "supersedes": None, "status": "open_material",
                    "issue_id": "UI1", "reader_impact": impact, "review_cycle": "RC1", "checkpoint": "proof",
                    "before": None, "after": None, "rationale": "Meaning remains unresolved", "evidence": []}
        write(self.root / "90-audit/uncertainty-candidates.jsonl", candidate)
        write(self.root / "90-audit/uncertainty-adjudication.jsonl", decision)
        write(self.root / "90-audit/uncertain-items.jsonl", {"adjudication_id": "UA1", "status": "open"})
        disclosure = "独水天眷：字形已定，语义未定。"
        (self.root / "30-normalized/review-notes.md").write_text(disclosure)
        self.semantic["checks"]["meaning_in_context"]["status"] = "passed_with_ledger"
        self.semantic["candidate_results"] = [{"candidate_id": "UC1", "result": "disclosed_unresolved",
                                               "finding": "Glyph is retained; meaning is not claimed resolved",
                                               "evidence": [source_ref],
                                               "reader_disclosure": {**self.ref("30-normalized/review-notes.md"), "quote": disclosure}}]
        self.save_semantic()
        self.save()

    def test_valid_record(self):
        self.assertEqual(gate.validate(self.root), [])

    def test_pending_is_only_candidate_integrity(self):
        self.record.update(status="pending", review=None)
        self.save()
        self.assertEqual(gate.validate(self.root, require_acceptance=False), [])
        self.assertIn("requires actual review: pending", str(gate.validate(self.root)))

    def test_changed_files_invalidate_review(self):
        for name in ("60-publication/supplements/proof-T1.pdf", "30-normalized/blocks.jsonl", "figure.png", "render.png"):
            with self.subTest(name=name):
                path = self.root / name
                before = path.read_bytes()
                path.write_bytes(before + b"changed")
                self.assertIn("stale file binding", str(gate.validate(self.root)))
                path.write_bytes(before)

    def test_missing_coverage(self):
        original = copy.deepcopy(self.record)
        for field in ("figures", "coverage", "pages"):
            with self.subTest(field=field):
                self.record = copy.deepcopy(original)
                self.record[field] = []
                self.save()
                self.assertTrue(gate.validate(self.root))

    def test_acceptance_needs_review_and_resolved_checks(self):
        original = copy.deepcopy(self.record)
        for field in ("review", "checks", "policy"):
            self.record = copy.deepcopy(original)
            if field == "review":
                self.record["review"] = None
            elif field == "checks":
                self.record["pages"][0]["checks"]["uniform_region_fonts"]["status"] = "changes_requested"
            else:
                self.record["validator_sha256"] = "old-policy"
            self.save()
            self.assertTrue(gate.validate(self.root))

    def test_legacy_workspace_not_migrated(self):
        del self.book["layout_proof_review"]
        write(self.root / "book.json", self.book)
        self.assertEqual(gate.validate(self.root), [])

    def test_acceptance_requires_semantic_review(self):
        self.record.pop("text_semantics_review")
        self.save()
        self.assertIn("lacks text/semantics review", str(gate.validate(self.root)))
        self.record.update(status="pending", review=None)
        self.save()
        self.assertEqual(gate.validate(self.root, require_acceptance=False), [])

    def test_legacy_acceptance_is_not_promoted(self):
        self.record["schema_version"] = "1.0"
        self.save()
        self.assertIn("requires layout proof schema 1.1", str(gate.validate(self.root)))

    def test_review_binds_actual_pdf_and_checks(self):
        self.record["pages"][0]["checks"]["contextual_corrections"]["findings"] = "Changed after review"
        self.save()
        self.assertIn("belongs to another proof or inputs", str(gate.validate(self.root)))

    def test_semantic_review_must_cover_unflagged_blocks(self):
        self.semantic["coverage"][0]["block_ids"] = []
        self.save_semantic(); self.save()
        self.assertIn("all source blocks", str(gate.validate(self.root)))

    def test_separate_review_execution_required(self):
        self.semantic["reviewer_run_id"] = self.semantic["producer_run_id"]
        self.save_semantic(); self.save()
        self.assertIn("separate execution", str(gate.validate(self.root)))

    def test_low_medium_open_disclosure_can_be_bounded(self):
        self.add_open_candidate()
        self.assertEqual(gate.validate(self.root), [])

    def test_visible_glyph_does_not_close_open_meaning(self):
        self.add_open_candidate()
        self.semantic["candidate_results"][0]["result"] = "verified"
        self.save_semantic(); self.save()
        self.assertIn("open meaning as resolved", str(gate.validate(self.root)))

    def test_high_impact_open_blocks_acceptance(self):
        self.add_open_candidate("high")
        self.assertIn("high-impact meaning uncertainty", str(gate.validate(self.root)))
        self.semantic["status"] = "changes_requested"
        self.save_semantic(); self.save()
        self.assertIn("returned changes_requested", str(gate.validate(self.root)))
        self.record["status"] = "changes_requested"
        self.save()
        self.assertEqual(gate.validate(self.root, require_acceptance=False), [])

    def test_dropping_a_candidate_or_disclosure_fails(self):
        self.add_open_candidate()
        original = copy.deepcopy(self.semantic)
        self.semantic["candidate_results"] = []
        self.save_semantic(); self.save()
        self.assertIn("candidate coverage differs", str(gate.validate(self.root)))
        self.semantic = original
        self.semantic["candidate_results"][0].pop("reader_disclosure")
        self.save_semantic(); self.save()
        self.assertTrue(gate.validate(self.root))

    def test_internal_audit_alone_is_not_reader_disclosure(self):
        self.add_open_candidate()
        text = (self.root / "30-normalized/review-notes.md").read_text()
        (self.root / "90-audit/only-internal.md").write_text(text)
        self.semantic["candidate_results"][0]["reader_disclosure"] = {**self.ref("90-audit/only-internal.md"), "quote": text}
        self.save_semantic(); self.save()
        self.assertIn("reader-visible disclosure", str(gate.validate(self.root)))

    def test_ledger_change_invalidates_semantic_review(self):
        self.add_open_candidate()
        with (self.root / "90-audit/uncertainty-candidates.jsonl").open("a") as f:
            f.write("\n")
        self.assertIn("stale canonical text review ledger", str(gate.validate(self.root)))

    def test_claimed_closed_item_still_needs_real_closure_evidence(self):
        self.add_open_candidate()
        path = self.root / "90-audit/uncertainty-adjudication.jsonl"
        decision = json.loads(path.read_text())
        decision["status"] = "resolved_confirmed"
        write(path, decision)
        (self.root / "90-audit/uncertain-items.jsonl").write_text("")
        self.semantic["candidate_results"][0]["result"] = "verified"
        self.save_semantic(); self.save()
        self.assertIn("closure evidence", str(gate.validate(self.root)))

    def test_semantics_policy_change_requires_new_review(self):
        self.record["text_semantics_policy_sha256"] = "obsolete-policy"
        self.save()
        self.assertIn("text/semantics policy changed", str(gate.validate(self.root)))

    def test_both_existing_gates_enforce_pending(self):
        self.record.update(status="pending", review=None)
        self.save()
        here = Path(__file__).resolve().parent
        commands = [(here / "validate_workspace.py", "--stage", "modernized"),
                    (here / "validate_workspace.py", "--stage", "publication"),
                    (here.parents[1] / "chaoyun-quality-publisher/scripts/audit_publication.py",)]
        for script, *extra in commands:
            result = subprocess.run([sys.executable, str(script), str(self.root), *extra], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("layout proof requires actual review: pending", result.stdout, result.stderr)


if __name__ == "__main__":
    unittest.main()
