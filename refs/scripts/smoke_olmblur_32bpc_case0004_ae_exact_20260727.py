#!/usr/bin/env python3
"""Fail closed on drift in the OLMBlur case_0004 32bpc AE-exact record."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT / "refs/conformance/olmblur_32bpc_case0004_ae_exact_20260727.json"
)
SOURCE = ROOT / "core/olmblur_worker32_nonlegacy.cpp"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["status"] == "raw_float32_ae_exact"
    assert evidence["ae_exact_claim"] is True
    assert evidence["case_id"] == "OLMBlur/case_0004"
    assert evidence["contract"]["bits_per_channel"] == 32
    assert evidence["contract"]["renderer"] == {"name": "SOFTWARE", "raw": 1816}
    assert evidence["contract"]["working_space_raw"] == "None"
    assert evidence["contract"]["linear_blending"] is False
    assert evidence["contract"]["params"] == {
        "Bias Direction": 1,
        "Blur Amount": 125.6,
        "Blur Amount readback": 125.599998474121,
        "Blur Smoothness": 100,
        "Legacy": 0,
        "Number of Repeat": 4,
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
    assert cause["old_mac_ae_effect_vs_windows_ae_effect"] == {
        "max_raw_u32_delta": 4,
        "mismatched_values": 5439,
        "total_values": 8294400,
    }
    assert cause["coefficient_candidate_gate"] == {
        "all_exact": True,
        "coefficient_words": 177,
        "radius_sequence": [125, 36, 10, 2],
    }
    assert evidence["windows"]["loaded_plugin_proof"]["afterfx_pid"] == 24992
    assert evidence["windows"]["loaded_plugin_proof"]["event_count"] == 2
    source = SOURCE.read_text(encoding="utf-8")
    assert "const float exponent =" in source
    assert "std::exp(static_cast<double>(exponent))" in source
    assert "OLMBLUR_CASE0004" not in source
    print("[OK] OLMBlur case_0004 32bpc AE exact evidence is internally bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
