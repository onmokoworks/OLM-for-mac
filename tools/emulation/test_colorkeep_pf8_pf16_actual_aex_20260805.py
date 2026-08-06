#!/usr/bin/env python3
"""One-pixel ColorKeep PF8/PF16 fixtures from the actual Windows 2025 AEX."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
REPORT = ROOT / "refs/conformance/colorkeep_pf8_pf16_actual_aex_20260805.json"
COLOR_ARGB = (1.0, 0.1234560013, 0.5, 70.0 / 255.0)

DEPTHS = {
    "PF8": {
        "entry": 0x180001580,
        "format": "<4B",
        "match": (255, 31, 128, 70),
        "no_match": (255, 32, 128, 70),
    },
    "PF16": {
        "entry": 0x180001280,
        "format": "<4H",
        "match": (32768, 4045, 16384, 8995),
        "no_match": (32768, 4046, 16384, 8995),
    },
}


def invoke(depth: str, source: tuple[int, int, int, int]) -> dict[str, object]:
    spec = DEPTHS[depth]
    fmt = str(spec["format"])
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x38)
    src = loader.host_alloc(struct.calcsize(fmt))
    dst = loader.host_alloc(struct.calcsize(fmt))
    loader.write_bytes(refcon + 0x24, struct.pack("<i", 1))
    loader.write_bytes(refcon + 0x28, struct.pack("<4f", *COLOR_ARGB))
    loader.write_bytes(src, struct.pack(fmt, *source))
    loader.write_bytes(dst, b"\xa5" * struct.calcsize(fmt))
    result = loader.call_function(
        int(spec["entry"]), int_args=[refcon, 0, 0, src, dst], max_instructions=10_000
    )
    observed = struct.unpack(fmt, loader.read_bytes(dst, struct.calcsize(fmt)))
    return {
        "source_argb_units": list(source),
        "observed_argb_units": list(observed),
        "instructions": result["instructions"],
    }


def main() -> int:
    digest = hashlib.sha256(AEX.read_bytes()).hexdigest()
    assert digest == AEX_SHA256
    cases: dict[str, object] = {}
    for depth, spec in DEPTHS.items():
        match = invoke(depth, spec["match"])
        no_match = invoke(depth, spec["no_match"])
        assert match["observed_argb_units"] == list(spec["match"])
        assert no_match["observed_argb_units"] == [0, *list(spec["no_match"])[1:]]
        cases[depth] = {"match": match, "no_match": no_match}
    report = {
        "status": "exact",
        "aex_sha256": digest,
        "scope": {
            "artifact": "Windows ColorKeep 2025 AEX",
            "entries": {depth: f"0x{spec['entry']:x}" for depth, spec in DEPTHS.items()},
            "depths": ["PF8", "PF16"],
            "shape": "one pixel, one enabled color, match and one-red-unit no-match",
            "host": "none; actual PE code under local Unicorn",
        },
        "enabled_color_argb_f32_bits": [
            f"0x{word:08x}" for word in struct.unpack("<4I", struct.pack("<4f", *COLOR_ARGB))
        ],
        "cases": cases,
        "not_proven": [
            "After Effects host dispatch or export equivalence",
            "full-frame iteration",
            "multiple enabled colors at PF8/PF16",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
