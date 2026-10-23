#!/usr/bin/env python3
"""Replay the current installed DistanceGradation PF32 Mode5/Power boundary."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset
import argparse,hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES={
 "probe":ROOT/"tools/emulation/probe_olmdistancegradation_current_installed_mode5_20260813.cpp",
 "source":ROOT/"mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
 "strings":ROOT/"mac/OLMDistanceGradation/OLMDistanceGradation_Strings.cpp",
 "fieldgen":ROOT/"core/olmdistancegradation_fieldgen.cpp","frontonly":ROOT/"core/dblur_frontonly.cpp",
 "rotate":ROOT/"core/dblur_rotate.cpp","rowdriver":ROOT/"core/dblur_rowdriver.cpp","field":ROOT/"core/dblur_field.cpp",
 "suite_cpp":resolve_asset(ROOT/"Util/AEGP_SuiteHandler.cpp"),"suite_h":resolve_asset(ROOT/"Util/AEGP_SuiteHandler.h"),"missing_cpp":resolve_asset(ROOT/"Util/MissingSuiteError.cpp"),"sdk_header":resolve_asset(ROOT/"Headers/AE_Effect.h"),
 "installed_binary":Path.home()/"Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation",
 "mode5_closure":ROOT/"refs/conformance/olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.json",
 "power_install_identity":ROOT/"refs/conformance/olmdistancegradation_power_failclose_incremental_install_identity_20260812.json"}
PINS={"probe":"ef0e7ccbb75d4d9d10c405306c2ee797d0f11e6d2cf3a5cad59e7d45533665f3","source":"06ffc5b7a2af5cf54a2503d3bf03f9baf2269acbf1277f034937ac79c4a7aba5","strings":"7c8e13d4490e67f9cb918199891d96831b50929d4faa87744830f1fa35d93dd8","fieldgen":"001493f40681ddf1f8408b15b25c5795500f84423019df6e51c30741dffb71c9","frontonly":"850e16884fb471ebcb313231a6d1c4593d33fc0d1cbebe18fa087166125ea2a5","rotate":"5b02748d421befb1ecda0fd36ff34c5b225ebee5e928e0460e1c14d174c101d7","rowdriver":"9f271073adaf2746a5144cf4793f0ebe574f51787705f265421710215596481d","field":"ccd409aea09f72fe8e274f58f6806fbf67628b7b56f414d3ed1bf820b2515ff1","suite_cpp":"7c054c7b0778b1b26463d6bf31cd57ee1d971946e8da22fb174e9f088741606f","suite_h":"36e1acf66a90979bd541bfb260e4dbf58dab2d00afec7d749dfcffc43a6843f7","missing_cpp":"8c0cc22b898c94c73556778f5cef1ccf9cded81ee590bd04feb49028ff4f44d9","sdk_header":"a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d","installed_binary":"231421e4a0c1607a70947778d99d748baefe07078b7e1145f4a4700268116605","mode5_closure":"d515135ac3b383d2f2a26d7df127d2526e63c5ddb4024141bade44ac395757ae","power_install_identity":"3623fb6fb6412836e00aba58b058ed0a319d43bfea84e9e27ecb3b773f417578"}
RUN_SHA256="bc3ec70ee1a1812574a07c35b7b13902c3d020a0f942b562996986a0eb52fb51"
STATUS="PASS_OLMDISTANCEGRADATION_CURRENT_INSTALLED_MODE5_6_POWER_FAILCLOSED_8_AE_FREE"
CLAIM="Both current installed Universal slices of DistanceGradation match their source-built real-SDK Smart path for six fixed17x11 PF32 Mode5 Constant/Linear/Sphere cells per slice, including padding and callback lifecycle. All eight PF32 Power cells per slice remain fail-closed with untouched output because native Windows UCRT powf has not been captured. The x86_64 route is executed under Rosetta. This AE-free dlopen replay does not generalize beyond the fixed contract or claim native After Effects."
SUMMARY={"architectures":["arm64","x86_64"],"mode5_positive_cells_per_slice":6,"mode5_positive_cells_total":12,"power_fail_closed_cells_per_slice":8,"power_fail_closed_cells_total":16,"source_installed_byte_identical":True,"power_output_untouched":True}
SCOPE={"installed_arm64":True,"installed_x86_64":True,"native_after_effects":False,"native_windows_ucrt_powf":False,"arbitrary_tuple_or_source":False}
REPORT=ROOT/"refs/conformance/olmdistancegradation_current_installed_mode5_20260813.json";MARKDOWN=REPORT.with_suffix(".md")
TOP={"schema","status","claim_boundary","authorities","summary","run_sha256","run_lines","after_effects_processes","scope"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def authorities():return {k:sha(v) for k,v in FILES.items()}
def ae_processes():
 out=[]
 for n in ("After Effects","AfterFX","aerender"):
  r=subprocess.run(["pgrep","-x",n],text=True,capture_output=True)
  if r.returncode==0:out += [f"{n}:{pid}" for pid in r.stdout.split()]
 return out
def compile_run(arch):
 with tempfile.TemporaryDirectory(prefix="dg-installed-mode5-") as td:
  exe=Path(td)/"probe";sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip();cmd=["clang++","-std=c++17","-arch",arch,"-O2","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations"]
  for inc in ("Headers","Headers/SP","Util","Resources","core","mac/OLMDistanceGradation"):cmd += ["-I",str(ROOT/inc)]
  cmd += [str(FILES[k]) for k in ("probe","strings","suite_cpp","missing_cpp","frontonly","rotate","rowdriver","field","fieldgen")]+["-framework","Cocoa","-o",str(exe)]
  b=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  if b.returncode:raise RuntimeError(b.stdout+b.stderr)
  env=os.environ.copy();env["OLMDISTANCEGRADATION_INSTALLED_BINARY"]=str(FILES["installed_binary"]);r=subprocess.run([str(exe)],cwd=ROOT,env=env,text=True,capture_output=True)
  if r.returncode or r.stderr:raise RuntimeError(f"probe rc={r.returncode}: {r.stdout} {r.stderr}")
  return r.stdout
def generate():
 live=authorities()
 if live!=PINS:raise RuntimeError(f"authority drift: {live}")
 processes=ae_processes()
 if processes:raise RuntimeError(f"After Effects must remain stopped: {processes}")
 stdout="".join(f"ARCH {arch}\n"+compile_run(arch) for arch in ("arm64","x86_64"))
 if sha_bytes(stdout.encode())!=RUN_SHA256:raise RuntimeError("transcript drift")
 return {"schema":"olmdistancegradation.current-installed-mode5/1","status":STATUS,"claim_boundary":CLAIM,"authorities":live,"summary":SUMMARY,"run_sha256":RUN_SHA256,"run_lines":stdout.splitlines(),"after_effects_processes":[],"scope":SCOPE}
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def validate(r):
 if set(r)!=TOP or r["schema"]!="olmdistancegradation.current-installed-mode5/1" or r["status"]!=STATUS:raise RuntimeError("schema/status drift")
 if r["claim_boundary"]!=CLAIM or r["authorities"]!=PINS or r["summary"]!=SUMMARY or r["scope"]!=SCOPE or r["after_effects_processes"]!=[]:raise RuntimeError("claim/authority/scope drift")
 if len(r["run_lines"])!=44 or r["run_lines"][0]!="ARCH arm64" or r["run_lines"][22]!="ARCH x86_64" or r["run_sha256"]!=RUN_SHA256 or sha_bytes(("\n".join(r["run_lines"])+"\n").encode())!=RUN_SHA256:raise RuntimeError("transcript drift")
def markdown(r):return f"# DistanceGradation current installed Mode5 boundary (2026-08-13)\n\nStatus: `{STATUS}`\n\n- Both Universal slices, fixed17x11 PF32 Mode5 Constant/Linear/Sphere × background off/on: 6/6 installed/source exact per slice.\n- Both slices, PF32 Power blur modes 2/3/4/5 × background off/on: 8/8 fail-closed per slice, output untouched.\n- x86_64 executes under Rosetta; AE was not launched.\n\nBoundary: {r['claim_boundary']}\n"
def main():
 p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args();fresh=generate();validate(fresh)
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");MARKDOWN.write_text(markdown(fresh))
 else:
  saved=json.loads(REPORT.read_text());validate(saved)
  if fresh!=saved or MARKDOWN.read_text()!=markdown(saved):raise RuntimeError("persisted drift")
 print(STATUS);return 0
if __name__=="__main__":raise SystemExit(main())
