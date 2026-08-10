#!/usr/bin/env python3
"""Read-only probe: Rotation Outer Edge Fade 50 x Mode3/UI4 offset."""
from __future__ import annotations

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
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base

CELLS = [(depth, side, mode, 4) for depth in (8, 16, 32)
         for side in ("outer", "inner") for mode in (2, 3)]
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_edge_offset_32x18_probe_20260811.json"


def configure(cell):
    depth, side, mode, offset = cell
    synthetic = ("rotation", depth, 32, 18, 0.0, 0.0, 1.0)
    target, *_ = base.configure(synthetic)
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_OUTER_STRENGTH = 4 if side == "outer" else 0
    fixture.FIXTURE_INNER_STRENGTH = 0 if side == "outer" else 4
    fixture.FIXTURE_OUTER_EDGE_FADE = 50 if side == "outer" else 0
    fixture.FIXTURE_INNER_EDGE_FADE = 0 if side == "outer" else 50
    fixture.CAPTURE_EDGE_INTERNALS = True
    if depth == 32:
        target.OUTER_STRENGTH = 4 if side == "outer" else 0
        target.INNER_STRENGTH = 0 if side == "outer" else 4
    m = target.base.m4 if depth == 32 else target.m4
    old = m.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({
            "Outer Offset Mode": mode if side == "outer" else 1,
            "Outer Offset": offset if side == "outer" else 0,
            "Inner Offset Mode": mode if side == "inner" else 1,
            "Inner Offset": offset if side == "inner" else 0,
        })
        return old(loader, params)

    m.install_reader_detours = install
    return synthetic, target


def capture(cell):
    return configure(cell)[1].actual_aex()


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="rotation_edge_offset_") as raw:
        out = Path(raw) / "a.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def production(cell, expected):
    _, side, mode, offset = cell
    synthetic, _ = configure(cell)
    old = Path.write_text

    def write_text(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            marker = "i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;"
            replacement = (
                f"i.outer_strength={4 if side == 'outer' else 0};"
                f"i.outer_edge_fade={50 if side == 'outer' else 0};"
                f"i.outer_offset_mode={mode if side == 'outer' else 1};"
                f"i.outer_offset={offset if side == 'outer' else 0};"
                f"i.inner_strength={4 if side == 'inner' else 0};"
                f"i.inner_edge_fade={50 if side == 'inner' else 0};"
                f"i.inner_offset_mode={mode if side == 'inner' else 1};"
                f"i.inner_offset={offset if side == 'inner' else 0};"
            )
            if marker not in data:
                raise RuntimeError("production parameter marker missing")
            data = data.replace(marker, replacement, 1)
        return old(path, data, *args, **kwargs)

    Path.write_text = write_text
    try:
        return base.production(synthetic, expected)
    finally:
        Path.write_text = old


def firstdiff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {"offset": i, "actual": x, "production": y}
    if len(a) != len(b):
        return {"offset": min(len(a), len(b)), "actual_len": len(a), "production_len": len(b)}
    return None


def main():
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    rows = []
    names = ("polar", "source_scalar", "prepass_alpha", "accum", "max_alpha", "final_rgba", "coordinates", "output")
    for cell in CELLS:
        depth, side, mode, offset = cell
        actual = actuals[cell]
        prod = production(cell, actual)
        matches = {name: name in actual and name in prod and actual[name] == prod[name] for name in names}
        diffs = {name: firstdiff(actual[name], prod[name]) for name in names
                 if name in actual and name in prod and actual[name] != prod[name]}
        rows.append({"depth": depth, "side": side, "strength": 4, "edge_fade": 50,
                     "offset_mode": mode, "offset": offset,
                     "matches": matches, "first_diffs": diffs})
        print(cell, matches, diffs, flush=True)
    exact = sum(all(row["matches"].values()) for row in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_rotation_edge_offset_32x18_probe_20260811",
        "status": "exact" if exact == len(rows) else "mismatch",
        "scope": "Rotation centered 32x18, PF8/PF16/PF32, matching Outer/Inner Strength4 + Edge Fade50 x Offset Mode2/UI4 or Mode3/UI4; opposite side and remaining controls neutral.",
        "exact_cases": exact,
        "total_cases": len(rows),
        "cases": rows,
        "boundary": "Only the enumerated shared-production Fade50 centered 32x18 Mode2/UI4 and Mode3/UI4 tuples are admitted. Fade100, Mode2/UI2, other values/geometries, and AE-host behavior remain unproved.",
    }, indent=2, sort_keys=True) + "\n")
    return 0 if exact == len(rows) else 1


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
        Path(sys.argv[6]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
