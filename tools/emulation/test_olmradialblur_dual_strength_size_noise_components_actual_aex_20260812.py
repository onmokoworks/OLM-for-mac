#!/usr/bin/env python3
"""Bounded actual-AEX Dual Strength x Size x Noise covering matrix."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_dual_strength_size_components_actual_aex_20260811 as dual_size
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
import probe_olmradialblur_zoom_size_noise_components_actual_aex_20260811 as zoom_size_noise
import probe_olmradialblur_rotation_size_noise_components_actual_aex_20260811 as rotation_size_noise

REPORT = ROOT / "refs/conformance/olmradialblur_dual_strength_size_noise_components_actual_aex_20260812.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_dual_strength_size_noise_components_20260812")
TUPLES = ((25.0, 25.0, 1), (100.0, 100.0, 2))
CELLS = [(mode, depth, inner, size, noise, noise_type)
         for mode in ("zoom", "rotation") for depth in (8, 16, 32)
         for inner in (2, 4) for size, noise, noise_type in TUPLES]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    mode, depth, inner, size, noise, noise_type = cell
    base_cell = (mode, depth, inner, size)
    target, frame, rb = dual_size.configure(base_cell)
    fixture = target.fixture if mode == "zoom" else (target.base if depth == 32 else target)
    module = fixture.m4
    previous = module.install_reader_detours

    def install(loader, params):
        values = dict(params)
        values.update({"Noise Variation": noise, "Noise Type": noise_type,
                       "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0})
        return previous(loader, values)

    module.install_reader_detours = install
    return target, frame, rb


def capture(cell):
    if cell[0] == "zoom":
        return zoom_size_noise.actual((cell[1], cell[3], cell[4], cell[5], 1.0, cell[2]))
    return rotation_size_noise.configure(
        cell[1], cell[3], cell[4], cell[5], 1.0, cell[2])[0].actual_aex()


def isolated(cell):
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / ("_".join(map(str, cell)) + ".pkl")
    if not out.exists():
        temporary = out.with_suffix(".tmp")
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(temporary)], check=True)
        temporary.replace(out)
    return pickle.loads(out.read_bytes())


def production(cell, expected):
    mode, depth, inner, size, noise, noise_type = cell
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
            noise_marker = "i.noise_type=1;i.seed=1;i.thickness=10;"
            replacement = (f"i.size_variation={size};i.noise_variation={noise};"
                           f"i.noise_type={noise_type};i.seed=1;i.noise_offset=0;i.thickness=10;")
            if noise_marker not in data:
                raise RuntimeError("production noise marker absent")
            data = data.replace(noise_marker, replacement, 1)
        return original_write(path, data, *args, **kwargs)

    base.configure = configured
    Path.write_text = write
    try:
        return base.production((mode, depth, 32, 18, 0.0, 0.0, 1.0), expected)
    finally:
        base.configure = original_configure
        Path.write_text = original_write


def rejected(cell, expected):
    try:
        production(cell, expected)
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
                 ("polar", "source_scalar", "accum", "max_alpha",
                  "final_rgba", "coordinates", "output"))
        matches = {name: produced.get(name) == actual.get(name) for name in names}
        consumed = tuple(name for name in names if name != "source_scalar")
        row = {"mode": cell[0], "depth": cell[1], "outer_strength": 4,
               "inner_strength": cell[2], "size_variation": cell[3],
               "noise_variation": cell[4], "noise_type": cell[5],
               "matches": matches, "exact": all(matches[name] for name in consumed),
               "actual_sha256": {name: sha(actual[name]) for name in names}}
        for optional in ("size_factor", "source_span", "source_size_factor"):
            if optional in actual:
                row[f"actual_{optional}_sha256"] = sha(actual[optional])
        rows.append(row)
        print(cell, row["exact"], matches, flush=True)
    controls = {}
    for mode in ("zoom", "rotation"):
        witness = actuals[(mode, 8, 2, 25.0, 25.0, 1)]
        controls[f"{mode}_off_diagonal"] = rejected((mode, 8, 2, 25.0, 100.0, 2), witness)
        controls[f"{mode}_type3"] = rejected((mode, 8, 2, 25.0, 25.0, 3), witness)
        controls[f"{mode}_inner3"] = rejected((mode, 8, 3, 25.0, 25.0, 1), witness)
    exact = all(row["exact"] for row in rows) and all(controls.values())
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_dual_strength_size_noise_components_actual_aex_20260812",
        "status": "24/24 consumed paths and typed outputs exact" if exact else "mismatch",
        "scope": "Centered 32x18 disconnected 1/4/9-component fixture; Zoom/Rotation; PF8/PF16/PF32; Outer4 + Inner2/4; covering tuples Size25+Noise25 Type1 and Size100+Noise100 Type2; neutral remaining controls.",
        "composition": "The component size-factor and procedural noise factor multiply before the resulting span drives both outer and inner strength contributions.",
        "pf32_inner_direction": "Rotation Inner remains reverse scatter; no PF32 exception is inferred.",
        "rotation_type1_source_scalar_boundary": "The already documented portable Type-1 sampler differs by a few ULP in the exported sampled scalar. Polar, accumulator, max-alpha, normalized/final RGBA, coordinates, and typed output remain byte exact; this scalar alone is not claimed exact.",
        "cases": rows, "fail_closed_controls": controls,
        "boundary": "Only these 24 fixed-fixture cells are admitted. Off-diagonal size/noise tuples, Type3/layers, other strengths, values, masks, geometry, fades, offsets, and AE-host behavior remain fail-closed.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Dual Strength × Size × Noise — 2026-08-12\n\n"
                   f"Status: **{'24/24 consumed paths and typed outputs exact' if exact else 'mismatch'}**\n\n"
                   "固定32×18 component fixtureで、Size factorとNoise factorを合成したspanがOuter/Inner両方向へ使われる経路を、Zoom/Rotationと全bit-depthで比較します。\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--capture":
        cell = (sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]),
                float(sys.argv[6]), int(sys.argv[7]))
        Path(sys.argv[8]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
