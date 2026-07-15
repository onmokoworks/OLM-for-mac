#!/usr/bin/env python3
"""Smoke the OLMBlur Mac request/runner contract without launching AE."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/"scripts/run_olmblur_32bpc_mac_validation_20260715.py"
REQUEST=ROOT/"refs/mac_validation_requests/olmblur_32bpc_mac_validation_20260715.json"
def main()->int:
    data=json.loads(REQUEST.read_text()); assert data["status"]=="request_only_no_ae_exact_claim"; assert data["case"]["id"]=="olmblur__case_0001"; assert len(data["case"]["effect"]["params"])==7
    assert data["ae_contract"]=={"major_minor":"26.3","bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False,"frame":0,"output_template":"OLM EXR 32 Float","output_module_settings_capture_api":"OutputModule.getSettings(GetSettingsFormat.STRING)","output_format":"OpenEXR","channels":["A","B","G","R"],"sample_type":"FLOAT","compression":"none","outputs":["no_effect","effect_on"]}
    with tempfile.TemporaryDirectory(prefix="olmblur_mac_smoke_") as t:
        dump=Path(t)/"wrapper.jsx"; p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(Path(t)/"wrong.plugin"),"--dump-js",str(dump)],cwd=ROOT,capture_output=True,text=True); assert p.returncode==2 and not dump.exists()
        plugin=Path(t)/"OLMBlur.plugin"; binary=plugin/"Contents"/"MacOS"/"OLMBlur"; binary.parent.mkdir(parents=True); binary.write_bytes(b"smoke only")
        p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(plugin),"--support-dir",str(Path(t)/"support"),"--dump-js",str(dump)],cwd=ROOT,capture_output=True,text=True); assert p.returncode==0, p.stdout+p.stderr
        assert dump.exists(); jsx=(Path(t)/"support"/"run_mac_olmblur_32bpc_validation.jsx").read_text()
        wrapper=dump.read_text()
        for token in ("GpuAccelType.SOFTWARE","bitsPerChannel","OLM_AE_MAC_PLUGIN_PATH","OLM_AE_MAC_PLUGIN_BINARY","OLM EXR 32 Float","getSettings(GetSettingsFormat.STRING)","clearRenderedFiles","rendered output cardinality","no_effect","effect_on","loadedPlugin","FAIL_CLOSED"):
            assert token in jsx, token
        assert "OLM_AE_MAC_PLUGIN_BINARY" in wrapper
        assert "error.txt" in wrapper and "e.line" in wrapper
        runner=RUNNER.read_text(encoding="utf-8")
        for token in ("vmmap_exact_path", "binary_predates_process_start", "modified after After Effects started", "loaded_plugin_proof"):
            assert token in runner, token
        for token in ("value:p.value", "requested_params:spec.effect.params", "params:parameterReadback", "re.escape(resolved)"):
            assert token in runner, token
    assert not any("case0006_mac_observation" in str(p) for p in [RUNNER])
    print("[OK] OLMBlur 32bpc Mac request smoke passed without launching AE"); return 0
if __name__=="__main__": raise SystemExit(main())
