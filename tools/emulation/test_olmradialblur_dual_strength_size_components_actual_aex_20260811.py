#!/usr/bin/env python3
"""Bounded actual-AEX Dual Strength x Size Variation component matrix."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
import probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811 as rotation_size
import probe_olmradialblur_zoom_size_variation_components_actual_aex_20260811 as zoom_size

REPORT = ROOT / "refs/conformance/olmradialblur_dual_strength_size_components_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_dual_strength_size_components_20260811")
CELLS = [(mode, depth, inner, size) for mode in ("zoom", "rotation")
         for depth in (8, 16, 32) for inner in (2, 4) for size in (25.0, 100.0)]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    mode, depth, inner, size = cell
    if mode == "zoom":
        target, frame, rb = zoom_size.configure(depth, size)
        fixture = target.fixture
        module = fixture.m4
    else:
        target, frame = rotation_size.configure(depth, size)
        rb = 32 * {8: 4, 16: 8, 32: 16}[depth] + {8: 8, 16: 16, 32: 16}[depth]
        fixture = target.base if depth == 32 else target
        module = target.base.m4 if depth == 32 else target.m4
    fixture.FIXTURE_OUTER_STRENGTH = 4
    fixture.FIXTURE_INNER_STRENGTH = inner
    if depth == 32 and mode == "rotation":
        target.OUTER_STRENGTH = 4
        target.INNER_STRENGTH = inner
    previous = module.install_reader_detours

    def install(loader, params):
        values = dict(params)
        values.update({
            "Outer Strength": 4, "Outer Edge Fade": 0,
            "Outer Offset Mode": 1, "Outer Offset": 0,
            "Inner Strength": inner, "Inner Edge Fade": 0,
            "Inner Offset Mode": 1, "Inner Offset": 0,
            "Size Variation": size, "Noise Variation": 0.0,
            "Noise Type": 1, "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0,
        })
        return previous(loader, values)

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


def production(cell, expected, noise_variation=0.0):
    mode, depth, inner, size = cell
    target, frame, rb = configure(cell)
    original_configure = base.configure
    original_write = Path.write_text

    def configured(requested):
        frame_fn = (lambda seed=False: frame(seed)) if callable(frame) else (lambda seed=False: frame)
        return target, frame_fn, rb, 16.0 if depth == 8 else 16, 9.0 if depth == 8 else 9

    def write(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            marker = "i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;"
            replacement = ("i.outer_strength=4;i.outer_edge_fade=0;"
                           "i.outer_offset_mode=1;i.outer_offset=0;"
                           f"i.inner_strength={inner};i.inner_edge_fade=0;"
                           "i.inner_offset_mode=1;i.inner_offset=0;")
            if marker not in data:
                raise RuntimeError("production parameter marker absent")
            data = data.replace(marker, replacement, 1)
            noise = "i.noise_type=1;i.seed=1;i.thickness=10;"
            data = data.replace(noise, f"i.size_variation={size};i.noise_variation={noise_variation};" + noise, 1)
        return original_write(path, data, *args, **kwargs)

    base.configure = configured
    Path.write_text = write
    try:
        return base.production((mode, depth, 32, 18, 0.0, 0.0, 1.0), expected)
    finally:
        base.configure = original_configure
        Path.write_text = original_write


def firstdiff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return {"offset": i, "actual": x, "production": y}
    return None if len(a) == len(b) else {"offset": min(len(a), len(b)), "actual_len": len(a), "production_len": len(b)}


def rejected(cell, expected, noise_variation=0.0):
    try:
        production(cell, expected, noise_variation=noise_variation)
    except AssertionError:
        return True
    return False


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    rows = []
    for cell in CELLS:
        actual = actuals[cell]
        produced = production(cell, actual)
        names = (("pre_blur", "post_blur", "output") if cell[0] == "zoom" else
                 ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output"))
        matches = {name: produced.get(name) == actual.get(name) for name in names}
        diffs = {name: firstdiff(actual[name], produced[name]) for name in names
                 if name in actual and name in produced and actual[name] != produced[name]}
        row = {"mode": cell[0], "depth": cell[1], "outer_strength": 4,
               "inner_strength": cell[2], "size_variation": cell[3],
               "matches": matches, "first_diffs": diffs, "exact": all(matches.values()),
               "actual_sha256": {name: sha(actual[name]) for name in names}}
        for optional in ("size_factor", "source_span", "source_size_factor"):
            if optional in actual:
                row[f"actual_{optional}_sha256"] = sha(actual[optional])
        rows.append(row)
        print(cell, row["exact"], matches, diffs, flush=True)
    exact = all(row["exact"] for row in rows)
    controls = {}
    for mode in ("zoom", "rotation"):
        witness = actuals[(mode, 8, 2, 25.0)]
        controls[f"{mode}_inner3"] = rejected((mode, 8, 3, 25.0), witness)
        controls[f"{mode}_size50"] = rejected((mode, 8, 2, 50.0), witness)
        # Size25 + Noise25 Type1 is now proven by the bounded dual-size-noise
        # closure. Keep this older matrix's negative control on an off-diagonal
        # tuple that remains deliberately unadmitted.
        controls[f"{mode}_size25_noise100_off_diagonal"] = rejected(
            (mode, 8, 2, 25.0), witness, noise_variation=100.0)
    exact = exact and all(controls.values())
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_dual_strength_size_components_actual_aex_20260811",
        "status": "24/24 exact" if exact else "mismatch",
        "scope": "Centered 32x18 disconnected 1/4/9-component fixture; Zoom/Rotation; PF8/PF16/PF32; Outer4 + Inner2/4; Size Variation25/100; neutral remaining tuple.",
        "coefficient_order": "The same owner component size-factor scales both outer and inner strength spans before their contributions overlap in the accumulator/max-alpha path.",
        "pf32_inner_direction": "Rotation Inner remains reverse scatter; no PF32 exception is inferred for this matrix.",
        "cases": rows,
        "fail_closed_controls": controls,
        "boundary": "Only these 24 size-only fixed-fixture cells are claimed here. Other strengths, size values, masks, geometry, fades, offsets, unproven Size x Noise tuples (including the off-diagonal Size25 + Noise100 Type1 control), Type3/layer intersections, and AE-host behavior remain fail-closed.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Dual Strength × Size Variation — 2026-08-11\n\n"
                   f"Status: **{'24/24 exact' if exact else 'mismatch'}**\n\n"
                   "固定32×18の分離component fixtureで、Zoom/Rotation、PF8/PF16/PF32、Outer4 + Inner2/4、Size 25/100を比較します。両方向のspanへ同じcomponent size-factorが適用され、重なり後の内部planeとtyped outputまで一致することを確認します。\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--capture":
        cell = (sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]))
        Path(sys.argv[6]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
