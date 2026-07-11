#!/usr/bin/env python3
"""Run the case_0023 full-frame AEX field fixtures and bind them to compose."""

from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / (
    "refs/win_references/olm_return_20260706/DistanceGradation/"
    "olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023_current_aex_before_effects.png"
)
COMPOSE = ROOT / "tools/emulation/fixtures/distancegradation_compose_case0023_triplet"
POINTS = ((414, 393), (415, 393), (416, 393))


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def read_f32(path: Path, width: int, x: int, y: int) -> float:
    with path.open("rb") as handle:
        handle.seek((y * width + x) * 4)
        return struct.unpack("<f", handle.read(4))[0]


def read_field_word(path: Path, width: int, x: int, y: int) -> int:
    with path.open("rb") as handle:
        handle.seek((y * width + x) * 8 + 2)
        return struct.unpack("<H", handle.read(2))[0]


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    with tempfile.TemporaryDirectory(prefix="olm_dg_case0023_fixture_") as temp_value:
        temp = Path(temp_value)
        inside = temp / "inside"
        outside = temp / "outside"
        replay = temp / "replay"
        base = [
            str(ROOT / "tools/emulation/.venv/bin/python"),
            "tools/emulation/export_dg_fieldgen_fixture.py",
            "--mask-png", str(SOURCE), "--mask-channel", "alpha", "--param8", "1",
        ]
        run(base + ["--output", str(inside), "--threshold", "36", "--case-id", "distancegradation.case0023.inside.fieldgen.aex"])
        run(base + ["--output", str(outside), "--threshold", "0", "--invert-mask", "--case-id", "distancegradation.case0023.outside.fieldgen.aex"])
        run([
            "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
            "core/olmdistancegradation_fieldgen.cpp",
            "tools/emulation/replay_dg_fieldgen_fixture.cpp",
            "-o", str(replay),
        ])
        for fixture in (inside, outside):
            run([
                str(replay), str(fixture / "input_mask_u8.bin"),
                str(fixture / "call_params_le_i32.bin"), str(fixture / "field_f32.bin"),
            ])

        expected = (0.0, 1.0, 1.0)
        actual = tuple(read_f32(inside / "field_f32.bin", 1920, x, y) for x, y in POINTS)
        if actual != expected:
            raise AssertionError(f"case_0023 AEX field triplet changed: {actual}")
        compose_words = tuple(read_field_word(COMPOSE / "field_agrb16.bin", 420, x, y) for x, y in POINTS)
        expected_words = tuple(int(value * 32768.0) for value in actual)
        if compose_words != expected_words:
            raise AssertionError(f"fieldgen->compose binding mismatch: field={expected_words} compose={compose_words}")

    print("[OK] DG case_0023 full-frame inside/outside AEX fields match portable core exactly")
    print("[OK] DG case_0023 fieldgen triplet binds to compose words: 0,32768,32768")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
