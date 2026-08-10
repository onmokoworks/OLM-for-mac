#!/usr/bin/env python3
"""Regression test for the bounded OLMBlur 32bpc residual classification."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from audit_olmblur_32bpc_red_only_residual_20260718 import (  # noqa: E402
    AEX,
    CASE,
    EXPECTED_AEX_SHA256,
    actual_aex_source_bytes,
    compile_worker,
    run_actual_aex_case,
    run_worker,
    sha256,
)


def main() -> int:
    import tempfile

    assert sha256(AEX) == EXPECTED_AEX_SHA256
    actual, run = run_actual_aex_case(CASE)
    source = actual_aex_source_bytes(CASE["width"], CASE["height"])
    with tempfile.TemporaryDirectory(prefix="olmblur_red_only_test_") as name:
        directory = Path(name)
        executable = compile_worker(directory)
        portable = run_worker(
            executable,
            directory,
            source,
            CASE["width"],
            CASE["height"],
            "bounded",
        )
    assert actual == portable

    report_path = ROOT / "refs/conformance/olmblur_32bpc_red_only_residual_20260718.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["facts"]["control_mismatches_by_channel"] == {"A": 0, "B": 0, "G": 0, "R": 0}
    assert report["facts"]["effect_mismatches_by_channel"] == {"A": 0, "B": 0, "G": 0, "R": 201576}
    assert report["facts"]["full_mac_effect_equals_current_core"] is True
    assert report["facts"]["bounded_current_aex_repeat1_equals_current_core"] is True
    assert report["hypotheses"]["channel_mapping"] == "rejected"
    assert report["hypotheses"]["source_stride"] == "rejected"
    assert report["hypotheses"]["simd_lane"].startswith("rejected")
    assert report["hypotheses"]["reference_selection"].startswith(
        "retained 20260710 Windows EXR conflicts"
    )
    assert report["facts"]["authoritative_same_aex_case0001_ae_exact"] is True
    authoritative = ROOT / report["facts"]["authoritative_exact_record"]
    assert sha256(authoritative) == report["facts"]["authoritative_exact_record_sha256"]
    exact = json.loads(authoritative.read_text(encoding="utf-8"))
    assert exact["ae_exact_claim"] is True
    assert exact["windows"]["loaded_plugin_proof"]["aex_sha256"] == EXPECTED_AEX_SHA256
    assert exact["comparison"]["effect_on"]["mismatched_values"] == 0
    assert exact["comparison"]["no_effect_control"]["mismatched_values"] == 0
    assert report["classification"] == "superseded_reference_conflict"
    assert report["ae_exact_claim"] is False
    assert report["plugin_source_change"] is False
    print(json.dumps({"status": "pass", "instructions": run["instructions"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
