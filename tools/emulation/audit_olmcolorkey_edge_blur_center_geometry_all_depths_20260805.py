#!/usr/bin/env python3
"""Exact audit for the independent center-key geometry."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"refs/conformance/olmcolorkey_edge_blur_center_geometry_all_depths_20260805.json"
EXPECTED={"PF8":([0.0]*5+[.5]+[0.0]*6,[255]*5+[128]+[255]*6),"PF16":([0.0]*5+[.5]+[0.0]*6,[32768]*5+[16384]+[32768]*6),"PF32":([0.0,.10730090737342834,0.0,0.0,.10730090737342834,.5,.10730090737342834,0.0,0.0,.10730090737342834,0.0,0.0],[1.0,.892699122428894,1.0,1.0,.892699122428894,.5,.892699122428894,1.0,1.0,.892699122428894,1.0,1.0])}
def main():
 r=subprocess.run(["python3",str(ROOT/"tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py")],cwd=ROOT,capture_output=True,text=True); prod=json.loads(r.stdout) if r.returncode==0 else {}; rows=[]; passed=r.returncode==0
 for fmt,(plane,alpha) in EXPECTED.items():
  cases=json.loads((ROOT/f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json").read_text())["cases"]; actual=next(c for c in cases if c["case"]=="enabled_black_key_edge_blur_2_center"); row=next((c for c in prod.get("cases",[]) if c["case"]==f"enabled_black_key_edge_blur_2_center_{fmt.lower()}"),{}); events=[e for e in actual["execution"]["events"] if "output_alpha" in e]; contract=row.get("numerical_contract",{}); pa=contract.get("alpha8",contract.get("alpha16",contract.get("alpha32")))
  gates={"center_coordinate_declared":contract.get("keyed_coordinate")==[1,1],"actual_plane_exact":actual["execution"]["temporary_handles"][0]["f32"]==plane,"actual_alpha_exact":events[-1]["output_alpha"]==alpha,"production_plane_exact":row.get("direction_plane")==plane,"production_alpha_exact":pa==alpha,"padding_preserved":row.get("input_padding_preserved") is True and row.get("output_padding_preserved") is True}; passed &= all(gates.values()); rows.append({"pixel_format":fmt,"gates":gates,"actual_aex_sha256":actual["aex"]["sha256"]})
 src=ROOT/"mac/OLMColorKey/OLMColorKey.cpp"; report={"status":"pass" if passed else "fail","scope":"4x3 key at (1,1), direction 2, amount 2.0, PF8/PF16/PF32","claim_boundary":"Independent center-key geometry only; does not generalize the corner single-key gate or arbitrary geometry.","production_source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"cases":rows}; OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); print(json.dumps({"status":report["status"],"json":str(OUT)})); return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
