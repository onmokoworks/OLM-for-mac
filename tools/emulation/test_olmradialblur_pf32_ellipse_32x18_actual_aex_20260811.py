#!/usr/bin/env python3
"""PF32 32x18 Zoom/Rotation ellipse geometry closure."""
from __future__ import annotations

import hashlib, importlib, json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810 as zoom32  # noqa:E402
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as rotation  # noqa:E402

REPORT = ROOT / "refs/conformance/olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CASES = [(ratio, angle) for ratio in (2.0, 5.0) for angle in (0.0, 30.0, 90.0)]
ZOOM_PLANES = ("pre_blur", "post_blur", "output")
ROTATION_PLANES = ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")


def configure_zoom(ratio: float, angle: float) -> None:
    zoom32.configure(0.0)
    zoom32.zoom.RATIO, zoom32.zoom.ANGLE_DEG = ratio, angle


def configure_rotation(ratio: float, angle: float) -> None:
    # The legacy Zoom fixture monkey-patches the shared Rotation module while
    # importing; restore its native entry points before configuring this lane.
    importlib.reload(rotation.base)
    importlib.reload(rotation)
    rotation.W, rotation.H, rotation.ROWBYTES, rotation.VISIBLE = zoom32.W, zoom32.H, zoom32.RB, zoom32.VISIBLE
    rotation.CENTER_X, rotation.CENTER_Y = 16.0, 9.0
    rotation.RATIO, rotation.ANGLE_DEG = ratio, angle
    def rotation_source_frame(seed: bool = False) -> bytes:
        raw = bytearray(zoom32.source_frame(seed))
        for y in range(zoom32.H):
            raw[y * zoom32.RB + zoom32.VISIBLE:(y + 1) * zoom32.RB] = bytes([0xC0 + y]) * (zoom32.RB - zoom32.VISIBLE)
        return bytes(raw)
    rotation.source_frame, rotation.build_world = rotation_source_frame, zoom32.build_world


def isolated(effect: str, mode: str, ratio: float, angle: float, expected=None):
    with tempfile.TemporaryDirectory(prefix=f"radial_{effect}_ellipse32_") as raw:
        out = Path(raw) / "out.pkl"
        cmd = [sys.executable, str(Path(__file__)), f"--{effect}-{mode}", str(ratio), str(angle)]
        if expected is not None:
            inp = Path(raw) / "in.pkl"
            inp.write_bytes(pickle.dumps(expected))
            cmd.append(str(inp))
        cmd.append(str(out))
        process = subprocess.run(cmd)
        return process.returncode, pickle.loads(out.read_bytes()) if out.exists() else None


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compare_effect(effect: str, planes: tuple[str, ...]):
    with ThreadPoolExecutor(max_workers=3) as pool:
        actual = dict(zip(CASES, pool.map(lambda cell: isolated(effect, "actual", *cell)[1], CASES)))
    with ThreadPoolExecutor(max_workers=3) as pool:
        produced = dict(zip(CASES, pool.map(lambda cell: isolated(effect, "production", cell[0], cell[1], actual[cell]), CASES)))
    rows, exact = [], True
    for cell in CASES:
        rc, production = produced[cell]
        matches = {plane: production[plane] == actual[cell][plane] for plane in planes} if production else {}
        cell_exact = rc == 0 and all(matches.values())
        exact &= cell_exact
        rows.append({"ratio": cell[0], "angle_deg": cell[1], "matches": matches,
                     "actual_sha256": {plane: sha(actual[cell][plane]) for plane in planes},
                     "exact": cell_exact})
    return rows, exact


def main() -> int:
    zoom_rows, zoom_exact = compare_effect("zoom", ZOOM_PLANES)
    rotation_rows, rotation_exact = compare_effect("rotation", ROTATION_PLANES)
    exact = zoom_exact and rotation_exact
    status = "exact" if exact else "mismatch"
    report = {
        "kind": "olmradialblur_pf32_ellipse_32x18_actual_aex_20260811",
        "status": status,
        "scope": "PF32 padded 32x18 centered same-shape comp/world; Zoom and Rotation; Ratio {2,5} x Angle {0,30,90}; Outer Strength4 neutral tuple.",
        "geometry": {"width": 32, "height": 18, "rowbytes": 528, "center": [16.0, 9.0]},
        "zoom": {"planes": list(ZOOM_PLANES), "cells": zoom_rows, "exact": zoom_exact},
        "rotation": {"planes": list(ROTATION_PLANES), "cells": rotation_rows, "exact": rotation_exact},
        "rule": "The 9x7 ellipse transform and its distinct Zoom/Rotation float multiply orders are geometry-independent for centered, positive, same-shape PF32 worlds with valid rowbytes and comp dimensions equal to the world.",
        "boundary": "PF8/PF16, off-center or comp/world-scaled geometry, nonpositive/mismatched worlds, other ratios/angles and other parameter families remain outside this admission.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur PF32 ellipse 32×18 — 2026-08-11\n\nStatus: **{status}**\n\nZoomとRotationのRatio 2/5 × Angle 0/30/90を、center `(16,9)`、rowbytes 528の32×18 worldで比較し、全plane byte-exactを確認しました。9×7で確定した各モード固有のfloat演算順を、centered same-shape PF32 geometryへ一般化します。\n")
    print(json.dumps({"status": status, "zoom": zoom_exact, "rotation": rotation_exact}, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if len(sys.argv) == 5 and action in ("--zoom-actual", "--rotation-actual"):
        ratio, angle = float(sys.argv[2]), float(sys.argv[3])
        if action == "--zoom-actual":
            configure_zoom(ratio, angle); result = zoom32.zoom.actual_aex()
        else:
            configure_rotation(ratio, angle); result = rotation.actual_aex()
        Path(sys.argv[4]).write_bytes(pickle.dumps(result)); raise SystemExit(0)
    if len(sys.argv) == 6 and action in ("--zoom-production", "--rotation-production"):
        ratio, angle = float(sys.argv[2]), float(sys.argv[3]); expected = pickle.loads(Path(sys.argv[4]).read_bytes())
        if action == "--zoom-production":
            configure_zoom(ratio, angle); result = zoom32.zoom.mac_production(expected)
        else:
            configure_rotation(ratio, angle); result = rotation.mac_production(expected)
        Path(sys.argv[5]).write_bytes(pickle.dumps(result)); raise SystemExit(0)
    raise SystemExit(main())
