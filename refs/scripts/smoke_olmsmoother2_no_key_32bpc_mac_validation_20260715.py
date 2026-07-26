#!/usr/bin/env python3
"""Smoke the OLMSmoother2 Mac request/runner without launching AE."""
from __future__ import annotations
import gzip, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RUNNER=ROOT/"scripts/run_olmsmoother2_no_key_32bpc_mac_validation_20260715.py"; REQUEST=ROOT/"refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json"
def main()->int:
    d=json.loads(REQUEST.read_text()); assert d["effect"]=={"name":"OLM Smoother v2","match_name":"OLM Smoother v2"}; assert d["scope"]["plugin_version_mode"]==2; assert len(d["cases"])==1; c=d["cases"][0]; assert c["params_full"][0]["value"]==0 and c["params_full"][6]["value"]==2; assert d["mac_run_contract"]["comparison"]["epsilon"]==0 and not d["mac_run_contract"]["comparison"]["normalization"]
    assert any("PF32 input-entry witness" in item for item in d["fail_closed"])
    win=d["windows_preserve_rgb_reference"]; manifest_path=ROOT/win["manifest"]; manifest=json.loads(manifest_path.read_text())
    assert manifest["kind"]=="olmsmoother2_case07_windows_ae_preserve_rgb_reference" and manifest["ae_exact_claim"] is False
    assert manifest["case_contract_sha256"]=="e8870b11b7a072b84fe8e4554c9e058468f15f7daf5b4be0d576d6b00a980403"
    assert manifest["output_module"]["aerender_omtemplate_override"] is False
    assert manifest["output_module"]["profile_observed"]==win["capture_contract"]["output_profile"]
    assert manifest["pf32_input_entry"]["same_run"] is True
    assert manifest["pf32_input_entry"]["same_run_effect_sha256"]==win["effect_sha256"]
    for key,name,sha in (("no_effect_control",win["no_effect_frame"],win["no_effect_sha256"]),("effect_on",win["effect_frame"],win["effect_sha256"])):
        assert manifest["artifacts"][key]["path"]==name and manifest["artifacts"][key]["sha256"]==sha
    entry=ROOT/win["pf32_input_entry_path"]; assert entry.is_file() and hashlib.sha256(entry.read_bytes()).hexdigest()==win["pf32_input_entry_stored_sha256"]
    with gzip.open(entry,"rb") as stream: entry_raw=stream.read()
    assert len(entry_raw)==33177600 and hashlib.sha256(entry_raw).hexdigest()==win["pf32_input_entry_uncompressed_sha256"]
    interpretation=d["mac_run_contract"]["input_interpretation"]; template=ROOT/interpretation["template"]; assert interpretation["preserve_rgb"] is True and template.is_file(); assert hashlib.sha256(template.read_bytes()).hexdigest()==interpretation["template_sha256"]
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_mac_smoke_") as t:
        root=Path(t); dump=root/"wrapper.jsx"; wrong=root/"wrong.plugin"; p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(wrong),"--dump-js",str(dump)],cwd=ROOT,text=True,capture_output=True); assert p.returncode==2 and not dump.exists()
        plugin=root/"OLMSmoother2.plugin"; binary=plugin/"Contents"/"MacOS"/"OLMSmoother2"; binary.parent.mkdir(parents=True); binary.write_bytes(b"smoke only"); p=subprocess.run([sys.executable,str(RUNNER),"--plugin-path",str(plugin),"--support-dir",str(root/"support"),"--dump-js",str(dump)],cwd=ROOT,text=True,capture_output=True); assert p.returncode==0,p.stdout+p.stderr
        jsx=(root/"support"/"run_mac_olmsmoother2_no_key_32bpc_validation.jsx").read_text(); wrapper=dump.read_text()
        for token in ("GpuAccelType.SOFTWARE","bitsPerChannel","OLMSmoother2.plugin","OLM EXR 32 Float","getSettings(GetSettingsFormat.STRING)","no_effect_control","effect_on","case_contract_sha256","hash_bound_aep_template_footage_replace","preserve_rgb:true","ft.replace(f)","FAIL_CLOSED"): assert token in jsx or token in wrapper, token
        assert "OLM_AE_MAC_PLUGIN_BINARY_PATH" in wrapper
        assert "OLM_AE_MAC_PROJECT_TEMPLATE" in wrapper
        assert "OLM_AE_MAC_PROJECT_TEMPLATE_SHA256" in wrapper
        assert str(template.resolve()) in wrapper
        assert interpretation["template_sha256"] in wrapper
        assert "OLM_AE_MAC_ERROR_PATH" in wrapper
        assert "OLM_MACOS_PRODUCT_VERSION" in wrapper
        assert "OLM_MACOS_BUILD_VERSION" in wrapper
        assert str(binary.resolve()) in wrapper
        assert "__olm_eval_result instanceof Error" in wrapper
        assert "Number(pr.gpuAccelType)!==Number(GpuAccelType.SOFTWARE)" in jsx
        assert 'workingSpaceText!==""&&workingSpaceText!=="None"' in jsx
        assert "working_space_raw:workingSpaceRaw" in jsx
        assert "macos_product_version:macosProductVersion" in jsx
        assert "macos_build_version:macosBuildVersion" in jsx
        assert '"comp":{"width":1920,"height":1080,"pixel_aspect":1,"frame_rate":24}' in jsx
        assert "rendered output cardinality" in jsx
        assert "cannot normalize rendered output" in jsx
        assert "--input-path" not in subprocess.run([sys.executable,str(RUNNER),"--help"],cwd=ROOT,text=True,capture_output=True,check=True).stdout
        assert "--output-template" not in subprocess.run([sys.executable,str(RUNNER),"--help"],cwd=ROOT,text=True,capture_output=True,check=True).stdout
        assert "app.open(templateFile)" in jsx
        assert "importFile" not in jsx and "app.newProject()" not in jsx
        assert "OLMBlur" not in jsx and "legacy" not in jsx.lower()
    print("[OK] OLMSmoother2 no-key 32bpc Mac request smoke passed without launching AE"); return 0
if __name__=="__main__": raise SystemExit(main())
