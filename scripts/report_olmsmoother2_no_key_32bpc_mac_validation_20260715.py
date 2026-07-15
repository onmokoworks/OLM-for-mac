#!/usr/bin/env python3
"""Validate an OLMSmoother2 v2/no-key Mac candidate return, fail closed."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
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
    expected_project={"bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False}
    if {k:d.get("project",{}).get(k) for k in expected_project} != expected_project: fail.append("project/renderer/color contract drift")
    om=d.get("output_module",{})
    if om.get("template_name")!="OLM EXR 32 Float" or om.get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)" or om.get("sample_type")!="FLOAT" or om.get("compression")!="none" or om.get("channels")!= ["A","B","G","R"]: fail.append("output contract drift")
    plugin=d.get("plugin",{}); pp=Path(plugin.get("path",""))
    if plugin.get("filename")!="OLMSmoother2.plugin" or len(plugin.get("sha256",""))!=64 or not pp.is_file() or (pp.is_file() and plugin.get("sha256")!=digest(pp)): fail.append("loaded plugin identity/hash missing or mismatched")
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
    ref=json.loads(REQUEST.read_text())["windows_reference"]; manifest=ROOT/ref["manifest"]; md=json.loads(manifest.read_text()) if manifest.is_file() else {}; wc=next((x for x in md.get("cases",[]) if x.get("id")==case["id"]),{})
    attested=bool(wc.get("sha256") and wc.get("before_effects_sha256") and wc.get("header_metadata"))
    status="candidate_return_verified" if attested else "blocked_pending_windows_artifact_attestation"
    report={"kind":"olmsmoother2_no_key_32bpc_mac_validation_report","schema_version":1,"status":status,"ae_exact_claim":False,"case_count":1,"result_json":str(a.result),"mac_candidate_return_verified":True,"windows_artifact_attestation_present":attested,"raw_float32_comparison": "not_run_pending_windows_artifact_attestation","reason": "Windows manifest lacks admissible per-artifact SHA-256/header metadata" if not attested else "raw FLOAT32 comparison is the next gate","next_gate":"attest Windows case-07 EXR hashes and required metadata, then compare both gates as raw FLOAT32 words"}
    target=out/"validation_report.json"; target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(f"[OK] wrote {target}"); return 0
if __name__=="__main__": raise SystemExit(main())
