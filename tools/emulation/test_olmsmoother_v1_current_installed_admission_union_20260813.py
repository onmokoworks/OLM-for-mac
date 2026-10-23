#!/usr/bin/env python3
"""Replay the complete bounded OLMSmoother v1 Classic admission union."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse,hashlib,importlib, json,os,struct,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/"tools/emulation/probe_olmsmoother_v1_current_installed_admission_union_20260813.cpp"
SOURCE=ROOT/"mac/OLMSmoother/Mac/OLMSmoother_port.cpp"; STRINGS=ROOT/"mac/OLMSmoother/OLMSmoother_Strings.cpp"
SUITE_CPP=resolve_asset(ROOT/"Util/AEGP_SuiteHandler.cpp"); MISSING_CPP=resolve_asset(ROOT/"Util/MissingSuiteError.cpp"); SDK=resolve_asset(ROOT/"Headers/AE_Effect.h")
INSTALLED=Path.home()/"Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin/Contents/MacOS/OLMSmoother"
GUARD=ROOT/"refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json"
IDENTITY=ROOT/"refs/conformance/olm_hostless_batch4_incremental_install_20260813.json"
IMAGE=resolve_asset(ROOT/"refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png")
REPORT=ROOT/"refs/conformance/olmsmoother_v1_current_installed_admission_union_20260813.json"; MD=REPORT.with_suffix(".md")
PINS={"probe":"9a6a2212869a537bcf2e268d30b6bc415a0fba7039f288e265f3e41dabcc6403","source":"c8c7b7728553ee4ccaadc7ef802be40e607d7e7a7b829958d4b8dfab80f633dc","strings":"ce4ed37933a67172f6cba6570a55a5f2ea592284e8a9f48cd852bf4fcf1484e7","suite_cpp":"7c054c7b0778b1b26463d6bf31cd57ee1d971946e8da22fb174e9f088741606f","missing_cpp":"8c0cc22b898c94c73556778f5cef1ccf9cded81ee590bd04feb49028ff4f44d9","sdk_header":"a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d","installed_binary":"f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162","guard_report":"6ee4224da89573be90d633a9eaca2f52335f304001cc4a8f2abc38c066716d28","install_identity":"415e1b26b77097248173da13239b85ae70d0b6a446fa6eb31bc13a0bdc6895af","fullframe_png":"166cafc8aaa2bb2d78ed26a12fe95b6dcf0f6eeeabd7f3a4daaf0ceece500e4c"}
RUN_SHA256="8a70694a745a4c0825a9551d73684f824ef581043235fc81806c58c4d8024b25"; STATUS="PASS_OLMSMOOTHER_V1_CURRENT_INSTALLED_COMPLETE_CLASSIC_ADMISSION_UNION_AE_FREE"
TOP={"schema","status","claim_boundary","authorities","summary","run_sha256","run_lines","scope","after_effects_processes"}
SUMMARY={"architectures":["arm64","x86_64"],"positive_cells_per_slice":67,"positive_cells_total":134,"families":{"fullframe_pf8":1,"checker_7x5":20,"colored_7x5":16,"ramp_7x5":20,"practical_7x5_pf16":4,"practical_64x36_pf16":4,"constant_5x3_pf16":2},"source_installed_byte_identical":True}
SCOPE={"complete_admission_union":True,"installed_arm64":True,"installed_x86_64":True,"native_after_effects":False,"arbitrary_source_or_tuple":False}
CLAIM="Both current installed Universal slices of OLMSmoother v1 match the source-built real-SDK Classic entry for all 67 cells in the fixed-source production admission union. The x86_64 route runs under Rosetta. This AE-free dlopen closure does not claim arbitrary source/tuple products or native After Effects."
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def authorities():return{"probe":sha(PROBE),"source":sha(SOURCE),"strings":sha(STRINGS),"suite_cpp":sha(SUITE_CPP),"missing_cpp":sha(MISSING_CPP),"sdk_header":sha(SDK),"installed_binary":sha(INSTALLED),"guard_report":sha(GUARD),"install_identity":sha(IDENTITY),"fullframe_png":sha(IMAGE)}
def ae_processes():
 out=[]
 for n in("After Effects","AfterFX","aerender"):
  p=subprocess.run(["pgrep","-x",n],text=True,capture_output=True)
  if p.returncode==0:out += [f"{n}:{x}" for x in p.stdout.split()]
 return out
def cases():
 sys.path.insert(0,str(ROOT/"tools/emulation"))
 checker=importlib.import_module("test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810")
 colored=importlib.import_module("test_olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811")
 ramp=importlib.import_module("test_olmsmoother_v1_multivalue_ramp_boundary_20260810")
 practical=importlib.import_module("test_olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812")
 rows=[]; image=Image.open(IMAGE).convert("RGBA"); payload=b"".join(bytes((a,r,g,b)) for r,g,b,a in image.getdata());rows.append(("fullframe_pf8",payload,8,960,540,3840,0,6,(255,255,255,255)))
 for family,module,tolerances in(("checker",checker,(0,1,6,127,255)),("colored",colored,(0,6,127,255)),("ramp",ramp,(0,1,6,127,255))):
  for depth in(8,16):
   payload,rb=module.fixture(depth)
   for use in(0,1):
    for tolerance in tolerances:rows.append((f"{family}_pf{depth}_key{use}_tol{tolerance}",payload,depth,7,5,rb,use,tolerance,(255,202,187,230)))
 payload,rb=practical.fixture(7,5,8)
 for use in(0,1):
  for tolerance in(6,127):rows.append((f"practical_7x5_pf16_key{use}_tol{tolerance}",payload,16,7,5,rb,use,tolerance,(255,202,187,230)))
 payload,rb=practical.fixture(64,36,32)
 for use in(0,1):
  for tolerance in(6,127):rows.append((f"practical_64x36_pf16_key{use}_tol{tolerance}",payload,16,64,36,rb,use,tolerance,(255,202,187,230)))
 key=tuple(checker.widen(x) for x in checker.KEY)
 for name,pixel in(("constant_exact",(0x8000,*key)),("constant_near",(0x8000,key[0]+1,key[1],key[2]))):
  active=struct.pack("<4H",*pixel)*5;payload=b"".join(active+b"\x3c"*8 for _ in range(3));rows.append((name,payload,16,5,3,48,1,6,(255,202,187,230)))
 assert len(rows)==67
 return rows
def compile_probe(arch,td):
 exe=td/f"probe-{arch}";sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip();cmd=[_UCRT_CXX,"-std=c++17","-arch",arch,"-O2","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations"]
 for inc in("Headers","Headers/SP","Util","Resources","mac/OLMSmoother","mac/OLMSmoother/Mac"):cmd += ["-I",str(ROOT/inc)]
 cmd += [str(PROBE),str(STRINGS),str(SUITE_CPP),str(MISSING_CPP),"-framework","Cocoa","-o",str(exe)];p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return exe
def run_arch(arch,td):
 exe=compile_probe(arch,td);lines=[]
 for index,(name,payload,depth,w,h,rb,use,tol,key) in enumerate(cases()):
  fixture=td/f"fixture-{index}.bin";fixture.write_bytes(payload);cmd=[str(exe),str(INSTALLED),str(fixture),str(depth),str(w),str(h),str(rb),str(use),str(tol),*map(str,key)];p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  if p.returncode or p.stderr or "pass=1" not in p.stdout:raise RuntimeError(f"{arch} {name}: {p.stdout} {p.stderr}")
  lines.append(f"POS {name} pass=1")
 return lines
def generate():
 if authorities()!=PINS:raise RuntimeError(f"authority drift: {authorities()}")
 processes=ae_processes()
 if processes:raise RuntimeError(f"After Effects must remain stopped: {processes}")
 with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-union-") as raw:
  td=Path(raw);lines=[]
  for arch in("arm64","x86_64"):lines += [f"ARCH {arch}",*run_arch(arch,td)]
 transcript="\n".join(lines)+"\n";digest=hashlib.sha256(transcript.encode()).hexdigest()
 if digest!=RUN_SHA256:raise RuntimeError(f"transcript drift {digest}")
 return{"schema":"olmsmoother.v1-current-installed-admission-union/1","status":STATUS,"claim_boundary":CLAIM,"authorities":PINS,"summary":SUMMARY,"run_sha256":RUN_SHA256,"run_lines":lines,"scope":SCOPE,"after_effects_processes":[]}
def validate(d):
 if set(d)!=TOP or d["schema"]!="olmsmoother.v1-current-installed-admission-union/1" or d["status"]!=STATUS:raise RuntimeError("schema/status drift")
 if d["claim_boundary"]!=CLAIM or d["authorities"]!=PINS or d["summary"]!=SUMMARY or d["scope"]!=SCOPE or d["after_effects_processes"]!=[]:raise RuntimeError("claim/authority drift")
 if len(d["run_lines"])!=136 or d["run_lines"][0]!="ARCH arm64" or d["run_lines"][68]!="ARCH x86_64":raise RuntimeError("row drift")
 if hashlib.sha256(("\n".join(d["run_lines"])+"\n").encode()).hexdigest()!=RUN_SHA256 or d["run_sha256"]!=RUN_SHA256:raise RuntimeError("transcript drift")
def markdown(d):return f"# OLMSmoother v1 current installed complete Classic admission replay (2026-08-13)\n\nStatus: `{STATUS}`\n\nAll 67 bounded admitted cells are exact on both installed Universal slices (134 slice replays): full-frame PF8; checker, colored and ramp 7x5 families; practical PF16 7x5 and 64x36; and two PF16 5x3 constants. x86_64 runs under Rosetta. AE was not launched.\n\nBoundary: {CLAIM}\n"
def main():
 p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args();fresh=generate();validate(fresh)
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");MD.write_text(markdown(fresh))
 else:
  saved=json.loads(REPORT.read_text());validate(saved)
  if saved!=fresh or MD.read_text()!=markdown(saved):raise RuntimeError("persisted report drift")
 print(STATUS)
if __name__=="__main__":main()
