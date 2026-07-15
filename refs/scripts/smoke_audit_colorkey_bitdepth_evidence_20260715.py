#!/usr/bin/env python3
"""Smoke-test the bounded OLMColorKey bit-depth evidence audit."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_colorkey_bitdepth_evidence_20260715 import build_report  # noqa: E402


def main() -> int:
    report = build_report(ROOT)
    assert report["evidence"]["8bpc"]["exact_cases"] == 9
    assert report["evidence"]["16bpc"]["exact_cases"] == 9
    assert report["evidence"]["32bpc"]["classification"] == "windows-software-float-reference-only"
    assert report["evidence"]["32bpc"]["float_preserving"] is True
    assert len(report["evidence"]["32bpc"]["pair_validation"]) == 9
    assert all(row["effect_float_exr"] and row["before_effects_float_exr"] for row in report["evidence"]["32bpc"]["pair_validation"])
    assert report["evidence"]["32bpc"]["historical_png_probe"]["classification"] == "probe-only-png-return"
    assert report["blocker"]["id"] == "32bpc-mac-windows-raw-float-comparison"
    assert report["algorithm_conclusion"]["inference"].startswith("No bounded source-code change")
    assert report["source_audit_inputs"]["edge_ir_current_exact_present"] is True
    assert all(report["feature_coverage_facts"]["source_markers_present"].values())
    assert report["mac_float_gate"]["raw_float_comparison_ready"] is False
    assert report["mac_float_gate"]["ae_exact_claim_allowed"] is False
    assert report["fail_closed"]["32bpc_ae_exact_claim_allowed"] is False
    print("[OK] OLMColorKey bit-depth evidence audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
