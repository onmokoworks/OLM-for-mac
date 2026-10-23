#!/usr/bin/env python3
"""Audit actual Universal binary codegen and run both slices for all Mode5 cells."""

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")
import argparse,hashlib,json,os,re,stat,struct,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BINARY=ROOT/"handoffs/olmdistancegradation_pf32_power_failclose_universal_candidate_20260812/product/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation";PROJECT=ROOT/"mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj/project.pbxproj";SOURCE=ROOT/"mac/OLMDistanceGradation/OLMDistanceGradation.cpp";HARNESS=ROOT/"tools/emulation/dg_exported_typed_owner_compare_harness_20260811.cpp";FIELDGEN=ROOT/"core/olmdistancegradation_fieldgen.cpp";REPORT=ROOT/"refs/conformance/olmdistancegradation_pf32_mode5_universal_codegen_20260812.json";DOC=REPORT.with_suffix(".md")
BUNDLE=BINARY.parents[2]
BLUR="__ZL30bilateral_blur_opencv455_f32x4Pfll";PRODUCT="__ZL32bilateral_noncontracting_productff";PROJECT_SHA="47a276d3f63a6275178eea858a85d8ca0392b994ee025df9d678f2dbdb8e210b";BASELINE_BINARY_SHA="0caf728ce871feefd606cdedd2054f17bce09c80639722748ebecd9ed5440093";BASE={"arm64":{"bilateral":2068,"text":98304},"x86_64":{"bilateral":2112,"text":90112}};DISASSEMBLY={"arm64":{"bilateral":"a9976a3ac02aabc4e0281bac5ce2f583032cd8a33a5aedb022a323c57809ca02","product":"d3400f469cf7d050e96b37231b3f9f6d642842a14209bb0000812602d70ac8be"},"x86_64":{"bilateral":"7f366b9ff7895f4976848f661e1bf60a0763d89fa5baf11333b4d89cef29f2a4","product":"5906b7be76c17f7192d76dbf9c0e288b92bb41d9d5dbb4ad735a4418271a2fed"}}
HASHES={("constant",False):"a47997492c742fcd23e8100ef9dacbb9c638ebf0e530ef8c883a52c43b156c3f",("constant",True):"3e8896c9ca75e05c3b262d88324f96e46039be02600dab0c97ec367b46003918",("linear",False):"50934ac830542ca73fee4a11b924b746a0ae93f97f34b0d2868170bc371dd387",("linear",True):"c21fa76f957ad1a94c0fd14ed28960d676e2dfff13de46e868ff951527e3420f",("sphere",False):"373408c57b6a6e9c5c06920402b8c08755ef6cca4625af326561c3dde38a346d",("sphere",True):"0d3655165718ea5acc787df41ad86fe3d147e6eb76ca34adc2d34a45d07ae5f3",("power",False):"40b5d262cdc0ab372036c9d2774fa9400f74daa7895c75c2222a246b01c485a5",("power",True):"fe715e7973fa79d6043cbe86dcfce3205869fb23ac9d69a8d98b288ab20ad6d7"}
UNTOUCHED_SHA="fb32705be5df99373690510e4c92b2d512a21f20f722b835d93afccdc864797d"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory():
 rows=[]
 for path in sorted(BUNDLE.rglob("*")):
  if path.is_file():rows.append({"path":str(path.relative_to(BUNDLE)),"size":path.stat().st_size,"mode":stat.S_IMODE(path.stat().st_mode),"sha256":sha(path)})
 return rows
def run(c):
 r=subprocess.run(c,cwd=ROOT,text=True,capture_output=True)
 if r.returncode:raise AssertionError({"cmd":c,"stderr":r.stderr})
 return r.stdout
def body(text,symbol):
 start=text.index(symbol+":");rest=text[start+len(symbol)+1:];m=re.search(r"^\S[^\n]*:\s*$",rest,re.M);return text[start:start+len(symbol)+1+(m.start()if m else len(rest))]
def symbols(arch):
 return [(int(x.split()[0],16),x.split()[-1])for x in run(["xcrun","nm","-arch",arch,"-n",str(BINARY)]).splitlines()if len(x.split())>=3 and x.split()[1]in("t","T")]
def ssize(arch,s):
 x=symbols(arch);i=next(i for i,v in enumerate(x)if v[1]==s);return x[i+1][0]-x[i][0]
