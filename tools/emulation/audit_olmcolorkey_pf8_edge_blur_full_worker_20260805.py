#!/usr/bin/env python3
"""Audit bounded PF8 Edge Blur full-worker planes and production SmartRender."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "refs/conformance/olmcolorkey_pf8_full_worker_actual_aex_20260805.json"
MAC = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT = ROOT / "refs/conformance/olmcolorkey_pf8_edge_blur_full_worker_20260805.json"
MD = OUT.with_suffix(".md")
def main() -> int:
    aex=json.loads(AEX.read_text()); run=subprocess.run(["python3",str(MAC)],cwd=ROOT,text=True,capture_output=True,timeout=120)
    assert run.returncode==0, run.stderr or run.stdout; mac=json.loads(run.stdout)
    expected={"single":([0.5]+[0.0]*11,[128]+[255]*11),"line":([0.5]*4+[0.0]*8,[128]*4+[255]*8),"all":([1.0]*12,[0]*12)}
    rows={}
    for shape,(plane,alpha) in expected.items():
        ac=next(x for x in aex["cases"] if x["case"]==f"enabled_black_key_edge_blur_1_{shape}")
        mc=next(x for x in mac["cases"] if x["case"]==f"enabled_black_key_edge_blur_1_{shape}_pf8")
        got_alpha=[bytes.fromhex(row)[x*4] for row in ac["captures"]["output_active_rows_hex"] for x in range(4)]
        got_plane=ac["execution"]["temporary_handles"][0]["f32"]
        exact=got_plane==plane and got_alpha==alpha and mc["numerical_contract"]["alpha8"]==alpha and ac["acceptance_gates"]["output_padding_preserved"] and mc["output_padding_preserved"]
        rows[shape]={"exact":exact,"actual_aex_direction_plane":got_plane,"actual_aex_alpha8":got_alpha,"production_alpha8":mc["numerical_contract"]["alpha8"]}
    passed=all(x["exact"] for x in rows.values())
    report={"kind":"olmcolorkey_pf8_edge_blur_full_worker_20260805","schema_version":1,"status":"pass" if passed else "mismatch","cases":rows,"scope":"4x3 PF8 single/line/all masks, Edge Blur 1.0, internal plane, final bytes, and padding only","quantization":"PF8 native rounds half-up; not derived by quantizing PF16/PF32 evidence","shim_boundary":"parameter materialization plus bounded PF World/Handle/Iterate8 and worker-prepare shims"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); MD.write_text(f"# OLMColorKey PF8 Edge Blur full worker\n\nStatus: **{report['status']}**\n\n{report['scope']}\n")
    print(json.dumps({"status":report["status"],"json":str(OUT),"md":str(MD)},sort_keys=True)); return 0 if passed else 3
if __name__=="__main__": raise SystemExit(main())
