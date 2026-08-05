#!/usr/bin/env python3
"""Audit the OLMDirectionalBlur AE Software host-phase package without launching AE."""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "refs/conformance/olmdirectionalblur_mac_ae_software_host_phase_20260805.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dimensions(path: Path) -> list[int]:
    with Image.open(path) as image:
        return list(image.size)


def main() -> int:
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    installed = Path(spec["installed_identity"]["binary"])
    case = spec["case"]
    runner = ROOT / spec["runner"]
    payload = ROOT / spec["payload"]
    result_audit = ROOT / "tools/emulation/audit_olmdirectionalblur_mac_ae_software_host_result_20260806.py"
    checks = {
        "prepared_not_run": spec["status"] == "prepared_not_run" and spec["ae_launched"] is False,
        "installed_sha": installed.is_file() and digest(installed) == spec["installed_identity"]["sha256"],
        "input_sha": digest(ROOT / case["input"]["path"]) == case["input"]["sha256"],
        "control_sha": digest(ROOT / case["expected_control"]["path"]) == case["expected_control"]["sha256"],
        "actual_output_sha": digest(ROOT / case["expected_actual_output"]["path"]) == case["expected_actual_output"]["sha256"],
        "control_dimensions": dimensions(ROOT / case["expected_control"]["path"]) == case["expected_control"]["dimensions"],
        "actual_output_dimensions": dimensions(ROOT / case["expected_actual_output"]["path"]) == case["expected_actual_output"]["dimensions"],
        "save_frame_dimensions": spec["project"]["save_frame_output"] == {"width": 960, "height": 540, "format": "PNG RGBA8"},
        "depth_renderer": spec["project"]["bits_per_channel"] == 8 and spec["project"]["renderer"] == "SOFTWARE",
        "parameter_count": len(case["parameters"]) == 15,
    }
    loader_text = runner.read_text(encoding="utf-8")
    text = payload.read_text(encoding="utf-8")
    for token in (spec["installed_identity"]["sha256"], case["input"]["sha256"],
                  case["expected_control"]["sha256"], case["expected_actual_output"]["sha256"],
                  "GpuAccelType.SOFTWARE", "module mapping requires external pre/post attestation",
                  "OLM Directional Blur"):
        checks["runner:" + token[:16]] = token in text
    result_audit_text = result_audit.read_text(encoding="utf-8")
    checks["external_identity_audit"] = all(token in result_audit_text for token in (
        '"lsof", "-Fn", "-p"', "sole_exact_loaded_module", "installed_binary_hash_exact",
        "same_single_ae_pid",
    ))
    checks["loader_evalfile"] = "$.evalFile(new File(PAYLOAD))" in loader_text
    checks["loader_absolute_trace"] = '/tmp/olm_dblur_host_loader_trace.log' in loader_text
    checks["loader_no_alert_rethrow"] = "alert(" not in loader_text and "throw " not in loader_text
    if not all(checks.values()):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: " + json.dumps(checks, sort_keys=True))
    print(json.dumps({"status": "pass", "plugin": "OLMDirectionalBlur", "ae_launched": False,
                      "installed_sha256": digest(installed), "depth": 8, "renderer": "SOFTWARE",
                      "expected_actual_output_sha256": case["expected_actual_output"]["sha256"],
                      "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
