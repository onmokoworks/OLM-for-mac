#!/usr/bin/env python3
"""Smoke the Mac ToonDilate package without launching AE."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
GEN=ROOT/"scripts/package_olmtoondilate_mac_32bpc_validation_20260715.py"
RUN=ROOT/"refs/scripts/run_olmtoondilate_mac_32bpc_validation_20260715.py"
def main():
  with tempfile.TemporaryDirectory(prefix="toondilate_mac_smoke_") as d:
    out=Path(d)/"package"; subprocess.run([sys.executable,str(GEN),"--output-dir",str(out)],cwd=ROOT,check=True,capture_output=True,text=True)
    req=json.loads((out/"request_manifest.json").read_text()); assert req["case"]["effect"]=="OLM Toon Dilate"; assert req["project"]=={"bits_per_channel":32,"working_space":"None","linear_blending":False}
    fixture=(out/"fixture/ae_generate_32bpc_olmtoondilate_fixture.jsx").read_text();
    for token in ("OLM Toon Dilate","OutputModule.getSettings(GetSettingsFormat.STRING)","GpuAccelType.SOFTWARE","project.bitsPerChannel = 32","project.linearBlending = false"):
      assert token in fixture, token
    proc=subprocess.run([sys.executable,str(RUN),"--package",str(out)],cwd=ROOT,text=True,capture_output=True); assert proc.returncode==0,proc.stderr
    report=json.loads((out/"mac_run/validation_report.json").read_text()); assert report["status"]=="blocked" and report["ae_exact"] is False
    proc=subprocess.run([sys.executable,str(RUN),"--package",str(out),"--execute"],cwd=ROOT,text=True,capture_output=True); assert proc.returncode!=0; assert "FAIL CLOSED" in proc.stderr+proc.stdout
  print("[OK] isolated ToonDilate Mac 32bpc package smoke")
if __name__=="__main__": main()
