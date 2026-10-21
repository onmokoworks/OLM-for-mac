#!/usr/bin/env python3
"""Replay a representative bounded OLMSmoother2 Smart cell through the installed Mach-O."""

from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
PROBE=ROOT/"tools/emulation/probe_olmsmoother2_current_installed_public_20260813.cpp"
UNION_PROBE=ROOT/"tools/emulation/probe_olmsmoother2_current_installed_admission_union_20260813.cpp"
SOURCE=ROOT/"mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
STRINGS=ROOT/"mac/OLMSmoother2/OLMSmoother2_Strings.cpp"
SUITE_CPP=ROOT/"Util/AEGP_SuiteHandler.cpp"; SUITE_H=ROOT/"Util/AEGP_SuiteHandler.h"; MISSING_CPP=ROOT/"Util/MissingSuiteError.cpp"; SDK_HEADER=ROOT/"Headers/AE_Effect.h"
INSTALLED=Path.home()/"Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother2.plugin/Contents/MacOS/OLMSmoother2"
BUILD_IDENTITY=ROOT/"handoffs/olmsmoother2_pf8_pf16_pf32_public_smart_candidate_20260814/build_identity.json"
INSTALL_IDENTITY=ROOT/"refs/conformance/olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.json"
GUARD_REPORT=ROOT/"refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json"
PF8_HARNESS=ROOT/"tools/emulation/olmsmoother2_pf8_legacy12_public_smart_harness_20260814.cpp"
PF16_HARNESS=ROOT/"tools/emulation/olmsmoother2_case07_pf16_public_smart_harness_20260814.cpp"
PF32_HARNESS=ROOT/"tools/emulation/olmsmoother2_case07_public_smart_harness_20260814.cpp"
PF8_INPUT=ROOT/"refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2/input\\current_olm_cells.png"
PF16_CLOSURE=ROOT/"tools/emulation/test_olmsmoother2_case07_pf16_unique_public_closure_20260814.py"
PF32_INPUT=ROOT/"refs/conformance/fixtures/olmsmoother2_case07_pf32_entry_20260727/pf32_input_entry_argb.bin.gz"
REPORT=ROOT/"refs/conformance/olmsmoother2_current_installed_public_20260813.json"; MARKDOWN=REPORT.with_suffix(".md")
PINS={
 "probe":"2cb2b6ba700de0d40ccddba48ce6c8a68bbf284c84340888df6822cfa358782a",
 "union_probe":"6f1c71820476c46f652db08ea187cfd9e39c7a94fb945a1e5e0ca27e290734c2",
 "source":"c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168",
 "strings":"f79e5cc65618c838a5a8b538e65e79730ce975a920fc360be03b7f43f6194b13",
 "suite_cpp":"7c054c7b0778b1b26463d6bf31cd57ee1d971946e8da22fb174e9f088741606f",
 "suite_h":"36e1acf66a90979bd541bfb260e4dbf58dab2d00afec7d749dfcffc43a6843f7",
 "missing_cpp":"8c0cc22b898c94c73556778f5cef1ccf9cded81ee590bd04feb49028ff4f44d9",
 "sdk_header":"a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d",
 "installed_binary":"c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f",
 "build_identity":"c0852db33833084681012fa4a854f21bd50f96d29b392deb784df0fa89a6bd0b",
 "install_identity":"38001b4343c5dea4078c2e2c9678bbfa9bf88b737043b453f0674eac7b159483",
 "guard_report":"6ee4224da89573be90d633a9eaca2f52335f304001cc4a8f2abc38c066716d28",
 "pf8_harness":"78b0c0ec1c7bd93d5e6f4f7eb71807b79d4d266f4ab21f98faa7b629a2089da2",
 "pf16_harness":"5877f576aaf927a5c34e504657a32f4900fc84bb327fc0834378e1207f7e671e",
 "pf32_harness":"df1419b9992e18442b91aa1d7d4aa84f2538ca5192a52ebfa298ae8d2c7afe31",
 "pf8_input":"9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265",
 "pf16_closure":"95f9550f7b22259072214dd40d08320d12a93777cea0fba82946c82157403553",
 "pf32_input":"f29cad40b4f0081fa5f279da0e875198a2970ea2d9c1161db7cc2058acf4044c"}
