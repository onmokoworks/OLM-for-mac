#!/usr/bin/env python3
"""Actual-AEX matrix for Outer4 + Inner2/4 crossed with Type-1/2 noise."""
from __future__ import annotations

import hashlib
import json
import pickle
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_olmradialblur_zoom_dual_strength_actual_aex_20260811 as zoom
import probe_olmradialblur_rotation_dual_strength_32x18_actual_aex_20260811 as rotation

REPORT = ROOT / "refs/conformance/olmradialblur_dual_strength_noise_32x18_actual_aex_20260811.json"
CACHE = Path("/tmp/olmradialblur_dual_strength_noise_32x18_actual_aex_20260811.pkl")
CELLS = [(mode, depth, inner, nv, noise_type)
         for mode in ("zoom", "rotation") for depth in (8, 16, 32)
         for inner in (2, 4) for nv in (25.0, 100.0) for noise_type in (1, 2)]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure_actual(cell):
    mode, depth, inner, nv, noise_type = cell
    if mode == "zoom":
        synthetic = ("zoom", depth, 32, 18, 0.0, 0.0, 1.0, inner)
        target, *_ = zoom.base.configure(synthetic[:-1])
        zoom.set_strength(target, inner)
        fixture = target.fixture
    else:
        synthetic = (depth, inner)
        _, target = rotation.configure(synthetic)
        fixture = target.base if depth == 32 else target
    module = fixture.m4
    original = module.install_reader_detours

    def install(loader, params):
        values = dict(params)
        values.update({"Outer Strength": 4, "Inner Strength": inner,
                       "Noise Variation": nv, "Noise Type": noise_type,
                       "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0,
                       "Size Variation": 0.0})
        return original(loader, values)

    module.install_reader_detours = install
    return target


def actual(cell):
    return configure_actual(cell).actual_aex()


