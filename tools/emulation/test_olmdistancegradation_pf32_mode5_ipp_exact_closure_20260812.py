#!/usr/bin/env python3
"""Natural/public closure for fixed17x11 PF32 Mode5 IPP exactness."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse, hashlib, json, os, re, struct, subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
AEX=resolve_asset(ROOT/"aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex")
SOURCE=ROOT/"mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
PROBE=ROOT/"tools/emulation/dg_pf32_mode5_ipp_exact_probe_20260812.cpp"
PUBLIC=ROOT/"tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp"
FIELDGEN=ROOT/"core/olmdistancegradation_fieldgen.cpp"
MATRIX=ROOT/"refs/conformance/olmdistancegradation_exported_typed_owner_matrix_20260811.json"
REPORT=ROOT/"refs/conformance/olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.json";DOC=REPORT.with_suffix(".md")
DEFAULT_WORKER=Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker")
AEX_SHA="a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae";WORKER_SHA="46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61"
PRE_SHA="6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c";POST_SHA="7aaab7918d72d64fc2c426c7a52748409294bcab8c473bb5a55cbd4d19e037a6"
LEGACY_SHA="d64cf3a5fe5768c365702a096e6665a9ec306af83a232a5bcd16b5cbb9a0133a";ORDER_SHA="959c754ee24f6e12c5d3fbb77e3497cf815483323077bacb7ccfc16e68ca31ba";ASSEMBLY_SHA="cbb451ab215d7685eecea3021bf88736b6cb9072a7e290c7c3fbcb1f89960995"
OUTPUT_SHA="50934ac830542ca73fee4a11b924b746a0ae93f97f34b0d2868170bc371dd387";INPUT_SHA="683259bea613463bb22679f36a78e6d7b4c26dabdbc90e4da480cf76e9eb626a"
SIX={("linear",False):OUTPUT_SHA,("linear",True):"c21fa76f957ad1a94c0fd14ed28960d676e2dfff13de46e868ff951527e3420f",("sphere",False):"373408c57b6a6e9c5c06920402b8c08755ef6cca4625af326561c3dde38a346d",("sphere",True):"0d3655165718ea5acc787df41ad86fe3d147e6eb76ca34adc2d34a45d07ae5f3",("power",False):"40b5d262cdc0ab372036c9d2774fa9400f74daa7895c75c2222a246b01c485a5",("power",True):"fe715e7973fa79d6043cbe86dcfce3205869fb23ac9d69a8d98b288ab20ad6d7"}
SELECTORS=["SEQUENCE_SETUP","FRAME_SETUP","FRAME_SETDOWN","SMART_PRE_RENDER","SMART_RENDER","SEQUENCE_SETDOWN"]
SUITES=["AEGP Utility Suite v7","PF ColorParamSuite v1","PF Handle Suite v2","PF iterateFloat Suite v1"]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(c,m):
 if not c:raise AssertionError(m)
def ordered(u):return 0x80000000-u if u&0x80000000 else u+0x80000000
def residual(a,b):
 x=struct.unpack("<187I",a);y=struct.unpack("<187I",b);d=[abs(ordered(i)-ordered(j)) for i,j in zip(x,y) if i!=j];return {"different_words":len(d),"max_ulp":max(d,default=0)}
def natural(worker,td):
 image=Image.new("RGBA",(17,11));image.putdata([((x*613+y*1231)%256,(x*997+y*211)%256,(x*1499+y*307)%256,255) if not(4<=x<13 and 2<=y<9) else(0,0,0,0) for y in range(11)for x in range(17)]);src=td/"in.png";out=td/"out.png";image.save(src)
 cmd=[str(worker),"render-trace-png",str(AEX),str(src),str(out),"--pixel-format","argb32f","--watch","rva=0x12c97d3,arg=rcx,deref=16,size=748","--watch","rva=0x12c97d3,arg=rdx,deref=16,size=748","Invert=1","In/Out=1","Inside Threshold=4","Outside Threshold=4","Render Mode=1","Use Background Color=0","Gradation Color=255,28,0,238","BG Color =255,16,160,48","Interpolation Mode=2","Power=2.25","Blur Mode=5","Blur Size=1"]
 r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=30);require(r.returncode==0,r.stderr);t=json.loads(r.stdout);smart=next(x for x in t["execution_traces"]if x["selector"]=="SMART_RENDER");s,d=smart["memory_witnesses"]
 require(s["before"]["sha256"]==s["after"]["sha256"]==PRE_SHA,"input");require(d["before"]["sha256"]==PRE_SHA and d["after"]["sha256"]==POST_SHA,"field")
 subset={"input_png_sha256":sha(src),"pre_field_sha256":PRE_SHA,"post_field_sha256":POST_SHA,"raw_output_sha256":t["raw_pixel_sha256"],"raw_output_bytes":t["raw_pixel_bytes"],"input_immutable":True,"guards_intact":t["guards_intact"],"render_error":t["render_error"],"pixel_format":t["pixel_format"],"width":t["width"],"height":t["height"],"render_mode":t["render_mode"],"selectors":[x["selector"]for x in t["execution_traces"]],"suite_requests":t["suite_requests"],"unsupported_suite_calls":t["unsupported_suite_calls"],"dropped_unsupported_suite_calls":t["dropped_unsupported_suite_calls"],"input_requests":t["input_requests"],"output_request":t["output_request"],"smart_return_value":smart["return_value"],"smart_entry_export":smart["entry_export"],"execution_backend":smart["execution_backend"],"smart_image_sha256":smart["image_sha256"],"smart_truncated":smart["truncated"],"dropped_memory_witnesses":smart["dropped_memory_witnesses"]}
 return subset,bytes.fromhex(d["before"]["hex"]),bytes.fromhex(d["after"]["hex"])
def mechanism(td,before,after):
 pre=td/"pre";pre.write_bytes(before);builds={};counter=None
 for name,flags in (("production_o0",["-O0"]),("adversarial_contract_fast_o3",["-O3","-ffp-contract=fast"])):
  exe=td/name;r=subprocess.run(["clang++","-std=c++17",*flags,"-I",str(ROOT/"tools/emulation/dg_renderbits_real_harness_20260716"),"-I",str(ROOT/"tools/emulation"),str(PROBE),str(FIELDGEN),"-o",str(exe)],text=True,capture_output=True);require(r.returncode==0,r.stderr)
  c,l,o=(td/f"{name}.{x}" for x in("c","l","o"));q=subprocess.run([str(exe),str(pre),str(c),str(l),str(o)]);require(q.returncode==0,"probe");require(c.read_bytes()==after and sha(c)==POST_SHA,name);builds[name]={"canonical_sha256":POST_SHA,"raw_exact":True}
  if name=="production_o0":counter={"superseded_lut_early_spatial_fused":{"sha256":sha(l),**residual(l.read_bytes(),after)},"direct_exp_lrtb_wrong_order":{"sha256":sha(o),**residual(o.read_bytes(),after)}}
 require(counter=={"superseded_lut_early_spatial_fused":{"sha256":LEGACY_SHA,"different_words":37,"max_ulp":2},"direct_exp_lrtb_wrong_order":{"sha256":ORDER_SHA,"different_words":7,"max_ulp":1}},"counter")
 asm=td/"p.s";r=subprocess.run(["clang++","-std=c++17","-O3","-ffp-contract=fast","-fno-inline-functions","-S","-I",str(ROOT/"tools/emulation/dg_renderbits_real_harness_20260716"),"-I",str(ROOT/"tools/emulation"),str(PROBE),"-o",str(asm)],text=True,capture_output=True);require(r.returncode==0,r.stderr);m=re.search(r"(__ZL30bilateral_blur_opencv455_f32x4Pfll:.*?\.cfi_endproc)",asm.read_text(),re.S);require(m and "_expf"in m.group(1)and not re.search(r"\b(?:fmadd|fmla|vfmadd\w*)\b",m.group(1)),"asm")
 return {"builds":builds,"counterfactuals":counter},{"flags":["-O3","-ffp-contract=fast","-fno-inline-functions"],"canonical_fused_op_count":0,"direct_expf_call_present":True,"canonical_assembly_sha256":hashlib.sha256(m.group(1).encode()).hexdigest()}
def validate(p):
 require(p.get("schema")=="olmdistancegradation.pf32-mode5-ipp-exact-closure/1"and p.get("status")=="PASS_FIXED17X11_PF32_MODE5_IPP_FIELD_EXACT_6_ADMITTED_2_POWER_FAIL_CLOSED","schema/status");worker=Path(os.environ.get("OLM_AEX_GUEST_WORKER",DEFAULT_WORKER));require(p["aex_sha256"]==AEX_SHA==sha(AEX)and p["worker_sha256"]==WORKER_SHA==sha(worker),"owners");require(p["production_source_sha256"]==sha(SOURCE)and p["probe_sha256"]==sha(PROBE)and p["public_harness_sha256"]==sha(PUBLIC)and p["matrix_sha256"]==sha(MATRIX),"ids")
 m=json.loads(MATRIX.read_text());require(m["schema"]=="olmdistancegradation.exported-typed-owner-matrix/1"and m["status"]=="PASS_56_ADMITTED_RAW_EXACT_8_PF32_POWER_FAIL_CLOSED"and m["actual_aex_sha256"]==AEX_SHA and m["worker_sha256"]==WORKER_SHA and m["production_source_sha256"]==sha(SOURCE),"matrix")
 expected_trace={"input_png_sha256":INPUT_SHA,"pre_field_sha256":PRE_SHA,"post_field_sha256":POST_SHA,"raw_output_sha256":OUTPUT_SHA,"raw_output_bytes":2992,"input_immutable":True,"guards_intact":True,"render_error":0,"pixel_format":"argb32f","width":17,"height":11,"render_mode":"smart-cpu","selectors":SELECTORS,"suite_requests":SUITES,"unsupported_suite_calls":[],"dropped_unsupported_suite_calls":0,"input_requests":[[0,0,17,11]],"output_request":[0,0,17,11],"smart_return_value":0,"smart_entry_export":"entryPointFunc","execution_backend":"unicorn-x86_64","smart_image_sha256":AEX_SHA,"smart_truncated":False,"dropped_memory_witnesses":0};require(p["natural_public_trace"]==expected_trace,"trace")
 rows=p["six_aexcompat_diagnostic_cells"];require(len(rows)==6,"six");seen=set()
 for r in rows:
  k=(r["interpolation"],r["use_background"]);require(k in SIX and k not in seen,"key");seen.add(k);h=SIX[k]
  require(r["depth"]=="PF32"and r["blur_mode"]==5 and r["bytes_compared"]==2992 and r["actual_exported_raw_sha256"]==h and r["guards_intact"],"row base")
  if r["interpolation"]=="power":require(r["fail_closed"]and not r["exact"]and r["oracle_boundary"]=="native Windows UCRT powf required","Power row")
  else:require(not r["fail_closed"]and r["exact"]and r["production_renderbits_sha256"]==h and r["different_bytes"]==0,"admitted row")
 require(seen==set(SIX)and p["matrix_summary"]=={"exact_admitted":56,"pf16_exact":32,"pf32_exact":24,"pf32_power_fail_closed":8,"pf32_mode5_exact":6,"pf32_mode5_fail_closed":2},"recount");require(p["field_mechanism"]["builds"]=={"production_o0":{"canonical_sha256":POST_SHA,"raw_exact":True},"adversarial_contract_fast_o3":{"canonical_sha256":POST_SHA,"raw_exact":True}},"builds");require(p["field_mechanism"]["counterfactuals"]=={"superseded_lut_early_spatial_fused":{"sha256":LEGACY_SHA,"different_words":37,"max_ulp":2},"direct_exp_lrtb_wrong_order":{"sha256":ORDER_SHA,"different_words":7,"max_ulp":1}},"counter")
 require(p["compiler_proof"]["flags"]==["-O3","-ffp-contract=fast","-fno-inline-functions"]and p["compiler_proof"]["canonical_fused_op_count"]==0 and p["compiler_proof"]["direct_expf_call_present"]and p["compiler_proof"]["canonical_assembly_sha256"]==ASSEMBLY_SHA,"compiler");require(p["public_contract"]=={"mode5_positive_cases":6,"power_fail_closed_cases":8,"input_immutable":True,"output_untouched_on_power_reject":True,"padding_preserved":True,"balanced_parameter_lifecycle":True,"balanced_layer_lifecycle":True,"unlisted_mode5_tuple_fail_closed":True,"marker":"positive=9 mode5_positive=6 power_fail_closed=8 negative=21 classic_guards=4"},"public");require(p["bounded_admission"]=={"width":17,"height":11,"depth":"PF32","blur_mode":5,"blur_size":1,"admitted_interpolation_modes":["constant","linear","sphere"],"power_requires_native_windows_ucrt_capture":True,"canonical_mask_and_parameter_tuple_required":True},"admission");require(p["not_promoted"]==["PF32 Power without native Windows UCRT powf capture","unlisted PF32 Smart tuple or geometry","partial-world/origin layouts","native After Effects pixels","project/global fast-math configuration and arbitrary fast-math codegen"],"bounds")
def generate():
 worker=Path(os.environ.get("OLM_AEX_GUEST_WORKER",DEFAULT_WORKER));require(sha(AEX)==AEX_SHA and sha(worker)==WORKER_SHA,"drift");m=json.loads(MATRIX.read_text());rows=[r for r in m["rows"]if r["depth"]=="PF32"and r["blur_mode"]==5 and r["interpolation"]!="constant"]
 with tempfile.TemporaryDirectory()as raw:
  td=Path(raw);trace,before,after=natural(worker,td);mech,compiler=mechanism(td,before,after);exe=td/"public";b=subprocess.run(["clang++","-std=c++17","-O0","-I",str(ROOT/"tools/emulation/dg_renderbits_real_harness_20260716"),str(PUBLIC),str(FIELDGEN),"-o",str(exe)],text=True,capture_output=True);require(b.returncode==0,b.stderr);r=subprocess.run([str(exe)],text=True,capture_output=True);marker="positive=9 mode5_positive=6 power_fail_closed=8 negative=21 classic_guards=4";require(r.returncode==0 and marker in r.stdout,"public")
 p={"schema":"olmdistancegradation.pf32-mode5-ipp-exact-closure/1","status":"PASS_FIXED17X11_PF32_MODE5_IPP_FIELD_EXACT_6_ADMITTED_2_POWER_FAIL_CLOSED","aex_sha256":AEX_SHA,"worker_sha256":WORKER_SHA,"production_source_sha256":sha(SOURCE),"probe_sha256":sha(PROBE),"public_harness_sha256":sha(PUBLIC),"matrix_sha256":sha(MATRIX),"natural_public_trace":trace,"six_aexcompat_diagnostic_cells":rows,"matrix_summary":{"exact_admitted":56,"pf16_exact":32,"pf32_exact":24,"pf32_power_fail_closed":8,"pf32_mode5_exact":6,"pf32_mode5_fail_closed":2},"field_mechanism":mech,"compiler_proof":compiler,"public_contract":{"mode5_positive_cases":6,"power_fail_closed_cases":8,"input_immutable":True,"output_untouched_on_power_reject":True,"padding_preserved":True,"balanced_parameter_lifecycle":True,"balanced_layer_lifecycle":True,"unlisted_mode5_tuple_fail_closed":True,"marker":marker},"bounded_admission":{"width":17,"height":11,"depth":"PF32","blur_mode":5,"blur_size":1,"admitted_interpolation_modes":["constant","linear","sphere"],"power_requires_native_windows_ucrt_capture":True,"canonical_mask_and_parameter_tuple_required":True},"not_promoted":["PF32 Power without native Windows UCRT powf capture","unlisted PF32 Smart tuple or geometry","partial-world/origin layouts","native After Effects pixels","project/global fast-math configuration and arbitrary fast-math codegen"]};validate(p);return p
def main():
 a=argparse.ArgumentParser();a.add_argument("--validate-only",action="store_true");q=a.parse_args()
 if q.validate_only:validate(json.loads(REPORT.read_text()))
 else:
  p=generate();REPORT.write_text(json.dumps(p,indent=2,sort_keys=True)+"\n");DOC.write_text("# OLMDistanceGradation PF32 Mode 5 IPP exact closure\n\nStatus: **PASS_FIXED17X11_PF32_MODE5_IPP_FIELD_EXACT_6_ADMITTED_2_POWER_FAIL_CLOSED**. The fixed IPP field mechanism is raw exact. Constant, Linear, and Sphere provide six admitted public Mode 5 cells; the two Power cells fail closed because no native Windows UCRT `powf` result is retained. AEXCompat Power hashes remain diagnostic host-substituted observations only. The prior portable body remains a 37-word/max-2-ULP counterfactual. Unlisted tuples and project/global fast-math remain unpromoted.\n")
 print("PASS_OLMDISTANCEGRADATION_PF32_MODE5_IPP_EXACT_CLOSURE_20260812")
if __name__=="__main__":main()
