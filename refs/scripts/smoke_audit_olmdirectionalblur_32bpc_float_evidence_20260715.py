#!/usr/bin/env python3
"""Smoke-test the bounded DirectionalBlur bit-depth evidence audit."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_olmdirectionalblur_32bpc_float_evidence_20260715 import build_report


def main() -> int:
    report = build_report()
    windows = report["evidence"]["32bpc_windows"]
    assert windows["classification"] == "windows-software-float-reference-only"
    assert windows["case_count"] == 10
    assert windows["float_preserving"] is True
    assert all(row["effect_float_exr"] and row["before_effects_float_exr"] for row in windows["cases"])
    assert report["evidence"]["16bpc"]["directionalblur_case_count"] == 0
    assert report["evidence"]["32bpc_family_counts"]["variation"] == 10
    assert report["decision"]["raw_cross_host_equality_required"] is True
    assert report["decision"]["ae_exact_claim_allowed_now"] is False
    print("[OK] OLMDirectionalBlur 16/32bpc evidence audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
