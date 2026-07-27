#!/usr/bin/env python3
"""Fail closed on drift in the OLMBlur case_0005 32bpc AE-exact record."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT / "refs/conformance/olmblur_32bpc_case0005_ae_exact_20260727.json"
)


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["status"] == "raw_float32_ae_exact"
    assert evidence["ae_exact_claim"] is True
    assert evidence["case_id"] == "OLMBlur/case_0005"
    assert evidence["contract"]["bits_per_channel"] == 32
    assert evidence["contract"]["renderer"] == {"name": "SOFTWARE", "raw": 1816}
    assert evidence["contract"]["working_space_raw"] == "None"
    assert evidence["contract"]["linear_blending"] is False
    assert evidence["contract"]["params"] == {
        "Bias Direction": 1,
        "Blur Amount": 5,
        "Blur Amount readback": 5,
        "Blur Smoothness": 100,
        "Legacy": 0,
        "Number of Repeat": 2,
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
    old = evidence["reference_generation_audit"]
    assert old["classification"] == "older_reference_contract_rejected"
    assert old["old_windows_no_effect_vs_fresh_mac_no_effect"] == {
        "max_raw_u32_delta": 94225591,
        "mismatched_values": 63644,
    }
    runtime = evidence["windows"]["loaded_plugin_proof"]
    assert runtime["afterfx_pid"] == 44300
    assert runtime["event_count"] == 2
    assert runtime["aex_sha256"] == \
        "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
    assert evidence["verification"]["core_change"] == \
        "none after the case_0004 coefficient fix"
    print("[OK] OLMBlur case_0005 32bpc AE exact evidence is internally bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
