#!/usr/bin/env python3
"""Fail-closed RadialBlur return validator and raw FLOAT32 comparison reporter."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_float_exr import compare
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr
from run_olmradialblur_32bpc_mac_validation_20260715 import AUDIT, ROOT, canonical_sha256, enrich_case, load_request

def digest(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(msg: str) -> None: raise ValueError(msg)
def resolve(root: Path, value: str) -> Path:
    p=Path(value); return p if p.is_absolute() else root/p.name

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("result",type=Path); ap.add_argument("--output-dir",type=Path); ap.add_argument("--report",type=Path); a=ap.parse_args()
    try:
        request=load_request(); audit=json.loads(AUDIT.read_text()); result=json.loads(a.result.read_text(encoding="utf-8")); root=(a.output_dir or a.result.parent).resolve(); errors=[]
        if result.get("kind")!="olmradialblur_32bpc_mac_validation_return": errors.append("wrong return kind")
        if result.get("ae_exact_claim") is not False: errors.append("ae_exact_claim must be false")
        if result.get("project") != {"bits_per_channel":32,"renderer":"SOFTWARE","working_space":result.get("project",{}).get("working_space"),"linear_blending":result.get("project",{}).get("linear_blending"),"frame":0,"frame_rate":24}: errors.append("project identity incomplete")
        om=result.get("output_module",{}); expected={"template_name":"OLM EXR 32 Float","capture_api":"OutputModule.getSettings(GetSettingsFormat.STRING)","format":"OpenEXR","compression":"uncompressed scanline","channels":["A","B","G","R"],"sample_type":"FLOAT","dimensions":[1920,1080]}
        if om != expected: errors.append("output module identity drift")
        plugin=result.get("loaded_plugin",{}); pp=Path(plugin.get("path",""));
        if plugin.get("filename")!="OLMRadialBlur.plugin" or not pp.is_file() or plugin.get("sha256")!=digest(pp): errors.append("plugin path/hash missing or mismatched")
        returned=result.get("cases",[]); expected_cases=request["cases"]; seen_outputs=set(); settings_hashes=[]
        if [c.get("id") for c in returned] != [c["id"] for c in expected_cases]: errors.append("case set/order mismatch")
        comparisons=[]
        for expected_case, case in zip(expected_cases, returned):
            if case.get("blur_type") != ("Zoom" if expected_case["params"]["Blur Type"]==1 else "Rotation"): errors.append(f"{expected_case['id']}: blur type mismatch")
            if case.get("input",{}).get("sha256") != expected_case["input_sha256"]: errors.append(f"{expected_case['id']}: input identity mismatch")
            expected_params=enrich_case(expected_case)["params_full"]
            if case.get("params_full") != expected_params: errors.append(f"{expected_case['id']}: parameter manifest mismatch")
            if case.get("params_sha256") != canonical_sha256(expected_params): errors.append(f"{expected_case['id']}: parameter hash mismatch")
            if case.get("no_effect_control_passed") is not True: errors.append(f"{expected_case['id']}: missing same-context control")
            win_root=ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMRadialBlur"
            win_before=win_root / Path(expected_case["input_exr"]).name
            win_effect=win_root / Path(expected_case["input_exr"]).name.replace("_before_effects.exr", ".exr")
            for branch, expected_path, key in (("no_effect_control",win_before,"before_effects"),("effect_on",win_effect,"effect")):
                item=case.get("outputs",{}).get(branch,{ }); p=resolve(root,item.get("path",""))
                if not p.is_file() or p.suffix.lower()!=".exr": errors.append(f"{expected_case['id']}: missing {branch}"); continue
                if str(p.resolve()) in seen_outputs: errors.append(f"{expected_case['id']}: reused output path")
                seen_outputs.add(str(p.resolve()))
                if item.get("sha256")!=digest(p): errors.append(f"{expected_case['id']}: {branch} hash mismatch")
                settings=item.get("output_module_settings",{}); settings_path=resolve(root,settings.get("path",""))
                if not settings_path.is_file() or len(settings.get("sha256", "")) != 64 or (settings_path.is_file() and settings.get("sha256") != digest(settings_path)):
                    errors.append(f"{expected_case['id']}: {branch} settings capture missing/hash mismatch")
                settings_hashes.append(settings.get("sha256"))
                try: info=inspect_float_rgba_exr(p,(1920,1080));
                except (VerificationError,OSError,ValueError) as exc: errors.append(f"{expected_case['id']}: invalid {branch}: {exc}"); continue
                if info["sample_counts"].get("nan",0) or info["sample_counts"].get("+inf",0) or info["sample_counts"].get("-inf",0): errors.append(f"{expected_case['id']}: non-finite {branch}")
                if not win_before.is_file() or digest(win_before if key=="before_effects" else win_effect) != audit["selected_artifacts"]["case_01" if expected_case["id"].endswith("_01") else "case_02"][key]["sha256"]: errors.append(f"{expected_case['id']}: Windows {key} hash mismatch")
                if win_before.is_file() and (win_before if key=="before_effects" else win_effect).is_file():
                    comparisons.append({"case_id":expected_case["id"],"branch":branch,"windows":str((win_before if key=="before_effects" else win_effect).resolve()),"mac":str(p.resolve()),"result":compare(win_before if key=="before_effects" else win_effect,p)})
            if len(settings_hashes[-2:]) == 2 and settings_hashes[-2] != settings_hashes[-1]: errors.append(f"{expected_case['id']}: control/effect output settings differ")
        if errors: raise ValueError("; ".join(errors))
        report={"kind":"olmradialblur_32bpc_mac_validation_report","schema_version":1,"status":"candidate_return_verified","ae_exact_claim":False,"case_count":2,"raw_float32_comparisons":comparisons,"all_raw_float32_equal":all(x["result"]["mismatched_values"]==0 for x in comparisons) and len(comparisons)==4,"next_gate":"retain both same-context controls, host/project/output identity, and loaded plugin hash before any exactness decision"}
        target=a.report or root/"validation_report.json"; target.write_text(json.dumps(report,indent=2)+"\n"); print(f"[OK] wrote {target}"); return 0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,VerificationError) as exc: print(f"[FAIL_CLOSED] {exc}",file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
