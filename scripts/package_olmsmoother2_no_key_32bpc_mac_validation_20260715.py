#!/usr/bin/env python3
"""Package the bounded OLMSmoother2 v2/no-key Mac FLOAT EXR request."""
from __future__ import annotations
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json"
STEM = "olmsmoother2_no_key_32bpc_mac_validation_20260715"
PLUGIN = "OLMSmoother2.plugin"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def load() -> dict:
    data = json.loads(REQUEST.read_text(encoding="utf-8"))
    if data.get("effect", {}).get("match_name") != "OLM Smoother v2" or data.get("scope", {}).get("plugin_version_mode") != 2:
        raise ValueError("request effect/version drift")
    case = data.get("cases", [])
    if len(case) != 1 or case[0]["id"] != "final_random10_olm_smoother_v2_07":
        raise ValueError("request must contain case 07 only")
    if case[0]["params_full"][0]["value"] != 0 or case[0]["params_full"][6]["value"] != 2:
        raise ValueError("request is not the v2/no-key slice")
    return data

def build(output: Path, support: Path) -> None:
    data = load(); ref = data["windows_reference"]
    root = ROOT / ref["artifact_root"]
    before, effect = root / ref["before_effects_frame"], root / ref["effect_frame"]
    if not before.is_file() or not effect.is_file(): raise FileNotFoundError("Windows case-07 EXR pair missing")
    if sha256(before) != ref["before_effects_sha256"] or sha256(effect) != ref["effect_sha256"]:
        raise ValueError("Windows EXR hash does not match request")
    manifest = ROOT / ref["manifest"]
    if not manifest.is_file(): raise FileNotFoundError(manifest)
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    win_case = next((c for c in manifest_data.get("cases", []) if c.get("id") == data["case"]["id"]), None)
    attested = bool(win_case and win_case.get("sha256") and win_case.get("before_effects_sha256") and win_case.get("header_metadata"))
    support.mkdir(parents=True, exist_ok=True); (support / "input").mkdir(exist_ok=True)
    shutil.copy2(before, support / "input" / before.name); shutil.copy2(effect, support / "windows_effect_reference.exr"); shutil.copy2(manifest, support / "windows_reference_manifest.json")
    request_case = {**data["case"], "input": {"filename": before.name, "sha256": sha256(before)}}
    contract_hash = canonical_sha256({"request_id": data["request_id"], "case": data["case"], "common_setup": data["common_setup"], "mac_run_contract": data["mac_run_contract"]})
    package_manifest = {"kind": "olmsmoother2_no_key_32bpc_mac_validation_request", "schema_version": 1, "request_id": STEM,
        "status": "blocked_pending_windows_artifact_attestation" if not attested else "request_only_no_ae_exact_claim",
        "windows_artifact_attestation_present": attested, "case_contract_sha256": contract_hash, "case": request_case,
        "windows_reference": {"manifest": "windows_reference_manifest.json", "before_effects": "input/" + before.name, "effect": "windows_effect_reference.exr", "before_effects_sha256": sha256(before), "effect_sha256": sha256(effect), "artifact_metadata_required": True},
        "required_ae": {"major_minor": "26.3", "renderer": "SOFTWARE", "bits_per_channel": 32, "working_space": "None", "linear_blending": False},
        "plugin_identity": {"filename": PLUGIN, "sha256_required": True, "path_must_be_explicit": True},
        "output": {"template": "OLM EXR 32 Float", "channels": ["A", "B", "G", "R"], "sample_type": "FLOAT", "compression": "none"},
        "return_contract": {"outputs": ["no_effect_control", "effect_on"], "raw_float32_comparison": True, "epsilon": 0, "normalization": False, "ae_exact_claim": False}}
    (support / "request_manifest.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(REQUEST, support / "mac_validation_request_index.json")
    (support / "README.md").write_text("Mac AE candidate runner only. It does not install a plug-in. Windows artifact attestation is required before AE exactness can be reported.\n", encoding="utf-8")
    from run_olmsmoother2_no_key_32bpc_mac_validation_20260715 import jsx_source
    (support / "run_mac_olmsmoother2_no_key_32bpc_validation.jsx").write_text(jsx_source(request_case, contract_hash), encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(support.rglob("*")):
            if p.is_file(): z.write(p, p.relative_to(support))

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--support-dir", type=Path); ap.add_argument("--output", type=Path, default=ROOT / "refs/runtime_trace_packages" / f"{STEM}.zip"); a = ap.parse_args()
    support = a.support_dir or ROOT / "refs/runtime_trace_packages" / STEM
    if support.exists(): shutil.rmtree(support)
    try: build(a.output, support)
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(f"[FAIL_CLOSED] {exc}"); return 1
    print(f"[OK] wrote {a.output}\n[OK] support tree {support}"); return 0
if __name__ == "__main__": raise SystemExit(main())