def isolated_actual(cell):
    with tempfile.TemporaryDirectory(prefix="radial_dual_noise_actual_") as raw:
        out = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--actual", *map(str, cell), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def production(cell, expected):
    mode, depth, inner, nv, noise_type = cell
    original = Path.write_text

    def write_text(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            marker = "i.noise_type=1;i.seed=1;i.thickness=10;"
            if marker not in data:
                raise RuntimeError("production noise marker absent")
            data = data.replace(marker,
                f"i.noise_variation={nv};i.noise_type={noise_type};"
                "i.seed=1;i.noise_offset=0;i.thickness=10;", 1)
        return original(path, data, *args, **kwargs)

    Path.write_text = write_text
    try:
        if mode == "zoom":
            synthetic = ("zoom", depth, 32, 18, 0.0, 0.0, 1.0, inner)
            return zoom.production_dual(synthetic, expected)
        return rotation.production((depth, inner), expected)
    finally:
        Path.write_text = original


def isolated_production(cell, expected):
    with tempfile.TemporaryDirectory(prefix="radial_dual_noise_prod_") as raw:
        inp = Path(raw) / "actual.pkl"
        out = Path(raw) / "production.pkl"
        inp.write_bytes(pickle.dumps(expected))
        proc = subprocess.run([sys.executable, __file__, "--production", *map(str, cell),
                               str(inp), str(out)])
        return proc.returncode, pickle.loads(out.read_bytes()) if out.exists() else None


def first_diff(a: bytes, b: bytes):
    offsets = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    return {"different_bytes": len(offsets), "first_byte_offset": offsets[0] if offsets else None}


def main() -> int:
    if CACHE.exists():
        captures = pickle.loads(CACHE.read_bytes())
    else:
        with ThreadPoolExecutor(max_workers=6) as pool:
            captures = dict(zip(CELLS, pool.map(isolated_actual, CELLS)))
        CACHE.write_bytes(pickle.dumps(captures))
    with ThreadPoolExecutor(max_workers=6) as pool:
        produced = dict(zip(CELLS, pool.map(lambda cell: isolated_production(cell, captures[cell]), CELLS)))
    rows = []
    for cell in CELLS:
        rc, got = produced[cell]
        names = (("pre_blur", "post_blur", "output") if cell[0] == "zoom" else
                 ("polar", "source_scalar", "prepass_alpha", "accum", "max_alpha",
                  "final_rgba", "coordinates", "output"))
        matches = {name: got is not None and got.get(name) == captures[cell].get(name) for name in names}
        consumed = tuple(name for name in names if name != "source_scalar")
        exact = rc == 0 and all(matches[name] for name in consumed)
        rows.append({
            "mode": cell[0], "depth": cell[1], "outer_strength": 4,
            "inner_strength": cell[2], "noise_variation": cell[3], "noise_type": cell[4],
            "exact": exact, "production_returncode": rc, "production_matches_actual": matches,
            "consumed_planes_and_output_exact": exact,
            "differences": ({name: first_diff(captures[cell][name], got[name])
                              for name, ok in matches.items() if not ok and got and name in got}),
            "actual_sha256": {name: sha(captures[cell][name]) for name in names},
        })
        print(cell, exact, matches, flush=True)
    exact_count = sum(row["exact"] for row in rows)
    scalar_boundary = [row for row in rows if not row["production_matches_actual"].get("source_scalar", True)]
    controls = {
        "zoom_inner3_nv25_type1": isolated_production(("zoom", 8, 3, 25.0, 1), captures[("zoom", 8, 2, 25.0, 1)])[0] != 0,
        "zoom_inner2_nv50_type1": isolated_production(("zoom", 8, 2, 50.0, 1), captures[("zoom", 8, 2, 25.0, 1)])[0] != 0,
        "zoom_inner2_nv25_type3": isolated_production(("zoom", 8, 2, 25.0, 3), captures[("zoom", 8, 2, 25.0, 1)])[0] != 0,
        "rotation_inner3_nv25_type1": isolated_production(("rotation", 8, 3, 25.0, 1), captures[("rotation", 8, 2, 25.0, 1)])[0] != 0,
        "rotation_inner2_nv50_type1": isolated_production(("rotation", 8, 2, 50.0, 1), captures[("rotation", 8, 2, 25.0, 1)])[0] != 0,
        "rotation_inner2_nv25_type3": isolated_production(("rotation", 8, 2, 25.0, 3), captures[("rotation", 8, 2, 25.0, 1)])[0] != 0,
    }
    status = "48/48 consumed internal planes and padded output byte exact" if exact_count == len(rows) and all(controls.values()) else "actual-AEX/shared-direct mismatch"
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_dual_strength_noise_32x18_actual_aex_20260811",
        "status": status,
        "scope": "Pinned actual AEX; centered 32x18 Zoom/Rotation; PF8/PF16/PF32; Outer4 + Inner2/4; Noise Variation25/100 Type1/2; Size0, fades0, neutral offsets, Brightness1, Repeat on, Quality5, Seed1 Offset0 Thickness10.",
        "compared": ["Zoom pre/post/output", "Rotation polar/source-scalar/prepass/accum/max/final/coordinates/output"],
        "exact_cases": exact_count, "total_cases": len(rows), "cases": rows,
        "fail_closed_controls": controls,
        "rotation_type1_source_scalar_boundary": {
            "cases": len(scalar_boundary),
            "classification": "1-4 ULP sampled-scalar differences that do not change prepass, shared accumulator, max-alpha, final RGBA, coordinates, or typed output",
            "note": "This is the already documented Type-1 sampled-scalar approximation boundary; it is captured explicitly and is not claimed byte exact.",
        },
        "boundary": "Only these 48 centered 32x18 cells are admitted. Other strengths, noise values/types, seed/offset/thickness, fades, geometry, Type3, and AE-host output remain unproven.",
    }, indent=2, sort_keys=True) + "\n")
    return 0 if exact_count == len(rows) else 1


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[1] == "--actual":
        cell = (sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6]))
        Path(sys.argv[7]).write_bytes(pickle.dumps(actual(cell)))
        raise SystemExit(0)
    if len(sys.argv) == 9 and sys.argv[1] == "--production":
        cell = (sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6]))
        Path(sys.argv[8]).write_bytes(pickle.dumps(production(cell, pickle.loads(Path(sys.argv[7]).read_bytes()))))
        raise SystemExit(0)
    raise SystemExit(main())
