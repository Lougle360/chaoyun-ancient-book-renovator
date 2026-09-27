#!/usr/bin/env python3
"""Audit a declared reader-facing publication and its local Markdown assets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
RAW_MARKUP = re.compile(r"</?(?:table|tbody|thead|tr|td|th)(?:\s[^>]*)?>", re.I)
INTERNAL_MESSAGES = (
    "本地硬校验仍未通过",
    "自动修复后核义模型仍建议修订",
    "已记录供后续自动处理",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    report = root / "90-audit/quality-report.json"
    report_data: dict = {}
    if report.is_file():
        try:
            report_data = json.loads(report.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid quality-report.json: {exc}")

    book_file = root / "book.json"
    book_data: dict = {}
    if book_file.is_file():
        try:
            book_data = json.loads(book_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid book.json: {exc}")

    publication = report_data.get("publication")
    publication = publication if isinstance(publication, dict) else {}
    book_declared_pdf = book_data.get("release_filename")
    report_declared_pdf = publication.get("pdf")
    if book_declared_pdf and report_declared_pdf and str(book_declared_pdf).replace("\\", "/") != str(report_declared_pdf).replace("\\", "/"):
        errors.append(
            "quality report PDF differs from book.json.release_filename; "
            f"got {report_declared_pdf!r}/{book_declared_pdf!r}"
        )
    declared_pdf = book_declared_pdf or report_declared_pdf
    if declared_pdf:
        pdf = (root / str(declared_pdf)).resolve()
    else:
        pdf = (root / "60-publication/modern-reading.pdf").resolve()
        warnings.append("official PDF is not declared; using 60-publication/modern-reading.pdf")
    try:
        pdf.relative_to(root)
    except ValueError:
        errors.append(f"declared official PDF escapes workspace: {declared_pdf!r}")
        pdf = root / "60-publication/modern-reading.pdf"

    required = [
        root / "60-publication/modern-reading.md",
        pdf,
        report,
        root / "90-audit/quality-report.md",
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty: {path.relative_to(root)}")

    markdown = required[0]
    if markdown.is_file():
        text = markdown.read_text(encoding="utf-8")
        raw_tags = RAW_MARKUP.findall(text)
        if raw_tags:
            errors.append(f"literal table markup remains in modern-reading.md: {len(raw_tags)} tags")
        for message in INTERNAL_MESSAGES:
            count = text.count(message)
            if count:
                errors.append(f"internal pipeline message leaked into reader text: {message!r} ({count})")
        for target in IMAGE.findall(text):
            raw = target.strip()
            clean = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw.split(maxsplit=1)[0]
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", clean):
                errors.append(f"remote image reference: {clean}")
                continue
            candidate = (markdown.parent / clean).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                errors.append(f"image escapes workspace: {clean}")
                continue
            if not candidate.is_file():
                errors.append(f"missing image: {clean}")

    if pdf.is_file() and not pdf.read_bytes()[:5] == b"%PDF-":
        errors.append(f"official PDF does not have a PDF header: {pdf.relative_to(root)}")

    allowed_pdfs = {pdf.resolve(), (root / "60-publication/modern-reading.pdf").resolve(),
                    (root / "60-publication/source-comparison.pdf").resolve()}
    extra_pdfs = [path for path in (root / "60-publication").glob("*.pdf") if path.resolve() not in allowed_pdfs]
    if extra_pdfs:
        errors.append("ambiguous extra PDFs in publication root: " + ", ".join(path.name for path in extra_pdfs))

    data = report_data
    if report.is_file() and data:
        if data.get("grade") not in {"A", "B", "C", "D"}:
            errors.append("quality-report.json requires grade A, B, C, or D")
        if "semantic_audit" not in data or "structural_audit" not in data:
            errors.append("quality-report.json requires semantic_audit and structural_audit")
        for key in ("semantic_audit", "structural_audit"):
            audit = data.get(key)
            if audit is not None and not isinstance(audit, dict):
                errors.append(f"quality-report.json {key} must be an object")

        source_pages = data.get("source_pages_total") or data.get("source_pages") or data.get("pages")
        semantic = data.get("semantic_audit")
        vision = data.get("vision_reconstruction")
        successful = semantic.get("page_level_visual_coverage") if isinstance(semantic, dict) else None
        if successful is None and isinstance(vision, dict):
            successful = vision.get("successful_pages")
        if data.get("grade") in {"A", "B"} and isinstance(source_pages, int):
            if successful != source_pages:
                errors.append(
                    "grade A/B scan publication requires complete page-level visual coverage; "
                    f"got {successful!r}/{source_pages}"
                )

        book_source_pages = book_data.get("source_pdf_pages")
        if isinstance(book_source_pages, int) and isinstance(source_pages, int):
            if book_source_pages != source_pages:
                errors.append(
                    "source-page accounting differs between book.json and quality report; "
                    f"got {book_source_pages}/{source_pages}"
                )

        uncertainty_summary = data.get("uncertainty_summary")
        if not isinstance(uncertainty_summary, dict):
            errors.append("quality-report.json requires uncertainty_summary")
        open_ledger = root / "90-audit/uncertain-items.jsonl"
        if not open_ledger.is_file():
            errors.append("missing 90-audit/uncertain-items.jsonl")
            open_items = []
        else:
            try:
                open_items = [json.loads(line) for line in open_ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
            except (json.JSONDecodeError, OSError) as exc:
                errors.append(f"invalid uncertain-items.jsonl: {exc}")
                open_items = []
        if isinstance(uncertainty_summary, dict) and uncertainty_summary.get("open_material") != len(open_items):
            errors.append("quality-report uncertainty_summary.open_material mismatch")
        high_open = sum(1 for row in open_items if row.get("reader_impact") == "high")
        if data.get("grade") == "A" and open_items:
            errors.append("grade A cannot contain open_material uncertainty")
        if data.get("grade") == "B" and high_open:
            errors.append("grade B cannot contain high-impact open_material uncertainty")

    if pdf.is_file() and pdf.read_bytes()[:5] == b"%PDF-":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(pdf))
            actual_pages = len(reader.pages)
            reported_pages = publication.get("pdf_pages")
            if isinstance(reported_pages, int) and reported_pages != actual_pages:
                errors.append(f"official PDF page count differs from report: {actual_pages}/{reported_pages}")

            inspected = publication.get("rendered_pages_inspected")
            if actual_pages <= 300 and isinstance(inspected, int) and inspected != actual_pages:
                errors.append(
                    "short/medium book requires full rendered-page inspection; "
                    f"got {inspected}/{actual_pages}"
                )

            internal_links = 0
            for page in reader.pages:
                annotations = page.get("/Annots") or []
                for annotation_ref in annotations:
                    annotation = annotation_ref.get_object()
                    if annotation.get("/Subtype") != "/Link":
                        continue
                    if annotation.get("/Dest") is not None:
                        internal_links += 1
                        continue
                    action = annotation.get("/A")
                    if action and action.get("/S") == "/GoTo":
                        internal_links += 1

            try:
                outline = reader.outline
                outline_items = len(outline) if isinstance(outline, list) else int(bool(outline))
            except Exception:
                outline_items = 0

            if actual_pages > 5 and internal_links == 0:
                errors.append("official PDF has no internal clickable TOC links")
            if actual_pages > 5 and outline_items == 0:
                errors.append("official PDF has no bookmarks/outlines")
        except ImportError:
            warnings.append("pypdf unavailable; PDF page, link, and bookmark checks skipped")
        except Exception as exc:
            errors.append(f"could not inspect official PDF structure: {exc}")

    result = {
        "valid": not errors,
        "official_pdf": str(pdf.relative_to(root)) if pdf.is_relative_to(root) else str(pdf),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
