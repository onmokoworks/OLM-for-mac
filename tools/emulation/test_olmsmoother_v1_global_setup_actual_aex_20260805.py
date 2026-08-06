#!/usr/bin/env python3
"""Actual-AEX GLOBAL_SETUP fixture against production EffectMain."""
from __future__ import annotations
import hashlib, json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs/conformance/olmsmoother_v1_independent_binary_discriminator_full_20260730.json"
FIXTURE_SHA256 = "3008b8239c48e56c6d0fb0aa707ef7e46df41d311c8f8aa710a79503e2d75735"
SOURCE = ROOT / "tools/emulation/olmsmoother_v1_global_setup_production_harness_20260805.cpp"
OUT_JSON = ROOT / "refs/conformance/olmsmoother_v1_global_setup_actual_aex_20260805.json"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    if sha(FIXTURE) != FIXTURE_SHA256:
        raise RuntimeError("actual-AEX fixture identity drift")
    fixture = json.loads(FIXTURE.read_text())
    setups = [c["render_readback"]["v1"]["worker_result"]["setup"] for c in fixture["cases"]]
    actual = {"error": setups[0]["global_setup_error"], "out_flags": setups[0]["out_flags"], "out_flags2": setups[0]["out_flags2"]}
    if any({"error": s["global_setup_error"], "out_flags": s["out_flags"], "out_flags2": s["out_flags2"]} != actual for s in setups):
        raise RuntimeError("actual-AEX GLOBAL_SETUP fixture is not stable across cases")
    with tempfile.TemporaryDirectory(prefix="olmsmoother_v1_setup_") as td:
        binary = Path(td) / "probe"
        subprocess.run(["clang++", "-std=c++17", "-I" + str(ROOT / "cli/OLMSmoother/shim"), "-I" + str(ROOT / "mac/OLMSmoother/Mac"), str(SOURCE), "-o", str(binary)], check=True)
        run = subprocess.run([str(binary)], text=True, capture_output=True, check=True)
    production = json.loads(run.stdout)
    report = {
        "schema_version": 1, "status": "exact" if production == actual else "mismatch",
        "entrypoint": "EffectMain(PF_Cmd_GLOBAL_SETUP)", "actual_aex": actual,
        "production": production, "fixture_sha256": FIXTURE_SHA256,
        "production_source": "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
        "scope": "public GLOBAL_SETUP return/out_flags/out_flags2 only",
        "not_proven": ["PARAMS_SETUP", "PF8/PF16 render", "Smart Render reachability", "After Effects host exactness"]
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "exact" else 1

if __name__ == "__main__": raise SystemExit(main())
