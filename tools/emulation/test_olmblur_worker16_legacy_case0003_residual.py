#!/usr/bin/env python3
"""Classify the current Mac-vs-Windows 16bpc Legacy case_0003 PNG residual."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np


WIDTH = 960
HEIGHT = 540


def read_rgba16(path: Path) -> np.ndarray:
    raw = subprocess.check_output(
        ["magick", str(path), "-depth", "16", "-endian", "MSB", "rgba:-"]
    )
    expected = WIDTH * HEIGHT * 4 * 2
    if len(raw) != expected:
        raise AssertionError(f"{path}: {len(raw)} bytes, expected {expected}")
    return np.frombuffer(raw, dtype=">u2").reshape(HEIGHT, WIDTH, 4)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    name = "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0003.png"
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("/tmp/olmblur_16bpc_candidates_c76c687c") / name,
    )
    parser.add_argument(
        "--expected",
        type=Path,
        default=root
        / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625/expected"
        / name,
    )
    args = parser.parse_args()

    candidate = read_rgba16(args.candidate)
    expected = read_rgba16(args.expected)
    delta = expected.astype(np.int32) - candidate.astype(np.int32)
    ys, xs, channels = np.where(delta != 0)
    if len(ys) != 20 or set(channels) != {0}:
        raise AssertionError(
            f"unexpected residual: samples={len(ys)} channels={sorted(set(channels))}"
        )
    counts = {int(value): int(np.count_nonzero(delta == value)) for value in (-2, 2)}
    if counts != {-2: 19, 2: 1}:
        raise AssertionError(f"unexpected exported deltas: {counts}")

    print("case_0003 Legacy 16bpc residual: 20 red samples")
    print(f"exported delta (expected - candidate): {counts}")
    print("inferred AE-word delta (expected - candidate): {-1: 19, +1: 1}")
    for y, x in zip(ys, xs):
        print(
            f"x={x} y={y} candidate={candidate[y, x, 0]} "
            f"expected={expected[y, x, 0]} delta={delta[y, x, 0]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
