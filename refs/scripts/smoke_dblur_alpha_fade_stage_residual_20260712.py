#!/usr/bin/env python3
"""Focused, non-production gate for the DirectionalBlur Alpha Fade residual."""

from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "refs/reports/dblur_ucrt_expf_return/olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711_return_windows_validated_tables.json"
RAW = ROOT / "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/raw/output_argb8_tight.bin"
INPUT = ROOT / "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/raw/input_argb8_tight.bin"
EXPECTED = ROOT / "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/expected/directionalblur_context_scale_20260606__software__fr24__db_angle0_alpha_fade_hard_edges.png"


def u32(value: str) -> int:
    return int(value, 16)


def main() -> int:
    payload = json.loads(TABLES.read_text(encoding="utf-8"))
    tables = {item["n"]: item["words"] for item in payload["tables"]}
    assert [len(tables[96]), len(tables[240])] == [96, 240]
    assert all(u32(word) <= 0xFFFFFFFF for words in tables.values() for word in words)

    # The current Gaussian model is the accepted double-exp/f32 model. Check
    # every returned UCRT word, not only the residual column's likely indices.
    import math

    model_mismatches = []
    for count, words in tables.items():
        ratio = struct.unpack("<f", struct.pack("<f", count / 3.0))[0]
        ratio_square = struct.unpack("<f", struct.pack("<f", ratio * ratio))[0]
        denominator = struct.unpack("<f", struct.pack("<f", float(ratio_square) * 2.0 + 1.0e-5))[0]
        for index, expected_word in enumerate(words):
            argument = struct.unpack("<f", struct.pack("<f", float(-(index * index)) / denominator))[0]
            result = struct.unpack("<f", struct.pack("<f", math.exp(float(argument))))[0]
            actual_word = struct.unpack("<I", struct.pack("<f", result))[0]
            if actual_word != u32(expected_word):
                model_mismatches.append((count, index, expected_word, f"0x{actual_word:08x}"))
    assert not model_mismatches, model_mismatches[:3]

    assert INPUT.stat().st_size == 1920 * 1080 * 4
    assert RAW.stat().st_size == 1920 * 1080 * 4
    assert EXPECTED.exists()

    commands = [
        [sys.executable, "tools/emulation/test_dblur_frontonly_current_exact_20260711.py"],
        [sys.executable, "tools/emulation/test_dblur_rowdriver_full_exact_20260711.py"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    print(json.dumps({
        "status": "pass",
        "ucrt_tables": {"n96": 96, "n240": 240, "model_word_mismatches": 0},
        "live_raw_pf_world": {"input_bytes": INPUT.stat().st_size, "output_bytes": RAW.stat().st_size},
        "bounded_stage_gates": ["frontonly_fullentry", "rowdriver_full"],
        "production_changed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
