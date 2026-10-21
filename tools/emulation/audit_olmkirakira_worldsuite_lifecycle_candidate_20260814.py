#!/usr/bin/env python3
"""Audit the source-bound Kira WorldSuite Universal candidate without AE."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, stat, subprocess
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
HANDOFF=ROOT/"handoffs/olmkirakira_worldsuite_lifecycle_candidate_20260814"
BUNDLE=HANDOFF/"Product/OLMKiraKira.plugin";BINARY=BUNDLE/"Contents/MacOS/OLMKiraKira"
SOURCE=ROOT/"mac/OLMKiraKira/OLMKiraKira.cpp"
PROJECT=ROOT/"mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj/project.pbxproj"
BASE=ROOT/"tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py"
BASE_REPORT=ROOT/"refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
SHIM=ROOT/"tools/emulation/olmkirakira_installed_effectmain_shim_20260813.h"
REPORT=HANDOFF/"build_identity.json";DOC=HANDOFF/"README.md"
PINS={"source":"f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2",
      "project":"81b2d4246a5dac6f0d8579cb545a7fd9ab201ee63d42a07ccfe544404aff4e4f",
      "base_report":"22ed602e6ba016a7f0fb5c36a13d74d082d656a66808e3606d330d4ef6fcf5c1",
      "candidate":"edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7"}
STATUS="PASS_OLMKIRAKIRA_WORLDSUITE_UNIVERSAL_CANDIDATE_42_765_3_NO_AE"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run(*a:str)->str:
 r=subprocess.run(a,text=True,capture_output=True)
 if r.returncode:raise RuntimeError(f"{a}: {r.stdout}{r.stderr}")
 return r.stdout+r.stderr
def inventory(root:Path)->list[dict[str,Any]]:
 return [{"path":p.relative_to(root).as_posix(),"size":p.stat().st_size,
          "mode":stat.S_IMODE(p.stat().st_mode),"sha256":sha(p)}
         for p in sorted(root.rglob("*")) if p.is_file()]
def load_base():
 s=importlib.util.spec_from_file_location("kira_candidate_base",BASE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def replay()->dict[str,Any]:
 m=load_base();old=m.SOURCE;env=os.environ.get("OLMKIRAKIRA_INSTALLED_BINARY")
 try:
  m.SOURCE=SHIM;os.environ["OLMKIRAKIRA_INSTALLED_BINARY"]=str(BINARY)
  cells,neg,req=m.run_harness()
 finally:
  m.SOURCE=old
  if env is None:os.environ.pop("OLMKIRAKIRA_INSTALLED_BINARY",None)
  else:os.environ["OLMKIRAKIRA_INSTALLED_BINARY"]=env
 dig={"positive_cells":m.canonical(cells),"negative_rows":m.canonical_negatives(neg),"request_controls":m.canonical_controls(req)}
 expected={"positive_cells":"112f5c2e11b84bff20ec961f046186e69a9e650e96cb5f1aec3449acfce2565a",
           "negative_rows":"a13a6b9b3e2372785a36566d4d0eff5aec905ab3b995f2574b384e9464378d28",
           "request_controls":"c205a7b68cc69db6520b9239e6af4babd54ae66d50fda53101185747b1cd4e68"}
 if dig!=expected:raise RuntimeError(f"candidate replay drift: {dig}")
 return {"positive_count":len(cells),"negative_count":len(neg),"request_count":len(req),"digests":dig}
def generate()->dict[str,Any]:
 live={"source":sha(SOURCE),"project":sha(PROJECT),"base_report":sha(BASE_REPORT),"candidate":sha(BINARY)}
 if live!=PINS:raise RuntimeError(f"candidate input drift: {live}")
 arch=run("lipo","-archs",str(BINARY)).strip().split()
 if arch!=["x86_64","arm64"]:raise RuntimeError("architecture drift")
 run("codesign","--verify","--deep","--strict",str(BUNDLE))
 builds=run("xcrun","vtool","-show-build",str(BINARY))
 minos=[x.split()[1] for x in builds.splitlines() if x.strip().startswith("minos ")]
 if minos!=["11.0","11.0"]:raise RuntimeError(f"minos drift: {minos}")
 exports={}
 for a in arch:
  names=run("nm","-arch",a,"-gU",str(BINARY)).split()
  exports[a]=sorted(x for x in ("_EffectMain","_PluginDataEntryFunction2") if x in names)
  if exports[a]!=["_EffectMain","_PluginDataEntryFunction2"]:raise RuntimeError("export drift")
 return {"schema":"olm.kirakira-worldsuite-candidate/1","status":STATUS,"authorities":live,
         "bundle":str(BUNDLE.relative_to(ROOT)),"architectures":arch,
         "minimum_versions":{"x86_64":"11.0","arm64":"11.0"},"exports":exports,
         "strict_deep_adhoc_codesign":True,"inventory":inventory(BUNDLE),"public_replay":replay(),
         "scope":{"installed":False,"native_ae":False,"developer_id_or_notarization":False}}
def validate(v:dict[str,Any])->None:
 assert set(v)=={"schema","status","authorities","bundle","architectures","minimum_versions","exports","strict_deep_adhoc_codesign","inventory","public_replay","scope"}
 assert v["schema"]=="olm.kirakira-worldsuite-candidate/1" and v["status"]==STATUS
 assert v["authorities"]==PINS and v["architectures"]==["x86_64","arm64"]
 assert v["minimum_versions"]=={"x86_64":"11.0","arm64":"11.0"}
 assert v["inventory"]==inventory(BUNDLE) and v["strict_deep_adhoc_codesign"] is True
 assert v["public_replay"]["positive_count"]==42 and v["public_replay"]["negative_count"]==765 and v["public_replay"]["request_count"]==3
 assert v["scope"]=={"installed":False,"native_ae":False,"developer_id_or_notarization":False}
def doc(v):return f"# OLMKiraKira WorldSuite candidate\n\nStatus: `{v['status']}`\n\nSource `{PINS['source']}`; executable `{PINS['candidate']}`. Universal minOS 11, strict-valid ad-hoc, and AE-free 42/765/3 public replay. Not installed and no native-AE claim.\n"
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--write",action="store_true");a=ap.parse_args();live=generate()
 if a.write:REPORT.write_text(json.dumps(live,indent=2,sort_keys=True)+"\n");DOC.write_text(doc(live))
 saved=json.loads(REPORT.read_text());validate(saved)
 if saved!=live or DOC.read_text()!=doc(saved):raise RuntimeError("candidate report drift")
 print(STATUS);return 0
if __name__=="__main__":raise SystemExit(main())
