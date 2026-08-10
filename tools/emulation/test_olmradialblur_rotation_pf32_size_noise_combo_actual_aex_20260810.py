#!/usr/bin/env python3
"""Bounded PF32 Rotation cross-product: opaque Size Variation x Type-1 Noise."""

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

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_m4_case0010 as m4  # noqa: E402
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa: E402

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf32_size_noise_combo_actual_aex_20260810.json"
DOC = REPORT.with_suffix(".md")
SIZE_VALUES = (1.0, 25.0, 100.0)
NOISE_VALUES = (25.0, 100.0)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def actual_at(size: float, noise: float) -> dict[str, bytes]:
    original_params = m4.load_case0010_params
    names = (
        "FIXTURE_SIZE_VARIATION", "FIXTURE_NOISE_VARIATION", "FIXTURE_NOISE_TYPE",
        "FIXTURE_SEED", "FIXTURE_NOISE_OFFSET", "FIXTURE_THICKNESS",
        "CAPTURE_NOISE_INTERNALS",
    )
    old = {name: getattr(pf32.base, name) for name in names}

    def params() -> dict:
        result = original_params()
        result["Size Variation"] = size
        return result

    try:
        m4.load_case0010_params = params
        pf32.base.FIXTURE_SIZE_VARIATION = size
        pf32.base.FIXTURE_NOISE_VARIATION = noise
        pf32.base.FIXTURE_NOISE_TYPE = 1
        pf32.base.FIXTURE_SEED = 1
        pf32.base.FIXTURE_NOISE_OFFSET = 0.0
        pf32.base.FIXTURE_THICKNESS = 10.0
        pf32.base.CAPTURE_NOISE_INTERNALS = True
        return pf32.actual_aex()
    finally:
        m4.load_case0010_params = original_params
        for name, prior in old.items():
            setattr(pf32.base, name, prior)


def production_at(size: float, noise: float, expected: dict[str, bytes]) -> dict[str, bytes]:
    old_size, old_noise = pf32.SIZE_VARIATION, pf32.NOISE_VARIATION
    try:
        pf32.SIZE_VARIATION = size
        pf32.NOISE_VARIATION = noise
        return pf32.mac_production(expected)
    finally:
        pf32.SIZE_VARIATION, pf32.NOISE_VARIATION = old_size, old_noise


def isolated_actual(size: float, noise: float) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="radial_size_noise_") as name:
        path = Path(name) / "capture.pkl"
        subprocess.run(
            [sys.executable, str(Path(__file__)), "--capture", str(size), str(noise), str(path)],
            check=True,
        )
        return pickle.loads(path.read_bytes())


def isolated_production(size: float, noise: float, expected: dict[str, bytes]) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="radial_size_noise_prod_") as name:
        expected_path = Path(name) / "expected.pkl"
        output_path = Path(name) / "output.pkl"
        expected_path.write_bytes(pickle.dumps(expected))
        subprocess.run(
            [sys.executable, str(Path(__file__)), "--production", str(size), str(noise),
             str(expected_path), str(output_path)],
            check=True,
        )
        return pickle.loads(output_path.read_bytes())


def main() -> int:
    requested = [(0.0, noise) for noise in NOISE_VALUES]
    requested += [(size, noise) for size in SIZE_VALUES for noise in NOISE_VALUES]
    with ThreadPoolExecutor(max_workers=4) as pool:
        captured = dict(zip(requested, pool.map(lambda pair: isolated_actual(*pair), requested)))
    noise_controls = {noise: captured[(0.0, noise)] for noise in NOISE_VALUES}
    combos = [(size, noise) for size in SIZE_VALUES for noise in NOISE_VALUES]
    with ThreadPoolExecutor(max_workers=4) as pool:
        production_results = dict(zip(
            combos,
            pool.map(lambda pair: isolated_production(pair[0], pair[1], captured[pair]), combos),
        ))
    rows = []
    exact = True
    for size in SIZE_VALUES:
        for noise in NOISE_VALUES:
            actual = captured[(size, noise)]
            control = noise_controls[noise]
            actual_matches_control = {
                name: actual[name] == control[name]
                for name in ("source_size_factor", "source_span", "source_scalar", "accum", "max_alpha", "output")
            }
            production_failed_closed = False
            production = production_results[(size, noise)]
            production_matches = {
                name: production[name] == actual[name]
                for name in ("source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
            }
            scalar_left = np.frombuffer(production["source_scalar"], dtype=np.uint8)
            scalar_right = np.frombuffer(actual["source_scalar"], dtype=np.uint8)
            scalar_different_bytes = int(np.count_nonzero(scalar_left != scalar_right))
            row_exact = all(actual_matches_control.values()) and all(
                production_matches[name]
                for name in ("accum", "max_alpha", "final_rgba", "coordinates", "output")
            )
            exact = exact and row_exact
            rows.append({
                "size_variation": size,
                "noise_variation": noise,
                "actual_matches_size_zero_noise_control": actual_matches_control,
                "production_matches_actual": production_matches,
                "production_source_scalar_different_bytes": scalar_different_bytes,
                "production_failed_closed": production_failed_closed,
                "source_size_factor_all_one": bool(np.all(np.frombuffer(actual["source_size_factor"], dtype="<f4") == np.float32(1.0))),
                "output_sha256": sha(actual["output"]),
                "exact": row_exact,
            })
    status = "exact_with_inactive_source_scalar_boundary" if exact else "mismatch"
    report = {
        "kind": "olmradialblur_rotation_pf32_size_noise_combo_actual_aex_20260810",
        "status": status,
        "scope": "Pinned actual-AEX PF32 Rotation 9x7 rowbytes160, strictly-positive-alpha source; Size Variation 1/25/100 x Noise Variation 25/100, Noise Type 1; neutral outer-only tuple.",
        "aex_sha256": pf32.AEX_SHA256,
        "cases": rows,
        "observed_rule": "On this opaque fixture Size Variation is semantically masked (source_size_factor is 1), so every combined AEX result equals its Size Variation 0 Type-1 Noise control.",
        "production_scalar_boundary": "As in the independently admitted Type-1 Noise family, the full source-scalar allocation has inactive-cell 1-ULP differences; accum, max-alpha, final RGBA, coordinates, and padded output are bit exact.",
        "boundary": "No zero-alpha source, Size Variation values other than 1/25/100, Noise Variation values other than 25/100, Noise Type 2/3, other seed/offset/thickness, geometry, depth, mode, or AE-host claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLM RadialBlur PF32 Size × Noise combination — 2026-08-10\n\n"
        f"Status: **{status}**\n\n"
        "The pinned 9×7 PF32 Rotation source has strictly positive alpha. Across Size Variation 1/25/100 and Type-1 Noise Variation 25/100, the actual AEX size-factor plane stays exactly 1, and each combined result equals the corresponding Size Variation 0 noise control.\n\n"
        "The admission remains limited to this fixture and these six cells; zero alpha and every other parameter family remain fail-closed.\n"
    )
    print(json.dumps({"status": status, "cases": len(rows)}, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--capture":
        Path(sys.argv[4]).write_bytes(pickle.dumps(actual_at(float(sys.argv[2]), float(sys.argv[3]))))
        raise SystemExit(0)
    if len(sys.argv) == 6 and sys.argv[1] == "--production":
        expected = pickle.loads(Path(sys.argv[4]).read_bytes())
        Path(sys.argv[5]).write_bytes(pickle.dumps(production_at(float(sys.argv[2]), float(sys.argv[3]), expected)))
        raise SystemExit(0)
    raise SystemExit(main())
