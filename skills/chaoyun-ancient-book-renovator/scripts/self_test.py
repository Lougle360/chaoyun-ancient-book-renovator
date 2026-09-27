#!/usr/bin/env python3
"""Exercise Chaoyun initialization, adjudication, grading, migration, and publication gates."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfWriter


HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
PUBLISH_AUDIT = SKILLS / "chaoyun-quality-publisher" / "scripts" / "audit_publication.py"
INSTALL_PDF = SKILLS / "chaoyun-quality-publisher" / "scripts" / "install_official_pdf.py"
PROJECT_OPEN = SKILLS / "chaoyun-uncertainty-adjudicator" / "scripts" / "project_open_items.py"
MIGRATE = SKILLS / "chaoyun-uncertainty-adjudicator" / "scripts" / "migrate_legacy_ledger.py"


def run(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args], text=True, capture_output=True,
        encoding="utf-8", errors="replace",
    )
    if result.returncode != expect:
        raise AssertionError(f"expected {expect}, got {result.returncode}: {result.stdout}\n{result.stderr}")
    return result


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def make_pdf(path: Path, pages: int = 1) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    with path.open("wb") as handle:
        writer.write(handle)


def set_accepted_stages(workspace: Path) -> None:
    state_path = workspace / "run-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    for stage in ("intake", "diagnosis", "source", "source_adjudicated", "normalized", "modernized", "edited", "final_adjudicated"):
        state["stages"][stage]["status"] = "passed"
    write_json(state_path, state)


def quality_report(workspace: Path, grade: str, counts: dict[str, int]) -> None:
    write_json(
        workspace / "90-audit/quality-report.json",
        {
            "grade": grade,
            "source_pages": 1,
            "semantic_audit": {"passed": True, "page_level_visual_coverage": 1},
            "structural_audit": {"passed": True},
            "uncertainty_summary": counts,
            "publication": {"pdf": "60-publication/source·现代白话版.pdf", "pdf_pages": 1},
        },
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="chaoyun-skill-test-") as temporary:
        temp = Path(temporary)
        source = temp / "source.pdf"
        source.write_bytes(b"%PDF-1.4\n% intake fixture\n%%EOF\n")
        workspace = temp / "workspace"
        run(str(HERE / "init_workspace.py"), str(source), str(workspace), "--copy-source",
            "--edition-label", "现代白话版", "--target-reader", "现代普通读者")
        if (workspace / "00-intake/source.pdf").read_bytes() != source.read_bytes():
            raise AssertionError("staged source differs from the original")
        set_accepted_stages(workspace)

        book_path = workspace / "book.json"
        book = json.loads(book_path.read_text(encoding="utf-8"))
        book["source_pages"] = 1
        book["source_pdf_pages"] = 1
        write_json(book_path, book)
        book_id = book["book_id"]
        record = {
            "schema_version": "1.0", "book_id": book_id, "page_id": "P000001", "block_id": "P000001-B001",
            "source_page": 1, "block_type": "body", "bbox": [0, 0, 100, 100], "source_image": None,
            "source_text": "天地玄黄", "normalized_text": "天地玄黄", "modern_text": "天是玄色的，地是黄色的。",
            "language": "lzh", "operation": "translate", "disposition": "translated", "confidence": 0.98,
            "evidence": [], "notes": [],
        }
        for relative in ("20-source/blocks.jsonl", "30-normalized/blocks.jsonl", "40-modernized/blocks.jsonl", "50-edited/blocks.jsonl"):
            write_jsonl(workspace / relative, [record])

        candidates = [{
            "schema_version": "1.1", "candidate_id": "UC000001", "page_id": "P000001",
            "block_id": "P000001-B001", "origin_stage": "source", "kind": "glyph", "excerpt": "玄",
            "reason": "fixture", "source_image": None, "severity": "low", "created_by": "self-test",
        }]
        decisions = [{
            "schema_version": "1.1", "adjudication_id": "UA000001", "candidate_ids": ["UC000001"],
            "status": "resolved_confirmed", "reader_impact": "none", "active": True, "supersedes": None,
            "issue_id": None, "page_id": "P000001", "block_id": "P000001-B001",
            "rationale": "The fixture glyph is explicit.", "evidence": [], "before": None, "after": None,
            "reviewed_at": "2026-01-01T00:00:00Z", "reviewer": "self-test",
        }]
        candidate_path = workspace / "90-audit/uncertainty-candidates.jsonl"
        decision_path = workspace / "90-audit/uncertainty-adjudication.jsonl"
        write_jsonl(candidate_path, candidates)
        write_jsonl(decision_path, decisions)
        run(str(PROJECT_OPEN), str(workspace))
        run(str(PROJECT_OPEN), str(workspace), "--check")

        publication = workspace / "60-publication"
        (publication / "modern-reading.md").write_text("# 测试\n\n天是玄色的。\n", encoding="utf-8")
        candidate_pdf = temp / "candidate.pdf"
        make_pdf(candidate_pdf)
        run(str(INSTALL_PDF), str(workspace), str(candidate_pdf), "--expected-pages", "1")
        (workspace / "90-audit/quality-report.md").write_text("# Quality report\n", encoding="utf-8")
        counts = {"candidates": 1, "adjudications": 1, "active_adjudications": 1, "open_material": 0}
        quality_report(workspace, "A", counts)
        run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "publication")
        run(str(PUBLISH_AUDIT), str(workspace))

        # A high-impact open item must make Grade B fail in both gates.
        candidates.append({
            "schema_version": "1.1", "candidate_id": "UC000002", "page_id": "P000001",
            "block_id": "P000001-B001", "origin_stage": "source", "kind": "missing", "excerpt": "黄",
            "reason": "high-risk fixture", "source_image": None, "severity": "high", "created_by": "self-test",
        })
        decisions.append({
            "schema_version": "1.1", "adjudication_id": "UA000002", "candidate_ids": ["UC000002"],
            "status": "open_material", "reader_impact": "high", "active": True, "supersedes": None,
            "issue_id": "UI-UC000002", "page_id": "P000001", "block_id": "P000001-B001",
            "rationale": "A central glyph remains unreadable.", "evidence": [], "before": None, "after": None,
            "reviewed_at": "2026-01-01T00:00:01Z", "reviewer": "self-test",
        })
        write_jsonl(candidate_path, candidates)
        write_jsonl(decision_path, decisions)
        run(str(PROJECT_OPEN), str(workspace))
        quality_report(workspace, "B", {"candidates": 2, "adjudications": 2, "active_adjudications": 2, "open_material": 1})
        grade_failure = run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "publication", expect=1)
        if "grade B cannot contain high-impact" not in grade_failure.stdout:
            raise AssertionError("workspace validator did not enforce Grade B uncertainty risk")
        audit_failure = run(str(PUBLISH_AUDIT), str(workspace), expect=1)
        if "grade B cannot contain high-impact" not in audit_failure.stdout:
            raise AssertionError("publication audit did not enforce Grade B uncertainty risk")

        # A later decision supersedes rather than overwrites the first decision.
        decisions[-1]["active"] = False
        decisions.append({
            "schema_version": "1.1", "adjudication_id": "UA000003", "candidate_ids": ["UC000002"],
            "status": "resolved_confirmed", "reader_impact": "none", "active": True, "supersedes": "UA000002",
            "issue_id": None, "page_id": "P000001", "block_id": "P000001-B001",
            "rationale": "Independent evidence confirms the glyph.", "evidence": [], "before": None, "after": None,
            "reviewed_at": "2026-01-01T00:00:02Z", "reviewer": "self-test",
        })
        write_jsonl(decision_path, decisions)
        run(str(PROJECT_OPEN), str(workspace))
        quality_report(workspace, "A", {"candidates": 2, "adjudications": 3, "active_adjudications": 2, "open_material": 0})
        run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "publication")
        run(str(PUBLISH_AUDIT), str(workspace))

        # Projection drift and cross-stage block drift must still fail.
        write_jsonl(workspace / "90-audit/uncertain-items.jsonl", [{
            "schema_version": "1.1", "issue_id": "UI-BAD", "adjudication_id": "UA-BAD",
            "status": "open", "reader_impact": "high", "note": "invalid fixture",
        }])
        mismatch = run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "publication", expect=1)
        if "not the current open-material projection" not in mismatch.stdout:
            raise AssertionError("validator did not reject an inconsistent open-item projection")
        run(str(PROJECT_OPEN), str(workspace))
        bad = dict(record)
        bad["block_id"] = "P000001-B999"
        write_jsonl(workspace / "30-normalized/blocks.jsonl", [bad])
        failed = run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "normalized", expect=1)
        if "block identity mismatch" not in failed.stdout:
            raise AssertionError("validator did not report the expected identity mismatch")

        # A legacy ledger is backed up and migrated to stable candidate IDs.
        legacy = temp / "legacy-workspace"
        run(str(HERE / "init_workspace.py"), str(source), str(legacy), "--edition-label", "现代白话版")
        legacy_item = {
            "schema_version": "1.0", "page_id": "P000001", "block_id": "P000001-B001",
            "severity": "medium", "status": "open", "note": "legacy fixture", "source_image": None,
        }
        write_jsonl(legacy / "90-audit/uncertain-items.jsonl", [legacy_item])
        write_jsonl(legacy / "90-audit/uncertainty-adjudication.jsonl", [{
            "schema_version": "1.0", "adjudication_id": "U001", "origin": "original_99",
            "original": legacy_item, "status": "open_material", "rationale": "Still materially uncertain.",
            "reviewed_at": "2026-01-01T00:00:00Z", "reviewer": "legacy-review",
        }])
        migration = run(str(MIGRATE), str(legacy))
        migrated = json.loads(migration.stdout)
        if migrated["candidates"] != 1 or migrated["adjudications"] != 1 or migrated["needs_review"] != 0:
            raise AssertionError("legacy migration did not preserve the adjudicated candidate")
        run(str(PROJECT_OPEN), str(legacy))
        run(str(PROJECT_OPEN), str(legacy), "--check")
        if not any((legacy / "90-audit/legacy-uncertainty-migration").iterdir()):
            raise AssertionError("legacy migration did not create a backup")

    print("Chaoyun skill self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
