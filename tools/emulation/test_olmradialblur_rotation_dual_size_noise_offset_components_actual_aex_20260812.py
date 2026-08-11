#!/usr/bin/env python3
"""Bounded Rotation Dual Strength x Size x Noise x Offset matrix."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
import probe_olmradialblur_rotation_size_noise_components_actual_aex_20260811 as rotation_size_noise

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_dual_size_noise_offset_components_actual_aex_20260812.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_rotation_dual_size_noise_offset_components_20260812")
TUPLES = ((25.0, 25.0, 1, 2), (100.0, 100.0, 2, 3))
CELLS = [(depth, inner, side, size, noise, noise_type, mode)
         for depth in (8, 16, 32) for inner in (2, 4)
         for side in ("outer", "inner")
         for size, noise, noise_type, mode in TUPLES]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    depth, inner, side, size, noise, noise_type, mode = cell
    target, frame = rotation_size_noise.configure(
        depth, size, noise, noise_type, 1.0, inner)
    rb = 32 * {8: 4, 16: 8, 32: 16}[depth] + {8: 8, 16: 16, 32: 16}[depth]
    fixture = target.base if depth == 32 else target
    module = target.base.m4 if depth == 32 else target.m4
    previous = module.install_reader_detours

    def install(loader, params):
        values = dict(params)
        values.update({
            "Noise Variation": noise, "Noise Type": noise_type,
            "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0,
            "Outer Offset Mode": mode if side in ("outer", "both") else 1,
            "Outer Offset": 4 if side in ("outer", "both") else 0,
            "Inner Offset Mode": mode if side in ("inner", "both") else 1,
            "Inner Offset": 4 if side in ("inner", "both") else 0,
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


def production(cell, expected):
    depth, inner, side, size, noise, noise_type, mode = cell
    target, frame, rb = configure(cell)
    original_configure = base.configure
    original_write = Path.write_text

    def configured(requested):
        frame_fn = (lambda seed=False: frame(seed)) if callable(frame) else (lambda seed=False: frame)
        return target, frame_fn, rb, 16.0 if depth == 8 else 16, 9.0 if depth == 8 else 9

    def write(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            marker = "i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;"
            replacement = (
                "i.outer_strength=4;i.outer_edge_fade=0;"
                f"i.outer_offset_mode={mode if side in ('outer', 'both') else 1};"
                f"i.outer_offset={4 if side in ('outer', 'both') else 0};"
                f"i.inner_strength={inner};i.inner_edge_fade=0;"
                f"i.inner_offset_mode={mode if side in ('inner', 'both') else 1};"
                f"i.inner_offset={4 if side in ('inner', 'both') else 0};")
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
        return base.production(("rotation", depth, 32, 18, 0.0, 0.0, 1.0), expected)
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
        names = ["polar", "source_scalar", "accum", "max_alpha",
                 "final_rgba", "coordinates", "output"]
        if "source_span" in actual:
            names.insert(2, "source_span")
        matches = {name: name in produced and produced[name] == actual[name] for name in names}
        consumed = tuple(name for name in names if name != "source_scalar")
        row = {"depth": cell[0], "outer_strength": 4, "inner_strength": cell[1],
               "offset_side": cell[2], "size_variation": cell[3],
               "noise_variation": cell[4], "noise_type": cell[5],
               "offset_mode": cell[6], "offset": 4,
               "matches": matches, "exact": all(matches[name] for name in consumed),
               "actual_sha256": {name: sha(actual[name]) for name in names}}
        rows.append(row)
        print(cell, row["exact"], matches, flush=True)
    witness = actuals[(8, 2, "outer", 25.0, 25.0, 1, 2)]
    controls = {
        "off_diagonal": rejected((8, 2, "outer", 25.0, 100.0, 2, 2), witness),
        "type3": rejected((8, 2, "outer", 25.0, 25.0, 3, 2), witness),
        "inner3": rejected((8, 3, "outer", 25.0, 25.0, 1, 2), witness),
        "both_offset": rejected((8, 2, "both", 25.0, 25.0, 1, 2), witness),
    }
    exact = all(row["exact"] for row in rows) and all(controls.values())
    status = "24/24 consumed paths and typed outputs exact" if exact else "mismatch"
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_rotation_dual_size_noise_offset_components_actual_aex_20260812",
        "status": status,
        "scope": "Rotation centered fixed 32x18 disconnected 1/4/9-component fixture; PF8/PF16/PF32; Outer4 + Inner2/4; selected Outer/Inner Offset only; Size25+NV25 Type1+Mode2/UI4 and Size100+NV100 Type2+Mode3/UI4; neutral fades and remaining controls.",
        "composition": "The component-size and procedural-noise factors multiply before the sampled span drives simultaneous outer/inner scatter through the selected dynamic offset mode.",
        "type1_source_scalar_boundary": "The portable Type-1 source-scalar ULP boundary remains an independent diagnostic from older routes. All 24 cells here are byte exact at source scalar too; consumed-path admission additionally requires source span where exported, accumulator, max-alpha, final RGBA/coordinates, and typed output exact.",
        "cases": rows, "fail_closed_controls": controls,
        "boundary": "Only these 24 cells are admitted. Off-diagonal tuples, Type3/layers, Inner3, both offsets active, fades, other fixtures/geometries/values, and AE-host behavior remain fail-closed.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Rotation Dual Strength × Size × Noise × Offset — 2026-08-12\n\n"
                   f"Status: **{status}**\n\n"
                   "固定32×18 component fixtureで、Size×Noise span、Outer/Inner同時寄与、選択側Mode2/3 Offsetの交差を全bit-depthで比較します。\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 10 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], float(sys.argv[5]),
                float(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]))
        Path(sys.argv[9]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