RUN_SHA256="2c5fd13c38273ccf8d6b83713043b1f83e0a2d8419d485d51036b32081159c8b"
STATUS="PASS_OLMSMOOTHER2_CURRENT_INSTALLED_COMPLETE_SMART_ADMISSION_UNION_AE_FREE"
CLAIM="Both installed Universal slices of OLMSmoother2 execute all 39 fixed-source bounded Smart cells: the prior 25-cell union, twelve full-HD PF8 legacy tuples, and exact case-07 PF16/PF32. The installed EffectMain passes the new PF8 46-row and PF16/PF32 24-row public matrices on each slice; source mutation, tuple, world, suite and lifecycle failures remain fail-closed and output-atomic. x86_64 runs under Rosetta. This is AE-free installed dlopen evidence, not arbitrary-source, arbitrary-tuple, native-Windows-output-world, or native-After-Effects evidence."
SUMMARY={"architectures":["arm64","x86_64"],"positive_cells_per_slice":39,"positive_cells_total":78,"prior_union_positive_per_slice":25,"new_positive_per_slice":14,"new_public_rows_per_slice":94,"source_installed_byte_identical":True,"suite_and_checkout_lifecycle_identical":True}
SCOPE={"installed_arm64":True,"installed_x86_64":True,"native_after_effects":False,"complete_admission_union":True,"arbitrary_source_or_tuple":False}
TOP_KEYS={"schema","status","claim_boundary","authorities","summary","run_sha256","run_lines","after_effects_processes","scope"}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def authorities():
 return {"probe":sha(PROBE),"union_probe":sha(UNION_PROBE),"source":sha(SOURCE),"strings":sha(STRINGS),"suite_cpp":sha(SUITE_CPP),"suite_h":sha(SUITE_H),"missing_cpp":sha(MISSING_CPP),"sdk_header":sha(SDK_HEADER),"installed_binary":sha(INSTALLED),"build_identity":sha(BUILD_IDENTITY),"install_identity":sha(INSTALL_IDENTITY),"guard_report":sha(GUARD_REPORT),"pf8_harness":sha(PF8_HARNESS),"pf16_harness":sha(PF16_HARNESS),"pf32_harness":sha(PF32_HARNESS),"pf8_input":sha(PF8_INPUT),"pf16_closure":sha(PF16_CLOSURE),"pf32_input":sha(PF32_INPUT)}
def ae_processes():
 out=[]
 for name in ("After Effects","AfterFX","aerender"):
  run=subprocess.run(["pgrep","-x",name],text=True,capture_output=True)
  if run.returncode==0: out += [f"{name}:{pid}" for pid in run.stdout.split()]
 return out
def compile_and_run(arch,probe=PROBE):
 with tempfile.TemporaryDirectory(prefix="olmsmoother2-installed-") as td:
  exe=Path(td)/"probe"; sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip()
  cmd=["clang++","-std=c++17","-arch",arch,"-O2","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations"]
  for inc in ("Headers","Headers/SP","Util","Resources","mac/OLMSmoother2","mac/OLMSmoother2/Mac"): cmd += ["-I",str(ROOT/inc)]
  cmd += [str(probe),str(STRINGS),str(SUITE_CPP),str(MISSING_CPP),"-framework","Cocoa","-o",str(exe)]
  build=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  if build.returncode: raise RuntimeError(build.stdout+build.stderr)
  env=os.environ.copy(); env["OLMSMOOTHER2_INSTALLED_BINARY"]=str(INSTALLED)
  run=subprocess.run([str(exe)],cwd=ROOT,env=env,text=True,capture_output=True)
  if run.returncode or run.stderr: raise RuntimeError(f"probe failed rc={run.returncode}: {run.stdout} {run.stderr}")
  return run.stdout
def load_pf16():
 spec=importlib.util.spec_from_file_location("smoother2_pf16_input",PF16_CLOSURE); module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
