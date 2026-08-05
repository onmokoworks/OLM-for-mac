#!/usr/bin/env python3
"""Audit the bounded noninteger Edge Blur 1.5 case at all three depths."""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAC = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT = ROOT / "refs/conformance/olmcolorkey_edge_blur_1_5_all_depths_20260805.json"
MD = OUT.with_suffix(".md")

EXPECTED = {
    "PF8": ([0.0, 255.0, 510.0, 765.0, 255.0, 510.0, 765.0, 1020.0, 510.0, 765.0, 1020.0, 1275.0],
            [0.5] + [0.0] * 11, [128] + [255] * 11),
    "PF16": ([0.0, 255.0, 510.0, 765.0, 255.0, 510.0, 765.0, 1020.0, 510.0, 765.0, 1020.0, 1275.0],
             [0.5] + [0.0] * 11, [16384] + [32768] * 11),
    "PF32": ([0.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0, 2.0, 3.0, 4.0, 5.0],
             [0.5, -0.023598790168762207, 0.0, 0.0, -0.023598790168762207] + [0.0] * 7,
             [0.5, 1.0235987901687622, 1.0, 1.0, 1.0235987901687622] + [1.0] * 7),
}


def alpha(case: dict, fmt: str) -> list[int | float]:
    size, code = {"PF8": (4, "B"), "PF16": (8, "H"), "PF32": (16, "f")}[fmt]
    return [struct.unpack_from("<" + code, bytes.fromhex(row), x * size)[0]
            for row in case["captures"]["output_active_rows_hex"] for x in range(4)]


def main() -> int:
    run = subprocess.run(["python3", str(MAC)], cwd=ROOT, text=True,
                         capture_output=True, timeout=120)
    assert run.returncode == 0, run.stderr or run.stdout
    production = json.loads(run.stdout)
    cases = {}
    for fmt, (expected_seed, expected_direction, expected_alpha) in EXPECTED.items():
        aex = json.loads((ROOT / f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json").read_text())
        native = next(row for row in aex["cases"] if row["case"] == "enabled_black_key_edge_blur_1.5_single")
        mac = next(row for row in production["cases"] if row["case"] == f"enabled_black_key_edge_blur_1.5_single_{fmt.lower()}")
        seed = native["execution"]["temporary_worlds"][-1]["first_channel_f32"]
        direction = native["execution"]["temporary_handles"][0]["f32"]
        native_alpha = alpha(native, fmt)
        mac_alpha = mac["numerical_contract"]["alpha" + fmt[2:]]
        gates = {
            "actual_seed_plane_exact": seed == expected_seed,
            "actual_direction_plane_exact": direction == expected_direction,
            "actual_final_alpha_exact": native_alpha == expected_alpha,
            "production_direction_plane_exact": mac["direction_plane"] == expected_direction,
            "production_final_alpha_exact": mac_alpha == expected_alpha,
            "actual_padding_preserved": native["acceptance_gates"]["output_padding_preserved"],
            "production_padding_preserved": mac["output_padding_preserved"],
        }
        cases[fmt] = {
            "status": "pass" if all(gates.values()) else "mismatch",
            "gates": gates,
            "actual_seed_plane": seed,
            "actual_direction_plane": direction,
            "actual_alpha": native_alpha,
            "production_alpha": mac_alpha,
            "distance_metric_units": mac["numerical_contract"]["distance_metric_units"],
        }
    passed = all(case["status"] == "pass" for case in cases.values())
    report = {
        "kind": "olmcolorkey_edge_blur_1_5_all_depths_20260805",
        "schema_version": 1,
        "status": "pass" if passed else "mismatch",
        "cases": cases,
        "scope": "4x3 single black key, noninteger Edge Blur 1.5, PF8/PF16/PF32 actual full worker through production SmartRender; internal metric/direction planes, exact final alpha, and row padding. No interpolation, general amount, or AE-host claim.",
        "interpretation": "PF8/PF16 use independently observed 255-per-pixel metric seeds. PF32 exposes a negative distance-1 direction shell and final alpha above one; neither value is inferred from Blur 1.0 or 2.0.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text("# OLMColorKey Edge Blur 1.5 — all depths\n\n"
                  f"Status: **{report['status']}**\n\nScope: {report['scope']}\n\n"
                  f"{report['interpretation']}\n")
    print(json.dumps({"status": report["status"], "json": str(OUT), "md": str(MD)}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
