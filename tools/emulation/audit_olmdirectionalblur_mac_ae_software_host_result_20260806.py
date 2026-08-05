#!/usr/bin/env python3
"""Attest the bounded current-binary DirectionalBlur Mac AE host result."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path("/tmp/olm_dblur_host_20260805")
RESULT = RUN / "result.json"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
EXPECTED_BINARY = "6a89dd4d9bca3f5b3c7af7782627d1b7b7bb6b0c45afe83945d056f1db7519f0"
EXPECTED_CONTROL = "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4"
EXPECTED_EFFECT = "91b2af26cfad17c1d0cb620ed9844ceb5254090567350c312c1999d9993a0e05"
OUT = ROOT / "refs/conformance/olmdirectionalblur_pf8_current_mac_ae_exact_20260806.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rendered = json.loads(RESULT.read_text()) if RESULT.is_file() else {}
    pids = [int(v) for v in subprocess.run(
        ["pgrep", "-x", "After Effects"], capture_output=True, text=True
    ).stdout.split() if v.isdigit()]
    pid = rendered.get("ae_pid")
    loaded = subprocess.run(
        ["lsof", "-Fn", "-p", str(pid)], capture_output=True, text=True
    ).stdout.splitlines() if pid else []
    exact_path = "n" + str(INSTALLED.resolve())
    gates = {
        "payload_status_pass": rendered.get("status") == "pass",
        "same_single_ae_pid": pids == [pid],
        "sole_exact_loaded_module": loaded.count(exact_path) == 1,
        "installed_binary_hash_exact": INSTALLED.is_file() and sha(INSTALLED) == EXPECTED_BINARY,
        "payload_binary_hash_exact": rendered.get("binary_sha256") == EXPECTED_BINARY,
        "software_pf8_contract": rendered.get("renderer") == "SOFTWARE" and rendered.get("bits_per_channel") == 8,
        "control_file_exact": (RUN / "case_0001__no_effect.png").is_file() and sha(RUN / "case_0001__no_effect.png") == EXPECTED_CONTROL,
        "effect_file_exact": (RUN / "case_0001__effect_on.png").is_file() and sha(RUN / "case_0001__effect_on.png") == EXPECTED_EFFECT,
        "payload_control_hash_exact": rendered.get("control_sha256") == EXPECTED_CONTROL,
        "payload_effect_hash_exact": rendered.get("actual_output_sha256") == EXPECTED_EFFECT,
    }
    report = {
        "status": "pass" if all(gates.values()) else "fail",
        "ae_exact_claim": all(gates.values()),
        "plugin": "OLMDirectionalBlur",
        "case": "case_0001",
        "host": {"application": "After Effects 26.3.0.87", "renderer": "SOFTWARE", "bits_per_channel": 8, "pid": pid},
        "identity": {"installed_binary": str(INSTALLED), "expected_sha256": EXPECTED_BINARY, "observed_ae_pids": pids},
        "output": {"control_sha256": EXPECTED_CONTROL, "effect_sha256": EXPECTED_EFFECT},
        "gates": gates,
        "claim_boundary": "Current installed binary, Mac AE 26.3.0.87 Software/PF8 case_0001 only; no other parameters, depths, renderer, or host are promoted.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "report": str(OUT)}))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
