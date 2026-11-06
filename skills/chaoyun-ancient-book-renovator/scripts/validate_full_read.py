"""Shared mechanical whole-manuscript reading check; never proves comprehension."""
from __future__ import annotations

import json
from pathlib import Path


def declares_partial(record: dict) -> bool:
    return (
        "new_full_section_read_this_run" in record and record["new_full_section_read_this_run"] is not True
    ) or any(
        flag in record and record[flag] is not False
        for flag in ("partial", "inherited", "hash_only", "local_regression")
    )


def validate_full_read_coverage(root: Path, manuscript_path: Path, errors: list[str]) -> None:
    """Reject partial declarations and require evidenced coverage of every line."""
    text = manuscript_path.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if not text.strip():
        errors.append("final-pass set cannot cover an empty or whitespace-only manuscript")
        return
    paths = sorted((root / "50-edited/review-history/full-passes").glob("*.json"))
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("expected object")
        except (OSError, ValueError) as exc:
            errors.append(f"final pass {path.name} is unreadable: {exc}")
            continue
        if record.get("review_mode") != "full_read":
            errors.append(f"final pass {path.name} must declare review_mode=full_read; local or inherited regressions do not count")
        if declares_partial(record):
            errors.append(f"final pass {path.name} declares partial, inherited or hash-only reading")
        sections = record.get("sections_covered")
        if not isinstance(sections, list) or not sections:
            errors.append(f"final pass {path.name} has no verifiable continuous line coverage")
            continue
        intervals = []
        for index, section in enumerate(sections, 1):
            if not isinstance(section, dict):
                errors.append(f"final pass {path.name} section {index} has no start_line/end_line; chapter names cannot verify coverage")
                continue
            start, end = section.get("start_line"), section.get("end_line")
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= line_count:
                errors.append(f"final pass {path.name} section {index} has an invalid manuscript line range")
                continue
            evidence = section.get("evidence")
            if not isinstance(evidence, str) or not evidence.strip():
                errors.append(f"final pass {path.name} section {index} has empty evidence; range labels alone do not count")
                continue
            if declares_partial(section) or (
                "review_mode" in section and section["review_mode"] != "full_read"
            ):
                errors.append(f"final pass {path.name} section {index} declares partial or inherited reading")
                continue
            intervals.append((start, end))
        cursor, missing = 1, []
        for start, end in sorted(intervals):
            if start > cursor:
                missing.append([cursor, start - 1])
            cursor = max(cursor, end + 1)
        if cursor <= line_count:
            missing.append([cursor, line_count])
        if missing:
            errors.append(f"final pass {path.name} does not cover every manuscript line; missing_ranges={missing}")
