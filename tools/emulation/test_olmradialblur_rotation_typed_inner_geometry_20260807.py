#!/usr/bin/env python3
"""Dimension-generic PF16/PF32 Rotation Inner actual-AEX differential."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as pf16  # noqa: E402
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa: E402

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_typed_inner_geometry_20260807.json"
PLANES = ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(depth: int, width: int, height: int, strength: int):
    if depth == 16:
        module = pf16
        module.W, module.H = width, height
        module.VISIBLE = width * 8
        module.ROWBYTES = module.VISIBLE + 16
        module.FIXTURE_CENTER_X, module.FIXTURE_CENTER_Y = width / 2.0, height / 2.0
        module.FIXTURE_OUTER_STRENGTH = 0
        module.FIXTURE_INNER_STRENGTH = strength
    else:
        module = pf32
        module.W, module.H = width, height
        module.VISIBLE = width * 16
        module.ROWBYTES = module.VISIBLE + 32
        module.CENTER_X, module.CENTER_Y = width / 2.0, height / 2.0
        module.OUTER_STRENGTH = 0
        module.INNER_STRENGTH = strength
    return module


def run_case(depth: int, width: int, height: int, strength: int) -> dict[str, object]:
    module = configure(depth, width, height, strength)
    actual = module.actual_aex()
    production = module.mac_production(actual)
    matches = {name: actual[name] == production[name] for name in PLANES}
    padding_byte_base = 0xA0 if depth == 16 else 0xC0
    padding_exact = all(
        production["output"][y * module.ROWBYTES + module.VISIBLE:(y + 1) * module.ROWBYTES]
        == bytes([(padding_byte_base + y) & 0xFF]) * (module.ROWBYTES - module.VISIBLE)
        for y in range(height)
    )
    return {
        "bit_depth": depth,
        "geometry": {"width": width, "height": height, "rowbytes": module.ROWBYTES,
                     "visible_bytes": module.VISIBLE, "padding_bytes": module.ROWBYTES - module.VISIBLE},
        "inner_strength": strength,
        "effective_span": max(0, strength - 1),
        "matches": matches,
        "padding_exact": padding_exact,
        "actual_aex_hashes": {name: sha256(actual[name]) for name in PLANES},
        "production_hashes": {name: sha256(production[name]) for name in PLANES},
        "status": "exact" if all(matches.values()) and padding_exact else "mismatch",
    }


def main() -> int:
    width = int(os.environ.get("OLM_RADIAL_TYPED_WIDTH", "64"))
    height = int(os.environ.get("OLM_RADIAL_TYPED_HEIGHT", "36"))
    strengths = tuple(int(v) for v in os.environ.get("OLM_RADIAL_TYPED_STRENGTHS", "3,33,64").split(","))
    depths = tuple(int(v) for v in os.environ.get("OLM_RADIAL_TYPED_DEPTHS", "16,32").split(","))
    aex_sha256 = sha256(pf16.m4.AEX_PATH.read_bytes())
    if aex_sha256 != pf16.AEX_SHA256:
        raise RuntimeError(f"actual AEX identity mismatch: {aex_sha256}")
    cases = [run_case(depth, width, height, strength) for depth in depths for strength in strengths]
    exact = all(case["status"] == "exact" for case in cases)
    report = {
        "kind": "olmradialblur_rotation_typed_inner_geometry_20260807",
        "status": "exact" if exact else "mismatch",
        "scope": "Offline actual-AEX owner versus Mac production, centered neutral Rotation Inner; native PF16/PF32, padded rowbytes, internal planes and typed output; no Windows host or AE-host claim",
        "aex": {"path": str(pf16.m4.AEX_PATH.relative_to(ROOT)), "sha256": aex_sha256,
                "identity_exact": True},
        "admitted_rule": "PF16/PF32 equal positive input/output geometry, centered center/comp, rowbytes >= visible bytes, Inner Strength 1..64, neutral remaining parameters",
        "cases": cases,
    }
    output = Path(os.environ.get("OLM_RADIAL_TYPED_REPORT", str(REPORT)))
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
