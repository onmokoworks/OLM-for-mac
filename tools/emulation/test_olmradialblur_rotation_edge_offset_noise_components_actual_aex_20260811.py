#!/usr/bin/env python3
"""Rotation Edge Fade x Offset x procedural Noise, fixed 32x18 component frame."""
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
import probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811 as comp
import test_olmradialblur_rotation_offset_noise_components_actual_aex_20260811 as pair

SIDES = ("outer", "inner")
CELLS = [(d, side, fade, mode, nv, nt) for d in (8, 16, 32)
         for side in SIDES for fade in (50, 100) for mode in (2, 3)
         for nv in (25.0, 100.0) for nt in (1, 2)]
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_edge_offset_noise_components_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_rotation_edge_offset_noise_20260811")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    depth, side, fade, mode, nv, noise_type = cell
    target, frame = comp.configure(depth, 0.0)
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_SIZE_VARIATION = 0.0
    fixture.FIXTURE_NOISE_VARIATION = nv
    fixture.FIXTURE_NOISE_TYPE = noise_type
    fixture.FIXTURE_SEED = 1
    fixture.FIXTURE_NOISE_OFFSET = 0.0
    fixture.FIXTURE_THICKNESS = 10.0
    fixture.FIXTURE_OUTER_STRENGTH = 4 if side == "outer" else 0
    fixture.FIXTURE_INNER_STRENGTH = 4 if side == "inner" else 0
    fixture.FIXTURE_OUTER_EDGE_FADE = fade if side == "outer" else 0
    fixture.FIXTURE_INNER_EDGE_FADE = fade if side == "inner" else 0
    fixture.CAPTURE_NOISE_INTERNALS = True
    fixture.CAPTURE_EDGE_INTERNALS = True
    if depth == 32:
        target.OUTER_STRENGTH = 4 if side == "outer" else 0
        target.INNER_STRENGTH = 4 if side == "inner" else 0
    m = target.base.m4 if depth == 32 else target.m4
    original = m.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({
            "Outer Strength": 4 if side == "outer" else 0,
            "Outer Edge Fade": fade if side == "outer" else 0,
            "Outer Offset Mode": mode if side == "outer" else 1,
            "Outer Offset": 4 if side == "outer" else 0,
            "Inner Strength": 4 if side == "inner" else 0,
            "Inner Edge Fade": fade if side == "inner" else 0,
            "Inner Offset Mode": mode if side == "inner" else 1,
            "Inner Offset": 4 if side == "inner" else 0,
        })
        return original(loader, params)

    m.install_reader_detours = install
    return target, frame


def capture(cell):
    return configure(cell)[0].actual_aex()


def isolated_capture(cell):
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / ("_".join(map(str, cell)) + ".pkl")
    if not out.exists():
        temporary = out.with_suffix(".tmp")
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(temporary)], check=True)
        temporary.replace(out)
    return pickle.loads(out.read_bytes())


def compile_runner(depth, expected, directory):
    original = Path.write_text

    def write_text(path, data, *args, **kwargs):
        if path.name == f"runner_{depth}.cpp":
            data = data.replace("if(argc!=13)return 2;", "if(argc!=14)return 2;")
            data = data.replace(
                "int side=std::atoi(argv[1]),mode=std::atoi(argv[2]),nt=std::atoi(argv[4]);",
                "int side=std::atoi(argv[1]),mode=std::atoi(argv[2]),nt=std::atoi(argv[4]),fade=std::atoi(argv[13]);")
            data = data.replace(
                "i.outer_strength=side==0?4:0;i.outer_offset_mode=side==0?mode:1;i.outer_offset=side==0?4:0;",
                "i.outer_strength=side==0?4:0;i.outer_edge_fade=side==0?fade:0;i.outer_offset_mode=side==0?mode:1;i.outer_offset=side==0?4:0;")
            data = data.replace(
                "i.inner_strength=side==1?4:0;i.inner_offset_mode=side==1?mode:1;i.inner_offset=side==1?4:0;",
                "i.inner_strength=side==1?4:0;i.inner_edge_fade=side==1?fade:0;i.inner_offset_mode=side==1?mode:1;i.inner_offset=side==1?4:0;")
        return original(path, data, *args, **kwargs)

    Path.write_text = write_text
    try:
        return pair.compile_runner(depth, expected, directory)
    finally:
        Path.write_text = original


