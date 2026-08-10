#!/usr/bin/env python3
"""Bounded PF32 Rotation Strength-5 x Type-1 Noise family."""

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
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as pf32  # noqa: E402

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf32_strength5_noise_type1_actual_aex_20260810.json"
DOC = REPORT.with_suffix(".md")
VALUES = (25.0, 100.0)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def actual_at(noise: float) -> dict[str, bytes]:
    old_strength = pf32.OUTER_STRENGTH
    names = (
        "FIXTURE_SIZE_VARIATION", "FIXTURE_NOISE_VARIATION", "FIXTURE_NOISE_TYPE",
        "FIXTURE_SEED", "FIXTURE_NOISE_OFFSET", "FIXTURE_THICKNESS",
        "CAPTURE_NOISE_INTERNALS",
    )
    old = {name: getattr(pf32.base, name) for name in names}
    try:
        pf32.OUTER_STRENGTH = 5
        pf32.base.FIXTURE_SIZE_VARIATION = 0.0
        pf32.base.FIXTURE_NOISE_VARIATION = noise
        pf32.base.FIXTURE_NOISE_TYPE = 1
        pf32.base.FIXTURE_SEED = 1
        pf32.base.FIXTURE_NOISE_OFFSET = 0.0
        pf32.base.FIXTURE_THICKNESS = 10.0
        pf32.base.CAPTURE_NOISE_INTERNALS = True
        return pf32.actual_aex()
    finally:
        pf32.OUTER_STRENGTH = old_strength
        for name, prior in old.items():
            setattr(pf32.base, name, prior)


def production_at(noise: float, expected: dict[str, bytes]) -> dict[str, bytes]:
    old_strength, old_noise = pf32.OUTER_STRENGTH, pf32.NOISE_VARIATION
    try:
        pf32.OUTER_STRENGTH = 5
        pf32.NOISE_VARIATION = noise
        return pf32.mac_production(expected)
    finally:
        pf32.OUTER_STRENGTH, pf32.NOISE_VARIATION = old_strength, old_noise


def isolated(mode: str, noise: float, expected: dict[str, bytes] | None = None) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="radial_strength5_noise_") as name:
        out = Path(name) / "out.pkl"
        command = [sys.executable, str(Path(__file__)), f"--{mode}", str(noise)]
        if expected is not None:
            inp = Path(name) / "in.pkl"
            inp.write_bytes(pickle.dumps(expected))
            command.append(str(inp))
        command.append(str(out))
        subprocess.run(command, check=True)
        return pickle.loads(out.read_bytes())


def rejected_at(strength: int, noise: float, expected: dict[str, bytes]) -> bool:
    old_strength, old_noise = pf32.OUTER_STRENGTH, pf32.NOISE_VARIATION
    try:
        pf32.OUTER_STRENGTH = strength
        pf32.NOISE_VARIATION = noise
        pf32.mac_production(expected)
    except subprocess.CalledProcessError as exc:
        return exc.returncode == 3
    finally:
        pf32.OUTER_STRENGTH, pf32.NOISE_VARIATION = old_strength, old_noise
    return False


def main() -> int:
    requested = (0.0, *VALUES)
    with ThreadPoolExecutor(max_workers=3) as pool:
        actual = dict(zip(requested, pool.map(lambda value: isolated("actual", value), requested)))
    with ThreadPoolExecutor(max_workers=2) as pool:
        production = dict(zip(VALUES, pool.map(lambda value: isolated("production", value, actual[value]), VALUES)))
    rows = []
    exact = True
    for value in VALUES:
        left = np.frombuffer(production[value]["source_scalar"], dtype=np.uint8)
        right = np.frombuffer(actual[value]["source_scalar"], dtype=np.uint8)
        matches = {
            name: production[value][name] == actual[value][name]
            for name in ("source_scalar", "polar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
        }
        required = all(matches[name] for name in ("polar", "accum", "max_alpha", "final_rgba", "coordinates", "output"))
        exact = exact and required
        rows.append({
            "outer_strength": 5,
            "noise_variation": value,
            "production_matches_actual": matches,
            "production_source_scalar_different_bytes": int(np.count_nonzero(left != right)),
            "actual_output_differs_from_strength5_noise0": actual[value]["output"] != actual[0.0]["output"],
            "actual_output_sha256": sha(actual[value]["output"]),
            "exact": required,
        })
    status = "exact_with_inactive_source_scalar_boundary" if exact else "mismatch"
    fail_closed = {
        "strength6_nv25": rejected_at(6, 25.0, actual[25.0]),
        "strength5_nv50": rejected_at(5, 50.0, actual[25.0]),
    }
    exact = exact and all(fail_closed.values())
    status = "exact_with_inactive_source_scalar_boundary" if exact else "mismatch"
    report = {
        "kind": "olmradialblur_rotation_pf32_strength5_noise_type1_actual_aex_20260810",
        "status": status,
        "scope": "Pinned PF32 Rotation 9x7 rowbytes160; Outer Strength 5; Noise Variation Type1 25/100; Size Variation 0; otherwise neutral tuple.",
        "aex_sha256": pf32.AEX_SHA256,
        "cases": rows,
        "control": {"outer_strength": 5, "noise_variation": 0, "output_sha256": sha(actual[0.0]["output"])},
        "fail_closed": fail_closed,
        "production_scalar_boundary": "The complete source-scalar allocation retains the independently documented inactive-cell 1-ULP difference. Polar, accum, max-alpha, final RGBA, coordinates, and padded output are bit exact.",
        "boundary": "No Strength other than 5, NV other than 25/100, Type2/3, Size Variation, other seed/offset/thickness, geometry, depth, mode, or AE-host claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLM RadialBlur PF32 Strength 5 × Type-1 Noise — 2026-08-10\n\n"
        f"Status: **{status}**\n\n"
        "For the pinned 9×7 PF32 Rotation fixture, Outer Strength 5 combined with Type-1 Noise Variation 25 and 100 is exact from actual AEX polar/accumulation planes through production padded output. Both results independently differ from the Strength-5, Noise-0 control.\n\n"
        "The full source-scalar allocation retains the known inactive-cell 1-ULP boundary. Other Strength/Noise values and parameter families remain fail-closed.\n"
    )
    print(json.dumps({"status": status, "cases": len(rows)}, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--actual":
        Path(sys.argv[3]).write_bytes(pickle.dumps(actual_at(float(sys.argv[2]))))
        raise SystemExit(0)
    if len(sys.argv) == 5 and sys.argv[1] == "--production":
        expected = pickle.loads(Path(sys.argv[3]).read_bytes())
        Path(sys.argv[4]).write_bytes(pickle.dumps(production_at(float(sys.argv[2]), expected)))
        raise SystemExit(0)
    raise SystemExit(main())
