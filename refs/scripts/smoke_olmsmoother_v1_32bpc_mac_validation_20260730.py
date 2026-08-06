#!/usr/bin/env python3
"""Smoke the v1 request and disabled-by-default runner; never launch AE."""
from __future__ import annotations
import hashlib, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/"scripts/run_olmsmoother_v1_32bpc_mac_validation_20260730.py"
REPORTER=ROOT/"scripts/report_olmsmoother_v1_32bpc_mac_validation_20260730.py"
ATTESTOR=ROOT/"scripts/attest_olmsmoother_v1_mac_process_20260730.py"
REQUEST=ROOT/"refs/mac_validation_requests/olmsmoother_v1_32bpc_mac_validation_20260730.json"
INPUT_TEMPLATE=ROOT/"refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep"
INPUT_TEMPLATE_SHA256="51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
def module_digest(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def main()->int:
    d=json.loads(REQUEST.read_text())
    assert d["status"]=="execution_disabled_by_default" and d["ae_exact_claim"] is False
    assert d["callback_claim"]=="classic_host_conversion_hypothesis_only"
    setup=d["common_setup"]
    assert {k:setup[k] for k in ("bits_per_channel","width","height","frame_rate","renderer","renderer_raw","working_space")}=={"bits_per_channel":32,"width":1920,"height":1080,"frame_rate":24,"renderer":"SOFTWARE","renderer_raw":1816,"working_space":None}
    assert setup["named_working_space_allowed"] is False and len(setup["working_space_raw_allowed"])==4
    interpretation=d["mac_run_contract"]["input_interpretation"]
    assert interpretation=={"method":"hash_bound_aep_template_footage_replace","template_path":"refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep","template_sha256":INPUT_TEMPLATE_SHA256,"footage_item_name":"OLM_COLOR_PROBE_INPUT","comp_item_name":"OLM_COLOR_PROBE_COMP","preserve_rgb":True,"verification":"all_ten_no_effect_controls_raw_float32_exact"}
    assert INPUT_TEMPLATE.is_file() and module_digest(INPUT_TEMPLATE)==INPUT_TEMPLATE_SHA256
    assert d["mac_run_contract"]["output_settings_capture"]=={"api":"OutputModule.getSettings(GetSettingsFormat.STRING)","one_sidecar_per_role":True,"no_effect_and_effect_settings_must_match":True}
    assert d["mac_run_contract"]["cache_policy"]=={"after_each_footage_replace":"app.purge(PurgeTarget.ALL_CACHES)","between_no_effect_and_effect":"forbidden"}
    assert len(d["cases"])==10 and [c["id"][-2:] for c in d["cases"]]==[f"{n:02d}" for n in range(1,11)]
    for c in d["cases"]:
        assert [p["match_name"] for p in c["params"]]==["OLM Smoother-0001","OLM Smoother-0002","OLM Smoother-0003"]
        assert not any(p["match_name"].startswith("ADBE ") for p in c["params"])
    p=subprocess.run([sys.executable,str(RUNNER)],text=True,capture_output=True)
    assert p.returncode==0 and "direct AE execution disabled" in p.stdout
    modspec=importlib.util.spec_from_file_location("olm_v1_runner_smoke",RUNNER)
    module=importlib.util.module_from_spec(modspec); modspec.loader.exec_module(module)
    sys.path.insert(0,str(ROOT/"scripts"))
    reportspec=importlib.util.spec_from_file_location("olm_v1_reporter_smoke",REPORTER)
    reportmod=importlib.util.module_from_spec(reportspec); reportspec.loader.exec_module(reportmod)
    attestorspec=importlib.util.spec_from_file_location("olm_v1_attestor_smoke",ATTESTOR)
    attmod=importlib.util.module_from_spec(attestorspec); attestorspec.loader.exec_module(attmod)
    assert attmod.HARNESS_KEYS=={"runner","reporter","request","manifest","input_template","smoke","boundary_probe","port_source","strings_source","generated_jsx"}
    for kind,raw in (("string",""),("string","None"),("null",None),("undefined",None)):
        assert reportmod.project_evidence({"bits_per_channel":32,"renderer_raw":1816,"working_space_raw":raw,"working_space_raw_type":kind})
    for raw in ("sRGB IEC61966-2.1","Adobe RGB (1998)","Rec.709 Gamma 2.4"):
        assert not reportmod.project_evidence({"bits_per_channel":32,"renderer_raw":1816,"working_space_raw":raw,"working_space_raw_type":"string"})
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td)
        generated=module.jsx_source(
            d,
            temp/"OLMSmoother.plugin",
            temp,
            temp/"mac_validation_return.json",
            "0"*64,
            "1"*64,
            temp/"jsx_started.json",
            temp/"jsx_error.json",
        )
        assert generated.startswith("(function(){") and generated.endswith("}})();")
        assert "olmsmoother_v1_jsx_started" in generated and "olmsmoother_v1_jsx_error" in generated
        assert "var PHASE='bootstrap';try{" in generated and "phase:PHASE" in generated
        assert "var SELF=new File($.fileName),SELFPATH=SELF.fsName" in generated
        assert "PHASE='project'" in generated and "PHASE='warmup'" in generated
        assert "PHASE='cases'" in generated and "PHASE='post_request'" in generated and "PHASE='result'" in generated
        assert "var pr=app.open(tf)" in generated and "ft.replace(f)" in generated
        assert "app.newProject" not in generated and "importFile" not in generated
        assert "Preserve RGB template item cardinality" in generated and "case cleanup contamination" in generated
        assert "OutputModule.getSettings(GetSettingsFormat.STRING)" in generated and "__output_module_settings.json" in generated
        assert "pr!==app.project" in generated and "pi instanceof FootageItem" in generated and "pi instanceof CompItem" in generated
        assert "ft.file.fsName!==f.fsName" in generated and "app.purge(PurgeTarget.ALL_CACHES)" in generated
        assert "om.postRenderAction!==PostRenderAction.NONE" in generated and "render queue cardinality" in generated
        assert "warmup restoration" in generated and "wc.layers.add(ft)" in generated
        assert "layers.addSolid(" not in generated
        assert "pr.numItems!==BASE_ITEMS" in generated and "ly=co.layer(1);g=ly&&ly.property('ADBE Effect Parade')" in generated
        assert "function ST(v)" in generated and "CloseOptions.DO_NOT_SAVE_CHANGES" in generated
        assert generated.count("pr.items.addComp(")==1 and generated.count("\n  app.purge(PurgeTarget.ALL_CACHES);\n  if(!ft.file")==1
        assert generated.index("var ch=RJ(CH)") < generated.index("var INPUT_EVIDENCE=") < generated.index("CIK!==7")
        for forbidden in ("let ","const ","=>","class ","Object.keys","`"):
            assert forbidden not in generated
        generated_path=temp/"generated.js"; generated_path.write_text(generated)
        syntax=subprocess.run(["node","--check",str(generated_path)],text=True,capture_output=True)
        assert syntax.returncode==0,syntax.stderr
        bad=json.loads(REQUEST.read_text()); bad["cases"][0]["before_effects_sha256"]="0"*64
        bad_request=temp/"bad_request.json"; bad_request.write_text(json.dumps(bad))
        original=module.REQUEST; module.REQUEST=bad_request
        try:
            module.load_contract(); raise AssertionError("tampered Windows reference hash accepted")
        except ValueError: pass
        mutations={
            "method":"wrong",
            "template_path":"refs/fixtures/wrong.aep",
            "template_sha256":"0"*64,
            "footage_item_name":"WRONG",
            "comp_item_name":"WRONG",
            "preserve_rgb":False,
            "verification":"wrong",
        }
        for field,value in mutations.items():
            mutated=json.loads(REQUEST.read_text()); mutated["mac_run_contract"]["input_interpretation"][field]=value
            mutated_request=temp/("mutated_"+field+".json"); mutated_request.write_text(json.dumps(mutated)); module.REQUEST=mutated_request
            try:
                module.load_contract(); raise AssertionError("tampered Preserve RGB field accepted: "+field)
            except ValueError: pass
        reordered=json.loads(REQUEST.read_text()); reordered["cases"][0],reordered["cases"][1]=reordered["cases"][1],reordered["cases"][0]
        reordered_request=temp/"reordered_request.json"; reordered_request.write_text(json.dumps(reordered)); module.REQUEST=reordered_request
        try:
            module.load_contract(); raise AssertionError("reordered manifest contract accepted")
        except ValueError: pass
        symlink_root=temp/"root_link"; symlink_root.symlink_to(ROOT/"refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMSmoother",target_is_directory=True)
        linked=json.loads(REQUEST.read_text()); linked["windows_reference"]["artifact_root"]=str(symlink_root)
        linked_request=temp/"linked_request.json"; linked_request.write_text(json.dumps(linked)); module.REQUEST=linked_request
        try:
            module.load_contract(); raise AssertionError("symlinked reference root accepted")
        except ValueError: pass
        canonical_temp=temp.resolve()
        targets=[canonical_temp/f"case_{n:02d}.artifact" for n in range(40)]
        module.preflight_outputs(targets)
        (canonical_temp/"case_00.artifact00000").write_bytes(b"stale")
        try:
            module.preflight_outputs(targets); raise AssertionError("stale sequence-prefix artifact accepted")
        except ValueError: pass
        (canonical_temp/"case_00.artifact00000").unlink()
        try:
            module.preflight_outputs(targets[:-1]+[targets[0]]); raise AssertionError("duplicate target/cardinality accepted")
        except ValueError: pass
        module.REQUEST=original
        link=temp/"request_link.json"; link.symlink_to(REQUEST)
        assert link.is_symlink()
        q=subprocess.run([sys.executable,str(REPORTER),str(temp/"missing.json")],text=True,capture_output=True)
        assert q.returncode==1 and "[FAIL_CLOSED]" in q.stdout
    source=RUNNER.read_text()
    assert "Popen" in source and '"--execute"' in source
    assert ".terminate(" not in source and ".kill(" not in source
    assert "attest_olmsmoother_v1_mac_process_20260730.py" in source and "attestor_nonce" in source
    assert "snapshot(" not in source and "pre_ok_path" not in source and "post_ok_path" not in source
    assert "olmsmoother_v1_pre_request" in source and "olmsmoother_v1_pre_ok" in source
    assert "olmsmoother_v1_post_request" in source and "olmsmoother_v1_post_ok" in source
    assert "__OLM_SMOOTHER_MODULE_WARMUP__" in source and "rendered:false" in source and "WARMUP.removed=true" in source
    assert source.count("preflight_outputs(output_paths)")>=2 and "os.lstat(p)" in source and "output pathname/parent-inode alias" in source and "stale output" in source and "exactly {expected_count} outputs required" in source
    assert "timeSpanStart=0" in source and "timeSpanDuration=1/co.frameRate" in source
    assert "rendered output prefix cardinality" in source and "rendered output normalization" in source and "rendered.fsName" in source
    assert "exact manifest case count/order/id drift" in source and "parent-chain symlink" in source
    assert "addProperty('OLM Smoother')" in source and "Number(pr.gpuAccelType)!==1816" in source
    assert "Contents/MacOS/After Effects" in source and "Contents/MacOS/AfterFX" not in source
    assert "WSNONE=" in source and "String(WSRAW)==='None'" in source and "workingSpace_type=" in source
    assert "readback_before_render" in source and "readback_after_render" in source
    assert "schema_version:2" in source and 'result.name!="mac_validation_return.json"' in source
    assert '"schema_version":4' in source and '"harness":' in source and '"diagnostics":' in source and '"input_template":INPUT_TEMPLATE' in source
    assert '"inputs":expected_inputs' in source and '"input_interpretation":runtime_input_interpretation(request)' in source
    assert "cache policy contract drift" in source and "output settings capture contract drift" in source
    assert '"generated_jsx":jsx' in source and "jsx_started.json" in source and "jsx_error.json" in source
    assert 'returned.get("ae_version")!=AE_VERSION' in source
    assert "attestor_rc is not None and attestor_rc!=0" in source
    assert '"method":"after_effects_file_scripts_run_script_file"' in source
    assert "subprocess.Popen([str(ae)])" in source and 'str(ae),\"-r\"' not in source
    report=REPORTER.read_text()
    assert '"ae_exact_claim":False' in report and '"effect_attribution_gate_passed":False' in report
    assert "raw_float32_exact_artifact_only_missing_windows_provenance" in report and "mac_preserve_rgb_roundtrip_all_exact" in report
    assert '"same_source_cross_host_proven":False' in report and '"schema_version":7' in report
    assert "native_pf32_callback_claim" in report and "classic_host_conversion_hypothesis_only" in report
    assert "challenge_sha256" in report and "independent attestor/pre-post process identity" in report
    assert "protocol causal ordering/timestamps" in report and "post request artifact binding" in report
    assert '"project_raw_contract":project' in report and '"working_space_evidence"' in report
    assert '"warmup_evidence":warmup' in report and "disposable non-rendered effect warmup precede pre_request" in report
    assert '"warmup_contract":expected_warmup_contract' in report and "warmup complete challenge/result contract equality" in report
    assert '"readback_count":40' in report and '"gate_count":20' in report and '"gates":working_space_readbacks' in report
    assert 'before["project"]' in report and 'after["project"]' in report and '"working_space_raw_type"' in report
    assert '"harness_provenance":harness' in report and "output settings serialization" in report
    assert '"ae_version_contract"' in report and 'data.get("ae_version")!=AE_VERSION' in report
    assert '"version_strings_equal":True' in report and '"effect_gate_all_exact":False' in report
    assert "result_keys=" in report and 'data.get("schema_version")!=2' in report
    assert "JSX start identity" in report and "generated JSX path/hash" in report and "diagnostic path binding" in report
    assert '"jsx_invocation_contract":expected_invocation' in report and "Mac JSX invocation contract" in report
    attestor=ATTESTOR.read_text()
    assert "_held_exact" in attestor and "snapshot_from_macos" in attestor and "_native_birth_token(os.getpid())" in attestor
    assert "assert_absent_outputs" in attestor and "artifact path/inode alias" in attestor
    assert "stale output sequence-prefix artifacts" in attestor
    assert "pre request replay/fabrication" in attestor and "post request replay/fabrication" in attestor
    assert "observed unique" in attestor and "paths/count=" in attestor and "warmup complete challenge contract" in attestor
    assert "warmup_project_matches" in attestor and "working_space_raw_allowed" in source
    assert 'challenge["schema_version"]!=4' in attestor and "HARNESS_KEYS" in attestor
    assert '"input_template"' in attestor and "40 output path uniqueness" in attestor and '"schema_version":3' in attestor
    assert "interpretation_keys=" in attestor and '"footage_item_name")!="OLM_COLOR_PROBE_INPUT"' in attestor
    assert "exact ten input/output case bindings required" in attestor and "declared identity" in attestor
    assert '"harness."+name' in attestor and "diagnostic path schema" in attestor
    assert "invocation contract" in attestor
    with tempfile.TemporaryDirectory() as td:
        bogus=Path(td)/"challenge.json"; bogus.write_text("{}")
        r=subprocess.run([sys.executable,str(ATTESTOR),"--challenge",str(bogus),"--attestor-nonce","0"*64,"--timeout","0.1"],text=True,capture_output=True)
        assert r.returncode==2 and "[FAIL_CLOSED]" in r.stdout
    assert "Windows reference path/hash" in report and "manifest containment" in report
    print("[PASS] v1 10-case request/runner/reporter smoke passed without launching AE")
    return 0
if __name__=="__main__": raise SystemExit(main())
