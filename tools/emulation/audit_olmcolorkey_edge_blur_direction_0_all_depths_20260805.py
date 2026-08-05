#!/usr/bin/env python3
"""Bounded actual-AEX -> production audit for Edge Blur direction 0."""
import hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "refs/conformance/olmcolorkey_edge_blur_direction_0_all_depths_20260805.json"
EXPECTED = {"PF8": ([1.0]+[0.0]*11,[0]+[255]*11), "PF16": ([1.0]+[0.0]*11,[0]+[32768]*11), "PF32": ([1.0,.4999999701976776,0.0,0.0,.4999999701976776]+[0.0]*7,[0.0,.5,1.0,1.0,.5]+[1.0]*7)}
def main():
    run=subprocess.run(["python3",str(ROOT/"tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py")],cwd=ROOT,capture_output=True,text=True)
    prod=json.loads(run.stdout) if run.returncode==0 else {}; rows=[]; passed=run.returncode==0
    for fmt,(plane,alpha) in EXPECTED.items():
        cases=json.loads((ROOT/f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json").read_text())["cases"]
        actual=next(c for c in cases if c["case"]=="enabled_black_key_edge_blur_2_single_direction_0")
        row=next((c for c in prod.get("cases",[]) if c["case"]==f"enabled_black_key_edge_blur_2_single_direction_0_{fmt.lower()}"),{})
        events=[e for e in actual["execution"]["events"] if "output_alpha" in e]; contract=row.get("numerical_contract",{}); pa=contract.get("alpha8",contract.get("alpha16",contract.get("alpha32")))
        gates={"actual_direction_is_0":actual["parameter_record"]["edge_blur_direction"]==0,"actual_amount_is_2":actual["parameter_record"]["edge_blur_amount"]==2.0,"actual_direction_plane_exact":actual["execution"]["temporary_handles"][0]["f32"]==plane,"actual_final_alpha_exact":events[-1]["output_alpha"]==alpha,"production_direction_plane_exact":row.get("direction_plane")==plane,"production_final_alpha_exact":pa==alpha,"production_padding_preserved":row.get("input_padding_preserved") is True and row.get("output_padding_preserved") is True}
        passed &= all(gates.values()); rows.append({"pixel_format":fmt,"actual_aex_sha256":actual["aex"]["sha256"],"gates":gates})
    src=ROOT/"mac/OLMColorKey/OLMColorKey.cpp"; report={"status":"pass" if passed else "fail","scope":"4x3 single black key, Edge Blur amount 2.0, direction 0, PF8/PF16/PF32","claim_boundary":"Bounded direction-0 actual full-worker to production source-adapter proof only; no equivalence to directions 3/4, other amount, shape, or AE-host claim.","production_source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"cases":rows}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); print(json.dumps({"status":report["status"],"json":str(OUT)})); return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
