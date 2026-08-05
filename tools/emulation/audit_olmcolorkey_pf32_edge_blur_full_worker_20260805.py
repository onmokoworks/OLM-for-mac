#!/usr/bin/env python3
"""Audit bounded PF32 Edge Blur full-worker planes and production SmartRender."""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "refs/conformance/olmcolorkey_pf32_full_worker_actual_aex_20260805.json"
MAC = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT = ROOT / "refs/conformance/olmcolorkey_pf32_edge_blur_full_worker_20260805.json"
MD = OUT.with_suffix(".md")


def active_alpha(case: dict) -> list[float]:
    return [struct.unpack("<f", bytes.fromhex(row)[x * 16:x * 16 + 4])[0]
            for row in case["captures"]["output_active_rows_hex"] for x in range(4)]


def main() -> int:
    aex = json.loads(AEX.read_text())
    run = subprocess.run(["python3", str(MAC)], cwd=ROOT, text=True,
                         capture_output=True, timeout=120)
    assert run.returncode == 0, run.stderr or run.stdout
    mac = json.loads(run.stdout)
    expected = {
        "single": ([0.5] + [0.0] * 11, [0.5] + [1.0] * 11),
        "line": ([0.5] * 4 + [0.0] * 8, [0.5] * 4 + [1.0] * 8),
        "all": ([1.0] * 12, [0.0] * 12),
    }
    rows = {}
    for shape, (plane, alpha) in expected.items():
        ac = next(row for row in aex["cases"] if row["case"] == f"enabled_black_key_edge_blur_1_{shape}")
        mc = next(row for row in mac["cases"] if row["case"] == f"enabled_black_key_edge_blur_1_{shape}_pf32")
        aex_plane = ac["execution"]["temporary_handles"][0]["f32"]
        aex_alpha = active_alpha(ac)
        exact = (aex_plane == plane and aex_alpha == alpha
                 and mc["numerical_contract"]["alpha32"] == alpha
                 and ac["acceptance_gates"]["output_padding_preserved"]
                 and mc["output_padding_preserved"])
        rows[shape] = {"exact": exact, "actual_aex_direction_plane": aex_plane,
                       "actual_aex_alpha": aex_alpha, "production_alpha": mc["numerical_contract"]["alpha32"]}
    passed = all(row["exact"] for row in rows.values())
    report = {"kind": "olmcolorkey_pf32_edge_blur_full_worker_20260805", "schema_version": 1,
              "status": "pass" if passed else "mismatch", "cases": rows,
              "scope": "4x3 PF32 single/line/all masks, Edge Blur 1.0, internal direction plane, active pixels, and padding; no general 32bpc claim",
              "shim_boundary": "parameter materialization plus PF World/Handle/IterateFloat and worker-prepare are bounded host shims"}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text("# OLMColorKey PF32 Edge Blur full worker\n\n"
                  f"Status: **{report['status']}**\n\nScope: {report['scope']}\n")
    print(json.dumps({"status": report["status"], "json": str(OUT), "md": str(MD)}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
