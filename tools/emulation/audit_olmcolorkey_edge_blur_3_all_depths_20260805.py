#!/usr/bin/env python3
"""Audit independently captured Edge Blur 3.0 at all depths."""

from __future__ import annotations
import json, struct, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAC = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT = ROOT / "refs/conformance/olmcolorkey_edge_blur_3_all_depths_20260805.json"
MD = OUT.with_suffix(".md")
ISEED = [0.,255.,510.,765.,255.,510.,765.,1020.,510.,765.,1020.,1275.]
FSEED = [0.,1.,2.,3.,1.,2.,3.,4.,2.,3.,4.,5.]
IDIR = [0.5] + [0.] * 11
FDIR = [0.5,0.2382006049156189,-0.023598790168762207,0.,0.2382006049156189,
        -0.023598790168762207,0.,0.,-0.023598790168762207,0.,0.,0.]
EXPECTED = {
    "PF8": (ISEED, IDIR, [128] + [255] * 11),
    "PF16": (ISEED, IDIR, [16384] + [32768] * 11),
    "PF32": (FSEED, FDIR, [0.5,0.7617993950843811,1.0235987901687622,1.,
                            0.7617993950843811,1.0235987901687622,1.,1.,
                            1.0235987901687622,1.,1.,1.]),
}

def alpha(case: dict, fmt: str):
    size, code = {"PF8":(4,"B"),"PF16":(8,"H"),"PF32":(16,"f")}[fmt]
    return [struct.unpack_from("<"+code, bytes.fromhex(row), x*size)[0]
            for row in case["captures"]["output_active_rows_hex"] for x in range(4)]

def main() -> int:
    run = subprocess.run(["python3",str(MAC)],cwd=ROOT,text=True,capture_output=True,timeout=120)
    assert run.returncode == 0, run.stderr or run.stdout
    prod = json.loads(run.stdout); results = {}
    for fmt,(eseed,edir,ealpha) in EXPECTED.items():
        aex = json.loads((ROOT/f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json").read_text())
        native = next(c for c in aex["cases"] if c["case"] == "enabled_black_key_edge_blur_3_single")
        mac = next(c for c in prod["cases"] if c["case"] == f"enabled_black_key_edge_blur_3_single_{fmt.lower()}")
        seed=native["execution"]["temporary_worlds"][-1]["first_channel_f32"]
        direction=native["execution"]["temporary_handles"][0]["f32"]
        aa=alpha(native,fmt); pa=mac["numerical_contract"]["alpha"+fmt[2:]]
        gates={"actual_seed_plane_exact":seed==eseed,"actual_direction_plane_exact":direction==edir,
               "actual_final_alpha_exact":aa==ealpha,"production_direction_plane_exact":mac["direction_plane"]==edir,
               "production_final_alpha_exact":pa==ealpha,
               "actual_padding_preserved":native["acceptance_gates"]["output_padding_preserved"],
               "production_padding_preserved":mac["output_padding_preserved"]}
        results[fmt]={"status":"pass" if all(gates.values()) else "mismatch","gates":gates,
                      "actual_seed_plane":seed,"actual_direction_plane":direction,
                      "actual_alpha":aa,"production_alpha":pa,"actual_aex_sha256":native["aex"]["sha256"],
                      "distance_metric_units":mac["numerical_contract"]["distance_metric_units"]}
    passed=all(c["status"]=="pass" for c in results.values())
    report={"kind":"olmcolorkey_edge_blur_3_all_depths_20260805","schema_version":1,
            "status":"pass" if passed else "mismatch","cases":results,
            "scope":"4x3 single black key, Edge Blur 3.0, PF8/PF16/PF32 actual full worker through production SmartRender; exact internal distance/direction planes, final alpha, padding, and AEX hash. No interpolation, general amount, or AE-host claim.",
            "interpretation":"PF32 has independently observed distance-1 and distance-2 shells; distance 3 is cut off at amount 3.0. Integer depths retain 255-per-pixel metric seeds."}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    MD.write_text(f"# OLMColorKey Edge Blur 3.0 — all depths\n\nStatus: **{report['status']}**\n\nScope: {report['scope']}\n\n{report['interpretation']}\n")
    print(json.dumps({"status":report["status"],"json":str(OUT),"md":str(MD)},sort_keys=True))
    return 0 if passed else 3

if __name__ == "__main__": raise SystemExit(main())
