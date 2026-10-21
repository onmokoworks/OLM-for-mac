#!/usr/bin/env python3
"""Replay ColorKeep count9 through the current installed public entries."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,subprocess,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
UPSTREAM=ROOT/"tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py";UPSTREAM_REPORT=ROOT/"refs/conformance/colorkeep_nine_color_public_closure_20260813.json";SOURCE=ROOT/"mac/ColorKeep/ColorKeep.cpp";INSTALL_REPORT=ROOT/"refs/conformance/colorkeep_count9_incremental_install_identity_20260813.json";INSTALLED=Path.home()/"Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin/Contents/MacOS/ColorKeep";REPORT=ROOT/"refs/conformance/colorkeep_current_installed_count9_20260813.json";MD=REPORT.with_suffix(".md")
PINS={"upstream_generator":"a647aa543e442a1ebc15269ab7b60e28884e518dc6c5b7678786655bfce84737","upstream_report":"3baaeef9aaf54aa89b7ec141b23cf369a78a291bed33b9b1e3b358eca990f071","source":"3ff3a4d4319f5b3b5519e517fcf591be417c97e4e9dd62117fe4e42f66ebdfd3","installed_binary":"fcd501dae5e62aaa0bb8c022cc55c3a6735e3021d465b42b80c939f33624dd77","install_report":"789722f224425fe1eedb3a3a73c34f1d7b5c86309cb36f0d189bd2eafa58bcc8"}
STATUS="PASS_COLORKEEP_CURRENT_INSTALLED_COUNT9_PUBLIC5_REJECT136_AE_FREE";OUTPUT_SHA="2e68fc7a643641652edb27b6400cbdb2358b10c438893a8c346f8efd1ef7aebe";CLAIM="Both current installed Universal slices of ColorKeep reproduce the pinned count9 public contract at Classic PF8/PF16 and Smart PF8/PF16/PF32, and all 136 canonical reject controls remain precommit-atomic on each slice. The x86_64 route runs under Rosetta. The output relation is also live-checked against the pinned Windows exported Smart owner hashes. This is AE-free dlopen evidence limited to the exact 4x3 source, palette, parameters and layout.";SUMMARY={"architectures":["arm64","x86_64"],"public_paths_per_slice":5,"public_paths_total":10,"smart_depths":[8,16,32],"classic_depths":[8,16],"reject_controls_per_slice":136,"reject_controls_total":272,"positive_bytes_per_slice":600,"positive_sha256_per_slice":OUTPUT_SHA};SCOPE={"installed_arm64":True,"installed_x86_64":True,"native_after_effects":False,"arbitrary_source_palette_tuple":False};TOP={"schema","status","claim_boundary","authorities","summary","owner_rows","negative","after_effects_processes","scope"}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def auth():return {"upstream_generator":sha(UPSTREAM),"upstream_report":sha(UPSTREAM_REPORT),"source":sha(SOURCE),"installed_binary":sha(INSTALLED),"install_report":sha(INSTALL_REPORT)}
def load():s=importlib.util.spec_from_file_location("ck9",UPSTREAM);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m);return m
def load_for_arch(arch):
 if arch=="arm64":return load()
 if arch!="x86_64":raise RuntimeError(f"unsupported architecture: {arch}")
 text=UPSTREAM.read_text();needle='cmd=["clang++","-std=c++17","-arch","arm64",'
 if text.count(needle)!=1:raise RuntimeError("upstream architecture anchor drift")
 module=types.ModuleType("ck9_x86_64");module.__file__=str(UPSTREAM)
 exec(compile(text.replace(needle,'cmd=["clang++","-std=c++17","-arch","x86_64",'),str(UPSTREAM),"exec"),module.__dict__)
 return module
def ae():
 out=[]
 for n in ("After Effects","AfterFX","aerender"):
  r=subprocess.run(["pgrep","-x",n],text=True,capture_output=True)
  if r.returncode==0:out += [f"{n}:{p}" for p in r.stdout.split()]
 return out
def generate():
 a=auth()
 if a!=PINS:raise RuntimeError(f"authority drift: {a}")
 processes=ae()
 if processes:raise RuntimeError(f"After Effects must remain stopped: {processes}")
 m=load();inputs,outputs,rows=m.fresh_oracle();expected=outputs["PF8"]+outputs["PF16"]+outputs["PF8"]+outputs["PF16"]+outputs["PF32"];negative={}
 for arch in ("arm64","x86_64"):
  observed,one=load_for_arch(arch).probe(INSTALLED,inputs)
  if observed!=expected or hashlib.sha256(observed).hexdigest()!=OUTPUT_SHA or one!={"rejects":136,"all_precommit_atomic":True}:raise RuntimeError(f"installed count9 relation drift for {arch}")
  negative[arch]=one
 owner=[{"depth":r["depth"],"raw_sha256":r["raw_sha256"]} for r in rows]
 return {"schema":"colorkeep.current-installed-count9/1","status":STATUS,"claim_boundary":CLAIM,"authorities":a,"summary":SUMMARY,"owner_rows":owner,"negative":negative,"after_effects_processes":[],"scope":SCOPE}
def validate(r):
 if set(r)!=TOP or r["schema"]!="colorkeep.current-installed-count9/1" or r["status"]!=STATUS:raise RuntimeError("schema/status drift")
 if r["claim_boundary"]!=CLAIM or r["authorities"]!=PINS or r["summary"]!=SUMMARY or r["scope"]!=SCOPE or r["after_effects_processes"]!=[]:raise RuntimeError("claim/authority/scope drift")
 expected=[{"depth":"PF8","raw_sha256":"ad5a9e2d70f0adcc6318d340b3fa47ef4b5d89e79d9827554197da41d81da3dd"},{"depth":"PF16","raw_sha256":"67b738b61c8197b32885019e6395612b7d065b42c8efd5070fc0ab3e84637392"},{"depth":"PF32","raw_sha256":"5304a3f80f4ed6be0e210e9d925ac4fa7350feacb1035778a0adfc3edec9f469"}]
 if r["owner_rows"]!=expected or r["negative"]!={arch:{"rejects":136,"all_precommit_atomic":True} for arch in ("arm64","x86_64")}:raise RuntimeError("owner/negative drift")
def markdown(r):return f"# ColorKeep current installed count9 replay (2026-08-13)\n\nStatus: `{STATUS}`\n\n- Both Universal slices, Classic PF8/PF16 and Smart PF8/PF16/PF32: 5/5 exact per slice.\n- Windows exported Smart owner hashes are live-checked.\n- Canonical rejects: 136/136 precommit-atomic per slice.\n- x86_64 runs under Rosetta; AE was not launched.\n\nBoundary: {r['claim_boundary']}\n"
def main():
 p=argparse.ArgumentParser();p.add_argument("--write",action="store_true");a=p.parse_args();fresh=generate();validate(fresh)
 if a.write:REPORT.write_text(json.dumps(fresh,indent=2,sort_keys=True)+"\n");MD.write_text(markdown(fresh))
 else:
  saved=json.loads(REPORT.read_text());validate(saved)
  if fresh!=saved or MD.read_text()!=markdown(saved):raise RuntimeError("persisted drift")
 print(STATUS);return 0
if __name__=="__main__":raise SystemExit(main())
