#!/usr/bin/env python3
"""Brightness x component Size Variation x procedural Noise, actual AEX vs production."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_olmradialblur_zoom_size_noise_components_actual_aex_20260811 as zoom
import probe_olmradialblur_rotation_size_noise_components_actual_aex_20260811 as rotation

REPORT = ROOT / "refs/conformance/olmradialblur_brightness_size_noise_components_actual_aex_20260811.json"
PILOT = (
    (.5, 25., 100., 1),
    (.5, 100., 25., 2),
    (2., 25., 25., 2),
    (2., 100., 100., 1),
)
FULL = tuple((gain, sv, nv, nt) for gain in (.5, 2.) for sv in (25., 100.)
             for nv in (25., 100.) for nt in (1, 2))


def cells(full: bool):
    matrix = FULL if full else PILOT
    return [(mode, depth, sv, nv, nt, gain) for mode in ("zoom", "rotation")
            for depth in (8, 16, 32) for gain, sv, nv, nt in matrix]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def actual(cell):
    mode, depth, sv, nv, nt, gain = cell
    target = zoom if mode == "zoom" else rotation
    return target.actual((depth, sv, nv, nt, gain)) if mode == "zoom" else target.capture((depth, sv, nv, nt, gain))


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_brightness_size_noise_") as raw:
        out = Path(raw) / "actual.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def production(cell, expected):
    mode, depth, sv, nv, nt, gain = cell
    target = zoom if mode == "zoom" else rotation
    return target.production((depth, sv, nv, nt, gain), expected)


def expected_output(depth: int, normalized: bytes, gain: float, actual_output: bytes) -> bytes:
    rgba = np.frombuffer(normalized, dtype="<f4").reshape(18, 32, 4)
    final = rgba.copy()
    final[:, :, :3] = np.minimum(
        np.multiply(final[:, :, :3], np.float32(gain), dtype=np.float32), np.float32(1.0))
    pixel_bytes = {8: 4, 16: 8, 32: 16}[depth]
    rowbytes = 32 * pixel_bytes + {8: 8, 16: 16, 32: 16}[depth]
    out = bytearray(len(actual_output))
    for y in range(18):
        for x in range(32):
            r, g, b, a = final[y, x]
            offset = y * rowbytes + x * pixel_bytes
            if depth == 8:
                values = [a, r, g, b]
                out[offset:offset + 4] = bytes(int(np.float32(v) * np.float32(255.0)) & 0xff for v in values)
            elif depth == 16:
                values = [a, r, g, b]
                struct.pack_into("<4H", out, offset,
                                 *(int(np.float32(v) * np.float32(32768.0)) & 0xffff for v in values))
            else:
                struct.pack_into("<4f", out, offset, a, r, g, b)
        out[y * rowbytes + 32 * pixel_bytes:(y + 1) * rowbytes] = actual_output[
            y * rowbytes + 32 * pixel_bytes:(y + 1) * rowbytes]
    return bytes(out)


def main(full: bool) -> int:
    requested = cells(full)
    controls = sorted({(mode, depth, sv, nv, nt, 1.0)
                       for mode, depth, sv, nv, nt, _gain in requested})
    all_cells = controls + requested
    with ThreadPoolExecutor(max_workers=6) as pool:
        captures = dict(zip(all_cells, pool.map(isolated, all_cells)))
    rows = []
    for cell in requested:
        mode, depth, sv, nv, nt, gain = cell
        got = captures[cell]
        control = captures[(mode, depth, sv, nv, nt, 1.0)]
        upstream_names = (("source_size_factor", "source_span", "pre_blur", "post_blur")
                          if mode == "zoom" else
                          ("size_factor", "source_scalar", "polar", "accum", "max_alpha", "coordinates"))
        upstream = {name: got[name] == control[name] for name in upstream_names if name in got and name in control}
        normalized_same = got["final_rgba"] == control["final_rgba"]
        formula = expected_output(depth, control["final_rgba"], gain, got["output"])
        formula_exact = formula == got["output"]
        visible = 32 * {8: 4, 16: 8, 32: 16}[depth]
        rowbytes = len(got["output"]) // 18
        padding_exact = all(got["output"][y * rowbytes + visible:(y + 1) * rowbytes] ==
                            control["output"][y * rowbytes + visible:(y + 1) * rowbytes]
                            for y in range(18))
        produced = production(cell, got)
        compared = (("pre_blur", "post_blur", "output") if mode == "zoom" else
                    ("polar", "accum", "max_alpha", "final_rgba", "coordinates", "output"))
        production_matches = {name: produced[name] == got[name] for name in compared if name in produced and name in got}
        production_source_scalar_exact = (produced.get("source_scalar") == got.get("source_scalar")) if mode == "rotation" else None
        exact = (all(upstream.values()) and normalized_same and formula_exact and padding_exact
                 and len(production_matches) == len(compared) and all(production_matches.values()))
        rows.append({
            "mode": mode, "depth": depth, "brightness_gain": gain,
            "size_variation": sv, "noise_variation": nv, "noise_type": nt,
            "upstream_gain_invariant": upstream,
            "normalized_rgba_gain_invariant": normalized_same,
            "actual_output_equals_f32_gain_upper_clamp_pack": formula_exact,
            "padding_gain_invariant": padding_exact,
            "production_matches_actual": production_matches,
            "production_source_scalar_exact": production_source_scalar_exact,
            "exact": exact,
            "actual_sha256": {name: sha(got[name]) for name in (*upstream_names, "final_rgba", "output") if name in got},
        })
        print(cell, exact, production_matches, flush=True)
    exact = all(row["exact"] for row in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_brightness_size_noise_components_actual_aex_20260811",
        "status": f"{len(rows)}/{len(rows)} exact" if exact else "mismatch",
        "phase": "full" if full else "pilot",
        "scope": "Centered Zoom/Rotation 32x18 component fixtures; PF8/PF16/PF32; Brightness .5/2; SV25/100 x NV25/100 x procedural Type1/2; seed1 offset0 thickness10; Outer4 neutral tuple.",
        "ordering": "Size factor and procedural noise compose source span upstream. Brightness is applied only after inverse-sample RGB normalization as f32(normalized*gain), then RGB-only min(1); alpha is unchanged.",
        "boundary": "Only the enumerated fixed-fixture tuples are admitted. Gain1 remains covered by the base Size x Noise matrix. Rotation Type1 retains the pre-existing non-consumed source-scalar tail ULP boundary from the gain1 matrix; actual-AEX upstream bytes are nevertheless gain-invariant and all consumed downstream planes/output are exact. Other gains, masks, geometry, values, Type3, seed/offset/thickness and AE-host output are unproven.",
        "cases": rows,
    }, indent=2, sort_keys=True) + "\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--capture":
        mode, depth, sv, nv, nt, gain = sys.argv[2:8]
        Path(sys.argv[8]).write_bytes(pickle.dumps(actual(
            (mode, int(depth), float(sv), float(nv), int(nt), float(gain)))))
        raise SystemExit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.full))
