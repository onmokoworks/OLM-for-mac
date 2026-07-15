#!/usr/bin/env python3
"""Smoke-test the OLMBlur Mac observation contract without AE."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.run_olmblur_case0006_mac_observation_20260715 import parse_observation, validate_artifacts


RUNNER = ROOT / "scripts/run_olmblur_case0006_mac_observation_20260715.py"
REQUEST = ROOT / "refs/mac_validation_requests/olmblur_case0006_mac_observation_20260715.json"


def main() -> None:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert request["status"] == "sendable_fail_closed"
    assert request["run_count"] == 1
    assert request["observation"]["coordinate"] == [601, 598]
    runner = RUNNER.read_text(encoding="utf-8")
    assert request["observation"]["mac_plugin_binary_sha256"] == (
        "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206"
    )
    for token in (
        "OLMBLUR_OBSERVE_CASE0006_PIXEL",
        "OLMBLUR_OBSERVE_PLUGIN_SHA256",
        "--plugin-path",
        "installed Mac OLMBlur binary identity mismatch",
        "--keep-open",
        "validate_artifacts",
        "FAIL-CLOSED",
    ):
        assert token in runner, token
    action = subprocess.run(
        [sys.executable, str(ROOT / "scripts/print_next_olm_action.py"), "--json"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    action_json = json.loads(action.stdout)
    assert "olmblur_case0006_mac_observation_20260715" not in action_json["pending_requests"]
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp)
        log_path = output / "observation.log"
        prefix = (
            "OLMBLUR_OBSERVE_STORE16 plugin=OLMBlur effect=OLM_Blur "
            "case_id=olmblur__case_0006 request_id=olmblur_case0006_mac_observation_20260715 "
            "render_id=smoke plugin_sha256="
            "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206 "
            "project_bpc=16 renderer=Software x=601 y=598 w=1920 h=1080 "
            "blur_amount=5 blur_smoothness=100 repeat=10 bias_dir=1 legacy=0 "
        )
        log_path.write_text(
            prefix
            + "pre_store=(1100.5,363.5,0) "
            + f"pre_store_hex=({(1100.5).hex()},{(363.5).hex()},{(0.0).hex()}) "
            + "stored=(1101,364,0,32768)\n",
            encoding="utf-8",
        )
        parsed = parse_observation(log_path)
        assert parsed["fields"]["stored"] == "(1101,364,0,32768)"
        log_path.write_text(
            prefix
            + "pre_store=(1100.5,363.5,0) "
            + f"pre_store_hex=({(1100.5).hex()},{(363.5).hex()},{(0.0).hex()}) "
            + "stored=(1101,364,0,32769)\n",
            encoding="utf-8",
        )
        try:
            parse_observation(log_path)
        except ValueError as error:
            assert "outside 0..32768" in str(error)
        else:
            raise AssertionError("out-of-range stored word did not fail closed")
        try:
            validate_artifacts(output, "olmblur-case0006-mac-observation-20260715")
        except ValueError as error:
            assert "missing AE_SINGLE_CASE_RESULT.json" in str(error)
        else:
            raise AssertionError("missing artifacts did not fail closed")
        validate_only = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--validate-only",
                "--output-dir",
                str(output),
                "--plugin-path",
                str(output / "missing.plugin"),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert validate_only.returncode == 2
        assert "Mac OLMBlur binary is missing" in validate_only.stdout
    print("[OK] OLMBlur case_0006 Mac observation request is deterministic and fail-closed")


if __name__ == "__main__":
    main()
