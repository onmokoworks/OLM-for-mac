#!/usr/bin/env python3
"""Fail closed if the OLMBlur case_0002 32bpc AE-exact record drifts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "refs/conformance/olmblur_32bpc_case0002_ae_exact_20260727.json"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["kind"] == "olmblur_32bpc_case0002_ae_exact"
    assert evidence["status"] == "raw_float32_ae_exact"
    assert evidence["ae_exact_claim"] is True
    assert evidence["ae_version"] == "26.3x87"

    contract = evidence["contract"]
    assert contract["bits_per_channel"] == 32
    assert contract["renderer"] == {"name": "SOFTWARE", "raw": 1816}
    assert contract["working_space_raw"] == "None"
    assert contract["linear_blending"] is False
    assert contract["params"] == {
        "Bias Direction": 2,
        "Blur Amount": 129.4,
        "Blur Amount readback": 129.399993896484,
        "Blur Smoothness": 100,
        "Legacy": 0,
        "Number of Repeat": 2,
    }
    assert contract["output"] == {
        "channels": ["A", "B", "G", "R"],
        "compression": "none",
        "dimensions": [1920, 1080],
        "sample_type": "FLOAT",
        "template": "OLM EXR 32 Float",
    }

    for gate in ("no_effect_control", "effect_on"):
        comparison = evidence["comparison"][gate]
        assert comparison == {
            "height": 1080,
            "max_raw_u32_delta": 0,
            "mismatched_values": 0,
            "total_values": 8294400,
            "width": 1920,
        }

    binding = evidence["cross_host_project_binding"]
    assert binding["result"] == "identical_after_path_normalization"
    assert binding["file_reference_normalized_sha256"] == (
        "2ed3afe9d2b82c7e4dab2c5e3ae821d6d9e71497a1865e08f9d8f75d1e70a97a"
    )

    runtime = evidence["windows"]["loaded_plugin_proof"]
    assert runtime["method"] == "Microsoft-Windows-Kernel-Process ETW process+image events"
    assert runtime["aerender_parent_pid"] == evidence["windows"]["aerender"]["pid"]
    assert runtime["afterfx_pid"] == 45732
    assert runtime["event_count"] == 2
    assert [event["event"] for event in runtime["events"]] == ["ImageLoad", "ImageUnload"]
    assert all(event["pid"] == runtime["afterfx_pid"] for event in runtime["events"])
    assert runtime["aex_path"].endswith(r"\OLM\OLMBlur.aex")
    assert runtime["aex_sha256"] == (
        "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
    )
    assert evidence["mac"]["plugin"]["sha256"] == (
        "71df7efc027b463327fefa23575fff5f80d4b38ff529ae97418d79297f4f0d72"
    )

    attribution = evidence["effect_attribution"]
    assert attribution["windows_effect_vs_control"] == attribution["mac_effect_vs_control"]
    assert attribution["windows_effect_vs_control"] == {
        "max_raw_u32_delta": 1054075639,
        "mismatched_values": 207108,
    }
    print("PASS: OLMBlur case_0002 32bpc AE exact evidence is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
