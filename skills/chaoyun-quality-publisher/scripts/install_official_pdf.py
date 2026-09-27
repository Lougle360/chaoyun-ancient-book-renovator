#!/usr/bin/env python3
"""Validate a candidate PDF and atomically install it at book.json.release_filename."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_pdf(path: Path, expected_pages: int | None) -> int:
    if not path.is_file() or path.stat().st_size == 0 or path.read_bytes()[:5] != b"%PDF-":
        raise ValueError(f"candidate is not a nonempty PDF: {path}")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to install the official PDF") from exc
    pages = len(PdfReader(str(path)).pages)
    if expected_pages is not None and pages != expected_pages:
        raise ValueError(f"candidate page count differs from expected: {pages}/{expected_pages}")
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("candidate_pdf", type=Path)
    parser.add_argument("--expected-pages", type=int)
    args = parser.parse_args()
    root = args.workspace.expanduser().resolve()
    candidate = args.candidate_pdf.expanduser().resolve()
    book = json.loads((root / "book.json").read_text(encoding="utf-8"))
    release = book.get("release_filename")
    if not release:
        raise SystemExit("book.json.release_filename is required")
    target = (root / str(release)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise SystemExit("release_filename escapes workspace") from exc
    pages = inspect_pdf(candidate, args.expected_pages)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            with target.open("r+b"):
                pass
        except PermissionError as exc:
            raise SystemExit(f"official PDF is locked or not writable: {target}") from exc
    handle = tempfile.NamedTemporaryFile("wb", delete=False, dir=target.parent, prefix=target.name + ".", suffix=".tmp.pdf")
    temporary = Path(handle.name)
    try:
        with handle, candidate.open("rb") as source:
            shutil.copyfileobj(source, handle)
            handle.flush()
            os.fsync(handle.fileno())
        inspect_pdf(temporary, pages)
        try:
            os.replace(temporary, target)
        except PermissionError as exc:
            raise SystemExit(f"could not atomically replace locked official PDF: {target}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    print(json.dumps({"official_pdf": str(target), "pages": pages, "bytes": target.stat().st_size, "sha256": sha256(target)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
