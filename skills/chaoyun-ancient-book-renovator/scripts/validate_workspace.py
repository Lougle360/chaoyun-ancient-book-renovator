#!/usr/bin/env python3
"""Validate Chaoyun workspace structure and cross-stage block identity."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path


STAGE_FILES = {
    "source": "20-source/blocks.jsonl",
    "normalized": "30-normalized/blocks.jsonl",
    "modernized": "40-modernized/blocks.jsonl",
    "edited": "50-edited/blocks.jsonl",
}
ORDER = ["source", "normalized", "modernized", "edited"]
REQUIRED_PREPUBLICATION_STAGES = [
    "intake", "diagnosis", "source", "source_adjudicated",
    "normalized", "modernized", "edited", "final_adjudicated",
]
REQUIRED = {"schema_version", "book_id", "page_id", "block_id", "source_page", "block_type", "source_text", "disposition"}
PAGE_ID = re.compile(r"^P\d{6}$")
UNCERTAINTY_STATUSES = {"resolved_confirmed", "resolved_noncontent", "resolved_structural", "resolved_duplicate", "open_material"}
READER_IMPACTS = {"none", "low", "medium", "high"}


def requires_editorial_report(book: dict) -> bool:
    target = str(book.get("target_reader") or "")
    label = str(book.get("edition_label") or "")
    return "普通" in target or "ordinary" in target.lower() or "现代白话" in label


def validate_editorial_report(root: Path, high_open: int, errors: list[str]) -> None:
    path = root / "50-edited" / "editorial-report.json"
    if not path.is_file():
        errors.append("ordinary-reader edition requires 50-edited/editorial-report.json")
        return
    try:
        report = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid editorial-report.json: {exc}")
        return

    reader_validator = Path(__file__).resolve().parents[2] / "chaoyun-reading-editor" / "scripts" / "validate_reader_value.py"
    if not reader_validator.is_file():
        errors.append("missing chaoyun-reading-editor reader-value validator")
        return
    spec = importlib.util.spec_from_file_location("chaoyun_reader_value_contract", reader_validator)
    if spec is None or spec.loader is None:
        errors.append("could not load reader-value validator")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reader_errors, reader_counts = module.validate(root)
    errors.extend(reader_errors)
    try:
        reader_aids = read_json(root / "50-edited/reader-aids.json")
    except (OSError, ValueError, json.JSONDecodeError):
        reader_aids = {}

    nature = report.get("book_nature") if isinstance(report.get("book_nature"), dict) else {}
    for key in ("summary", "attribution_basis"):
        if not str(nature.get(key) or "").strip():
            errors.append(f"editorial-report book_nature.{key} is required")
    if nature.get("compilation_status") not in {"single_work", "layered_compilation", "uncertain"}:
        errors.append("editorial-report book_nature.compilation_status is invalid")

    toc = report.get("source_toc") if isinstance(report.get("source_toc"), dict) else {}
    if toc.get("status") == "reconstructed":
        if toc.get("physical_page_mapping_verified") is not True:
            errors.append("editorial-report source TOC physical-page mapping is not verified")
        if not isinstance(toc.get("source_pages"), list) or not toc.get("source_pages"):
            errors.append("editorial-report reconstructed source TOC requires source_pages")
        if not isinstance(toc.get("entry_count"), int) or toc.get("entry_count", 0) < 1:
            errors.append("editorial-report reconstructed source TOC requires entries")
    elif toc.get("status") == "source_absent_with_reason":
        if not str(toc.get("reason") or "").strip():
            errors.append("editorial-report absent source TOC requires a reason")
    else:
        errors.append("editorial-report source_toc.status is invalid")

    structure = report.get("reader_structure") if isinstance(report.get("reader_structure"), dict) else {}
    if not isinstance(structure.get("entry_count"), int) or structure.get("entry_count", 0) < 1:
        errors.append("editorial-report reader structure requires entries")
    if structure.get("editor_additions_labeled") is not True:
        errors.append("editorial-report requires labeled editor additions")

    glossary = report.get("glossary") if isinstance(report.get("glossary"), dict) else {}
    if glossary.get("status") == "completed":
        entries = glossary.get("entry_count")
        if not isinstance(entries, int) or entries < 1 or glossary.get("entries_with_first_occurrence") != entries:
            errors.append("editorial-report glossary entries require first-occurrence evidence")
        for report_key, count_key in (
            ("entry_count", "glossary_entries"),
            ("entries_with_first_occurrence", "glossary_with_first_occurrence"),
            ("core_entry_count", "glossary_core"),
            ("reader_review_sampled", "glossary_sampled"),
        ):
            if glossary.get(report_key) != reader_counts.get(count_key):
                errors.append(f"editorial-report glossary.{report_key} does not match reader-aids.json")
    elif glossary.get("status") == "not_applicable_with_reason":
        if not str(glossary.get("reason") or "").strip():
            errors.append("editorial-report omitted glossary requires a reason")
    else:
        errors.append("editorial-report glossary.status is invalid")

    reader_value = report.get("reader_value") if isinstance(report.get("reader_value"), dict) else {}
    aids_review = reader_aids.get("reader_review") if isinstance(reader_aids.get("reader_review"), dict) else {}
    expected_reader_value = {
        "introduction_sections": reader_counts.get("introduction_sections"),
        "required_questions_passed": reader_counts.get("reader_review_questions"),
        "producer": aids_review.get("producer"),
        "reviewer": aids_review.get("reviewer"),
        "status": aids_review.get("status"),
    }
    for key, expected in expected_reader_value.items():
        if reader_value.get(key) != expected:
            errors.append(f"editorial-report reader_value.{key} does not match reader-aids.json")

    figures = report.get("figures") if isinstance(report.get("figures"), dict) else {}
    figure_counts = [figures.get(key) for key in (
        "content_figures_total", "content_figures_rendered", "content_figures_guided"
    )]
    if any(not isinstance(value, int) or value < 0 for value in figure_counts) or len(set(figure_counts)) != 1:
        errors.append("editorial-report content figures must all be rendered and specifically guided")

    semantic = report.get("semantic_review") if isinstance(report.get("semantic_review"), dict) else {}
    if semantic.get("high_impact_open") != high_open:
        errors.append("editorial-report semantic_review.high_impact_open mismatch")
    if high_open and semantic.get("status") != "blocked_by_high_impact_open_items":
        errors.append("editorial-report must mark active high-impact items as blocking")
    if not high_open and semantic.get("status") not in {"passed", "passed_with_ledger"}:
        errors.append("editorial-report semantic_review.status is invalid")

    pipeline = report.get("pipeline_language_scan") if isinstance(report.get("pipeline_language_scan"), dict) else {}
    if pipeline.get("forbidden_matches") != 0:
        errors.append("editorial-report reader layer contains internal pipeline language")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{number}")
        value["_line"] = number
        records.append(value)
    return records


def validate_uncertainties(root: Path, errors: list[str]) -> dict[str, int]:
    audit = root / "90-audit"
    candidate_path = audit / "uncertainty-candidates.jsonl"
    decision_path = audit / "uncertainty-adjudication.jsonl"
    open_path = audit / "uncertain-items.jsonl"
    for path in (candidate_path, decision_path, open_path):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(root)}")
            return {}
    try:
        candidates = read_jsonl(candidate_path)
        decisions = read_jsonl(decision_path)
        open_items = read_jsonl(open_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        return {}
    helper = Path(__file__).resolve().parents[2] / "chaoyun-uncertainty-adjudicator" / "scripts" / "project_open_items.py"
    if not helper.is_file():
        errors.append("missing chaoyun-uncertainty-adjudicator validator")
        return {}
    spec = importlib.util.spec_from_file_location("chaoyun_uncertainty_contract", helper)
    if spec is None or spec.loader is None:
        errors.append("could not load chaoyun uncertainty validator")
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors.extend(module.validate(root, candidates, decisions))
    expected = module.projection(decisions)
    comparable_open_items = [{key: value for key, value in row.items() if key != "_line"} for row in open_items]
    if comparable_open_items != expected:
        errors.append("uncertain-items.jsonl is not the current open-material projection")
    active = module.active_decisions(decisions)
    high_open = sum(1 for row in active if row.get("status") == "open_material" and row.get("reader_impact") == "high")
    return {"candidates": len(candidates), "adjudications": len(decisions),
            "active_adjudications": len(active), "open_material": len(open_items), "high_open": high_open}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--stage", choices=["source", "normalized", "modernized", "edited", "publication"], default="publication")
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    try:
        book = read_json(root / "book.json")
        state = read_json(root / "run-state.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1

    book_id = book.get("book_id")
    if state.get("book_id") != book_id:
        errors.append("book_id differs between book.json and run-state.json")

    target_index = len(ORDER) - 1 if args.stage == "publication" else ORDER.index(args.stage)
    source_ids: set[str] | None = None
    source_pages_seen: set[int] = set()
    counts: dict[str, int] = {}
    for stage in ORDER[: target_index + 1]:
        path = root / STAGE_FILES[stage]
        if not path.is_file():
            errors.append(f"missing {STAGE_FILES[stage]}")
            continue
        try:
            records = read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            continue
        counts[stage] = len(records)
        ids: set[str] = set()
        for record in records:
            missing = sorted(REQUIRED - record.keys())
            if missing:
                errors.append(f"{stage}:{record['_line']} missing {','.join(missing)}")
            if record.get("book_id") != book_id:
                errors.append(f"{stage}:{record['_line']} wrong book_id")
            page_id = record.get("page_id")
            if not isinstance(page_id, str) or not PAGE_ID.fullmatch(page_id):
                errors.append(f"{stage}:{record['_line']} invalid page_id {page_id!r}")
            source_page = record.get("source_page")
            if not isinstance(source_page, int) or source_page < 1:
                errors.append(f"{stage}:{record['_line']} invalid source_page {source_page!r}")
            elif stage == "source":
                source_pages_seen.add(source_page)
            block_id = record.get("block_id")
            if not block_id:
                errors.append(f"{stage}:{record['_line']} empty block_id")
            elif block_id in ids:
                errors.append(f"{stage}:{record['_line']} duplicate block_id {block_id}")
            else:
                ids.add(block_id)
                if isinstance(page_id, str) and not block_id.startswith(page_id + "-"):
                    errors.append(f"{stage}:{record['_line']} block_id does not start with page_id")
        if source_ids is None:
            source_ids = ids
        elif ids != source_ids:
            missing_ids = sorted(source_ids - ids)[:10]
            extra_ids = sorted(ids - source_ids)[:10]
            errors.append(f"{stage} block identity mismatch; missing={missing_ids}, extra={extra_ids}")

    expected_pages = book.get("source_pages")
    if isinstance(expected_pages, int) and expected_pages > 0 and source_pages_seen:
        expected = set(range(1, expected_pages + 1))
        if source_pages_seen != expected:
            errors.append(
                "source page coverage mismatch; "
                f"missing={sorted(expected - source_pages_seen)[:20]}, "
                f"extra={sorted(source_pages_seen - expected)[:20]}"
            )

    uncertainty_counts: dict[str, int] = {}
    if args.stage == "publication":
        uncertainty_counts = validate_uncertainties(root, errors)
        declared_pdf = book.get("release_filename")
        if not declared_pdf:
            try:
                report = read_json(root / "90-audit/quality-report.json")
                publication = report.get("publication")
                if isinstance(publication, dict):
                    declared_pdf = publication.get("pdf")
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        declared_pdf = declared_pdf or "60-publication/modern-reading.pdf"
        required_outputs = [
            "60-publication/modern-reading.md",
            str(declared_pdf),
            "90-audit/quality-report.json",
            "90-audit/quality-report.md",
        ]
        for relative in required_outputs:
            path = (root / relative).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                errors.append(f"publication output escapes workspace: {relative}")
                continue
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing or empty {relative}")
        stages = state.get("stages") if isinstance(state.get("stages"), dict) else {}
        for stage in REQUIRED_PREPUBLICATION_STAGES:
            status = (stages.get(stage) or {}).get("status") if isinstance(stages.get(stage), dict) else None
            if status not in {"passed", "passed_with_ledger"}:
                errors.append(f"run-state stage {stage} is not accepted: {status!r}")
        for stage in ORDER:
            status = (stages.get(stage) or {}).get("status") if isinstance(stages.get(stage), dict) else None
            if status in {"passed", "passed_with_ledger"} and not (root / STAGE_FILES[stage]).is_file():
                errors.append(f"run-state marks {stage} {status} but {STAGE_FILES[stage]} is missing")

        try:
            report_data = read_json(root / "90-audit/quality-report.json")
        except (OSError, ValueError, json.JSONDecodeError):
            report_data = {}
        grade = report_data.get("grade")
        summary = report_data.get("uncertainty_summary")
        if not isinstance(summary, dict):
            errors.append("quality-report.json requires uncertainty_summary")
        else:
            for key in ("candidates", "adjudications", "active_adjudications", "open_material"):
                if summary.get(key) != uncertainty_counts.get(key):
                    errors.append(f"quality-report uncertainty_summary.{key} mismatch")
        if grade == "A" and uncertainty_counts.get("open_material", 0):
            errors.append("grade A cannot contain open_material uncertainty")
        if grade == "B" and uncertainty_counts.get("high_open", 0):
            errors.append("grade B cannot contain high-impact open_material uncertainty")
        if requires_editorial_report(book):
            validate_editorial_report(root, uncertainty_counts.get("high_open", 0), errors)

    result = {"valid": not errors, "stage": args.stage, "counts": counts,
              "uncertainties": uncertainty_counts, "warnings": warnings, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
