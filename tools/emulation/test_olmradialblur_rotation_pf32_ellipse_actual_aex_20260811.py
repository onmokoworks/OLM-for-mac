#!/usr/bin/env python3
"""PF32 Rotation ellipse Ratio x Angle actual-AEX closure."""
from __future__ import annotations

import hashlib, json, pickle, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as fixture  # noqa:E402

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CASES = [(ratio, angle) for ratio in (2.0, 5.0) for angle in (0.0, 30.0, 90.0)]
PLANES = ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")


def configure(ratio: float, angle: float) -> None:
    fixture.RATIO, fixture.ANGLE_DEG = ratio, angle


def isolated(mode: str, ratio: float, angle: float, expected=None):
    with tempfile.TemporaryDirectory(prefix="radial_rotation_ellipse_") as raw:
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
    for cell in CASES:
        rc, produced = production[cell]
        matches = {plane: produced[plane] == actual[cell][plane] for plane in PLANES} if produced else {}
        cell_exact = rc == 0 and all(matches.values())
        exact &= cell_exact
        rows.append({"ratio": cell[0], "angle_deg": cell[1], "matches": matches,
                     "actual_sha256": {plane: sha(actual[cell][plane]) for plane in PLANES},
                     "exact": cell_exact})
    status = "exact" if exact else "mismatch"
    report = {
        "kind": "olmradialblur_rotation_pf32_ellipse_actual_aex_20260811",
        "status": status,
        "scope": "PF32 Rotation padded 9x7 centered; Ratio {2,5} x Angle {0,30,90}; Outer Strength4 and neutral remaining controls.",
        "aex_sha256": fixture.AEX_SHA256,
        "planes": list(PLANES),
        "cells": rows,
        "transform": "Forward setup shares Zoom's radians signed16.16 truncation and integer-to-double sin/cos. Rotation has a distinct ellipse multiply order: (radius*ratio)*sin(theta), while Zoom uses radius*(sin(theta)*ratio). Rotation scatter/gather and inverse coordinates are independently compared here.",
        "boundary": "Admission is limited to cells whose polar, source scalar, accumulation, max alpha, final RGBA, inverse coordinates and padded PF32 output all match actual AEX byte-for-byte.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur PF32 Rotation ellipse — 2026-08-11\n\nStatus: **{status}**\n\nRatio 2/5 × Angle 0/30/90 の6セルについて、forward polarからRotation worker、inverse coordinates、padded PF32 outputまでactual AEXとbyte-exactです。Angle setupはZoomと共通ですが、Rotationのellipseは `(radius * ratio) * sin(theta)` のfloat順です。\n")
    print(json.dumps({"status": status, "cells": len(rows)}, sort_keys=True))
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--actual":
        configure(float(sys.argv[2]), float(sys.argv[3]))
        Path(sys.argv[4]).write_bytes(pickle.dumps(fixture.actual_aex()))
        raise SystemExit(0)
    if len(sys.argv) == 6 and sys.argv[1] == "--production":
        configure(float(sys.argv[2]), float(sys.argv[3]))
        try:
            result = fixture.mac_production(pickle.loads(Path(sys.argv[4]).read_bytes()))
        except subprocess.CalledProcessError as error:
            raise SystemExit(error.returncode)
        Path(sys.argv[5]).write_bytes(pickle.dumps(result))
        raise SystemExit(0)
    raise SystemExit(main())
