#!/usr/bin/env python3
"""Validate uncertainty adjudication and project material open items."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATUSES = {"resolved_confirmed", "resolved_noncontent", "resolved_structural", "resolved_duplicate", "open_material"}
IMPACTS = {"none", "low", "medium", "high"}


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise ValueError(f"missing {path}")
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{number}")
        rows.append(value)
    return rows


def validate(candidates: list[dict], decisions: list[dict]) -> list[str]:
    errors: list[str] = []
    candidate_ids = [row.get("candidate_id") for row in candidates]
    if any(not value for value in candidate_ids):
        errors.append("every candidate requires candidate_id")
    if len(set(candidate_ids)) != len(candidate_ids):
        errors.append("duplicate candidate_id")
    decision_ids = [row.get("adjudication_id") for row in decisions]
    if any(not value for value in decision_ids):
        errors.append("every adjudication requires adjudication_id")
    if len(set(decision_ids)) != len(decision_ids):
        errors.append("duplicate adjudication_id")
    candidate_set = set(candidate_ids)
    referenced: list[str] = []
    for row in decisions:
        decision_id = row.get("adjudication_id")
        if row.get("status") not in STATUSES:
            errors.append(f"{decision_id} invalid status")
        if row.get("reader_impact") not in IMPACTS:
            errors.append(f"{decision_id} invalid reader_impact")
        ids = row.get("candidate_ids")
        if not isinstance(ids, list) or not ids:
            errors.append(f"{decision_id} requires candidate_ids")
            continue
        referenced.extend(ids)
        unknown = sorted(set(ids) - candidate_set)
        if unknown:
            errors.append(f"{decision_id} unknown candidates {unknown}")
        if not row.get("rationale"):
            errors.append(f"{decision_id} missing rationale")
        if row.get("status") == "resolved_confirmed" and (row.get("before") is None) != (row.get("after") is None):
            errors.append(f"{decision_id} correction requires both before and after")
    missing = sorted(candidate_set - set(referenced))
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in referenced:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    if missing:
        errors.append(f"unadjudicated candidates {missing}")
    if repeated:
        errors.append(f"candidates adjudicated more than once {sorted(repeated)}")
    return errors


def projection(decisions: list[dict]) -> list[dict]:
    rows = []
    for index, row in enumerate((item for item in decisions if item.get("status") == "open_material"), 1):
        rows.append({
            "schema_version": "1.0",
            "issue_id": f"UI{index:06d}",
            "adjudication_id": row["adjudication_id"],
            "status": "open",
            "reader_impact": row["reader_impact"],
            "page_id": row.get("page_id"),
            "block_id": row.get("block_id"),
            "note": row["rationale"],
            "source_image": next((value for value in row.get("evidence", []) if str(value).lower().endswith((".jpg", ".jpeg", ".png"))), None),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    audit = args.workspace.expanduser().resolve() / "90-audit"
    try:
        candidates = read_jsonl(audit / "uncertainty-candidates.jsonl")
        decisions = read_jsonl(audit / "uncertainty-adjudication.jsonl")
        errors = validate(candidates, decisions)
        expected = projection(decisions)
        target = audit / "uncertain-items.jsonl"
        if args.check:
            actual = read_jsonl(target)
            if actual != expected:
                errors.append("uncertain-items.jsonl is not the current open-material projection")
        elif not errors:
            target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in expected), encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
        candidates = []
        decisions = []
        expected = []
    result = {"valid": not errors, "candidates": len(candidates), "adjudications": len(decisions), "open_material": len(expected), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