def compile_public(arch,harness,input_path):
 with tempfile.TemporaryDirectory(prefix="olmsmoother2-installed-public-") as td:
  exe=Path(td)/"probe";sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip()
  cmd=["clang++","-std=c++17","-arch",arch,"-O2","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations"]
  for inc in ("Headers","Headers/SP","Util","Resources","mac/OLMSmoother2","mac/OLMSmoother2/Mac"):cmd += ["-I",str(ROOT/inc)]
  cmd += [str(harness),str(STRINGS),str(SUITE_CPP),str(MISSING_CPP),"-framework","Cocoa","-lz","-o",str(exe)]
  build=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  if build.returncode:raise RuntimeError(build.stdout+build.stderr)
  run=subprocess.run([str(exe),str(input_path),str(INSTALLED)],cwd=ROOT,text=True,capture_output=True)
  if run.returncode:raise RuntimeError(f"installed public harness failed rc={run.returncode}: {run.stdout} {run.stderr}")
  return run.stdout+("STDERR\n"+run.stderr if run.stderr else "")
def generate():
 live=authorities()
 if live!=PINS: raise RuntimeError(f"authority drift: {live}")
 processes=ae_processes()
 if processes: raise RuntimeError(f"After Effects must remain stopped: {processes}")
 with tempfile.TemporaryDirectory(prefix="olmsmoother2-installed-inputs-") as td:
  work=Path(td); image=Image.open(PF8_INPUT).convert("RGBA"); pf8=work/"input.argb8";pf8.write_bytes(b"".join(bytes((a,r,g,b)) for r,g,b,a in image.getdata()))
  pf16,_=load_pf16().reconstruct_input(work)
  chunks=[]
  for arch in ("arm64","x86_64"):
   chunks += [f"ARCH {arch}\n",compile_and_run(arch),compile_and_run(arch,UNION_PROBE),"PF8\n",compile_public(arch,PF8_HARNESS,pf8),"PF16\n",compile_public(arch,PF16_HARNESS,pf16),"PF32\n",compile_public(arch,PF32_HARNESS,PF32_INPUT)]
  stdout="".join(chunks)
 digest=hashlib.sha256(stdout.encode()).hexdigest()
 if RUN_SHA256 and digest!=RUN_SHA256: raise RuntimeError(f"transcript drift: {digest}")
 return {"schema":"olmsmoother2.current-installed-public/1","status":STATUS,"claim_boundary":CLAIM,"authorities":live,"summary":SUMMARY,"run_sha256":digest,"run_lines":stdout.splitlines(),"after_effects_processes":[],"scope":SCOPE}
def validate(report):
 if set(report)!=TOP_KEYS or report["schema"]!="olmsmoother2.current-installed-public/1" or report["status"]!=STATUS: raise RuntimeError("schema/status drift")
 if report["claim_boundary"]!=CLAIM or report["authorities"]!=PINS or report["summary"]!=SUMMARY or report["scope"]!=SCOPE: raise RuntimeError("claim/authority/summary/scope drift")
 if report["after_effects_processes"]!=[] or report["run_lines"][0]!="ARCH arm64" or "ARCH x86_64" not in report["run_lines"]: raise RuntimeError("process/row drift")
 digest=hashlib.sha256(("\n".join(report["run_lines"])+"\n").encode()).hexdigest()
 if RUN_SHA256 and (report["run_sha256"]!=RUN_SHA256 or digest!=RUN_SHA256): raise RuntimeError("transcript drift")
def markdown(report): return f"# OLMSmoother2 current installed complete Smart admission replay (2026-08-14)\n\nStatus: `{STATUS}`\n\n- Both Universal slices execute all 39 bounded Smart cells (78 installed-slice positives).\n- New installed matrices per slice: PF8 46 rows, PF16 24 rows, PF32 24 rows.\n- World/Color suite, checkout/checkin, input immutability and atomic output controls pass.\n- x86_64 runs under Rosetta; AE was not launched.\n\nBoundary: {report['claim_boundary']}\n"
def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--write",action="store_true"); args=parser.parse_args(); fresh=generate(); validate(fresh)
 if args.write:
  REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n"); MARKDOWN.write_text(markdown(fresh))
 else:
  persisted=json.loads(REPORT.read_text()); validate(persisted)
  if fresh!=persisted or MARKDOWN.read_text()!=markdown(persisted): raise RuntimeError("persisted report drift")
 print(STATUS); return 0
if __name__=="__main__": raise SystemExit(main())
