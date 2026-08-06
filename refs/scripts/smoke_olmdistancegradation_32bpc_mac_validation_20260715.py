#!/usr/bin/env python3
"""Smoke the DistanceGradation Mac lane without launching After Effects."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RUNNER=ROOT/"scripts/run_olmdistancegradation_32bpc_mac_validation_20260715.py"; REQUEST=ROOT/"refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json"
def main()->int:
    d=json.loads(REQUEST.read_text()); assert d["candidate_case_count"]==29; assert d["ae_contract"]["outputs"]==["no_effect","effect_on"]; assert d["acceptance"]["epsilon"]==0; assert "FLOAT32" in d["acceptance"]["comparison"]
    with tempfile.TemporaryDirectory(prefix="olmdistancegradation_mac_smoke_") as t:
        root=Path(t); dump=root/"wrapper.jsx"; wrong=root/"wrong.plugin"; p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(wrong),"--dump-js",str(dump)],cwd=ROOT,text=True,capture_output=True); assert p.returncode==2 and not dump.exists()
        plugin=root/"OLMDistanceGradation.plugin";(plugin/"Contents/MacOS").mkdir(parents=True);(plugin/"Contents/MacOS/OLMDistanceGradation").write_bytes(b"smoke");p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(plugin),"--support-dir",str(root/"support"),"--dump-js",str(dump)],cwd=ROOT,text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
        jsx=(root/"support"/"run_mac_olmdistancegradation_32bpc_validation.jsx").read_text()
        for token in ("GpuAccelType.SOFTWARE","bitsPerChannel","workingSpace","OLM_AE_MAC_PLUGIN_BUNDLE","OLM_AE_MAC_PLUGIN_EXECUTABLE","656537d052f67a9e7eb4d4ba2c6f5c890fe34e3d2c47069bcfba01854d96055e","OLM EXR 32 Float","getSettings(GetSettingsFormat.STRING)","no_effect","effect_on","OLMDistanceGradation.plugin","FAIL_CLOSED"): assert token in jsx,token
    print("[OK] OLMDistanceGradation 32bpc Mac lane smoke passed without launching AE");return 0
if __name__=="__main__": raise SystemExit(main())
