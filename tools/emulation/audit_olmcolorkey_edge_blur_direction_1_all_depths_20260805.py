#!/usr/bin/env python3
"""Audit public Edge Blur direction 1 at amount 2.0 for all depths."""
from __future__ import annotations
import json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; MAC=ROOT/"tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
OUT=ROOT/"refs/conformance/olmcolorkey_edge_blur_direction_1_all_depths_20260805.json"; MD=OUT.with_suffix(".md")
ISEED=[0.,255.,510.,765.,255.,510.,765.,1020.,510.,765.,1020.,1275.]; FSEED=[0.,1.,2.,3.,1.,2.,3.,4.,2.,3.,4.,5.]
DIRECTION=[-0.2853981554508209]+[0.]*11
EXPECTED={"PF8":(ISEED,[71]+[255]*11),"PF16":(ISEED,[42119]+[32768]*11),"PF32":(FSEED,[1.2853981256484985]+[1.]*11)}
def alpha(c,f):
 s,k={"PF8":(4,"B"),"PF16":(8,"H"),"PF32":(16,"f")}[f]; return [struct.unpack_from("<"+k,bytes.fromhex(r),x*s)[0] for r in c["captures"]["output_active_rows_hex"] for x in range(4)]
def main():
 run=subprocess.run(["python3",str(MAC)],cwd=ROOT,text=True,capture_output=True,timeout=120); assert run.returncode==0,run.stderr or run.stdout
 prod=json.loads(run.stdout); results={}
 for fmt,(eseed,ealpha) in EXPECTED.items():
  aex=json.loads((ROOT/f"refs/conformance/olmcolorkey_{fmt.lower()}_full_worker_actual_aex_20260805.json").read_text()); n=next(c for c in aex["cases"] if c["case"]=="enabled_black_key_edge_blur_2_single_direction_1"); m=next(c for c in prod["cases"] if c["case"]==f"enabled_black_key_edge_blur_2_single_direction_1_{fmt.lower()}")
  seed=n["execution"]["temporary_worlds"][-1]["first_channel_f32"]; direction=n["execution"]["temporary_handles"][0]["f32"]; aa=alpha(n,fmt); pa=m["numerical_contract"]["alpha"+fmt[2:]]
  g={"public_direction_parameter_exact":n["parameter_record"]["edge_blur_direction"]==1,"actual_seed_plane_exact":seed==eseed,"actual_direction_plane_exact":direction==DIRECTION,"actual_final_alpha_exact":aa==ealpha,"production_direction_plane_exact":m["direction_plane"]==DIRECTION,"production_final_alpha_exact":pa==ealpha,"actual_padding_preserved":n["acceptance_gates"]["output_padding_preserved"],"production_padding_preserved":m["output_padding_preserved"]}
  results[fmt]={"status":"pass" if all(g.values()) else "mismatch","gates":g,"actual_seed_plane":seed,"actual_direction_plane":direction,"actual_alpha":aa,"production_alpha":pa,"actual_aex_sha256":n["aex"]["sha256"],"integer_alpha_behavior":m["numerical_contract"]["integer_alpha_behavior"]}
 passed=all(c["status"]=="pass" for c in results.values()); report={"kind":"olmcolorkey_edge_blur_direction_1_all_depths_20260805","schema_version":1,"status":"pass" if passed else "mismatch","cases":results,"scope":"4x3 single black key, Edge Blur amount 2.0 and public direction 1, PF8/PF16/PF32 actual full worker through production SmartRender; exact internal distance/direction planes, final alpha, padding, and AEX hash. No other direction/amount or AE-host claim.","interpretation":"Direction 1 exposes a negative boundary plane and an unbounded final multiplier. PF8 wraps after integer cast, PF16 exceeds its nominal 32768 channel maximum, and PF32 remains above one."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); MD.write_text(f"# OLMColorKey Edge Blur direction 1\n\nStatus: **{report['status']}**\n\nScope: {report['scope']}\n\n{report['interpretation']}\n"); print(json.dumps({"status":report["status"],"json":str(OUT),"md":str(MD)},sort_keys=True)); return 0 if passed else 3
if __name__=="__main__": raise SystemExit(main())