def production(cell, expected, exe, directory):
    depth, side, fade, mode, nv, noise_type = cell
    inp = directory / f"in_{depth}"
    inp.write_bytes(configure(cell)[1])
    names = ("output", "source_span", "polar", "source_scalar", "prepass_alpha", "accum", "tail")
    paths = [directory / ("_".join(map(str, cell)) + f"_{name}") for name in names]
    result = subprocess.run([str(exe), "0" if side == "outer" else "1", str(mode), str(nv),
                             str(noise_type), str(inp), *map(str, paths), str(fade)])
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    got = {name: path.read_bytes() for name, path in zip(names, paths)}
    tail = got.pop("tail")
    max_bytes = len(expected["max_alpha"])
    final_bytes = len(expected["final_rgba"])
    got["max_alpha"] = tail[:max_bytes]
    got["final_rgba"] = tail[max_bytes:max_bytes + final_bytes]
    got["coordinates"] = tail[max_bytes + final_bytes:]
    return got


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actual = dict(zip(CELLS, pool.map(isolated_capture, CELLS)))
    rows = []
    with tempfile.TemporaryDirectory(prefix="radial_edge_offset_noise_prod_") as raw:
        directory = Path(raw)
        runners = {d: compile_runner(d, actual[next(c for c in CELLS if c[0] == d)], directory)
                   for d in (8, 16, 32)}
        for cell in CELLS:
            a = actual[cell]
            p = production(cell, a, runners[cell[0]], directory)
            names = ("source_span", "polar", "source_scalar", "prepass_alpha", "accum",
                     "max_alpha", "final_rgba", "coordinates", "output")
            available = [name for name in names if name in a and name in p]
            matches = {name: a[name] == p[name] for name in available}
            semantic = {name: value for name, value in matches.items()
                        if not (name == "source_scalar" and cell[5] == 1)}
            exact = all(semantic.values())
            rows.append({"depth": cell[0], "side": cell[1], "edge_fade": cell[2],
                         "offset_mode": cell[3], "offset_ui": 4,
                         "noise_variation": cell[4], "noise_type": cell[5],
                         "exact": exact, "matches": matches,
                         "actual_sha256": {name: sha(a[name]) for name in available}})
            print(cell, exact, matches, flush=True)
    exact_count = sum(row["exact"] for row in rows)
    report = {
        "kind": "olmradialblur_rotation_edge_offset_noise_components_actual_aex_20260811",
        "status": "exact" if exact_count == len(rows) else "mismatch",
        "scope": "Rotation centered 32x18 component fixture; PF8/PF16/PF32; Outer/Inner Strength4; Edge Fade50/100; Offset Mode2/3 UI4; Noise Variation25/100; Noise Type1/2; SV0, Seed1, Noise Offset0, Thickness10.",
        "exact_cases": exact_count, "total_cases": len(rows), "cases": rows,
        "ordering": "Edge prepass consumes independent size factor 1.0; per-radius Mode2/3 span is multiplied by the procedural noise-composed source span before truncation and scatter.",
        "pf32_inner_direction": "Unlike the neutral-offset Edge x Noise path, Mode2/3 Edge x Offset x Noise uses the normal reverse Inner scatter direction at PF32.",
        "boundary": "Only these 96 fixed-fixture cells are admitted. PF8 source-span is unavailable; all available consumed planes and padded output are byte exact. Other values, Type3, Size Variation, geometry, and AE-host behavior remain fail-closed/unproved.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Rotation Edge Fade × Offset × Noise — 2026-08-11\n\n"
                   f"Status: **{report['status']}** ({exact_count}/{len(rows)})\n\n"
                   + report["scope"] + "\n\n" + report["ordering"] + "\n\nEvidence boundary: "
                   + report["boundary"] + "\n")
    return 0 if exact_count == len(rows) else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]),
                float(sys.argv[6]), int(sys.argv[7]))
        Path(sys.argv[8]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
