#!/usr/bin/env python3
"""Replay DirectionalBlur's fixed dual-side Type2 route through the installed Mach-O."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
FILES={"probe":ROOT/"tools/emulation/probe_olmdirectionalblur_current_installed_dual_side_20260813.cpp","source":ROOT/"mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp","strings":ROOT/"mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp","frontonly":ROOT/"core/dblur_frontonly.cpp","rotate":ROOT/"core/dblur_rotate.cpp","rowdriver":ROOT/"core/dblur_rowdriver.cpp","field":ROOT/"core/dblur_field.cpp","suite_cpp":ROOT/"Util/AEGP_SuiteHandler.cpp","suite_h":ROOT/"Util/AEGP_SuiteHandler.h","missing_cpp":ROOT/"Util/MissingSuiteError.cpp","sdk_header":ROOT/"Headers/AE_Effect.h","installed_binary":Path.home()/"Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur","source_guard":ROOT/"refs/conformance/olmdirectionalblur_dual_side_public_source_guard_closure_20260813.json","fixture_png":ROOT/"refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png","build_identity":ROOT/"handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/build_identity.json","install_identity":ROOT/"handoffs/olmdirectionalblur_testseam_compat_install_20260814/install_transaction.json","all10_authority":ROOT/"refs/conformance/olm_installed_identity_manifest_20260806.json"}
PINS={"probe":"da328189a619f9d245a4780b353a2d17d5559718a8b0c074a0d6c1eb05a7c377","source":"494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845","strings":"a9898e0e2cdd9d9c4e6f234c680081f68bb229772254a10ab1c1810fbf348daf","frontonly":"850e16884fb471ebcb313231a6d1c4593d33fc0d1cbebe18fa087166125ea2a5","rotate":"5b02748d421befb1ecda0fd36ff34c5b225ebee5e928e0460e1c14d174c101d7","rowdriver":"9f271073adaf2746a5144cf4793f0ebe574f51787705f265421710215596481d","field":"ccd409aea09f72fe8e274f58f6806fbf67628b7b56f414d3ed1bf820b2515ff1","suite_cpp":"7c054c7b0778b1b26463d6bf31cd57ee1d971946e8da22fb174e9f088741606f","suite_h":"36e1acf66a90979bd541bfb260e4dbf58dab2d00afec7d749dfcffc43a6843f7","missing_cpp":"8c0cc22b898c94c73556778f5cef1ccf9cded81ee590bd04feb49028ff4f44d9","sdk_header":"a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d","installed_binary":"856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de","source_guard":"813013833b2a276de0513a567fb53d638a5ec2866868ba8c59a495550520a7b2","fixture_png":"cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4","build_identity":"ddc9256d6ca78eec2f521335573589f7c626ae5827927a3399ea64d3a1934eff","install_identity":"237cb44594e15267e5d397c348b2ec4c8fefef06ad81eb8d0ed1db86da96f9fe","all10_authority":"94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650"}
RUN_SHA="3443333ffec2b2e40f8de2f152f20956c42678a65d65a058a663671432b33e0c";STATUS="PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_DUAL_SIDE_TYPE2_ALL_DEPTHS_AE_FREE";CLAIM="Both current installed Universal slices of DirectionalBlur match their source-built real-SDK SmartPreRender to SmartRender route for the fixed 32x18 dual-side Type2 tuple at PF8, PF16 and PF32, including 21 parameter checkout/checkin operations, input/noise optional lifecycle, padding and input immutability. Per-depth source-bit mutations fail closed with untouched output on each slice. The x86_64 route is executed under Rosetta. This is AE-free dlopen evidence and does not generalize the fixed actual-AEX source/tuple contract or claim native After Effects.";SUMMARY={"architectures":["arm64","x86_64"],"positive_cells_per_slice":3,"positive_cells_total":6,"source_mutation_rejects_per_slice":3,"depths":[8,16,32],"source_installed_byte_identical":True};SCOPE={"installed_arm64":True,"installed_x86_64":True,"native_after_effects":False,"arbitrary_source_tuple_geometry":False};REPORT=ROOT/"refs/conformance/olmdirectionalblur_current_installed_dual_side_20260813.json";MD=REPORT.with_suffix(".md");TOP={"schema","status","claim_boundary","authorities","summary","run_sha256","run_lines","after_effects_processes","scope"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def auth():return {k:sha(v) for k,v in FILES.items()}
def ae():
 out=[]
 for n in ("After Effects","AfterFX","aerender"):
  r=subprocess.run(["pgrep","-x",n],text=True,capture_output=True)
  if r.returncode==0:out += [f"{n}:{p}" for p in r.stdout.split()]
 return out
def compile_run(arch):
 with tempfile.TemporaryDirectory(prefix="directional-installed-") as td:
  d=Path(td);rgba=d/"rgba.bin";rgba.write_bytes(Image.open(FILES["fixture_png"]).convert("RGBA").crop((472,262,504,280)).tobytes());exe=d/"probe";sdk=subprocess.check_output(["xcrun","--show-sdk-path"],text=True).strip();cmd=["clang++","-std=c++17","-arch",arch,"-O2","-fno-fast-math","-ffp-contract=off","-isysroot",sdk,"-Wno-pragma-pack","-Wno-deprecated-declarations"]
  for inc in ("Headers","Headers/SP","Util","Resources","core","mac/OLMDirectionalBlur"):cmd += ["-I",str(ROOT/inc)]
  cmd += [str(FILES[k]) for k in ("probe","strings","suite_cpp","missing_cpp","frontonly","rotate","rowdriver","field")]+["-framework","Cocoa","-o",str(exe)]
  b=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
  if b.returncode:raise RuntimeError(b.stdout+b.stderr)
  r=subprocess.run([str(exe),str(FILES["installed_binary"]),str(rgba)],cwd=ROOT,text=True,capture_output=True)
  if r.returncode or r.stderr:raise RuntimeError(f"probe rc={r.returncode}: {r.stdout} {r.stderr}")
  return r.stdout
def generate():
 a=auth()
 if a!=PINS:raise RuntimeError(f"authority drift: {a}")
 processes=ae()
 if processes:raise RuntimeError(f"After Effects must remain stopped: {processes}")
 out="".join(f"ARCH {arch}\n"+compile_run(arch) for arch in ("arm64","x86_64"))
 if hashlib.sha256(out.encode()).hexdigest()!=RUN_SHA:raise RuntimeError("transcript drift")
 return {"schema":"olmdirectionalblur.current-installed-dual-side/1","status":STATUS,"claim_boundary":CLAIM,"authorities":a,"summary":SUMMARY,"run_sha256":RUN_SHA,"run_lines":out.splitlines(),"after_effects_processes":[],"scope":SCOPE}
def validate(r):
 if set(r)!=TOP or r["schema"]!="olmdirectionalblur.current-installed-dual-side/1" or r["status"]!=STATUS:raise RuntimeError("schema/status drift")
 if r["claim_boundary"]!=CLAIM or r["authorities"]!=PINS or r["summary"]!=SUMMARY or r["scope"]!=SCOPE or r["after_effects_processes"]!=[]:raise RuntimeError("claim/authority/scope drift")
 if len(r["run_lines"])!=16 or r["run_lines"][0]!="ARCH arm64" or r["run_lines"][8]!="ARCH x86_64" or r["run_sha256"]!=RUN_SHA or hashlib.sha256(("\n".join(r["run_lines"])+"\n").encode()).hexdigest()!=RUN_SHA:raise RuntimeError("transcript drift")
def markdown(r):return f"# DirectionalBlur current installed dual-side replay (2026-08-13)\n\nStatus: `{STATUS}`\n\n- Both Universal slices, fixed 32x18 dual-side Type2 at PF8/PF16/PF32: 3/3 exact per slice.\n- Per-depth source-bit mutations: 3/3 fail-closed and output untouched per slice.\n- SmartPre/Smart lifecycle, 21 params, padding and input immutability are exact.\n- x86_64 executes under Rosetta; AE was not launched.\n\nBoundary: {r['claim_boundary']}\n"
def main():
 p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args();fresh=generate();validate(fresh)
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");MD.write_text(markdown(fresh))
 else:
  saved=json.loads(REPORT.read_text());validate(saved)
  if fresh!=saved or MD.read_text()!=markdown(saved):raise RuntimeError("persisted drift")
 print(STATUS);return 0
if __name__=="__main__":raise SystemExit(main())
