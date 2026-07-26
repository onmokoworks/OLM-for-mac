#!/usr/bin/env python3
"""Validate an OLMSmoother2 v2/no-key Mac candidate return, fail closed."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import compare
from compare_pf32_entry_to_exr import compare_pf32_entry
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr
REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json"
def digest(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v: object) -> str: return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("result",type=Path); ap.add_argument("--output-dir",type=Path); a=ap.parse_args()
    request=json.loads(REQUEST.read_text()); fail=[]
    try: d=json.loads(a.result.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: print(f"[FAIL_CLOSED] {e}"); return 1
    if d.get("kind")!="olmsmoother2_no_key_32bpc_mac_validation_return": fail.append("wrong return kind")
    if d.get("ae_exact_claim") is not False: fail.append("ae_exact_claim must be false")
    if d.get("platform")!="macOS" or not d.get("macos_product_version") or not d.get("macos_build_version") or not d.get("ae_version"): fail.append("host OS/AE identity missing")
    expected_project={"bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False}
    if {k:d.get("project",{}).get(k) for k in expected_project} != expected_project: fail.append("project/renderer/color contract drift")
    expected_interpretation=request["mac_run_contract"]["input_interpretation"]; template=ROOT/expected_interpretation["template"]; interpretation=d.get("input_interpretation",{})
    if interpretation.get("method")!="hash_bound_aep_template_footage_replace" or interpretation.get("preserve_rgb") is not True or interpretation.get("verification")!="no_effect_raw_float32_gate": fail.append("input Preserve RGB interpretation contract drift")
    if interpretation.get("template_path")!=str(template.resolve()) or interpretation.get("template_sha256")!=expected_interpretation["template_sha256"] or not template.is_file() or (template.is_file() and digest(template)!=expected_interpretation["template_sha256"]): fail.append("input Preserve RGB template identity missing/mismatched")
    om=d.get("output_module",{})
    expected_output_template=request["mac_run_contract"]["output_template"]
    if om.get("template_name")!=expected_output_template or om.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or om.get("sample_type")!="FLOAT" or om.get("compression")!="none" or om.get("channels")!= ["A","B","G","R"]: fail.append("output contract drift")
    plugin=d.get("plugin",{}); pp=Path(plugin.get("path","")); pb=Path(plugin.get("binary_path",""))
    if plugin.get("filename")!="OLMSmoother2.plugin" or not pp.is_dir() or pb != pp/"Contents"/"MacOS"/"OLMSmoother2" or len(plugin.get("sha256",""))!=64 or not pb.is_file() or (pb.is_file() and plugin.get("sha256")!=digest(pb)): fail.append("loaded plugin bundle/binary identity or hash missing/mismatched")
    reference=request["windows_reference"]; expected_input={"filename":reference["before_effects_frame"],"sha256":reference["before_effects_sha256"]}; expected_case={**request["cases"][0],"input":expected_input}
    expected_contract=canonical({"request_id":request["request_id"],"case":expected_case,"common_setup":request["common_setup"],"mac_run_contract":request["mac_run_contract"],"output_template":expected_output_template})
    if d.get("case_contract_sha256")!=expected_contract: fail.append("case/parameter contract hash missing or mismatched")
    cases=d.get("cases",[]); case=cases[0] if len(cases)==1 else {}
    if case.get("id")!=request["cases"][0]["id"] or case.get("input")!=expected_input or case.get("no_effect_control_passed") is not True: fail.append("case/input/control missing")
    expected_params=request["cases"][0]["params_full"]
    if case.get("params_full")!=expected_params: fail.append("full parameter binding drift")
    for p in case.get("params_full",[]):
        if p.get("match_name")=="OLM Smoother v2-0001" and p.get("value")!=0: fail.append("Enable Color Key is not exactly 0")
        if p.get("match_name")=="OLM Smoother v2-0006" and p.get("value")!=2: fail.append("Smoother Version is not exactly 2")
    out=a.output_dir or a.result.parent; outputs=case.get("outputs",{}); setting_serial=[]
    for branch in ("no_effect_control","effect_on"):
        item=outputs.get(branch,{}); path=Path(item.get("path","")); path=path if path.is_absolute() else out/path.name
        if path.suffix.lower()!=".exr" or not path.is_file(): fail.append(f"missing {branch} FLOAT EXR"); continue
        if item.get("sha256")!=digest(path): fail.append(f"{branch} hash mismatch")
        try:
            info=inspect_float_rgba_exr(path,(1920,1080)); counts=info.get("sample_counts",{})
            if counts.get("nan",0) or counts.get("+inf",0) or counts.get("-inf",0): fail.append(f"{branch} contains non-finite samples")
        except (VerificationError,OSError,ValueError) as e: fail.append(f"{branch} is not uncompressed FLOAT RGBA EXR: {e}")
        settings=item.get("output_module_settings",{}); sp=Path(settings.get("path","")); sp=sp if sp.is_absolute() else out/sp.name
        if not sp.is_file() or len(settings.get("sha256",""))!=64 or (sp.is_file() and settings["sha256"]!=digest(sp)): fail.append(f"{branch} settings capture missing/hash mismatch")
        setting_serial.append(settings.get("serialization"))
        if item.get("effect_enabled") is not (branch=="effect_on"): fail.append(f"{branch} enabled-state drift")
    if len(setting_serial)==2 and setting_serial[0]!=setting_serial[1]: fail.append("control/effect settings differ")
    if fail: print("[FAIL_CLOSED] "+"; ".join(fail)); return 1
    ref=request["windows_preserve_rgb_reference"]; manifest=ROOT/ref["manifest"]; ref_root=ROOT/ref["artifact_root"]
    try: md=json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: print(f"[FAIL_CLOSED] Windows Preserve RGB manifest missing/invalid: {e}"); return 1
    source=ROOT/ref["source_input"]; win_control=ref_root/ref["no_effect_frame"]; win_effect=ref_root/ref["effect_frame"]; effect_aep=ROOT/ref["effect_aep_path"]; entry_path=ROOT/ref["pf32_input_entry_path"]
    for label,path,expected in (
        ("source",source,ref["source_input_sha256"]),
        ("no-effect",win_control,ref["no_effect_sha256"]),
        ("effect-on",win_effect,ref["effect_sha256"]),
        ("effect AEP",effect_aep,ref["effect_aep_sha256"]),
        ("PF32 entry",entry_path,ref["pf32_input_entry_stored_sha256"]),
    ):
        if not path.is_file() or digest(path)!=expected: print(f"[FAIL_CLOSED] Windows Preserve RGB {label} missing/hash mismatch"); return 1
    if md.get("kind")!="olmsmoother2_case07_windows_ae_preserve_rgb_reference" or md.get("ae_exact_claim") is not False or md.get("case_id")!=case["id"] or md.get("case_contract_sha256")!=d.get("case_contract_sha256"): print("[FAIL_CLOSED] Windows Preserve RGB manifest identity/contract drift"); return 1
    host=md.get("host",{})
    if host.get("ae_version")!="26.3x87" or host.get("renderer")!="SOFTWARE" or host.get("bits_per_channel")!=32 or host.get("working_space")!="None" or host.get("linear_blending") is not False or host.get("comp")!={"width":1920,"height":1080,"frame_rate":24,"frame":0}: print("[FAIL_CLOSED] Windows Preserve RGB host contract drift"); return 1
    binaries=md.get("binaries",{})
    if binaries.get("aex",{}).get("sha256")!="7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7" or binaries.get("aerender",{}).get("sha256")!="711859d183bdabec7c358a344208323bbbd665fffd7e88e42b9b234f9b99692a" or binaries.get("cdb",{}).get("sha256")!="b806eaea373d6add99fd9825a34820eb0779b9045cf71eecd7d070d58b8b6f6d": print("[FAIL_CLOSED] Windows binary identity drift"); return 1
    if md.get("source",{}).get("path")!=ref["source_input"] or md.get("source",{}).get("sha256")!=ref["source_input_sha256"] or md.get("source",{}).get("interpretation")!="Preserve RGB": print("[FAIL_CLOSED] Windows Preserve RGB source binding drift"); return 1
    project=md.get("project",{})
    if project.get("path")!=ref["effect_aep_path"] or project.get("sha256")!=ref["effect_aep_sha256"] or project.get("effect_enabled") is not True or project.get("full_parameter_binding") is not True: print("[FAIL_CLOSED] Windows Preserve RGB AEP binding drift"); return 1
    for support in md.get("support",{}).values():
        support_path=ROOT/support.get("path","")
        if not support_path.is_file() or support.get("sha256")!=digest(support_path): print("[FAIL_CLOSED] Windows PF32 support artifact missing/hash mismatch"); return 1
    output_module=md.get("output_module",{}); capture=ref["capture_contract"]
    if output_module.get("source")!="AEP-embedded settings" or output_module.get("aerender_omtemplate_override") is not False or output_module.get("profile_observed")!=capture["output_profile"] or capture.get("same_effect_render_entry_and_output") is not True or capture.get("raw_float32_epsilon")!=0: print("[FAIL_CLOSED] Windows Preserve RGB output-module contract drift"); return 1
    expected_header={"dimensions":[1920,1080],"physical_channel_order":["A","B","G","R"],"sample_types":[2,2,2,2],"compression":0,"finite_sample_count":8294400,"nonfinite_sample_count":0,"alpha_mode":"premultiplied","color_profile":"Preserve RGB"}
    artifacts=md.get("artifacts",{})
    for branch,path,expected in (("no_effect_control",win_control,ref["no_effect_sha256"]),("effect_on",win_effect,ref["effect_sha256"])):
        artifact=artifacts.get(branch,{})
        if artifact.get("path")!=path.name or artifact.get("sha256")!=expected or artifact.get("header_metadata")!=expected_header: print(f"[FAIL_CLOSED] Windows {branch} manifest attestation drift"); return 1
        try:
            inspected=inspect_float_rgba_exr(path,(1920,1080)); counts=inspected["sample_counts"]
            if inspected["channel_order"]!=["A","B","G","R"] or inspected["sample_types"]!=[2,2,2,2] or inspected["compression"]!=0 or counts.get("finite")!=8294400 or any(counts.get(k,0) for k in ("nan","+inf","-inf")): raise VerificationError("header/sample contract drift")
        except (VerificationError,OSError,ValueError) as e: print(f"[FAIL_CLOSED] Windows {branch} EXR contract failed: {e}"); return 1
    entry=md.get("pf32_input_entry",{})
    entry_attested=bool(
        entry.get("path")==ref["pf32_input_entry_path"] and
        entry.get("stored_sha256")==ref["pf32_input_entry_stored_sha256"] and
        entry.get("uncompressed_sha256")==ref["pf32_input_entry_uncompressed_sha256"] and
        entry.get("uncompressed_size")==33177600 and
        entry.get("same_run") is True and
        entry.get("same_run_effect_sha256")==ref["effect_sha256"] and
        entry.get("channel_order")==["A","R","G","B"] and
        entry.get("width")==1920 and entry.get("height")==1080 and entry.get("rowbytes")==30720
    )
    try: entry_comparison=compare_pf32_entry(entry_path,source)
    except (OSError,ValueError,VerificationError) as e: print(f"[FAIL_CLOSED] PF32 entry comparison failed: {e}"); return 1
    entry_attested=entry_attested and entry_comparison["raw"]["uncompressed_sha256"]==ref["pf32_input_entry_uncompressed_sha256"] and entry_comparison["mismatched_words"]==0 and entry_comparison["max_raw_u32_delta"]==0
    attested=entry_attested
    mac_control=Path(outputs["no_effect_control"]["path"]); mac_effect=Path(outputs["effect_on"]["path"])
    try:
        comparisons={"no_effect_control":compare(win_control,mac_control),"effect_on":compare(win_effect,mac_effect)}
    except (VerificationError,OSError,ValueError) as e: print(f"[FAIL_CLOSED] raw FLOAT32 comparison failed: {e}"); return 1
    control_exact=comparisons["no_effect_control"]["mismatched_values"]==0
    effect_exact=comparisons["effect_on"]["mismatched_values"]==0
    exact=attested and entry_attested and control_exact and effect_exact
    if not control_exact: status="blocked_no_effect_control_mismatch"
    elif not entry_attested: status="blocked_input_entry_identity"
    elif not attested: status="blocked_pending_windows_artifact_attestation"
    elif not effect_exact: status="candidate_return_verified_effect_mismatch"
    else: status="raw_float32_exact"
    reasons=[]
    if not attested: reasons.append("Windows Preserve RGB manifest or same-run PF32 entry attestation is not admissible")
    if not entry_attested: reasons.append("Windows Preserve RGB effect run lacks an exact same-run PF32 input-entry witness")
    if not control_exact: reasons.append("Windows before-effects vs Mac no-effect raw FLOAT32 control mismatch blocks effect attribution")
    if control_exact and not effect_exact: reasons.append("no-effect control is exact but effect-on raw FLOAT32 words differ")
    if exact: reasons.append("both raw FLOAT32 gates and Windows artifact attestation pass")
    if not control_exact: next_gate="repair/aligned-capture the no-effect host/export path before attributing the effect output"
    elif not entry_attested: next_gate="repair the same-run Windows PF32 input-entry witness before attributing effect residuals"
    else: next_gate="eliminate the attributable 32bpc effect-on raw FLOAT32 residual without changing the frozen 8bpc core"
    report={"kind":"olmsmoother2_no_key_32bpc_mac_validation_report","schema_version":1,"status":status,"ae_exact_claim":exact,"case_count":1,"result_json":str(a.result),"mac_candidate_return_verified":True,"windows_reference_manifest":str(manifest),"windows_artifact_attestation_present":attested,"windows_pf32_input_entry_attestation_present":entry_attested,"windows_pf32_input_entry_comparison":entry_comparison,"raw_float32_comparisons":comparisons,"control_gate_passed":control_exact,"effect_gate_passed":effect_exact,"reason":"; ".join(reasons),"next_gate":next_gate}
    target=out/"validation_report.json"; target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(f"[OK] wrote {target}"); return 0 if exact else 1
if __name__=="__main__": raise SystemExit(main())
