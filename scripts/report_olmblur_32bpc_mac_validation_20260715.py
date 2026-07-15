#!/usr/bin/env python3
"""Validate a returned one-case Mac record without claiming AE exactness."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr

def digest(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("return_json",type=Path); ap.add_argument("--output-dir",type=Path); a=ap.parse_args()
    d=json.loads(a.return_json.read_text(encoding="utf-8")); fail=[]
    if d.get("kind")!="olmblur_32bpc_mac_validation_return": fail.append("wrong return kind")
    if d.get("ae_exact_claim") is not False: fail.append("exact claim was not explicitly false")
    if d.get("project") != {"bits_per_channel":32,"renderer":"SOFTWARE","working_space":"None","linear_blending":False}: fail.append("project contract drift")
    if d.get("output_module",{}).get("template_name")!="OLM EXR 32 Float" or d.get("output_module",{}).get("capture_api")!="OutputModule.getSettings(GetSettingsFormat.STRING)": fail.append("output module contract drift")
    plugin=d.get("loaded_plugin",{}); p=plugin.get("path","")
    plugin_path=Path(p)
    if plugin.get("filename")!="OLMBlur.plugin" or len(plugin.get("sha256", ""))!=64 or not plugin_path.is_file() or plugin.get("sha256")!=digest(plugin_path): fail.append("loaded plugin hash missing or mismatched")
    proof=d.get("loaded_plugin_proof",{})
    if proof.get("method")!="vmmap_exact_path" or proof.get("module_path")!=p or proof.get("module_sha256")!=plugin.get("sha256") or proof.get("binary_predates_process_start") is not True or not isinstance(proof.get("pid"),int): fail.append("loaded plugin is not bound to the AE process mapping")
    cases=d.get("cases",[])
    if len(cases)!=1 or cases[0].get("id")!="olmblur__case_0001" or cases[0].get("no_effect_control_passed") is not True: fail.append("case/control missing")
    out=a.output_dir or a.return_json.parent; case=cases[0] if cases else {}; outputs=case.get("outputs",{})
    setting_hashes=[]
    for branch in ("no_effect","effect_on"):
        item=outputs.get(branch,{}); path=Path(item.get("path","")); path=path if path.is_absolute() else out/path.name
        if path.suffix.lower()!=".exr" or not path.exists(): fail.append(f"missing {branch} FLOAT EXR"); continue
        if item.get("sha256")!=digest(path): fail.append(f"{branch} hash mismatch")
        try: inspect_float_rgba_exr(path, (1920, 1080))
        except (VerificationError, OSError, ValueError) as exc: fail.append(f"{branch} is not an uncompressed FLOAT RGBA EXR: {exc}")
        settings=item.get("output_module_settings",{}); sp=Path(settings.get("path","")); sp=sp if sp.is_absolute() else out/sp.name
        if not sp.exists() or len(settings.get("sha256",""))!=64 or (sp.exists() and settings["sha256"]!=digest(sp)): fail.append(f"{branch} settings capture missing/hash mismatch")
        setting_hashes.append(settings.get("serialization"))
    if len(setting_hashes)==2 and setting_hashes[0]!=setting_hashes[1]: fail.append("control/effect settings differ")
    if fail: print("[FAIL_CLOSED] "+"; ".join(fail)); return 1
    report={"kind":"olmblur_32bpc_mac_validation_report","schema_version":1,"status":"candidate_return_verified","ae_exact_claim":False,"case_count":1,"return_json":str(a.return_json),"next_gate":"compare this case's raw FLOAT32 RGBA words with the Windows effect/control pair"}
    target=out/"validation_report.json"; target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(f"[OK] wrote {target}"); return 0
if __name__ == "__main__": raise SystemExit(main())
