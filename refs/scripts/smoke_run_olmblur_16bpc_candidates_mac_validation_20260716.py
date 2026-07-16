#!/usr/bin/env python3
"""Static smoke for the identity-bound OLMBlur 16bpc candidate wrapper."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts/run_olmblur_16bpc_candidates_mac_validation_20260716.py"
CONTRACT = ROOT / "refs/conformance/olmblur_16bpc_candidates_mac_validation_20260716.json"
BINARY = ROOT / "mac/OLMBlur/Mac/build/Debug/OLMBlur.plugin/Contents/MacOS/OLMBlur"


def main() -> int:
    source_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    binary_sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    record = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert record["status"] == "pending_live_loaded_module_proof"
    assert record["platform"] == "macOS-only"
    assert record["ae_execution"] == "not_run_by_this_wrapper"
    assert record["source_identity"]["git_revision_required"] == source_revision
    assert {item["path"] for item in record["source_identity"]["files"]} == {
        "mac/OLMBlur/OLMBlur.cpp", "core/olmblur_worker16_legacy.cpp"
    }
    assert not Path(record["binary_identity"]["path"]).is_absolute()
    assert record["binary_identity"]["sha256"] == binary_sha
    assert record["request_identity"]["selected_case_ids"] == ["olmblur__case_0003", "olmblur__case_0004"]
    assert {case["id"] for case in record["cases"]} == set(record["request_identity"]["selected_case_ids"])
    assert "PNG-only, byte-view, or pre-store-only evidence" in record["fail_closed"]
    assert "exact is permitted only when loaded-module identity and raw true16 equality both pass" in record["required_future_proof"]["promotion"]
    with tempfile.TemporaryDirectory(prefix="olmblur_16bpc_candidate_contract_") as temporary:
        output = Path(temporary) / "contract.json"
        proc = subprocess.run([
            sys.executable, str(WRAPPER), "--source-revision", source_revision,
            "--binary-path", str(BINARY), "--output", str(output),
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert proc.returncode == 2
        assert "PAUSED: live loaded-module proof" in proc.stderr
        generated = json.loads(output.read_text(encoding="utf-8"))
        assert generated == record
    print("[OK] OLMBlur 16bpc candidate wrapper is identity-bound and fail-closed")
    print(f"[OK] selected cases: {record['request_identity']['selected_case_ids']}")
    print("[OK] static smoke did not launch AE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
