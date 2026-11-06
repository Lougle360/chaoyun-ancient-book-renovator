#!/usr/bin/env python3
"""Freeze workflow 1.9 acceptance code and edition scope before semantic review."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from validate_integrity import (
    FOCUSED_PROTOCOL, REQUIRED_REVIEW_METHODS, layout_proof_applicability,
    read_json, review_protocol, sha256, validator_paths,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    target = root / "90-audit/acceptance-policy-lock.json"
    if target.exists():
        parser.error("preserve or explicitly archive the existing policy lock before creating another")
    scope = root / "10-diagnosis/edition-scope.json"
    if not scope.is_file():
        parser.error("lock 10-diagnosis/edition-scope.json first")
    try:
        book = read_json(root / "book.json")
        policy_path = root / "50-edited/review-policy.json"
        policy = read_json(policy_path) if policy_path.is_file() else {}
        errors: list[str] = []
        protocol = review_protocol(book, policy, errors)
        binding = {}
        if protocol == FOCUSED_PROTOCOL:
            applicability = layout_proof_applicability(book, errors)
            minimum, stable = policy.get("minimum_full_passes"), policy.get("required_stable_passes")
            if type(minimum) is not int or type(stable) is not int or not 1 <= stable <= minimum:
                errors.append("focused-v1 requires minimum_full_passes >= required_stable_passes >= 1")
            methods = policy.get("required_methods")
            if not isinstance(methods, list) or any(not isinstance(method, str) for method in methods) or not REQUIRED_REVIEW_METHODS.issubset(methods):
                errors.append("focused-v1 requires manuscript_reader, source_fidelity and final_pdf_reader methods")
            if read_json(scope).get("status") != "locked":
                errors.append("edition scope must be locked first")
            binding = {"review_protocol": protocol, "review_policy_sha256": sha256(policy_path),
                       "layout_proof_applicability": applicability}
        if errors:
            parser.error("; ".join(errors))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    data = {
        "schema_version": "1.0",
        "policy_version": book["workflow_schema_version"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "edition_scope_sha256": sha256(scope),
        "validators": {name: sha256(path) for name, path in validator_paths(protocol).items()},
        **binding,
    }
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"policy_lock": str(target), "validators": len(data["validators"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