def runtime():
 with tempfile.TemporaryDirectory()as raw:
  td=Path(raw);exe=td/"h";src=td/"src";data=bytearray()
  for y in range(11):
   for x in range(17):data.extend(struct.pack("<4f",0.0 if 4<=x<13 and 2<=y<9 else 1.0,(x*613+y*1231)%256/255,(x*997+y*211)%256/255,(x*1499+y*307)%256/255))
  src.write_bytes(data);r=subprocess.run([_UCRT_CXX,"-std=c++17","-O0","-arch","arm64","-arch","x86_64","-mmacosx-version-min=11.0","-I",str(ROOT/"tools/emulation/dg_renderbits_real_harness_20260716"),str(HARNESS),str(FIELDGEN),"-o",str(exe)],cwd=ROOT,text=True,capture_output=True);assert r.returncode==0,r.stderr;result={}
  for arch in("arm64","x86_64"):
   rows=[]
   for (interp,bg),expected in HASHES.items():
    out=td/f"{arch}.{interp}.{bg}";q=subprocess.run(["arch",f"-{arch}",str(exe),"PF32",str(src),str(out),interp,str(int(bg)),"5"],cwd=ROOT);assert q.returncode==0;actual=sha(out);assert actual==(UNTOUCHED_SHA if interp=="power" else expected);rows.append({"interpolation":interp,"use_background":bg,"expected_actual_aex_raw_sha256":expected,"production_raw_sha256":actual,"bytes_compared":2992,"raw_exact":interp!="power"})
   for row in rows:
    if row["interpolation"]=="power":
     row["production_raw_sha256"]=UNTOUCHED_SHA;row["raw_exact"]=False;row["fail_closed"]=True;row["native_windows_ucrt_required"]=True
    else:row["fail_closed"]=False
   power=[]
   for blur in (2,3,4,5):
    for bg in (False,True):
     out=td/f"{arch}.power.{blur}.{bg}";q=subprocess.run(["arch",f"-{arch}",str(exe),"PF32",str(src),str(out),"power",str(int(bg)),str(blur)],cwd=ROOT);assert q.returncode==0 and sha(out)==UNTOUCHED_SHA;power.append({"blur_mode":blur,"use_background":bg,"fail_closed":True,"output_untouched_sha256":UNTOUCHED_SHA})
   result[arch]={"mode5_cells":8,"raw_exact_cells":6,"power_fail_closed_cells":8,"rows":rows,"power_fail_closed_rows":power}
  return result
def validate(p):
 assert p["schema"]=="olmdistancegradation.pf32-mode5-universal-codegen/1"and p["status"]=="PASS_UNIVERSAL_MODE5_CODEGEN_6_EXACT_2_POWER_FAIL_CLOSED";assert p["binary_sha256"]==sha(BINARY)and p["project_sha256"]==PROJECT_SHA==sha(PROJECT)and p["production_source_sha256"]==sha(SOURCE)and p["runtime_harness_sha256"]==sha(HARNESS)and p["pre_integration_baseline_binary_sha256"]==BASELINE_BINARY_SHA;assert p["candidate_bundle"]==str(BUNDLE.relative_to(ROOT))and p["candidate_bundle_inventory"]==inventory()and p["strict_codesign"]and p["signing_kind"]=="ad-hoc";assert subprocess.run(["codesign","--verify","--deep","--strict",str(BUNDLE)],capture_output=True).returncode==0;assert set(p["architectures"])=={"arm64","x86_64"}and p["global_compiler_setting_changed"]is False
 for arch,row in p["slices"].items():
  assert row["baseline_bilateral_text_bytes"]==BASE[arch]["bilateral"]and row["bilateral_text_bytes"]<=BASE[arch]["bilateral"]and row["bilateral_text_delta_bytes"]==row["bilateral_text_bytes"]-BASE[arch]["bilateral"];assert 0<row["product_helper_text_bytes"]<=64 and row["baseline_whole_text_bytes"]==BASE[arch]["text"] and row["whole_text_growth_bound_bytes"]==16384 and row["whole_text_bytes"]<=BASE[arch]["text"]+16384 and row["direct_expf"]and row["product_helper_calls"]==3 and row["fused_op_count"]==0 and row["bilateral_disassembly_sha256"]==DISASSEMBLY[arch]["bilateral"] and row["product_disassembly_sha256"]==DISASSEMBLY[arch]["product"]
 for arch,g in p["runtime_production_source_universal_mode5"].items():
  assert g["mode5_cells"]==8 and g["raw_exact_cells"]==6 and g["power_fail_closed_cells"]==8 and len(g["rows"])==8 and len(g["power_fail_closed_rows"])==8;seen=set()
  for row in g["rows"]:
   k=(row["interpolation"],row["use_background"]);assert k in HASHES and k not in seen;seen.add(k);assert row["expected_actual_aex_raw_sha256"]==HASHES[k]and row["bytes_compared"]==2992
   if row["interpolation"]=="power":assert row["production_raw_sha256"]==UNTOUCHED_SHA and not row["raw_exact"] and row["fail_closed"] and row["native_windows_ucrt_required"]
   else:assert row["production_raw_sha256"]==HASHES[k]and row["raw_exact"]and not row["fail_closed"]
  assert seen==set(HASHES)
  assert {(r["blur_mode"],r["use_background"])for r in g["power_fail_closed_rows"]}=={(b,bg)for b in(2,3,4,5)for bg in(False,True)} and all(r["fail_closed"]and r["output_untouched_sha256"]==UNTOUCHED_SHA for r in g["power_fail_closed_rows"])
 assert p["scope"]=="fixed17x11 PF32 Smart non-Power Mode5 codegen plus all-Power fail-closed policy"and p["claims_not_made"]==["No native Windows UCRT powf result for PF32 Power","No 64/64 whole-matrix claim on either architecture","No project/global fast-math configuration or arbitrary fast-math codegen claim"]
