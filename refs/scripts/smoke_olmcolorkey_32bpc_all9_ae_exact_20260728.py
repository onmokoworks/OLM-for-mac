#!/usr/bin/env python3
"""Smoke the durable OLMColorKey all-nine 32bpc AE-exact record."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "refs/conformance/olmcolorkey_32bpc_all9_ae_exact_20260728.json"


def main() -> int:
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert data["kind"] == "olmcolorkey_32bpc_all9_ae_exact"
    assert data["ae_exact_claim"] is True
    assert data["classification"] == "windows_mac_ae_exact"
    contract = data["contract"]
    assert contract["ae_version"] == "26.3x87"
    assert contract["bits_per_channel"] == 32
    assert contract["renderer_raw"] == 1816
    assert contract["working_space_raw"] == "None"
    assert contract["linear_blending"] is False
    assert contract["word_count_per_gate"] == 8294400
    assert "Preserve RGB" in contract["output"]

    rows = data["new_windows_native_parameter_attested_cases"]
    assert [row["case_id"] for row in rows] == [
        "olmcolorkey__case_0001",
        "olmcolorkey__case_0003",
        "olmcolorkey__case_0004",
        "olmcolorkey__case_0005",
        "olmcolorkey__case_0006",
        "olmcolorkey__case_0007",
        "olmcolorkey__case_0008",
    ]
    for row in rows:
        assert row["parameter_count"] == 219
        assert row["parameter_readback_exact"] is True
        assert row["preparation_pid"] > 0
        assert row["aerender_pid"] > 0
        assert row["afterfx_pid"] > 0
        etw = row["etw"]
        assert etw["afterfx_process_start_line"] > 0
        assert etw["aex_image_load_line"] > 0
        assert etw["aex_image_unload_line"] > etw["aex_image_load_line"]
        for gate_name in ("no_effect", "effect_on"):
            gate = row["gates"][gate_name]
            assert len(gate["windows_exr_sha256"]) == 64
            assert len(gate["mac_exr_sha256"]) == 64
            assert gate["mismatched_float32_words"] == 0
            assert gate["max_raw_u32_delta"] == 0

    assert [row["case_id"] for row in data["previously_promoted_cases"]] == [
        "olmcolorkey__case_0002",
        "olmcolorkey__case_0009",
    ]
    summary = data["summary"]
    assert summary["declared_case_count"] == 9
    assert summary["raw_gate_count"] == 18
    assert summary["exact_gate_count"] == 18
    assert summary["max_raw_u32_delta"] == 0
    print("PASS: OLMColorKey declared 32bpc all-nine AE-exact evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
