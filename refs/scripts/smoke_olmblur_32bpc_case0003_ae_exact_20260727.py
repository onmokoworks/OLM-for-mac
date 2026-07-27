#!/usr/bin/env python3
"""Fail closed on drift in the OLMBlur case_0003 32bpc AE-exact record."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT / "refs/conformance/olmblur_32bpc_case0003_ae_exact_20260727.json"
)
SOURCE = ROOT / "core/olmblur_worker32_legacy.cpp"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["status"] == "raw_float32_ae_exact"
    assert evidence["ae_exact_claim"] is True
    assert evidence["case_id"] == "OLMBlur/case_0003"
    assert evidence["contract"]["bits_per_channel"] == 32
    assert evidence["contract"]["renderer"] == {"name": "SOFTWARE", "raw": 1816}
    assert evidence["contract"]["working_space_raw"] == "None"
    assert evidence["contract"]["linear_blending"] is False
    assert evidence["contract"]["params"] == {
        "Bias Direction": 1,
        "Blur Amount": 248.6,
        "Blur Amount readback": 248.600006103516,
        "Blur Smoothness": 100,
        "Legacy": 1,
        "Number of Repeat": 10,
    }
    for branch in ("no_effect_control", "effect_on"):
        comparison = evidence["comparison"][branch]
        assert comparison["mismatched_values"] == 0
        assert comparison["max_raw_u32_delta"] == 0
        assert comparison["total_values"] == 8294400
    attribution = evidence["effect_attribution"]
    assert attribution["windows_effect_vs_control"] == \
        attribution["mac_effect_vs_control"]
    assert attribution["windows_effect_vs_control"]["mismatched_values"] > 0
    cause = evidence["root_cause"]
    assert cause["mac_libsystem_expf_vs_windows_ucrtbase_expf"] == {
        "max_raw_u32_delta": 1,
        "mismatch_count": 8,
        "mismatches_by_iteration": [0, 0, 0, 0, 1, 1, 2, 3, 1, 0],
    }
    assert cause["windows_ucrtbase_expf_vs_double_exp_float_cast"] == {
        "max_raw_u32_delta": 0,
        "mismatch_count": 0,
    }
    assert cause["native_fullframe_discriminator"][
        "mac_double_exp_vs_windows_ucrt_exp"
    ] == {
        "max_raw_u32_delta": 0,
        "mismatched_values": 0,
        "total_values": 33177600,
    }
    source = SOURCE.read_text(encoding="utf-8")
    assert "const float exponent = -square / denominator;" in source
    assert "std::exp(static_cast<double>(exponent))" in source
    assert "OLMBLUR_CASE0003" not in source
    print("[OK] OLMBlur case_0003 32bpc AE exact evidence is internally bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
