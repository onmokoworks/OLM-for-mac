#!/usr/bin/env python3
"""Bounded actual-AEX Size Variation x Edge Fade component matrix."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
import probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811 as rotation_size
import probe_olmradialblur_zoom_size_variation_components_actual_aex_20260811 as zoom_size

REPORT = ROOT / "refs/conformance/olmradialblur_size_edge_components_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_size_edge_components_20260811")
CELLS = [(mode, depth, side, size, fade)
         for mode, sides in (("zoom", ("outer",)), ("rotation", ("outer", "inner")))
         for depth in (8, 16, 32) for side in sides
         for size in (25.0, 100.0) for fade in (50, 100)]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    mode, depth, side, size, fade = cell
    if mode == "zoom":
        target, frame, rb = zoom_size.configure(depth, size)
        module = target.fixture.m4
    else:
        target, frame = rotation_size.configure(depth, size)
        rb = 32 * {8: 4, 16: 8, 32: 16}[depth] + {8: 8, 16: 16, 32: 16}[depth]
        fixture = target.base if depth == 32 else target
        fixture.FIXTURE_OUTER_STRENGTH = 4 if side == "outer" else 0
        fixture.FIXTURE_INNER_STRENGTH = 0 if side == "outer" else 4
        fixture.FIXTURE_OUTER_EDGE_FADE = fade if side == "outer" else 0
        fixture.FIXTURE_INNER_EDGE_FADE = fade if side == "inner" else 0
        fixture.CAPTURE_EDGE_INTERNALS = True
        module = target.base.m4 if depth == 32 else target.m4
    previous = module.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({
            "Outer Strength": 4 if side == "outer" else 0,
            "Outer Edge Fade": fade if side == "outer" else 0,
            "Outer Offset Mode": 1, "Outer Offset": 0,
            "Inner Strength": 4 if side == "inner" else 0,
            "Inner Edge Fade": fade if side == "inner" else 0,
            "Inner Offset Mode": 1, "Inner Offset": 0,
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
    mode, depth, side, size, fade = cell
    configured_target, configured_frame, configured_rb = configure(cell)
    original_configure = base.configure
    original_write = Path.write_text

    def configured(requested):
        cx = 16.0 if depth == 8 else 16
        cy = 9.0 if depth == 8 else 9
        frame_fn = (lambda seed=False: configured_frame(seed)) if callable(configured_frame) else (lambda seed=False: configured_frame)
        return configured_target, frame_fn, configured_rb, cx, cy

    def write(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            needle = "i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;"
            replacement = (f"i.outer_strength={4 if side == 'outer' else 0};"
                           f"i.outer_edge_fade={fade if side == 'outer' else 0};"
                           "i.outer_offset_mode=1;i.outer_offset=0;"
                           f"i.inner_strength={4 if side == 'inner' else 0};"
                           f"i.inner_edge_fade={fade if side == 'inner' else 0};"
                           "i.inner_offset_mode=1;i.inner_offset=0;")
            if needle not in data:
                raise RuntimeError("production info marker absent")
            data = data.replace(needle, replacement, 1)
            noise = "i.noise_type=1;i.seed=1;i.thickness=10;"
            data = data.replace(noise, f"i.size_variation={size};" + noise, 1)
        return original_write(path, data, *args, **kwargs)

    base.configure = configured
    Path.write_text = write
    try:
        synthetic = (mode, depth, 32, 18, 0.0, 0.0, 1.0)
        return base.production(synthetic, expected)
    finally:
        base.configure = original_configure
        Path.write_text = original_write


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    rows = []
    for cell in CELLS:
        actual = actuals[cell]
        produced = production(cell, actual)
        if cell[0] == "zoom":
            names = ("pre_blur", "post_blur", "output")
        else:
            names = ("polar", "source_scalar", "prepass_alpha", "accum", "max_alpha",
                     "final_rgba", "coordinates", "output")
        matches = {name: produced.get(name) == actual.get(name) for name in names}
        row = {"mode": cell[0], "depth": cell[1], "side": cell[2],
               "size_variation": cell[3], "edge_fade": cell[4],
               "matches": matches, "exact": all(matches.values()),
               "actual_sha256": {name: sha(actual[name]) for name in names}}
        if "size_factor" in actual:
            row["actual_size_factor_sha256"] = sha(actual["size_factor"])
        if "source_span" in actual:
            row["actual_source_span_sha256"] = sha(actual["source_span"])
        rows.append(row)
        print(cell, row["exact"], matches, flush=True)
    exact = all(row["exact"] for row in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_size_edge_components_actual_aex_20260811",
        "status": "36/36 exact" if exact else "mismatch",
        "scope": "Centered 32x18 disconnected 1/4/9-component fixture; PF8/PF16/PF32; Size Variation 25/100 x Edge Fade 50/100; Zoom Outer4 and Rotation Outer4/Inner4; neutral remaining tuple.",
        "coefficient_order": "The owner component size-factor is sampled into polar space. Edge Fade prepass consumes that size-factor, and the later strength scatter consumes the same factor because Noise Variation is zero.",
        "pf32_inner_direction": "Rotation Inner remains reverse scatter. The forward exception is confined to the independently witnessed PF32 Edge x Noise route.",
        "cases": rows,
        "boundary": "Only these 36 fixed-fixture cells are admitted. Other masks, component shapes, geometry, values, noise/layer intersections, offsets, strengths, modes, and AE-host behavior remain fail-closed.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Size Variation × Edge Fade — 2026-08-11\n\n"
                   f"Status: **{'36/36 exact' if exact else 'mismatch'}**\n\n"
                   "固定32×18の分離component fixtureで、PF8/PF16/PF32、Size 25/100、Fade 50/100、Zoom Outer・Rotation Outer/Innerを比較します。Edge prepassはcomponent size-factorを使い、Noise=0のため後段scatterも同じfactorを使います。PF32 Rotation Innerはreverse scatterのままです。\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[1] == "--capture":
        cell = (sys.argv[2], int(sys.argv[3]), sys.argv[4], float(sys.argv[5]), int(sys.argv[6]))
        Path(sys.argv[7]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
