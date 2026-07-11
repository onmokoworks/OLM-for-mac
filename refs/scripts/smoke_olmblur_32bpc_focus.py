#!/usr/bin/env python3
"""Validate and materialize the focused OLMBlur 32bpc bridge spec."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json"
SOURCE = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur"
MATERIALIZER = ROOT / "scripts/materialize_32bpc_mac_request.py"


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["scope"] == {
        "bit_depth": "32bpc",
        "plugin_filters": ["OLMBlur"],
        "feature_filters": [],
        "plugin_count": 1,
        "case_count": 7,
    }
    assert [case["id"] for case in spec["cases"]] == [f"olmblur__case_{i:04d}" for i in range(1, 8)]
    assert [case["input"] for case in spec["cases"]] == [f"olmblur_case_{i:04d}_source" for i in range(1, 8)]
    assert spec["render_sets"] == [{
        "id": "software_32bpc",
        "project_gpu_accel_type.current_name": "SOFTWARE",
        "bit_depth": "32bpc",
        "bits_per_channel": 32,
        "required": True,
    }]
    assert spec["output_requirements"]["preferred_formats"] == ["exr"]
    assert spec["compare_policy"]["ae_exact_claim"] is False
    assert spec["source_provenance"]["float_exr_status"]["normalized_input_directory"] is False
    assert spec["source_provenance"]["float_exr_status"]["windows_answered_partial_return"] is True
    for item in spec["inputs"]:
        frame = SOURCE / item["before_effects_frame"]
        assert frame.is_file(), frame
        assert hashlib.sha256(frame.read_bytes()).hexdigest() == item["sha256"]

    with tempfile.TemporaryDirectory(prefix="olmblur_32bpc_focus_") as tmp:
        output = Path(tmp) / "bridge"
        subprocess.run([
            sys.executable, str(MATERIALIZER), "--spec", str(SPEC), "--source-reference", str(SOURCE),
            "--output", str(output), "--case-id", "olmblur__case_0001",
        ], check=True)
        request = json.loads((output / "request_manifest.json").read_text(encoding="utf-8"))
        reference = json.loads((output / "reference_manifest.json").read_text(encoding="utf-8"))
        result = json.loads((output / "AE_32BPC_RESULT.template.json").read_text(encoding="utf-8"))
        assert request["render_set"]["id"] == "software_32bpc"
        assert request["cases"][0]["frame"] == "olmblur__case_0001.exr"
        assert reference["project"] == {"bits_per_channel": 32, "renderer": "SOFTWARE"}
        assert len(reference["cases"][0]["effects"][0]["params"]) == 7
        assert result["cases"][0]["output_format"] == "exr"
        assert list((output / "input").glob("*.png"))
    print("[OK] OLMBlur focused 32bpc spec contract")
    print("[OK] OLMBlur focused 32bpc Mac bridge materialization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
