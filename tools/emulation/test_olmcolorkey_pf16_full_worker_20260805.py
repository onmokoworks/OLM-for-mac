#!/usr/bin/env python3
"""Regression for the bounded actual-AEX OLMColorKey PF16 worker fixture."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmcolorkey_pf16_full_worker_actual_aex_20260805.json"


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["schema_version"] == 2
    assert [case["case"] for case in report["cases"]] == [
        "no_key", "enabled_black_key", "enabled_black_key_edge_blur_1_single",
        "enabled_black_key_edge_blur_1_line", "enabled_black_key_edge_blur_1_all",
        "enabled_black_key_edge_blur_2_single",
        "enabled_black_key_edge_blur_1.5_single",
        "enabled_black_key_edge_blur_0.5_single",
        "enabled_black_key_edge_blur_2.5_single",
        "enabled_black_key_edge_blur_3_single",
        "enabled_black_key_edge_blur_3.5_single",
        "enabled_black_key_edge_blur_4_single",
        "enabled_black_key_edge_blur_2_single_direction_1",
        "enabled_black_key_edge_blur_2_single_direction_3",
        "enabled_black_key_edge_blur_2_single_direction_4",
        "enabled_black_key_edge_blur_2_single_direction_0",
        "enabled_black_key_edge_blur_1_single_direction_1",
        "enabled_black_key_edge_blur_2_center",
    ]
    for case in report["cases"]:
        assert case["aex"]["sha256"] == "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
        assert case["fixture"] == {
            "active_bytes_per_row": 32, "dimensions": [4, 3],
            "padding_bytes_per_row": 8, "pixel_format": "PF16", "rowbytes": 40,
        }
        assert case["execution"]["hits"] == {
            "parameter_materialize": 1, "pf16_worker": 1, "smart_worker": 1,
        }
        iterate = [event for event in case["execution"]["events"] if event["callback"] == "PF_Iterate16"]
        assert [(event["guest_callback"], event["calls"]) for event in iterate] == [
            ("0x1800029d0", 12), ("0x1800035b0", 12),
        ]
        assert all(case["acceptance_gates"].values())
        captures = case["captures"]
        if case["parameter_record"]["edge_blur_amount"] == 0.0:
            assert captures["output_actual_sha256"] == captures["direct_actual_pixel_callback_sha256"]
            assert captures["worker_first_pixel_hex"] == captures["direct_pixel_first_pixel_hex"]
    no_key, enabled, single, line, all_key, single2, single15, single05, single25, single3, single35, single4, direction1, direction3, direction4, direction0, direction1_amount1, center = report["cases"]
    assert no_key["parameter_record"]["enabled_black_key_count"] == 0
    assert enabled["parameter_record"]["enabled_black_key_count"] == 1
    assert enabled["captures"]["input_first_pixel_hex"] == "0080000000000000"
    assert enabled["captures"]["worker_first_pixel_hex"] == "0000000000000000"
    assert single["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert line["execution"]["temporary_handles"][0]["f32"] == [0.5] * 4 + [0.0] * 8
    assert all_key["execution"]["temporary_handles"][0]["f32"] == [1.0] * 12
    assert single2["parameter_record"]["edge_blur_amount"] == 2.0
    assert single2["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single2["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert single15["parameter_record"]["edge_blur_amount"] == 1.5
    assert single15["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single15["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert single05["parameter_record"]["edge_blur_amount"] == 0.5
    assert single05["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single05["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert single25["parameter_record"]["edge_blur_amount"] == 2.5
    assert single25["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single25["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert single3["parameter_record"]["edge_blur_amount"] == 3.0
    assert single3["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single3["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert single35["parameter_record"]["edge_blur_amount"] == 3.5
    assert single35["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single35["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert single4["parameter_record"]["edge_blur_amount"] == 4.0
    assert single4["execution"]["temporary_handles"][0]["f32"] == [0.5] + [0.0] * 11
    assert bytes.fromhex(single4["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0040000000000000")
    assert direction1["parameter_record"]["edge_blur_direction"] == 1
    assert direction1["execution"]["temporary_handles"][0]["f32"] == [-0.2853981554508209] + [0.0] * 11
    assert bytes.fromhex(direction1["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("87a4000000000000")
    assert direction3["parameter_record"]["edge_blur_direction"] == 3
    assert direction3["execution"]["temporary_handles"][0]["f32"] == [1.0] + [0.0] * 11
    assert bytes.fromhex(direction3["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0000000000000000")
    assert direction4["parameter_record"]["edge_blur_direction"] == 4
    assert direction4["execution"]["temporary_handles"][0]["f32"] == [1.0] + [0.0] * 11
    assert bytes.fromhex(direction4["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0000000000000000")
    assert direction0["parameter_record"]["edge_blur_direction"] == 0
    assert direction0["execution"]["temporary_handles"][0]["f32"] == [1.0] + [0.0] * 11
    assert bytes.fromhex(direction0["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("0000000000000000")
    assert direction1_amount1["parameter_record"]["edge_blur_direction"] == 1
    assert direction1_amount1["parameter_record"]["edge_blur_amount"] == 1.0
    assert direction1_amount1["execution"]["temporary_handles"][0]["f32"] == [-0.2853981554508209] + [0.0] * 11
    assert bytes.fromhex(direction1_amount1["captures"]["output_active_rows_hex"][0])[:8] == bytes.fromhex("87a4000000000000")
    assert center["parameter_record"]["edge_blur_direction"] == 2
    assert center["parameter_record"]["edge_blur_amount"] == 2.0
    assert center["execution"]["temporary_handles"][0]["f32"] == [0.0] * 5 + [0.5] + [0.0] * 6
    center_rows = b"".join(bytes.fromhex(row) for row in center["captures"]["output_active_rows_hex"])
    assert center_rows[5 * 8:6 * 8] == bytes.fromhex("0040000000000000")
    assert "parameter materialization" in report["claim_boundary"]
    assert "No AE-host or general case0001 exact claim" in report["claim_boundary"]
    print("PASS: OLMColorKey bounded actual-AEX PF16 full worker fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
