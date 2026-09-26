#!/usr/bin/env python3
"""Smoke-test Chaoyun workspace initialization and contract validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfWriter


HERE = Path(__file__).resolve().parent
PUBLISH_AUDIT = HERE.parent.parent / "chaoyun-quality-publisher" / "scripts" / "audit_publication.py"


def run(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([sys.executable, *args], text=True, capture_output=True, encoding="utf-8")
    if result.returncode != expect:
        raise AssertionError(f"expected {expect}, got {result.returncode}: {result.stdout}\n{result.stderr}")
    return result


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="chaoyun-skill-test-") as temporary:
        temp = Path(temporary)
        source = temp / "source.pdf"
        source.write_bytes(b"%PDF-1.4\n% smoke fixture\n%%EOF\n")
        workspace = temp / "workspace"
        run(
            str(HERE / "init_workspace.py"),
            str(source),
            str(workspace),
            "--copy-source",
            "--edition-label",
            "现代白话版",
            "--target-reader",
            "现代普通读者",
        )
        if (workspace / "00-intake/source.pdf").read_bytes() != source.read_bytes():
            raise AssertionError("staged source differs from the original")

        book_id = json.loads((workspace / "book.json").read_text(encoding="utf-8"))["book_id"]
        record = {
            "schema_version": "1.0",
            "book_id": book_id,
            "page_id": "P000001",
            "block_id": "P000001-B001",
            "source_page": 1,
            "block_type": "body",
            "bbox": [0, 0, 100, 100],
            "source_image": None,
            "source_text": "天地玄黄",
            "normalized_text": "天地玄黄",
            "modern_text": "天是玄色的，地是黄色的。",
            "language": "lzh",
            "operation": "translate",
            "disposition": "translated",
            "confidence": 0.98,
            "evidence": [],
            "notes": [],
        }
        for relative in [
            "20-source/blocks.jsonl",
            "30-normalized/blocks.jsonl",
            "40-modernized/blocks.jsonl",
            "50-edited/blocks.jsonl",
        ]:
            (workspace / relative).write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

        publication = workspace / "60-publication"
        (publication / "modern-reading.md").write_text("# 测试\n\n天是玄色的。\n", encoding="utf-8")
        release_pdf = publication / "source·现代白话版.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with release_pdf.open("wb") as handle:
            writer.write(handle)
        write_json(
            workspace / "90-audit/quality-report.json",
            {
                "grade": "B",
                "semantic_audit": {"passed": True},
                "structural_audit": {"passed": True},
                "publication": {"pdf": "60-publication/source·现代白话版.pdf", "pdf_pages": 1},
            },
        )
        (workspace / "90-audit/quality-report.md").write_text("# Quality report\n\nGrade: B\n", encoding="utf-8")

        run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "publication")
        run(str(PUBLISH_AUDIT), str(workspace))

        bad = dict(record)
        bad["block_id"] = "P000001-B999"
        (workspace / "30-normalized/blocks.jsonl").write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")
        failed = run(str(HERE / "validate_workspace.py"), str(workspace), "--stage", "normalized", expect=1)
        if "block identity mismatch" not in failed.stdout:
            raise AssertionError("validator did not report the expected identity mismatch")

    print("Chaoyun skill self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
