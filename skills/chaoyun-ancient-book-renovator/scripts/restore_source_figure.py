#!/usr/bin/env python3
"""Conservatively restore a source figure without inventing missing strokes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def crop_visible(gray: Image.Image) -> Image.Image:
    bbox = gray.point(lambda p: 255 if p < 244 else 0).getbbox()
    if not bbox:
        return gray
    x0, y0, x1, y1 = bbox
    pad = max(4, round(min(gray.size) * 0.025))
    return gray.crop((max(0, x0-pad), max(0, y0-pad), min(gray.width, x1+pad), min(gray.height, y1+pad)))


def restore(source: Image.Image, scale: int) -> Image.Image:
    gray = crop_visible(ImageOps.grayscale(source))
    arr = np.asarray(gray, dtype=np.float32)
    radius = max(6.0, min(gray.size) / 18.0)
    background = np.asarray(gray.filter(ImageFilter.GaussianBlur(radius=radius)), dtype=np.float32)
    normalized = np.clip((arr + 2.0) / (background + 2.0) * 247.0, 0, 255)
    lo, hi = np.percentile(normalized, (0.6, 99.4))
    if hi - lo > 20:
        normalized = (normalized - lo) * 240.0 / (hi - lo) + 10.0
    cleaned = Image.fromarray(np.clip(normalized, 0, 252).astype(np.uint8), mode="L")
    cleaned = cleaned.filter(ImageFilter.MedianFilter(3))
    cleaned = ImageEnhance.Contrast(cleaned).enhance(1.06)
    up = cleaned.resize((cleaned.width * scale, cleaned.height * scale), Image.Resampling.LANCZOS)
    up = up.filter(ImageFilter.UnsharpMask(radius=1.25, percent=145, threshold=3))
    up = Image.blend(up, up.filter(ImageFilter.MinFilter(3)), 0.10)
    return up


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=int, default=8)
    parser.add_argument("--sidecar", type=Path)
    args = parser.parse_args()
    if not 2 <= args.scale <= 12:
        parser.error("--scale must be between 2 and 12")
    if args.output.suffix.lower() != ".png":
        parser.error("output must be a lossless .png")
    source = Image.open(args.input)
    fixed = restore(source, args.scale)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fixed.save(args.output, optimize=True)
    sidecar = args.sidecar or args.output.with_suffix(".restoration.json")
    sidecar.write_text(json.dumps({
        "schema_version": "1.0",
        "source": str(args.input),
        "source_sha256": digest(args.input),
        "source_pixels": list(source.size),
        "output": str(args.output),
        "output_sha256": digest(args.output),
        "output_pixels": list(fixed.size),
        "restoration_level": "R2",
        "operations": ["tight_crop", "background_flatten", "median_denoise", f"{args.scale}x_lanczos", "conservative_unsharp", "10_percent_stroke_strengthen"],
        "warning": "No missing strokes were generated; inspect against the untouched source before publication.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
