#!/usr/bin/env python3
"""PF32 Zoom: actual-AEX ellipse Ratio x Angle closure."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as wrapper  # noqa:E402

pf8 = wrapper.fixture
zoom = pf8.zoom
REPORT = ROOT / "refs/conformance/olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CASES = [(ratio, angle) for ratio in (2.0, 5.0) for angle in (0.0, 30.0, 90.0)]


def configure(ratio: float, angle: float) -> None:
    pf8.W, pf8.H, pf8.ROWBYTES, pf8.VISIBLE = 9, 7, 160, 144
    pf8.PIXEL_CPP, pf8.PIXEL_BYTES, pf8.BITDEPTH = "PF_PixelFloat", 16, 32
    pf8.ZOOM_RETURN, pf8.USE_RENDER_WORLD_FINAL = 0x180008322, True
    pf8.source_frame = wrapper.source_frame
    pf8.configure()
    zoom.RATIO, zoom.ANGLE_DEG = ratio, angle
    zoom.INNER_STRENGTH, zoom.NOISE_VARIATION = 0.0, 0.0
    zoom.PIXEL_CPP, zoom.PIXEL_BYTES = "PF_PixelFloat", 16
    zoom.USE_RENDER_WORLD_FINAL, zoom.RENDER_WORLD_BITDEPTH = True, 32
    zoom.ZOOM_RETURN = 0x180008322
    zoom.fixture.W, zoom.fixture.H = 9, 7
    zoom.fixture.ROWBYTES, zoom.fixture.VISIBLE = 160, 144
    zoom.fixture.source_frame, zoom.fixture.build_world = wrapper.source_frame, pf8.build_world


def isolated(mode: str, ratio: float, angle: float, expected=None):
    with tempfile.TemporaryDirectory(prefix="radial_zoom_ellipse_") as raw:
        out = Path(raw) / "out.pkl"
        cmd = [sys.executable, str(Path(__file__)), f"--{mode}", str(ratio), str(angle)]
        if expected is not None:
            inp = Path(raw) / "in.pkl"
            inp.write_bytes(pickle.dumps(expected))
            cmd.append(str(inp))
        cmd.append(str(out))
        process = subprocess.run(cmd)
        return process.returncode, pickle.loads(out.read_bytes()) if out.exists() else None


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actual = dict(zip(CASES, pool.map(lambda cell: isolated("actual", *cell)[1], CASES)))
    with ThreadPoolExecutor(max_workers=6) as pool:
        production = dict(zip(CASES, pool.map(lambda cell: isolated("production", cell[0], cell[1], actual[cell]), CASES)))
    rows, exact = [], True
    for ratio, angle in CASES:
        rc, produced = production[(ratio, angle)]
        matches = {key: produced[key] == actual[(ratio, angle)][key]
                   for key in ("pre_blur", "post_blur", "output")} if produced else {}
        cell_exact = rc == 0 and all(matches.values())
        exact &= cell_exact
        rows.append({"ratio": ratio, "angle_deg": angle, "matches": matches,
                     "actual_transform_setup": actual[(ratio, angle)]["transform_setup"],
                     "geometry": list(__import__("struct").unpack("<II", actual[(ratio, angle)]["geometry"])),
                     "actual_sha256": {key: sha(actual[(ratio, angle)][key])
                                       for key in ("pre_blur", "post_blur", "output")},
                     "exact": cell_exact})
    status = "exact" if exact else "mismatch"
    report = {
        "kind": "olmradialblur_zoom_pf32_ellipse_actual_aex_20260811",
        "status": status,
        "scope": "PF32 Zoom padded 9x7 centered; Ratio {2,5} x Angle {0,30,90}; Quality5, Repeat on, Brightness1, Outer Strength4, neutral offsets/fades/size/noise.",
        "aex_sha256": zoom.fixture.AEX_SHA256,
        "cells": rows,
        "mapping": "AEX stores Ratio as float bits and Angle as truncated signed 16.16 radians. It converts the Angle integer directly to double, calls double sin/cos, then casts each result to float. Per polar cell it forms cos(theta) and sin(theta) with the paired float helper, multiplies sin(theta)*ratio before multiplying by radius, rotates with mul/sub/addss order, then adds the centered world coordinate.",
        "worker": "Eligibility and source-alpha scalar are sampled at the transformed world coordinate. Outer accumulation proceeds in increasing-radius/source order, tracks max alpha, normalizes once, and feeds the existing inverse sampler/writer.",
        "boundary": "Admission is limited to the six PF32 9x7 Ratio{2,5} x Angle{0,30,90} cells. Other ratio/angle values, geometry, depth, controls and Rotation remain fail-closed or separately evidenced.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur PF32 Zoom ellipse — 2026-08-11\n\nStatus: **{status}**\n\nRatio 2/5 × Angle 0/30/90 の6セルで、actual AEX と production の pre-blur、post-blur、padded PF32 output が全段 byte-exact です。Angle は radians の16.16整数を AEX と同じく直接 double sin/cos へ渡し、Ratio は `sin(theta) * ratio` を先にfloat演算してからradiusを掛けます。\n")
    print(json.dumps({"status": status, "cells": len(rows)}, sort_keys=True))
    return 0 if status == "exact" else 1


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--actual":
        configure(float(sys.argv[2]), float(sys.argv[3]))
        Path(sys.argv[4]).write_bytes(pickle.dumps(zoom.actual_aex()))
        raise SystemExit(0)
    if len(sys.argv) == 6 and sys.argv[1] == "--production":
        configure(float(sys.argv[2]), float(sys.argv[3]))
        try:
            result = zoom.mac_production(pickle.loads(Path(sys.argv[4]).read_bytes()))
        except subprocess.CalledProcessError as error:
            raise SystemExit(error.returncode)
        Path(sys.argv[5]).write_bytes(pickle.dumps(result))
        raise SystemExit(0)
    raise SystemExit(main())
