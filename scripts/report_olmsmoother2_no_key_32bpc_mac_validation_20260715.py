#!/usr/bin/env python3
"""Validate an OLMSmoother2 v2/no-key Mac candidate return, fail closed."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import compare
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
    om=d.get("output_module",{})
    if om.get("template_name")!="OLM EXR 32 Float" or om.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or om.get("sample_type")!="FLOAT" or om.get("compression")!="none" or om.get("channels")!= ["A","B","G","R"]: fail.append("output contract drift")
    plugin=d.get("plugin",{}); pp=Path(plugin.get("path","")); pb=Path(plugin.get("binary_path",""))
    if plugin.get("filename")!="OLMSmoother2.plugin" or not pp.is_dir() or pb != pp/"Contents"/"MacOS"/"OLMSmoother2" or len(plugin.get("sha256",""))!=64 or not pb.is_file() or (pb.is_file() and plugin.get("sha256")!=digest(pb)): fail.append("loaded plugin bundle/binary identity or hash missing/mismatched")
    expected_contract=canonical({"request_id":request["request_id"],"case":request["cases"][0],"common_setup":request["common_setup"],"mac_run_contract":request["mac_run_contract"]})
    if d.get("case_contract_sha256")!=expected_contract: fail.append("case/parameter contract hash missing or mismatched")
    cases=d.get("cases",[]); case=cases[0] if len(cases)==1 else {}
    if case.get("id")!=request["cases"][0]["id"] or case.get("no_effect_control_passed") is not True: fail.append("case/control missing")
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
    ref=request["windows_reference"]; manifest=ROOT/ref["manifest"]; md=json.loads(manifest.read_text()) if manifest.is_file() else {}; wc=next((x for x in md.get("cases",[]) if x.get("id")==case["id"]),{})
    attested=bool(wc.get("sha256") and wc.get("before_effects_sha256") and wc.get("header_metadata"))
    ref_root=ROOT/ref["artifact_root"]; win_control=ref_root/ref["before_effects_frame"]; win_effect=ref_root/ref["effect_frame"]
    if not win_control.is_file() or digest(win_control)!=ref["before_effects_sha256"]: print("[FAIL_CLOSED] Windows no-effect artifact missing/hash mismatch"); return 1
    if not win_effect.is_file() or digest(win_effect)!=ref["effect_sha256"]: print("[FAIL_CLOSED] Windows effect artifact missing/hash mismatch"); return 1
    mac_control=Path(outputs["no_effect_control"]["path"]); mac_effect=Path(outputs["effect_on"]["path"])
    try:
        comparisons={"no_effect_control":compare(win_control,mac_control),"effect_on":compare(win_effect,mac_effect)}
    except (VerificationError,OSError,ValueError) as e: print(f"[FAIL_CLOSED] raw FLOAT32 comparison failed: {e}"); return 1
    control_exact=comparisons["no_effect_control"]["mismatched_values"]==0
    effect_exact=comparisons["effect_on"]["mismatched_values"]==0
    exact=attested and control_exact and effect_exact
    if not control_exact: status="blocked_no_effect_control_mismatch"
    elif not attested: status="blocked_pending_windows_artifact_attestation"
    elif not effect_exact: status="candidate_return_verified_effect_mismatch"
    else: status="raw_float32_exact"
    reasons=[]
    if not attested: reasons.append("Windows manifest lacks admissible per-artifact SHA-256/header metadata")
    if not control_exact: reasons.append("Windows before-effects vs Mac no-effect raw FLOAT32 control mismatch blocks effect attribution")
    if control_exact and not effect_exact: reasons.append("no-effect control is exact but effect-on raw FLOAT32 words differ")
    if exact: reasons.append("both raw FLOAT32 gates and Windows artifact attestation pass")
    report={"kind":"olmsmoother2_no_key_32bpc_mac_validation_report","schema_version":1,"status":status,"ae_exact_claim":exact,"case_count":1,"result_json":str(a.result),"mac_candidate_return_verified":True,"windows_artifact_attestation_present":attested,"raw_float32_comparisons":comparisons,"control_gate_passed":control_exact,"effect_gate_passed":effect_exact,"reason":"; ".join(reasons),"next_gate":"repair/aligned-capture the no-effect host/export path before attributing the effect output" if not control_exact else "attest Windows artifacts and eliminate any effect-on raw FLOAT32 residual"}
    target=out/"validation_report.json"; target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(f"[OK] wrote {target}"); return 0 if exact else 1
if __name__=="__main__": raise SystemExit(main())
