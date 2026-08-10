#!/usr/bin/env python3
"""Capture the bounded PF32 Rotation Noise Variation Type-1 family from the AEX."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa: E402

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf32_noise_variation_type1_actual_aex_20260810.json"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_rotation_pf32_noise_variation_type1_20260810"
VALUES = (0.0, 25.0, 100.0)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def capture(value: float) -> dict[str, bytes]:
    base = pf32.base
    names = (
        "FIXTURE_SIZE_VARIATION", "FIXTURE_NOISE_VARIATION", "FIXTURE_NOISE_TYPE",
        "FIXTURE_SEED", "FIXTURE_NOISE_OFFSET", "FIXTURE_THICKNESS",
        "CAPTURE_NOISE_INTERNALS",
    )
    old = {name: getattr(base, name) for name in names}
    try:
        base.FIXTURE_SIZE_VARIATION = 0.0
        base.FIXTURE_NOISE_VARIATION = value
        base.FIXTURE_NOISE_TYPE = 1
        base.FIXTURE_SEED = 1
        base.FIXTURE_NOISE_OFFSET = 0.0
        base.FIXTURE_THICKNESS = 10.0
        base.CAPTURE_NOISE_INTERNALS = True
        return pf32.actual_aex()
    finally:
        for name, prior in old.items():
            setattr(base, name, prior)


def f32_formula(noise: np.ndarray, variation: float, size: np.ndarray) -> np.ndarray:
    nv = np.float32(variation * 0.01)
    one = np.float32(1.0)
    return ((nv * noise + (one - nv)) * size).astype("<f4")


def main() -> int:
    FIXTURE.mkdir(parents=True, exist_ok=True)
    cases = {int(value): capture(value) for value in VALUES}
    production: dict[int, dict[str, bytes]] = {}
    old_noise_variation = pf32.NOISE_VARIATION
    try:
        for value, planes in cases.items():
            pf32.NOISE_VARIATION = float(value)
            production[value] = pf32.mac_production(planes)
    finally:
        pf32.NOISE_VARIATION = old_noise_variation
    reference_noise = np.frombuffer(cases[100]["source_span"], dtype="<f4")
    artifacts: dict[str, dict[str, object]] = {}
    relations: dict[str, object] = {}
    for value, planes in cases.items():
        for plane in ("noise_lattice_geometry", "noise_lattice", "source_size_factor", "source_span", "source_scalar", "accum", "max_alpha", "output"):
            raw = planes[plane]
            encoded = zlib.compress(raw, 9)
            path = FIXTURE / f"nv{value}_{plane}.bin.zlib"
            path.write_bytes(encoded)
            artifacts[f"nv{value}_{plane}"] = {
                "bytes": len(raw), "raw_sha256": sha(raw), "zlib_sha256": sha(encoded),
                "path": str(path.relative_to(ROOT)),
            }
        size = np.frombuffer(planes["source_size_factor"], dtype="<f4")
        span = np.frombuffer(planes["source_span"], dtype="<f4")
        expected = f32_formula(reference_noise, float(value), size)
        relations[f"nv{value}"] = {
            "span_formula_bit_exact": expected.tobytes() == planes["source_span"],
            "size_factor_all_one": bool(np.all(size == np.float32(1.0))),
            "source_scalar_raw_sha256": sha(planes["source_scalar"]),
            "output_raw_sha256": sha(planes["output"]),
            "production_matches": {
                name: production[value][name] == planes[name]
                for name in ("polar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
            },
            "production_source_scalar_bit_exact": production[value]["source_scalar"] == planes["source_scalar"],
        }
    lattice_same = len({sha(cases[v]["noise_lattice"]) for v in cases}) == 1
    geometry_same = len({cases[v]["noise_lattice_geometry"] for v in cases}) == 1
    exact = lattice_same and geometry_same and all(
        item["span_formula_bit_exact"] and item["size_factor_all_one"] and
        all(item["production_matches"].values())
        for item in relations.values()
    )
    nw, nh = struct.unpack("<II", cases[0]["noise_lattice_geometry"])
    report = {
        "kind": "olmradialblur_rotation_pf32_noise_variation_type1_actual_aex_20260810",
        "status": "exact" if exact else "mismatch",
        "scope": "actual AEX; PF32 Rotation 9x7 rowbytes160; neutral outer-only tuple; SV=0; NV=0/25/100; Noise Type=1; Seed=1; Offset=0; Thickness=10",
        "aex_sha256": pf32.AEX_SHA256,
        "noise_lattice_geometry": {"width": nw, "height": nh},
        "noise_lattice_identical_across_nv": lattice_same,
        "geometry_identical_across_nv": geometry_same,
        "relation": "source_span = (NV * interpolated_noise + (1-NV)) * source_size_factor; NV is normalized by 0.01",
        "relations": relations,
        "artifacts": artifacts,
        "boundary": "The full production source-scalar allocation and accum/max/final/output are bit exact for the bounded Type-1 family. Type 2/3, other seed/offset/thickness, other geometry/depth/mode, and AE-host behavior are not claimed.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
