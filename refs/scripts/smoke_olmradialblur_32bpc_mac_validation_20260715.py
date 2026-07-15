#!/usr/bin/env python3
"""Smoke the RadialBlur Mac runner/reporter contract without launching AE."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/"scripts/run_olmradialblur_32bpc_mac_validation_20260715.py"
REQUEST=ROOT/"refs/mac_validation_requests/olmradialblur_32bpc_mac_validation_20260715.json"
def main()->int:
    d=json.loads(REQUEST.read_text()); assert d["ae_exact_claim"] is False; assert [c["blur_type"] for c in d["cases"]]==["Zoom","Rotation"]; assert len(d["cases"])==2
    for c in d["cases"]: assert len(c["params"])==23; assert len(c["input_sha256"])==64
    with tempfile.TemporaryDirectory(prefix="olmradialblur_mac_smoke_") as raw:
        t=Path(raw); bad=t/"wrong.plugin"; p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(bad),"--dump-js",str(t/"bad.jsx")],cwd=ROOT,text=True,capture_output=True); assert p.returncode==2 and not (t/"bad.jsx").exists()
        plugin=t/"OLMRadialBlur.plugin"; plugin.write_bytes(b"smoke only"); dump=t/"wrapper.jsx"; p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(plugin),"--support-dir",str(t/"support"),"--dump-js",str(dump)],cwd=ROOT,text=True,capture_output=True); assert p.returncode==0,p.stdout+p.stderr
        jsx=(t/"support"/"run_mac_olmradialblur_32bpc_validation.jsx").read_text(); assert jsx.count("params_full")>=2
        for token in ("GpuAccelType.SOFTWARE","bitsPerChannel","OLMRadialBlur.plugin","OLM EXR 32 Float","getSettings(GetSettingsFormat.STRING)","no_effect_control","effect_on","params_sha256","FAIL_CLOSED"): assert token in jsx,token
    print("[OK] OLMRadialBlur 32bpc Mac request smoke passed without launching AE"); return 0
if __name__=="__main__": raise SystemExit(main())
