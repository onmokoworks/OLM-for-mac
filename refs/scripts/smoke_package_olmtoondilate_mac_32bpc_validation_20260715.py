#!/usr/bin/env python3
"""Smoke the Mac ToonDilate package without launching AE."""
from __future__ import annotations
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
GEN=ROOT/"scripts/package_olmtoondilate_mac_32bpc_validation_20260715.py"
RUN=ROOT/"refs/scripts/run_olmtoondilate_mac_32bpc_validation_20260715.py"
COMPARE=ROOT/"refs/scripts/compare_olmtoondilate_mac_32bpc_validation_20260715.py"
PLUGIN_BINARY=ROOT/"mac/OLMToonDilate/Mac/build/Debug/OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"

def archs(path):
  proc=subprocess.run(["lipo","-archs",str(path)],cwd=ROOT,check=True,text=True,capture_output=True)
  return sorted({token for token in proc.stdout.split() if token})

def main():
  with tempfile.TemporaryDirectory(prefix="toondilate_mac_smoke_") as d:
    spec=importlib.util.spec_from_file_location("olmtoondilate_run_validation",RUN); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert Path(module.PACKAGE)==ROOT/"refs/runtime_trace_packages/olmtoondilate_mac_32bpc_validation_20260715"
    out=Path(d)/"package"; subprocess.run([sys.executable,str(GEN),"--output-dir",str(out)],cwd=ROOT,check=True,capture_output=True,text=True)
    req=json.loads((out/"request_manifest.json").read_text()); assert req["case"]["effect"]=="OLM Toon Dilate"; assert req["project"]=={"bits_per_channel":32,"working_space":"None","linear_blending":False}
    plugin=req["case"]["plugin"]; assert plugin["binary"]=="Contents/MacOS/OLMToonDilate"; assert len(plugin["sha256"])==64
    provenance=plugin["candidate_provenance"]; assert provenance["build_architectures"]==archs(PLUGIN_BINARY)
    assert set(provenance["source_sha256"])=={
      "mac/OLMToonDilate/OLMToonDilate.cpp","mac/OLMToonDilate/OLMToonDilate.h",
      "mac/OLMToonDilate/OLMToonDilatePiPL.r","mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj/project.pbxproj",
    }; assert all(len(value)==64 for value in provenance["source_sha256"].values())
    fixture=(out/"fixture/ae_generate_32bpc_olmtoondilate_fixture.jsx").read_text();
    for token in ("OLM Toon Dilate","OutputModule.getSettings(GetSettingsFormat.STRING)","GpuAccelType.SOFTWARE","project.bitsPerChannel = 32","project.linearBlending = false"):
      assert token in fixture, token
    proc=subprocess.run([sys.executable,str(RUN),"--package",str(out)],cwd=ROOT,text=True,capture_output=True); assert proc.returncode==0,proc.stderr
    report=json.loads((out/"mac_run/validation_report.json").read_text()); assert report["status"]=="blocked" and report["ae_exact"] is False
    proc=subprocess.run([sys.executable,str(RUN),"--package",str(out),"--execute"],cwd=ROOT,text=True,capture_output=True); assert proc.returncode!=0; assert "FAIL CLOSED" in proc.stderr+proc.stdout
    fixture_sha="f"*64
    base_case={
      "id": req["case"]["id"], "fixture_contract": req["fixture_contract"],
      "output_module": {"template_name":"OLM EXR 32 Float","capture_api":"OutputModule.getSettings(GetSettingsFormat.STRING)","settings_sha256":"a"*64},
      "outputs": {"no_effect":{"path":"missing1.exr","sha256":"0"*64},"effect_on":{"path":"missing2.exr","sha256":"1"*64}},
    }
    mac_record={"platform":"macos","required_ae_major_minor":"26.3","ae_version":"26.3x1","output_template":"OLM EXR 32 Float","renderer_class":"SOFTWARE","linear_blending":False,"fixture_jsx_sha256":fixture_sha,"cases":[dict(base_case, plugin={"name":"OLMToonDilate.plugin","sha256":req["case"]["plugin"]["sha256"]})]}
    win_record={"platform":"windows","required_ae_major_minor":"26.3","ae_version":"26.3x1","output_template":"OLM EXR 32 Float","renderer_class":"SOFTWARE","linear_blending":False,"fixture_jsx_sha256":fixture_sha,"cases":[dict(base_case, plugin={"name":"OLMToonDilate.aex","sha256":"c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"})]}
    mac_path=Path(d)/"mac_record.json"; win_path=Path(d)/"windows_record.json"
    mac_path.write_text(json.dumps(mac_record), encoding="utf-8"); win_path.write_text(json.dumps(win_record), encoding="utf-8")
    proc=subprocess.run([sys.executable,str(COMPARE),str(mac_path),str(win_path),"--package",str(out),"--json"],cwd=ROOT,text=True,capture_output=True)
    assert proc.returncode!=0; assert "FLOAT EXR output missing" in proc.stderr+proc.stdout
    mac_record["cases"][0]["plugin"]["sha256"]="0"*64; mac_path.write_text(json.dumps(mac_record), encoding="utf-8")
    proc=subprocess.run([sys.executable,str(COMPARE),str(mac_path),str(win_path),"--package",str(out),"--json"],cwd=ROOT,text=True,capture_output=True)
    assert proc.returncode!=0; assert "mac plugin identity/hash drifted" in proc.stderr+proc.stdout
    mac_record["cases"][0]["plugin"]["sha256"]=req["case"]["plugin"]["sha256"]; mac_path.write_text(json.dumps(mac_record), encoding="utf-8")
    win_record["cases"][0]["plugin"]["sha256"]="1"*64; win_path.write_text(json.dumps(win_record), encoding="utf-8")
    proc=subprocess.run([sys.executable,str(COMPARE),str(mac_path),str(win_path),"--package",str(out),"--json"],cwd=ROOT,text=True,capture_output=True)
    assert proc.returncode!=0; assert "windows plugin identity/hash drifted" in proc.stderr+proc.stdout
    runner=RUN.read_text(encoding="utf-8")
    for token in ("Adobe After Effects 2026","pgrep\", \"-x\", \"After Effects","vmmap_exact_path","binary_predates_process_start","re.escape(resolved)","Contents/MacOS/OLMToonDilate"):
      assert token in runner, token
  print("[OK] isolated ToonDilate Mac 32bpc package smoke")
if __name__=="__main__": main()
