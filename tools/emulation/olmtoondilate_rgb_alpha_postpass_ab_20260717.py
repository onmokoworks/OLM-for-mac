#!/usr/bin/env python3
"""A/B metric probe for the authorized no-RGB*=alpha ToonDilate candidate."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np


def read_rgba(path: Path, depth: int) -> tuple[int, int, np.ndarray]:
    identify = subprocess.check_output(
        ["magick", "identify", "-format", "%w %h", str(path)], text=True
    ).split()
    width, height = map(int, identify)
    raw = subprocess.check_output(["magick", str(path), "-depth", str(depth), "RGBA:-"])
    dtype = np.dtype(">u2" if depth == 16 else "u1")
    values = np.frombuffer(raw, dtype=dtype).astype(np.uint32).reshape((height, width, 4))
    return width, height, values


def render(source: np.ndarray, width: int, height: int, radius: int, maximum: int, postpass: bool) -> np.ndarray:
    output = source.copy()
    inf = 2**32 - 1
    distances = np.full((height, width), inf, dtype=np.uint32)
    for y in range(height):
        for x in range(width):
            if source[y, x, 3] == maximum:
                distances[y, x] = 0

    def relax(x: int, y: int, coords: tuple[tuple[int, int], ...]) -> None:
        if distances[y, x] == 0:
            return
        best = inf
        best_xy = None
        for nx, ny in coords:
            if 0 <= nx < width and 0 <= ny < height and distances[ny, nx] < best:
                best = distances[ny, nx]
                best_xy = (nx, ny)
        if best_xy is None or best + 1 >= distances[y, x]:
            return
        distances[y, x] = best + 1
        if best + 1 <= radius:
            sx, sy = best_xy
            output[y, x] = output[sy, sx]

    for y in range(height):
        for x in range(width):
            relax(x, y, ((x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1)))
    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            relax(x, y, ((x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1)))

    if postpass:
        alpha = output[:, :, 3]
        mask = (alpha > 0) & (alpha < maximum)
        for c in range(3):
            channel = output[:, :, c]
            channel[mask] = (channel[mask] * alpha[mask] + maximum // 2) // maximum
    return output


def metrics(candidate: np.ndarray, reference: np.ndarray, maximum: int) -> dict[str, float | int]:
    diffs = np.abs(candidate.astype(np.int64) - reference.astype(np.int64))
    pixel_diffs = np.any(candidate != reference, axis=2)
    return {
        "max_diff": int(diffs.max(initial=0)),
        "mean_diff": float(diffs.mean()),
        "nonzero_channel_count": int(np.count_nonzero(diffs)),
        "nonzero_pixel_count": int(np.count_nonzero(pixel_diffs)),
        "nonzero_pixel_percent": 100.0 * float(np.count_nonzero(pixel_diffs)) / pixel_diffs.size,
        "max_diff_normalized": int(diffs.max(initial=0)) / maximum,
    }


def suite(root: Path, bit_depth: int) -> list[dict[str, object]]:
    if bit_depth == 8:
        base = root / "refs/win_references/20260604_olm/OLMToonDilate"
        names = {f"case_{i:04d}": (base / f"case_{i:04d}_before_effects.png", base / f"case_{i:04d}.png") for i in range(1, 4)}
        maximum = 255
        radii = {"case_0001": 13, "case_0002": 13, "case_0003": 27}
    else:
        base = root / "refs/win_references/olm_reference_return_windows_20260703_combined/OLMbit-depthconformancebatch"
        names = {}
        for i in range(1, 4):
            stem = f"olm_bitdepth_16bpc_toondilate_exact_20260703__software_16bpc__fr24__olmtoondilate__case_{i:04d}"
            names[f"case_{i:04d}"] = (base / f"{stem}_before_effects.png", base / f"{stem}.png")
        maximum = 65535
        radii = {"case_0001": 13, "case_0002": 13, "case_0003": 27}

    rows = []
    for case_id, (source_path, reference_path) in names.items():
        width, height, source = read_rgba(source_path, bit_depth)
        rw, rh, reference = read_rgba(reference_path, bit_depth)
        if (width, height) != (rw, rh):
            raise RuntimeError(f"dimension mismatch for {case_id}")
        effective_radius = int(np.ceil(radii[case_id] * width / 1920.0))
        current = render(source, width, height, effective_radius, maximum, True)
        disabled = render(source, width, height, effective_radius, maximum, False)
        rows.append({
            "case_id": case_id,
            "width": width,
            "height": height,
            "radius": radii[case_id],
            "effective_radius": effective_radius,
            "candidate_no_postpass": metrics(disabled, reference, maximum),
            "legacy_postpass": metrics(current, reference, maximum),
            "candidate_vs_legacy_changed_channels": int(np.count_nonzero(current != disabled)),
            "candidate_vs_legacy_changed_pixels": int(np.count_nonzero(np.any(current != disabled, axis=2))),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"8bpc": suite(args.root, 8), "16bpc": suite(args.root, 16)}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
