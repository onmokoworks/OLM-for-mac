#!/usr/bin/env python3
"""Actual-AEX Rotation matrix for component Size Variation x Type-1/2 Noise."""
from __future__ import annotations

import hashlib
import json
import pickle
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811 as comp

SVS = (25.0, 100.0)
NVS = (25.0, 100.0)
TYPES = (1, 2)
CELLS = [(d, sv, nv, nt) for d in (8, 16, 32) for sv in SVS for nv in NVS for nt in TYPES]
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_size_noise_components_actual_aex_20260811.json"


def configure(depth: int, sv: float, nv: float, noise_type: int):
    target, frame = comp.configure(depth, sv)
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_NOISE_VARIATION = nv
    fixture.FIXTURE_NOISE_TYPE = noise_type
    fixture.FIXTURE_SEED = 1
    fixture.FIXTURE_NOISE_OFFSET = 0.0
    fixture.FIXTURE_THICKNESS = 10.0
    fixture.CAPTURE_NOISE_INTERNALS = True
    return target, frame


def capture(cell):
    return configure(*cell)[0].actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_rot_sv_noise_") as raw:
        out = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def production(cell, expected):
    depth, sv, nv, noise_type = cell
    original = Path.write_text

    def write_text(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            needle = "i.noise_type=1;i.seed=1;i.thickness=10;"
            if needle not in data:
                raise RuntimeError("noise info marker absent")
            data = data.replace(
                needle,
                f"i.noise_variation={nv};i.noise_type={noise_type};i.seed=1;i.noise_offset=0;i.thickness=10;",
                1,
            )
        return original(path, data, *args, **kwargs)

    Path.write_text = write_text
    try:
        return comp.production((depth, sv), expected)
    finally:
        Path.write_text = original


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def diff(actual: bytes, got: bytes):
    offsets = [i for i, (a, b) in enumerate(zip(actual, got)) if a != b]
    return {"different_bytes": len(offsets), "first_byte_offset": offsets[0] if offsets else None}


def main() -> int:
    controls = [(d, 0.0, nv, nt) for d in (8, 16, 32) for nv in NVS for nt in TYPES]
    size_controls = [(d, sv, 0.0, 1) for d in (8, 16, 32) for sv in SVS]
    requested = controls + size_controls + CELLS
    with ThreadPoolExecutor(max_workers=6) as pool:
        captures = dict(zip(requested, pool.map(isolated, requested)))
    rows = []
    semantic = ("polar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
    required = ("size_factor", "source_scalar", *semantic)
    for cell in CELLS:
        actual = captures[cell]
        prod = production(cell, actual)
        production_failed_closed = False
        observed = (*required, *(("source_span",) if "source_span" in actual else ()))
        missing = [name for name in required if name not in actual]
        if missing:
            raise AssertionError((cell, missing, sorted(actual)))
        matches = {name: prod[name] == actual[name] for name in semantic if name in prod}
        control = captures[(cell[0], 0.0, cell[2], cell[3])]
        size_control = captures[(cell[0], cell[1], 0.0, 1)]
        # The owner forms the noise blend first and multiplies the component size
        # factor last, with a float32 rounding at the multiply.
        expected_span = np.multiply(
            np.frombuffer(control["source_span"], dtype="<f4"),
            np.frombuffer(size_control["source_span"], dtype="<f4"),
            dtype=np.float32,
        ).tobytes() if "source_span" in actual else None
        span_formula_exact = (expected_span == actual["source_span"]) if expected_span is not None else None
        exact = span_formula_exact is not False and not production_failed_closed and all(matches.values())
        rows.append({
            "depth": cell[0], "size_variation": cell[1], "noise_variation": cell[2],
            "noise_type": cell[3], "exact": exact,
            "source_span_equals_f32_noise_control_times_size_factor": span_formula_exact,
            "production_failed_closed": production_failed_closed,
            "production_matches_actual": matches,
            "differences": {name: diff(actual[name], prod[name]) for name, ok in matches.items() if not ok},
            "actual_sha256": {name: sha(actual[name]) for name in observed},
        })
        print(cell, exact, matches, flush=True)
    exact = all(row["exact"] for row in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_rotation_size_noise_components_actual_aex_20260811",
        "status": "24/24 actual-AEX source-span and shared-direct output exact" if exact else "actual-AEX/shared-direct mismatch",
        "scope": "Rotation centered 32x18, PF8/PF16/PF32, disconnected opaque component areas 9/4/1 on transparent black; Size Variation 25/100 x Noise Variation 25/100 x Noise Type 1/2; seed1, offset0, thickness10, neutral Outer4/Inner0.",
        "boundary": "Only the 24 enumerated shared-direct cells and fixed component fixture are admitted. The source-span seam is available in PF16/PF32 and proves the final float32 multiply directly; PF8 is established through its consumed internal planes and typed output. Other masks, geometry, values, seed/offset/thickness, Type3, and AE-host output remain unproven.",
        "fixture_sha256": {str(d): sha(configure(d, 25.0, 25.0, 1)[1]) for d in (8, 16, 32)},
        "cases": rows,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "exact" if exact else "mismatch", "cases": len(rows)}))
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]))
        Path(sys.argv[6]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
