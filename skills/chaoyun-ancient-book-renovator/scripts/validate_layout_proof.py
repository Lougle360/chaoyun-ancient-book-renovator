#!/usr/bin/env python3
"""Validate recorded proof/applicability evidence, not diagnosis or visual approval.

Actual source diagnosis decides whether G3.5 is required. This validator cannot
infer PDF complexity or certify a recorded reason for omitting the proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CHECKS = (
    "text_coverage", "figure_coverage", "layout_alignment", "uniform_region_fonts",
    "simplified_body_and_labels", "contextual_corrections", "figure_semantics",
    "pdf_readability",
)
FIGURE_TYPES = {"figure", "diagram", "table", "image", "map", "chart", "figure/table"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def obj(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), f"expected object: {path}")
    return value


def local(root, path):
    need(isinstance(path, str) and bool(path), "missing file path")
    resolved = (root / path).resolve()
    need(resolved.is_relative_to(root), f"path escapes workspace: {path}")
    return resolved


def binding(root, ref, external=False):
    need(isinstance(ref, dict), "missing file binding")
    name = ref.get("path")
    need(isinstance(name, str) and bool(name), "missing bound path")
    path = (root / name).resolve() if external else local(root, name)
    need(path.is_file() and path.stat().st_size > 0, f"missing or empty file: {name}")
    need(sha(path) == ref.get("sha256"), f"stale file binding: {name}")
    return path


def page_set(value, maximum):
    need(isinstance(value, list) and bool(value), "empty page mapping")
    need(all(type(v) is int and 1 <= v <= maximum for v in value), "invalid page mapping")
    need(len(set(value)) == len(value), "duplicate page mapping")
    return set(value)


def validate(root: Path, *, require_acceptance=True) -> list[str]:
    root = root.resolve()
    try:
        book = obj(root / "book.json")
        config = book.get("layout_proof_review")
        if book.get("review_protocol") == "focused-v1":
            applicability = book.get("layout_proof_applicability")
            need(isinstance(applicability, dict),
                 "focused-v1 requires explicit layout_proof_applicability from actual source diagnosis")
            need(type(applicability.get("required")) is bool,
                 "layout_proof_applicability.required must be a boolean")
            need(isinstance(applicability.get("reason"), str) and applicability["reason"].strip(),
                 "layout_proof_applicability requires a nonempty source-diagnosis reason")
            if applicability["required"]:
                need(config is not None,
                     "layout_proof_applicability.required=true requires layout_proof_review; do not omit the applicable G3.5 review")
            else:
                need(config is None,
                     "layout_proof_applicability.required=false conflicts with registered layout_proof_review; preserve required proof registration")
                # Only the declaration is checked; no PDF complexity is inferred.
                return []
        if config is None:
            return []  # Existing unrelated workspaces are not silently migrated.
        need(isinstance(config, dict) and config.get("required") is True,
             "layout_proof_review must remain required once registered")
        record = obj(local(root, config.get("record")))
        schema = record.get("schema_version")
        need(schema in {"1.0", "1.1"}, "unsupported layout proof schema")
        need(record.get("book_id") == book.get("book_id"), "layout proof book_id mismatch")
        need(record.get("edition_kind") == "original_layout_simplified_proof", "wrong proof edition")
        need(isinstance(record.get("version"), str) and record["version"].strip(), "missing proof version")
        need(record.get("validator_sha256") == sha(Path(__file__)), "layout proof policy changed; fresh review required")
        status = record.get("status")
        need(status in {"pending", "changes_requested", "accepted"}, "invalid proof status")

        from pypdf import PdfReader
        manifest = obj(root / "00-intake/source-manifest.json")
        source = binding(root, record.get("source_pdf"), external=True)
        original = Path(manifest.get("staged_source") or manifest["source_path"])
        need(source == original.resolve() and sha(source) == manifest.get("source_sha256"), "proof source differs from intake")
        source_count = len(PdfReader(str(source)).pages)
        pdf = binding(root, record.get("pdf"))
        pdf_count = len(PdfReader(str(pdf)).pages)
        need(pdf_count > 0, "empty proof PDF")
        scope = record["scope"]
        need(scope.get("kind") in {"sample", "complete"} and str(scope.get("reason", "")).strip(), "missing proof scope/reason")
        selected = page_set(scope.get("source_pages"), source_count)
        if scope["kind"] == "complete":
            need(selected == set(range(1, source_count + 1)), "complete proof omits source pages")

        roles = set()
        inputs = record["inputs"]
        need(isinstance(inputs, list), "inputs must be a list")
        for ref in inputs:
            role = ref.get("role")
            roles.add(role)
            path = binding(root, ref, external=role in {"font", "ocr", "renderer"})
            canonical = {"source_blocks": "20-source/blocks.jsonl", "normalized_blocks": "30-normalized/blocks.jsonl"}.get(role)
            if canonical:
                need(path == root / canonical, f"wrong {role} binding")
        need({"source_blocks", "normalized_blocks", "corrections", "renderer", "font"} <= roles, "missing proof input roles")
        blocks = [json.loads(line) for line in (root / "20-source/blocks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        by_id = {b["block_id"]: b for b in blocks}
        coverage = record["coverage"]
        need(isinstance(coverage, list) and len(coverage) == len(selected), "source page coverage count differs")
        need({c["source_page"] for c in coverage} == selected, "source page coverage differs")
        for row in coverage:
            expected = {b["block_id"] for b in blocks if b["source_page"] == row["source_page"]}
            need(expected and set(row["block_ids"]) == expected and len(row["block_ids"]) == len(expected), "source block coverage differs")
            binding(root, row.get("source_image"))

        pages = record["pages"]
        need(isinstance(pages, list) and len(pages) == pdf_count, "proof PDF page coverage count differs")
        need({p["pdf_page"] for p in pages} == set(range(1, pdf_count + 1)), "proof PDF page coverage differs")
        page_sources, compared = {}, set()
        for page in pages:
            sources = page_set(page.get("source_pages"), source_count)
            need(sources <= selected, "PDF page exceeds proof scope")
            page_sources[page["pdf_page"]] = sources
            need(page.get("role") in {"comparison", "standalone"}, "invalid proof page role")
            if page["role"] == "comparison":
                compared |= sources
            binding(root, page.get("render"))
            for key in CHECKS:
                check = page.get("checks", {}).get(key, {})
                check_status = check.get("status")
                need(check_status in {"pending", "passed", "changes_requested", "not_applicable"}, f"missing/invalid page check: {key}")
                if check_status != "pending":
                    need(isinstance(check.get("findings"), str) and check["findings"].strip(), f"missing concrete findings: {key}")
                if status == "accepted":
                    need(check_status in {"passed", "not_applicable"}, f"unresolved page check: {key}")
        need(compared == selected, "source page has no comparison view")

        figures = record["figures"]
        need(isinstance(figures, list), "figures must be a list")
        need(len({f["figure_id"] for f in figures}) == len(figures), "duplicate figure_id")
        expected_figures = {b["block_id"] for b in blocks if b["source_page"] in selected and b["block_type"] in FIGURE_TYPES}
        need(expected_figures <= {f["block_id"] for f in figures}, "source figure block missing from inventory")
        for figure in figures:
            block = by_id.get(figure.get("block_id"), {})
            source_page = figure.get("source_page")
            need(source_page in selected and block.get("source_page") == source_page, "figure source mapping differs")
            box = figure.get("source_bbox")
            need(isinstance(box, list) and len(box) == 4 and all(type(v) in (int, float) for v in box)
                 and 0 <= box[0] < box[2] and 0 <= box[1] < box[3], "invalid figure source_bbox")
            for page in page_set(figure.get("pdf_pages"), pdf_count):
                need(source_page in page_sources[page], "figure PDF/source page mismatch")
            binding(root, figure.get("asset"))

        if schema == "1.1":
            from validate_text_semantics import validate as validate_text_semantics
            validate_text_semantics(root, record, blocks, selected)
        elif status == "accepted":
            need(False, "new acceptance requires layout proof schema 1.1 and text/semantics review; preserve legacy approval as history")

        if status == "accepted":
            review = record.get("review")
            need(isinstance(review, dict), "accepted proof lacks actual review evidence")
            need(review.get("kind") in {"user", "human", "model"}, "missing reviewer kind")
            need(all(isinstance(review.get(k), str) and review[k].strip() for k in ("reviewer", "reviewed_at")), "missing reviewer/time")
            need(review.get("pdf_sha256") == sha(pdf), "review belongs to another PDF")
            binding(root, review.get("evidence"))
        if require_acceptance:
            need(status == "accepted", f"layout proof requires actual review: {status}")
        return []
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError) as exc:
        return [f"layout proof: {exc}"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--allow-pending", action="store_true", help="Candidate integrity only; does not pass the review gate")
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    errors = validate(root, require_acceptance=not args.allow_pending)
    print(json.dumps({"valid": not errors, "mode": "candidate_integrity" if args.allow_pending else "review_gate",
                      "scope": "record integrity only; applicability requires actual source diagnosis, not inferred PDF complexity",
                      "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
