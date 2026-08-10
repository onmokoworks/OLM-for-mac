#!/usr/bin/env python3
"""Pin OLMColorKey's actual Windows UPDATE_PARAMS_UI decision surface."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
AEX_SHA = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
UPDATE_METHOD = 0x180001A50
REPORT = ROOT / "refs/conformance/olmcolorkey_update_params_ui_actual_aex_20260810.json"
PIPL = ROOT / "mac/OLMColorKey/OLMColorKeyPiPL.r"

CASES = (
    {"name": "global", "count": 1, "per_color": 0, "per_component": 0, "replace": 0,
     "use_color": {0: 0}, "use_replace": {0: 0}},
    {"name": "component", "count": 1, "per_color": 0, "per_component": 1, "replace": 0,
     "use_color": {0: 1}, "use_replace": {0: 0}},
    {"name": "per_color", "count": 2, "per_color": 1, "per_component": 0, "replace": 1,
     "use_color": {0: 1, 1: 0}, "use_replace": {0: 1, 1: 0}},
    {"name": "per_color_component", "count": 25, "per_color": 1, "per_component": 1,
     "replace": 1, "use_color": {0: 1, 24: 1}, "use_replace": {0: 1, 24: 1}},
)


def expected(case: dict) -> list[list[int | str]]:
    pc, component = case["per_color"], case["per_component"]
    rows: list[list[int | str]] = [
        ["param_ui_disabled", 2, int(bool(pc or component))],
        ["stream_enabled", 8, int(bool(component and not pc))],
        ["stream_enabled", 9, int(bool(component and not pc))],
        ["stream_enabled", 10, int(bool(component and not pc))],
    ]
    for i in range(25):
        inactive = i >= case["count"]
        scalar = int(not inactive and pc and not component)
        channels = int(not inactive and pc and component)
        color_disk, use_disk, replace_use_disk = 0x16 + i * 5, 0x20C + i * 3, 0x20D + i * 3
        replace_disk = replace_use_disk + 1
        use_color = case["use_color"].get(i, 0)
        use_replace = case["use_replace"].get(i, 0)
        rows += [
            ["param_ui_disabled", color_disk, int(not use_color)],
            ["stream_enabled", color_disk, int(not inactive)],
            ["stream_enabled", use_disk, int(not inactive)],
            ["stream_enabled", replace_use_disk,
             int(not inactive and case["replace"])],
            ["param_ui_disabled", replace_use_disk, int(not use_color)],
            ["stream_enabled", replace_disk,
             int(not inactive and case["replace"] and use_replace)],
            ["param_ui_disabled", replace_disk, int(not use_color)],
            ["stream_enabled", color_disk + 1, scalar],
            ["stream_enabled", color_disk + 2, channels],
            ["stream_enabled", color_disk + 3, channels],
            ["stream_enabled", color_disk + 4, channels],
        ]
    return rows


def run_actual(case: dict) -> list[list[int | str]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    calls: list[list[int | str]] = []

    def getter(current, args):
        disk_id, output = args[2], args[3]
        if disk_id == 5:
            current.write_bytes(output, struct.pack("<i", 1))
        elif disk_id == 2:
            current.write_bytes(output, struct.pack("<f", 0.0))
        elif disk_id == 0x15:
            current.write_bytes(output, struct.pack("<i", case["count"]))
        elif disk_id == 6:
            current.write_bytes(output, bytes([case["per_color"]]))
        elif disk_id == 7:
            current.write_bytes(output, bytes([case["per_component"]]))
        elif disk_id == 0x20B:
            current.write_bytes(output, bytes([case["replace"]]))
        elif disk_id >= 0x20C and (disk_id - 0x20C) % 3 == 0:
            current.write_bytes(output, bytes([case["use_color"].get((disk_id - 0x20C) // 3, 0)]))
        elif disk_id >= 0x20D and (disk_id - 0x20D) % 3 == 0:
            current.write_bytes(output, bytes([case["use_replace"].get((disk_id - 0x20D) // 3, 0)]))
        else:
            raise AssertionError(f"unexpected getter disk ID {disk_id}")
        return 0

    def param_ui(current, args):
        calls.append(["param_ui_disabled", args[2], args[3] & 0xFF])
        return 0

    def stream_ui(current, args):
        calls.append(["stream_enabled", args[2], args[3] & 0xFF])
        return 0

    for address, name in ((0x18000F0A0, "bool"), (0x18000F100, "int"),
                          (0x18000F160, "float"), (0x18000F1C0, "popup")):
        loader.detour_function(address, name, getter)
    loader.detour_function(0x18000BD30, "PF_UpdateParamUI", param_ui)
    loader.detour_function(0x18000BEE0, "SetDynamicStreamFlag", stream_ui)
    loader.call_function(UPDATE_METHOD, int_args=[0x1111, 0x2222, 0, 0x3333], max_instructions=100_000)
    return calls


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA
    source = (ROOT / "mac/OLMColorKey/OLMColorKey.cpp").read_text()
    required = (
        "PF_OutFlag_SEND_UPDATE_PARAMS_UI", "case PF_Cmd_UPDATE_PARAMS_UI:",
        "UpdateParameterUI(in_data, params)", "active && use_color",
        "active && use_color && replace_enabled && use_replace",
        "active && per_color && !per_component", "active && per_color && per_component",
    )
    assert all(token in source for token in required)
    assert "AE_Effect_Global_OutFlags { 0x06000040 }" in PIPL.read_text()
    results = []
    for case in CASES:
        actual, wanted = run_actual(case), expected(case)
        assert actual == wanted, case["name"]
        results.append({"name": case["name"], "calls": len(actual),
                        "transcript_sha256": hashlib.sha256(json.dumps(actual).encode()).hexdigest()})
    report = {
        "schema_version": 1, "status": "exact", "actual_aex_sha256": AEX_SHA,
        "actual_method": hex(UPDATE_METHOD), "cases": results,
        "contract": "Windows UPDATE_PARAMS_UI emits 279 deterministic UI operations: global threshold mode plus 25 eight-control color blocks, gated by count/use/replace/per-color/per-component.",
        "production": "Mac advertises SEND_UPDATE_PARAMS_UI and handles PF_Cmd_UPDATE_PARAMS_UI with the same combined Effect Controls enabled state.",
        "boundary": "Actual AEX helper calls are executed under Unicorn; native AE redraw remains a host-level visual check.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"PASS_OLMCOLORKEY_UPDATE_PARAMS_UI_ACTUAL_AEX_20260810 cases={len(results)} calls=279")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
