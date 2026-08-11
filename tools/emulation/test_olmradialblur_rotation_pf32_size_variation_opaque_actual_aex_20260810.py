#!/usr/bin/env python3
"""Exact PF32 Rotation Size Variation family for strictly positive alpha."""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_m4_case0010 as m4  # noqa: E402
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as base  # noqa: E402

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf32_size_variation_opaque_actual_aex_20260810.json"
DOC = REPORT.with_suffix(".md")
VALUES = (1.0, 25.0, 100.0)
COMPARED_PLANES = ("polar", "source_scalar", "prepass_alpha", "accum", "max_alpha",
                   "final_rgba", "coordinates", "output")
ACTUAL_REQUIRED = ("geometry", *COMPARED_PLANES)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def actual_with_prepass() -> dict[str, bytes]:
    """Capture the B150 prepass plane from the actual AEX, not production only."""
    old_capture = base.base.CAPTURE_EDGE_INTERNALS
    base.base.CAPTURE_EDGE_INTERNALS = True
    try:
        actual = base.actual_aex()
    finally:
        base.base.CAPTURE_EDGE_INTERNALS = old_capture
    missing = [name for name in ACTUAL_REQUIRED if name not in actual]
    if missing:
        raise RuntimeError(f"actual AEX required-plane capture incomplete: {missing}")
    return actual


def actual_at(value: float) -> dict[str, bytes]:
    original = m4.load_case0010_params
    def params() -> dict:
        result = original()
        result["Size Variation"] = value
        return result
    m4.load_case0010_params = params
    try:
        return actual_with_prepass()
    finally:
        m4.load_case0010_params = original


def main() -> int:
    baseline = actual_with_prepass()
    baseline_hashes = {name: sha(raw) for name, raw in baseline.items()}
    cases = []
    for value in VALUES:
        actual = actual_at(value)
        matches = {name: actual[name] == raw for name, raw in baseline.items()}
        assert all(matches.values()), (value, matches)
        old_size = base.SIZE_VARIATION
        base.SIZE_VARIATION = value
        try:
            production = base.mac_production(actual)
        finally:
            base.SIZE_VARIATION = old_size
        production_missing = [name for name in COMPARED_PLANES if name not in production]
        if production_missing:
            raise RuntimeError(f"production required-plane capture incomplete: {production_missing}")
        production_matches = {name: production[name] == actual[name]
                              for name in COMPARED_PLANES}
        assert all(production_matches.values()), (value, production_matches)
        cases.append({"size_variation": value, "matches_zero_variation": matches,
                      "production_matches_actual": production_matches,
                      "hashes": {name: sha(raw) for name, raw in actual.items()}})
    original_source = base.source_frame
    old_size = base.SIZE_VARIATION
    def zero_alpha_source(output_seed: bool = False) -> bytes:
        raw = bytearray(original_source(output_seed))
        if not output_seed:
            struct.pack_into("<f", raw, 0, 0.0)
        return bytes(raw)
    base.source_frame = zero_alpha_source
    base.SIZE_VARIATION = 25.0
    rejected_zero_alpha = False
    try:
        base.mac_production(baseline)
    except subprocess.CalledProcessError as exc:
        rejected_zero_alpha = exc.returncode == 3
    finally:
        base.source_frame = original_source
        base.SIZE_VARIATION = old_size
    assert rejected_zero_alpha
    report = {
        "kind": "olmradialblur_rotation_pf32_size_variation_opaque_actual_aex_20260810",
        "status": "exact_actual_aex_and_production_semantic_noop_family",
        "scope": "Pinned actual-AEX PF32 Rotation 9x7 rowbytes160, all source alpha strictly positive (0.5 or 1.0), Size Variation 1/25/100; all other parameters use the existing neutral outer-only tuple.",
        "aex": {"path": str(m4.AEX_PATH.relative_to(ROOT)), "sha256": base.AEX_SHA256},
        "source_alpha": {"minimum": 0.5, "maximum": 1.0, "contains_zero": False},
        "baseline_zero_variation_hashes": baseline_hashes,
        "cases": cases,
        "fail_closed_gate": {"one_zero_alpha_pixel_rejected": rejected_zero_alpha},
        "admitted_rule": "For this strictly-positive-alpha tuple, witnessed Size Variation values 1/25/100 are semantically masked: actual-AEX and production captured internal planes plus padded output equal Size Variation 0 byte-for-byte.",
        "actual_required_plane_contract": list(ACTUAL_REQUIRED),
        "production_compared_plane_contract": list(COMPARED_PLANES),
        "boundary": "No claim for any zero-alpha pixel, Noise Variation, PF8/PF16, other geometry, or other parameter tuple.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur PF32 opaque Size Variation family — 2026-08-10\n\n"
                   "Status: **PASS (bounded actual-AEX exact)**\n\n"
                   "For the pinned 9×7 PF32 Rotation fixture whose alpha is everywhere 0.5 or 1.0, Size Variation 1, 25, and 100 produce the same polar/source-scalar/accum/max/final-coordinate planes and padded output as Size Variation 0, byte-for-byte. Production may admit this semantic-noop family only after checking every input alpha is strictly positive.\n\n"
                   "This does not cover inputs containing alpha zero, Noise Variation, other bit depths/geometries, or other parameter tuples.\n")
    print("PASS_OLMRADIALBLUR_ROTATION_PF32_SIZE_VARIATION_OPAQUE values=3 actual_production=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
