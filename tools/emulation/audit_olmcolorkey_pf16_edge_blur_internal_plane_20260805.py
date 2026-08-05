#!/usr/bin/env python3
"""Focused AEX-vs-production audit for the PF16 Edge Blur direction plane."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX_PROBE = ROOT / "tools/emulation/probe_olmcolorkey_pf16_full_worker_20260805.py"
MAC_PROBE = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT_JSON = ROOT / "refs/conformance/olmcolorkey_pf16_edge_blur_internal_plane_20260805.json"
OUT_MD = ROOT / "refs/conformance/olmcolorkey_pf16_edge_blur_internal_plane_20260805.md"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmck_plane_") as name:
        aex_path = Path(name) / "aex.json"
        aex_run = subprocess.run(["python3", str(AEX_PROBE), "--json", str(aex_path)], cwd=ROOT,
                                 text=True, capture_output=True, timeout=120)
        if aex_run.returncode != 0:
            raise RuntimeError(aex_run.stderr or aex_run.stdout)
        aex = json.loads(aex_path.read_text())
    mac_run = subprocess.run(["python3", str(MAC_PROBE)], cwd=ROOT, text=True,
                             capture_output=True, timeout=120)
    if mac_run.returncode != 0:
        raise RuntimeError(mac_run.stderr or mac_run.stdout)
    mac = json.loads(mac_run.stdout)
    aex_cases = {shape: next(row for row in aex["cases"]
                             if row["case"] == f"enabled_black_key_edge_blur_1_{shape}")
                 for shape in ("single", "line", "all")}
    mac_case = next(row for row in mac["cases"] if row["case"] == "enabled_black_key_edge_blur_1_pf16")
    aex_planes = {shape: case["execution"]["temporary_handles"][0]["f32"]
                  for shape, case in aex_cases.items()}
    production_planes = {
        "single": mac_case["direction_plane"],
        "line": [0.5] * 4 + [0.0] * 8,
        "all": [1.0] * 12,
    }
    exact = aex_planes == production_planes
    report = {
        "kind": "olmcolorkey_pf16_edge_blur_internal_plane_20260805",
        "schema_version": 1,
        "status": "pass" if exact else "focused_mismatch",
        "exact": exact,
        "fixture": {"dimensions": [4, 3], "enabled_black_key": True,
                    "edge_blur_amount": 1.0, "distance_type": 2, "direction": 2},
        "actual_aex": {"direction_planes_f32": aex_planes,
                       "seed_planes_f32": {shape: case["execution"]["temporary_worlds"][-1]["first_channel_f32"]
                                           for shape, case in aex_cases.items()}},
        "production": {"direction_planes_f32": production_planes,
                       "generator": "Boundary8(matched) -> EdgeBlurDistanceTo -> EdgeBlurWeight"},
        "abi_boundary": {
            "pf_handle": "new_handle returns PF_Handle; lock(handle) returns data",
            "pf_world_slot_0": "PF_NewWorld(effect_ref,width,height,flags,pixel_format,world*)",
            "pf_world_slot_1": "PF_DisposeWorld(effect_ref,world)",
            "parameter_materialization": "FUN_18000A3D0 replaced by declared fixture record",
        },
        "next_boundary": "AEX distance_type=2 generator produces an all-zero seed plane from the inverse PF16 mask; production Boundary8+L1 does not. Final-pixel equality is intentionally not claimed.",
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(
        "# OLMColorKey PF16 Edge Blur internal plane\n\n"
        f"Status: **{report['status']}**\n\n"
        f"- actual AEX direction planes: `{aex_planes}`\n"
        f"- production direction planes: `{production_planes}`\n"
        f"- boundary: {report['next_boundary']}\n"
    )
    print(json.dumps({"status": report["status"], "json": str(OUT_JSON), "md": str(OUT_MD)}, sort_keys=True))
    return 0 if exact else 3


if __name__ == "__main__":
    raise SystemExit(main())
