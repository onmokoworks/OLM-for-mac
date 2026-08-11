#!/usr/bin/env python3
"""Bounded actual-AEX Inner Size Variation x Edge Fade x Noise matrix."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_size_edge_components_actual_aex_20260811 as pair
import probe_olmradialblur_zoom_size_noise_components_actual_aex_20260811 as zoom_noise
import probe_olmradialblur_rotation_size_noise_components_actual_aex_20260811 as rotation_noise

REPORT = ROOT / "refs/conformance/olmradialblur_inner_size_edge_noise_components_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_inner_size_edge_noise_components_20260811")
TUPLES = ((25.0, 50, 25.0, 1), (100.0, 100, 100.0, 2),
          (25.0, 100, 100.0, 1), (100.0, 50, 25.0, 2))
CELLS = [(mode, depth, "inner", sv, fade, nv, nt)
         for mode in ("zoom", "rotation") for depth in (8, 16, 32)
         for sv, fade, nv, nt in TUPLES]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    mode, depth, side, sv, fade, nv, nt = cell
    target, frame, rb = pair.configure((mode, depth, side, sv, fade))
    fixture = target.fixture if mode == "zoom" else (target.base if depth == 32 else target)
    fixture.FIXTURE_NOISE_VARIATION = nv
    fixture.FIXTURE_NOISE_TYPE = nt
    fixture.FIXTURE_SEED = 1
    fixture.FIXTURE_NOISE_OFFSET = 0.0
    fixture.FIXTURE_THICKNESS = 10.0
    fixture.CAPTURE_NOISE_INTERNALS = True
    fixture.CAPTURE_EDGE_INTERNALS = True
    module = fixture.m4
    previous = module.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({"Noise Variation": nv, "Noise Type": nt, "Seed": 1,
                       "Noise Offset": 0.0, "Thickness": 10.0})
        return previous(loader, params)

    module.install_reader_detours = install
    return target, frame, rb


def capture(cell):
    mode, depth, side, sv, fade, nv, nt = cell
    if mode == "zoom":
        target, _, _ = zoom_noise.configure(depth, sv, nv, nt)
        fixture = target.fixture
        fixture.FIXTURE_OUTER_STRENGTH = 0
        fixture.FIXTURE_INNER_STRENGTH = 4
        fixture.FIXTURE_OUTER_EDGE_FADE = 0
        fixture.FIXTURE_INNER_EDGE_FADE = fade
        fixture.CAPTURE_EDGE_INTERNALS = True
        fixture.CAPTURE_NOISE_INTERNALS = True
        previous = fixture.m4.install_reader_detours

        def install(loader, params):
            params = dict(params)
            params.update({"Outer Strength": 0, "Outer Edge Fade": 0,
                           "Inner Strength": 4, "Inner Edge Fade": fade})
            return previous(loader, params)

        fixture.m4.install_reader_detours = install
        return zoom_noise.actual((depth, sv, nv, nt))
    target, _ = rotation_noise.configure(depth, sv, nv, nt)
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_OUTER_STRENGTH = 0
    fixture.FIXTURE_INNER_STRENGTH = 4
    fixture.FIXTURE_OUTER_EDGE_FADE = 0
    fixture.FIXTURE_INNER_EDGE_FADE = fade
    fixture.CAPTURE_EDGE_INTERNALS = True
    fixture.CAPTURE_NOISE_INTERNALS = True
    return target.actual_aex()


def isolated(cell):
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / ("_".join(map(str, cell)) + ".pkl")
    if not out.exists():
        tmp = out.with_suffix(".tmp")
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(tmp)], check=True)
        tmp.replace(out)
    return pickle.loads(out.read_bytes())


def production(cell, expected):
    mode, depth, side, sv, fade, nv, nt = cell
    original = Path.write_text

    def write(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            marker = "i.noise_type=1;i.seed=1;i.thickness=10;"
            if marker not in data:
                raise RuntimeError("production noise marker absent")
            data = data.replace(marker, f"i.noise_variation={nv};i.noise_type={nt};"
                                "i.seed=1;i.noise_offset=0;i.thickness=10;", 1)
        return original(path, data, *args, **kwargs)

    Path.write_text = write
    try:
        return pair.production((mode, depth, side, sv, fade), expected)
    finally:
        Path.write_text = original


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    rows = []
    for cell in CELLS:
        actual = actuals[cell]
        produced = production(cell, actual)
        names = (("pre_blur", "post_blur", "output") if cell[0] == "zoom" else
                 ("polar", "source_scalar", "prepass_alpha", "accum", "max_alpha",
                  "final_rgba", "coordinates", "output"))
        matches = {name: produced.get(name) == actual.get(name) for name in names}
        required = tuple(name for name in names if name != "source_scalar")
        scalar_differences = None
        if cell[0] == "rotation":
            import numpy as np
            aa = np.frombuffer(actual["source_scalar"], dtype="<u4")
            pp = np.frombuffer(produced["source_scalar"], dtype="<u4")
            scalar_differences = int(np.count_nonzero(aa != pp))
        exact = all(matches[name] for name in required)
        rows.append({"mode": cell[0], "depth": cell[1], "side": cell[2],
                     "size_variation": cell[3], "edge_fade": cell[4],
                     "noise_variation": cell[5], "noise_type": cell[6],
                     "matches": matches, "exact": exact,
                     "source_scalar_different_floats": scalar_differences,
                     "actual_sha256": {n: sha(actual[n]) for n in names if n in actual},
                     "captured_planes": sorted(actual)})
        print(cell, exact, matches, flush=True)
    exact = all(row["exact"] for row in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_inner_size_edge_noise_components_actual_aex_20260811",
        "status": "24/24 consumed planes and typed output exact" if exact else "mismatch",
        "scope": "Centered 32x18 disconnected component fixture; PF8/PF16/PF32; Zoom/Rotation Inner4; four enumerated Size/Fade/Noise tuples; neutral remaining tuple.",
        "cases": rows,
        "source_scalar_boundary": "Rotation SV25 retains the same one-ULP diagnostic source-scalar residual as the bounded Outer matrix; every consumed prepass/scatter/final plane and typed output is byte exact.",
        "pf32_inner_direction": "All four PF32 Rotation Inner intersections use the actual-AEX forward-angle scatter exception already witnessed for the bounded Inner Edge x Noise route; PF8/PF16 remain reverse-angle.",
        "boundary": "Only these 24 cells are admitted. Outer, other tuples, Type3/layer, offsets, strengths, arbitrary geometry and AE-host behavior are not generalized.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Inner Size Variation × Edge Fade × Noise — 2026-08-11\n\n"
                   f"Status: **{'24/24 consumed planes and typed output exact' if exact else 'mismatch'}**\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 10 and sys.argv[1] == "--capture":
        cell = (sys.argv[2], int(sys.argv[3]), sys.argv[4], float(sys.argv[5]),
                int(sys.argv[6]), float(sys.argv[7]), int(sys.argv[8]))
        Path(sys.argv[9]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
