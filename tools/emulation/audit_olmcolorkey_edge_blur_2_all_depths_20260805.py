#!/usr/bin/env python3
"""Audit the bounded Edge Blur 2.0 single-key case at all three depths."""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAC = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT = ROOT / "refs/conformance/olmcolorkey_edge_blur_2_all_depths_20260805.json"
MD = OUT.with_suffix(".md")

EXPECTED = {
    "PF8": {
        "seed": [0.0, 255.0, 510.0, 765.0, 255.0, 510.0, 765.0, 1020.0, 510.0, 765.0, 1020.0, 1275.0],
        "direction": [0.5] + [0.0] * 11,
        "alpha": [128] + [255] * 11,
    },
    "PF16": {
        "seed": [0.0, 255.0, 510.0, 765.0, 255.0, 510.0, 765.0, 1020.0, 510.0, 765.0, 1020.0, 1275.0],
        "direction": [0.5] + [0.0] * 11,
        "alpha": [16384] + [32768] * 11,
    },
    "PF32": {
        "seed": [0.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 5.0],
        "direction": [0.5, 0.10730090737342834, 0.0, 0.0, 0.10730090737342834] + [0.0] * 7,
        "alpha": [0.5, 0.892699122428894, 1.0, 1.0, 0.892699122428894] + [1.0] * 7,
    },
}


def actual_alpha(case: dict, pixel_format: str) -> list[int | float]:
    size, code = {"PF8": (4, "B"), "PF16": (8, "H"), "PF32": (16, "f")}[pixel_format]
    return [struct.unpack_from("<" + code, bytes.fromhex(row), x * size)[0]
            for row in case["captures"]["output_active_rows_hex"] for x in range(4)]


def main() -> int:
    run = subprocess.run(["python3", str(MAC)], cwd=ROOT, text=True,
                         capture_output=True, timeout=120)
    assert run.returncode == 0, run.stderr or run.stdout
    mac = json.loads(run.stdout)
    results = {}
    for pixel_format, expected in EXPECTED.items():
        path = ROOT / f"refs/conformance/olmcolorkey_{pixel_format.lower()}_full_worker_actual_aex_20260805.json"
        aex = json.loads(path.read_text())
        case = next(row for row in aex["cases"] if row["case"] == "enabled_black_key_edge_blur_2_single")
        production = next(row for row in mac["cases"]
                          if row["case"] == f"enabled_black_key_edge_blur_2_single_{pixel_format.lower()}")
        seed = case["execution"]["temporary_worlds"][-1]["first_channel_f32"]
        direction = case["execution"]["temporary_handles"][0]["f32"]
        alpha = actual_alpha(case, pixel_format)
        production_alpha = production["numerical_contract"]["alpha" + pixel_format[2:]]
        gates = {
            "actual_seed_plane_exact": seed == expected["seed"],
            "actual_direction_plane_exact": direction == expected["direction"],
            "actual_final_alpha_exact": alpha == expected["alpha"],
            "production_final_alpha_exact": production_alpha == expected["alpha"],
            "actual_padding_preserved": case["acceptance_gates"]["output_padding_preserved"],
            "production_padding_preserved": production["output_padding_preserved"],
            "production_direction_plane_exact": production["direction_plane"] == expected["direction"],
        }
        results[pixel_format] = {
            "status": "pass" if all(gates.values()) else "mismatch",
            "gates": gates,
            "actual_seed_plane": seed,
            "actual_direction_plane": direction,
            "actual_alpha": alpha,
            "production_alpha": production_alpha,
            "distance_metric_units": production["numerical_contract"]["distance_metric_units"],
        }
    passed = all(row["status"] == "pass" for row in results.values())
    report = {
        "kind": "olmcolorkey_edge_blur_2_all_depths_20260805",
        "schema_version": 1,
        "status": "pass" if passed else "mismatch",
        "cases": results,
        "scope": "4x3 single black key, Edge Blur 2.0, PF8/PF16/PF32 actual full worker through production SmartRender; internal metric/direction planes, exact final alpha, and row padding. No general amount or AE-host claim.",
        "interpretation": "PF8/PF16 independently retain the Blur 1.0 final quantization because native integer metric seeds advance by 255 per pixel; PF32 uses pixel units and exposes the nontrivial distance-1 shell.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text("# OLMColorKey Edge Blur 2.0 — all depths\n\n"
                  f"Status: **{report['status']}**\n\nScope: {report['scope']}\n\n"
                  f"{report['interpretation']}\n")
    print(json.dumps({"status": report["status"], "json": str(OUT), "md": str(MD)}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
