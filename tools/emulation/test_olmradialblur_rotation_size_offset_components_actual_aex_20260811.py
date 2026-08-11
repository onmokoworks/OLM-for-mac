#!/usr/bin/env python3
"""Bounded actual-AEX Rotation Size Variation x Offset component matrix."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
import probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811 as rotation_size

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_size_offset_components_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_rotation_size_offset_components_20260811")
CELLS = [(depth, side, size, mode) for depth in (8, 16, 32)
         for side in ("outer", "inner") for size in (25.0, 100.0) for mode in (2, 3)]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    depth, side, size, mode = cell
    target, frame = rotation_size.configure(depth, size)
    rb = 32 * {8: 4, 16: 8, 32: 16}[depth] + {8: 8, 16: 16, 32: 16}[depth]
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_OUTER_STRENGTH = 4 if side == "outer" else 0
    fixture.FIXTURE_INNER_STRENGTH = 0 if side == "outer" else 4
    if depth == 32:
        target.OUTER_STRENGTH = 4 if side == "outer" else 0
        target.INNER_STRENGTH = 0 if side == "outer" else 4
    module = target.base.m4 if depth == 32 else target.m4
    previous = module.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({
            "Outer Strength": 4 if side == "outer" else 0,
            "Outer Edge Fade": 0,
            "Outer Offset Mode": mode if side == "outer" else 1,
            "Outer Offset": 4 if side == "outer" else 0,
            "Inner Strength": 4 if side == "inner" else 0,
            "Inner Edge Fade": 0,
            "Inner Offset Mode": mode if side == "inner" else 1,
            "Inner Offset": 4 if side == "inner" else 0,
            "Size Variation": size, "Noise Variation": 0.0,
            "Noise Type": 1, "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0,
        })
        return previous(loader, params)

    module.install_reader_detours = install
    return target, frame, rb


def capture(cell):
    return configure(cell)[0].actual_aex()


def isolated(cell):
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / ("_".join(map(str, cell)) + ".pkl")
    if not out.exists():
        temporary = out.with_suffix(".tmp")
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(temporary)], check=True)
        temporary.replace(out)
    return pickle.loads(out.read_bytes())


def production(cell, expected):
    depth, side, size, mode = cell
    configured_target, configured_frame, configured_rb = configure(cell)
    original_configure = base.configure
    original_write = Path.write_text

    def configured(requested):
        frame_fn = (lambda seed=False: configured_frame(seed)) if callable(configured_frame) else (lambda seed=False: configured_frame)
        return configured_target, frame_fn, configured_rb, 16.0 if depth == 8 else 16, 9.0 if depth == 8 else 9

    def write(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            needle = "i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;"
            replacement = (f"i.outer_strength={4 if side == 'outer' else 0};"
                           "i.outer_edge_fade=0;"
                           f"i.outer_offset_mode={mode if side == 'outer' else 1};"
                           f"i.outer_offset={4 if side == 'outer' else 0};"
                           f"i.inner_strength={4 if side == 'inner' else 0};"
                           "i.inner_edge_fade=0;"
                           f"i.inner_offset_mode={mode if side == 'inner' else 1};"
                           f"i.inner_offset={4 if side == 'inner' else 0};")
            if needle not in data:
                raise RuntimeError("production info marker absent")
            data = data.replace(needle, replacement, 1)
            noise = "i.noise_type=1;i.seed=1;i.thickness=10;"
            data = data.replace(noise, f"i.size_variation={size};" + noise, 1)
        return original_write(path, data, *args, **kwargs)

    base.configure = configured
    Path.write_text = write
    try:
        return base.production(("rotation", depth, 32, 18, 0.0, 0.0, 1.0), expected)
    finally:
        base.configure = original_configure
        Path.write_text = original_write


def firstdiff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {"offset": i, "actual": x, "production": y}
    return None if len(a) == len(b) else {"offset": min(len(a), len(b)), "actual_len": len(a), "production_len": len(b)}


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    # With Edge Fade neutral the owner does not export a prepass-alpha plane;
    # source_span is the relevant pre-scatter witness for this intersection.
    names = ("polar", "source_scalar", "accum", "max_alpha",
             "final_rgba", "coordinates", "output")
    rows = []
    for cell in CELLS:
        actual = actuals[cell]
        produced = production(cell, actual)
        compared_names = names
        matches = {name: produced.get(name) == actual.get(name) for name in compared_names}
        diffs = {name: firstdiff(actual[name], produced[name]) for name in compared_names
                 if name in actual and name in produced and actual[name] != produced[name]}
        row = {"depth": cell[0], "side": cell[1], "size_variation": cell[2],
               "offset_mode": cell[3], "offset": 4, "matches": matches,
               "first_diffs": diffs, "exact": all(matches.values()),
               "actual_sha256": {name: sha(actual[name]) for name in compared_names}}
        if "size_factor" in actual:
            row["actual_size_factor_sha256"] = sha(actual["size_factor"])
        if "source_span" in actual:
            row["actual_source_span_sha256"] = sha(actual["source_span"])
        rows.append(row)
        print(cell, row["exact"], matches, diffs, flush=True)
    exact = all(row["exact"] for row in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_rotation_size_offset_components_actual_aex_20260811",
        "status": "24/24 exact" if exact else "mismatch",
        "scope": "Rotation centered 32x18 disconnected 1/4/9-component fixture; PF8/PF16/PF32; Size Variation 25/100 x Offset Mode2/UI4 or Mode3/UI4; Outer4/Inner4; neutral remaining tuple.",
        "coefficient_order": "The owner component size-factor is sampled into polar space and multiplies the per-radius Mode2/3 offset span before integer truncation and scatter.",
        "pf32_inner_direction": "Rotation Inner remains reverse scatter; no PF32 Inner exception is inferred for this matrix.",
        "cases": rows,
        "boundary": "Only these 24 fixed-fixture cells are admitted. Type3, other masks, geometries, values, edge/noise/layer intersections, strengths, modes, and AE-host behavior remain fail-closed.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Size Variation × Offset — 2026-08-11\n\n"
                   f"Status: **{'24/24 exact' if exact else 'mismatch'}**\n\n"
                   "固定32×18の分離component fixtureで、PF8/PF16/PF32、Size 25/100、Offset Mode2/3 UI4、Rotation Outer/Innerを比較します。component size-factorがpolarへsampleされ、Mode2/3のscatter位置へ反映される交差を確認します。\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), int(sys.argv[5]))
        Path(sys.argv[6]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