def generate():
 assert sha(PROJECT)==PROJECT_SHA and "ffast-math"not in PROJECT.read_text()and "ffp-contract=fast"not in PROJECT.read_text();archs=run(["lipo","-archs",str(BINARY)]).split();assert set(archs)=={"arm64","x86_64"};slices={}
 for arch in("arm64","x86_64"):
  text=run(["xcrun","otool","-arch",arch,"-tvV",str(BINARY)]);b=body(text,BLUR);h=body(text,PRODUCT);assert b.count(PRODUCT)==3 and "symbol stub for: _expf"in b and not re.search(r"\b(?:fmadd|fmla|vfmadd\w*)\b",b+h);bs=ssize(arch,BLUR);hs=ssize(arch,PRODUCT);whole=int(run(["size","-arch",arch,str(BINARY)]).splitlines()[-1].split()[0]);assert bs<=BASE[arch]["bilateral"]and hs<=64 and whole<=BASE[arch]["text"]+16384;slices[arch]={"bilateral_text_bytes":bs,"baseline_bilateral_text_bytes":BASE[arch]["bilateral"],"bilateral_text_delta_bytes":bs-BASE[arch]["bilateral"],"product_helper_text_bytes":hs,"whole_text_bytes":whole,"baseline_whole_text_bytes":BASE[arch]["text"],"whole_text_growth_bound_bytes":16384,"direct_expf":True,"product_helper_calls":3,"fused_op_count":0,"bilateral_disassembly_sha256":hashlib.sha256(b.encode()).hexdigest(),"product_disassembly_sha256":hashlib.sha256(h.encode()).hexdigest()}
 p={"schema":"olmdistancegradation.pf32-mode5-universal-codegen/1","status":"PASS_UNIVERSAL_MODE5_CODEGEN_6_EXACT_2_POWER_FAIL_CLOSED","binary_sha256":sha(BINARY),"candidate_bundle":str(BUNDLE.relative_to(ROOT)),"candidate_bundle_inventory":inventory(),"strict_codesign":True,"signing_kind":"ad-hoc","project_sha256":sha(PROJECT),"production_source_sha256":sha(SOURCE),"runtime_harness_sha256":sha(HARNESS),"pre_integration_baseline_binary_sha256":BASELINE_BINARY_SHA,"architectures":archs,"global_compiler_setting_changed":False,"slices":slices,"runtime_production_source_universal_mode5":runtime(),"scope":"fixed17x11 PF32 Smart non-Power Mode5 codegen plus all-Power fail-closed policy","claims_not_made":["No native Windows UCRT powf result for PF32 Power","No 64/64 whole-matrix claim on either architecture","No project/global fast-math configuration or arbitrary fast-math codegen claim"]};validate(p);return p
def main():
 a=argparse.ArgumentParser();a.add_argument("--validate-only",action="store_true");q=a.parse_args()
 if q.validate_only:validate(json.loads(REPORT.read_text()))
 else:
  p=generate();REPORT.write_text(json.dumps(p,indent=2,sort_keys=True)+"\n");DOC.write_text("# OLMDistanceGradation PF32 Mode 5 Universal codegen\n\nStatus: **PASS_UNIVERSAL_MODE5_CODEGEN_6_EXACT_2_POWER_FAIL_CLOSED**. Both Universal slices retain direct expf, three noncontracting helper calls and zero fused operations for the IPP field; each executes six admitted non-Power Mode 5 cells raw-exact. All eight PF32 Power cells (Blur 2–5 × background off/on) fail closed with output untouched because native Windows UCRT powf evidence is absent. No whole-matrix claim is made.\n")
 print("PASS_OLMDISTANCEGRADATION_PF32_MODE5_UNIVERSAL_CODEGEN_20260812")
if __name__=="__main__":main()
