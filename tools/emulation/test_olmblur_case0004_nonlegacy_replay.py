#!/usr/bin/env python3
"""Replay the retained OLMBlur 16bpc Non-Legacy case_0004 input portably."""

from __future__ import annotations

import os
import re
import struct
import subprocess
import tempfile
from pathlib import Path


WIDTH = 960
HEIGHT = 540
ROOT = Path(__file__).resolve().parents[2]
INPUT = (
    ROOT
    / "handoff/ae_pixel_validation_20260618/requests/"
    / "ae_pixel_bitdepth16_olmblur_exact_20260625/input/"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0004_before_effects.png"
)
PROBE = ROOT / "tools/emulation/probe_olmblur_case0004_worker16.cpp"
SOURCES = [PROBE, ROOT / "core/olmblur_helper.cpp", ROOT / "core/olmblur_worker16_nonlegacy.cpp"]
OBSERVATIONS = {
    (411, 258): ("46ac2aff", 22037),
    (458, 314): ("46ce0aff", 26373),
}


def read_rgba16(path: Path) -> bytes:
    raw = subprocess.check_output(
        ["magick", str(path), "-depth", "16", "-endian", "MSB", "rgba:-"]
    )
    expected = WIDTH * HEIGHT * 4 * 2
    if len(raw) != expected:
        raise AssertionError(f"{path}: {len(raw)} bytes, expected {expected}")
    return raw


def make_worker_source(path: Path) -> None:
    exported = read_rgba16(INPUT)
    words = struct.unpack(f">{WIDTH * HEIGHT * 4}H", exported)
    source = bytearray()
    for pixel in range(WIDTH * HEIGHT):
        r, g, b, a = words[pixel * 4 : pixel * 4 + 4]
        # Exported PNG words are 0..65535; AE PF16 RGB words are 0..32768.
        pf16 = tuple((word + 1) // 2 for word in (a, r, g, b))
        source.extend(struct.pack("<4H", *pf16))
    path.write_bytes(source)


def main() -> int:
    if not INPUT.is_file():
        raise AssertionError(f"retained request input is missing: {INPUT}")
    compiler = os.environ.get("CXX", "c++")
    with tempfile.TemporaryDirectory(prefix="olmblur_case0004_replay_") as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "case0004_before_effects_argb16.bin"
        executable = tmp_path / "probe_olmblur_case0004_worker16"
        make_worker_source(source)
        subprocess.run(
            [compiler, "-std=c++17", "-O2", "-ffp-contract=off", *map(str, SOURCES), "-o", str(executable)],
            cwd=ROOT,
            check=True,
        )
        output = subprocess.check_output([str(executable), str(source)], text=True)

    observed = {}
    for line in output.splitlines():
        match = re.fullmatch(
            r"(\d+),(\d+) pre_store=.* bits=0x([0-9a-f]+) floor05=.* nearby=.* stored=(\d+)",
            line,
        )
        if not match:
            raise AssertionError(f"unexpected probe output: {line!r}")
        observed[(int(match.group(1)), int(match.group(2)))] = (
            match.group(3),
            int(match.group(4)),
        )
    if observed != OBSERVATIONS:
        raise AssertionError(f"observations differ: {observed!r}")
    print("case_0004 portable Non-Legacy replay: two raw float/stored-word observations match")
    for (x, y), (bits, stored) in observed.items():
        print(f"x={x} y={y} bits=0x{bits} stored={stored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
