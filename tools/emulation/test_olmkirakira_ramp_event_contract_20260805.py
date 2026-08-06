#!/usr/bin/env python3
"""Verify the recovered PF_Cmd_EVENT dispatch and native focused event seam."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
CPP = ROOT / "tools/emulation/test_kirakira_ramp_event.cpp"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_event_contract_20260805.json"
ENTRY_PROBE = ROOT / "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"
ENTRY_REPORT = ROOT / "refs/conformance/olmkirakira_ramp_arbitrary_entrypoint_20260805.json"


def main() -> int:
    decomp = DECOMP.read_text(encoding="utf-8")
    event = decomp[decomp.index("// === FUN_181151800"):decomp.index("// === FUN_181151ae0")]
    for needle in ("+ 0x54) != 2", "+ 0x50", "+ 0x48", "+ 0x68", "+ 0x70", "+ 0xcc"):
        assert needle in event
    def actual_probe(
        x: int, y: int, dx: int, drag_y: int, color: bool = False,
        picker_result: int = 0, picker_write: bool = True,
    ) -> dict:
        env = os.environ.copy()
        env.update({
            "OLM_KK_RAMP_UI_PROBE": "1", "OLM_KK_RAMP_UI_X": str(x),
            "OLM_KK_RAMP_UI_Y": str(y), "OLM_KK_RAMP_UI_DX": str(dx),
            "OLM_KK_RAMP_UI_DRAG_Y": str(drag_y),
        })
        if color:
            env["OLM_KK_RAMP_UI_COLOR_PROBE"] = "1"
            env["OLM_KK_RAMP_UI_PICKER_RESULT"] = hex(picker_result)
            env["OLM_KK_RAMP_UI_PICKER_WRITE"] = "1" if picker_write else "0"
        subprocess.run(["python3", str(ENTRY_PROBE)], cwd=ROOT, env=env, check=True,
                       stdout=subprocess.DEVNULL)
        return json.loads(ENTRY_REPORT.read_text(encoding="utf-8"))["ui_probe"]

    actual_delete = actual_probe(10, 65, 20, 80)
    assert actual_delete["count_before_after"] == [3, 2]
    assert actual_delete["selected_before_after"] == [0, -1]
    assert actual_delete["changed_offsets"] == [
        16, 20, 21, 22, 23, 32, 33, 34, 35, 40, 41, 42,
        52, 53, 54, 58, 59, 356, 357, 358, 359,
    ]
    assert len(actual_delete["invalidations"]) == 2
    actual_add = actual_probe(100, 40, 0, 40)
    assert actual_add["count_before_after"] == [3, 4]
    assert actual_add["selected_before_after"] == [0, -1]
    assert actual_add["ramp_rect_before"] == [10, 5, 202, 55]
    assert actual_add["stops_after"][1] == [
        0.46875, 1.0, 1.0, 0.39122599363327026, 0.0,
    ]
    assert actual_add["stops_after"][2:] == actual_add["stops_before"][1:]
    assert len(actual_add["invalidations"]) == 2
    actual_color = actual_probe(10, 65, 0, 65, color=True)
    assert actual_color["count_before_after"] == [3, 3]
    assert actual_color["selected_before_after"] == [0, 0]
    assert actual_color["stops_after"][0] == [0.0, 0.25, 0.125, 0.5, 0.875]
    assert actual_color["stops_after"][1:] == actual_color["stops_before"][1:]
    assert actual_color["picker_calls"][0]["title"] == "Color select"
    assert actual_color["picker_calls"][0]["before"] == [1.0, 1.0, 0.0, 0.0]
    assert len(actual_color["invalidations"]) == 2
    actual_cancel = actual_probe(10, 65, 0, 65, color=True, picker_result=0x205, picker_write=False)
    assert actual_cancel["stops_after"] == actual_cancel["stops_before"]
    assert actual_cancel["selected_before_after"] == [0, -1]
    assert actual_cancel["event_results"][1]["evt_out_flags"] == 9
    assert actual_cancel["event_results"][1]["param_change_flags"] == 1
    assert actual_cancel["event_results"][1]["rax"] == 0
    assert len(actual_cancel["invalidations"]) == 2
    actual_error = actual_probe(10, 65, 0, 65, color=True, picker_result=13, picker_write=False)
    assert actual_error["stops_after"] == actual_error["stops_before"]
    assert actual_error["selected_before_after"] == [0, 0]
    assert actual_error["event_results"][1]["evt_out_flags"] == 9
    assert actual_error["event_results"][1]["param_change_flags"] == 1
    assert actual_error["event_results"][1]["rax"] == 0
    assert len(actual_error["invalidations"]) == 2
    mac = MAC.read_text(encoding="utf-8")
    for needle in ("PF_Cmd_EVENT", "PF_Event_DRAW", "PF_Event_DO_CLICK", "PF_Event_DRAG",
                   "continue_refcon[0]", "PF_ChangeFlag_CHANGED_VALUE", "PF_InvalidateRect"):
        assert needle in mac
    with tempfile.TemporaryDirectory(prefix="kk_ramp_event_") as td:
        exe = Path(td) / "event"
        subprocess.run(["c++", "-std=c++17", str(CPP), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
    report = {
        "schema": "olmkirakira-ramp-event-contract/5",
        "status": "actual_stop_add_delete_color_return_boundaries_grounded_native_synthetic_green",
        "actual": {
            "command": "PF_Cmd_EVENT = 15",
            "effect_control_area_offset": "extra+0x54 == 2",
            "parameter_index_offset": "extra+0x50",
            "value_handle_offset": "PF_ParamDef+0x48",
            "draw_dispatch": "RampDataHandler +0x68 -> RampContainer vslot +0x00",
            "click_drag_dispatch": "RampDataHandler +0x70 -> RampContainer vslot +0x08",
            "delete_boundary": "FUN_181235bb0 internal event 5: final drag with y-ramp_y >= 0x15 shifts later records left, decrements count, clears selection",
            "add_boundary": "FUN_181235bb0 internal event 2: single-click inside [10,5,202,55] appends a sampled stop when count < 16, sorts records, and clears selection",
            "color_boundary": "FUN_181235bb0 internal event 3: marker double-click calls PF AE App Suite v1 PF_AppColorPickerDialog at +0x38 with alpha/RGB, writes the four returned floats, and retains selection on success",
            "color_cancel_boundary": "picker 0x205 leaves records unchanged and clears selection; outer event still sets flags 9, parameter change 1, invalidates, and returns 0",
            "color_error_boundary": "non-cancel picker error with unchanged output leaves records and selection unchanged; outer event still sets flags 9, parameter change 1, invalidates, and returns 0",
            "result": "evt_out_flags at extra+0xcc OR 9; parameter change flag OR 1",
            "synthetic_entrypoint_delete": actual_delete,
            "synthetic_entrypoint_add": actual_add,
            "synthetic_entrypoint_color": actual_color,
            "synthetic_entrypoint_color_cancel": actual_cancel,
            "synthetic_entrypoint_color_error": actual_error,
        },
        "native": {
            "draw": "Drawbot gradient plus stop markers",
            "click": "nearest stop stored in continue_refcon[0], send_drag=true",
            "drag": "position clamped between neighboring stops; change flag and invalidate",
            "delete": "final drag below the ramp erases the selected stop, shifts records, and clears continue_refcon",
            "add": "single-click in the gradient inserts an alpha-1 stop with sampled RGB, sorts records, and clears continue_refcon",
            "color": "marker double-click invokes PF_AppColorPickerDialog and replaces only alpha/RGB while preserving position and selection",
            "color_returns": "success updates color and keeps selection; cancel keeps record and clears selection; other error keeps both record and selection; all handled events set change/update flags and invalidate",
            "synthetic": "selection, drag, both clamps, erase/shift, sampled insert/sort, marker hit, alpha/RGB replacement, cancel, and error pass",
        },
        "host_gate": "Live AE Drawbot/context and continuous mouse delivery are not claimed until real-host interaction is captured.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_RAMP_EVENT_CONTRACT_20260805 color_returns=actual_and_synthetic host=gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
