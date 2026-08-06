#!/usr/bin/env python3
"""Bounded ColorKeep PF32 unordered-comparison fixture from the 2025 AEX."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
ENTRY = 0x180001850
REPORT = ROOT / "refs/conformance/colorkeep_pf32_nan_actual_aex_20260805.json"


def bits(values: tuple[float, float, float, float]) -> list[str]:
    return [f"0x{word:08x}" for word in struct.unpack("<4I", struct.pack("<4f", *values))]


def invoke(source: tuple[float, float, float, float], color: tuple[float, float, float, float]) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x80)
    src = loader.host_alloc(16)
    dst = loader.host_alloc(16)
    # Actual callback-local layout: count at +0x24, then ARGB PF32 colors at +0x28.
    loader.write_bytes(refcon + 0x24, struct.pack("<i", 1))
    loader.write_bytes(refcon + 0x28, struct.pack("<4f", *color))
    loader.write_bytes(src, struct.pack("<4f", *source))
    loader.write_bytes(dst, b"\xa5" * 16)
    result = loader.call_function(ENTRY, int_args=[refcon, 0, 0, src, dst], max_instructions=10_000)
    observed = struct.unpack("<4f", loader.read_bytes(dst, 16))
    return {
        "source_argb_bits": bits(source),
        "color_argb_bits": bits(color),
        "observed_argb_bits": bits(observed),
        "observed_alpha": observed[0],
        "instructions": result["instructions"],
    }


def main() -> int:
    digest = hashlib.sha256(AEX.read_bytes()).hexdigest()
    assert digest == AEX_SHA256
    cases = {
        "nan_source_red": invoke((0.75, math.nan, 0.0, 0.0), (0.75, 0.0, 0.0, 0.0)),
        "nan_color_red": invoke((0.75, 0.25, 0.0, 0.0), (0.75, math.nan, 0.0, 0.0)),
        "finite_just_outside": invoke((0.75, 0.0001001, 0.0, 0.0), (0.75, 0.0, 0.0, 0.0)),
    }
    assert cases["nan_source_red"]["observed_alpha"] == 0.75
    assert cases["nan_color_red"]["observed_alpha"] == 0.75
    assert cases["finite_just_outside"]["observed_alpha"] == 0.0
    report = {
        "status": "exact",
        "scope": {
            "artifact": "Windows ColorKeep 2025 AEX",
            "entry": f"0x{ENTRY:x}",
            "depth": "PF32",
            "shape": "direct one-pixel worker calls, one enabled color",
            "host": "none; actual PE code under local Unicorn",
        },
        "aex_sha256": digest,
        "cases": cases,
        "proven_fact": "COMISS/JA unordered differences fall through as matches; finite differences above 1e-4 reject",
        "not_proven": [
            "After Effects host dispatch or export equivalence",
            "PF8/PF16 full-frame equivalence",
            "more than one enabled color",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
