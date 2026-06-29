#!/usr/bin/env python3
"""Package debugger/runtime trace requests for a Windows helper machine."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


TRACE_NOTE = Path("notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md")
DEFAULT_REQUESTS = [
    Path("refs/reference_requests/radialblur_inner_20260605.json"),
    Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
    Path("refs/reference_requests/kirakira_strength0_brightness_20260614.json"),
]
SUPPORTING_NOTES = [
    Path("notes/OLMRadialBlur_ASM_FACTS.md"),
    Path("notes/OLMKiraKira_ASM_FACTS.md"),
    Path("notes/PROGRESS_MATRIX.md"),
]
KIRAKIRA_STAGE_SUPPORTING_NOTES = [
    Path("notes/IR_OLMKiraKira.md"),
    Path("notes/OLMKiraKira_ASM_FACTS.md"),
    Path("notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("refs/reports/runtime_trace_summary.md"),
]
COLORKEY_SUPPORTING_NOTES = [
    Path("notes/OLMColorKey_ASM_FACTS.md"),
    Path("notes/IR_OLMColorKey_Edge.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
]
COLORKEY_16BPC_CASE0009_SUPPORTING_FILES = [
    Path("refs/conformance/olmcolorkey_16bpc_case_0009_analysis.md"),
    Path("refs/conformance/olmcolorkey_16bpc_case_0009_analysis.json"),
    Path(
        "refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable/"
        "bitdepth16_olmcolorkey_exact/reports/ae_pixel_16bpc_all_exact.json"
    ),
    Path("refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json"),
]
OLMBLUR_SUPPORTING_NOTES = [
    Path("notes/IR_OLMBlur.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("notes/AE_HOST_VALIDATION_20260618.md"),
    Path("notes/PORTING_BOARD.md"),
]
DIRECTIONALBLUR_SUPPORTING_NOTES = [
    Path("notes/IR_OLMDirectionalBlur.md"),
    Path("notes/OLMDirectionalBlur_ASM_FACTS.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/residual_clusters.md"),
    Path("refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/residual_clusters.json"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip. Defaults to refs/runtime_trace_packages/olm_runtime_trace_requests_YYYYMMDD_HHMMSS.zip.",
    )
    parser.add_argument(
        "--profile",
        choices=[
            "hard-paths",
            "dense-all",
            "dense-live-followup",
            "colorkey-edge",
            "colorkey-16bpc-case0009",
            "olmblur-repeat-threshold",
            "kirakira-stage-values",
            "kirakira-stage-values-deep",
            "kirakira-forward-warp-box-input",
            "kirakira-boxfilter-pass1-microprobe",
            "kirakira-aggregation-compose-bt709",
            "radialblur-residual-witness",
            "radialblur-inner-cell-witness",
            "directionalblur-residual-witness",
            "smoother2-no-key-grid",
            "smoother2-legacy-key-gamma",
            "smoother2-legacy-writeback-extract",
            "smoother2-legacy-u8-writer-trace",
            "smoother2-legacy-u8-pixel-trace",
            "smoother2-legacy-cce0-pixel-trace",
            "smoother2-legacy-cce0-internals-trace",
            "smoother2-legacy-current-aex-residuals",
            "smoother2-legacy-current-aex-polygon",
            "smoother2-current-aex-f270-witness",
            "smoother2-current-aex-writer-frame-followup",
            "distancegradation-field-prep",
            "distancegradation-layer-no-bg-source-ownership",
            "distancegradation-16bpc-case0026-x-witness",
        ],
        default="hard-paths",
        help="Trace request set to package.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def next_actions_snapshot(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(root / "refs" / "scripts" / "next_reference_actions.py"), "--json"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    data = json.loads(proc.stdout)
    if not isinstance(data, dict):
        raise ValueError("next_reference_actions.py did not return an object")
    return data


def ensure_kirakira_deep_witness_plan(root: Path) -> None:
    required = [
        root / "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.json",
        root / "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md",
    ]
    if all(path.exists() for path in required):
        return
    subprocess.run(
        [sys.executable, str(root / "refs" / "scripts" / "write_olmkirakira_deep_witness_plan.py")],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def runtime_actions(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    actions = snapshot.get("covered_actions")
    if not isinstance(actions, list):
        return []
    return [
        action
        for action in actions
        if isinstance(action, dict) and str(action.get("mode", "")).endswith("trace")
    ]


def colorkey_edge_action() -> dict[str, Any]:
    return {
        "request_id": "colorkey_edge_runtime_trace_20260619",
        "plugin_area": "OLMColorKey Edge Thin/Edge Blur runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMColorKey case_0005/case_0006 Edge Thin erode witnesses "
            "and case_0008/case_0009 Edge Blur witnesses around FUN_1800094b0/"
            "FUN_180008c90/FUN_180008320/FUN_1800085b0. Record ctx fields plus "
            "local matte/distance/weight/apply samples at the listed coordinates. "
            "Compare against Mac baseline logs in "
            "refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/."
        ),
        "stop_condition": (
            "Return ctx+0x28/+0x2c/+0x40/+0x44/+0x48 and sample values that "
            "distinguish manifest/ctx scaling, border seed ownership, <= vs < "
            "erode/dilate shell, and Edge Blur apply semantics."
        ),
    }


def colorkey_16bpc_case0009_action() -> dict[str, Any]:
    return {
        "request_id": "colorkey_16bpc_case0009_runtime_trace_20260626",
        "plugin_area": "OLMColorKey 16bpc case_0009 positive Edge Thin runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMColorKey 16bpc normalized Software case_0009 on the "
            "current MediaCore AEX path rooted at OLMColorKey+0x9000 and its "
            "positive Edge Thin compare/copy path around +0x9237/+0x9247/+0x924c. "
            "Record ctx fields, seed/matte bytes, distance/limit values, copy "
            "condition, edge ownership, and final RGBA for witness pixels "
            "(1110,149), (1213,785), (369,95), (1503,57), (668,945), and "
            "optional top-edge sanity (1699,7). "
            "Use the narrow witness plan in notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md "
            "and compare against refs/conformance/olmcolorkey_16bpc_case_0009_analysis.md."
        ),
        "stop_condition": (
            "Return concrete 16bpc case_0009 ctx/seed/dilate witness values, or "
            "the exact failed breakpoint/watchpoint reason. Static branch names "
            "or sparse wrapper hits are not enough."
        ),
    }


def olmblur_repeat_threshold_action() -> dict[str, Any]:
    return {
        "request_id": "olmblur_repeat_threshold_runtime_trace_20260619",
        "plugin_area": "OLMBlur repeat-10 threshold/runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMBlur normalized Software cases case_0006 and case_0007 at "
            "the listed residual pixels. Record post-blur/pre-writeback float "
            "RGB, final writeback operation, and the Legacy helper border/all_same "
            "state needed to distinguish accumulation/writeback ordering. Compare "
            "against Mac baseline logs in "
            "refs/reports/olmblur_trace_baseline_20260619_030633_mac/."
        ),
        "stop_condition": (
            "Return enough values to decide why case_0006 (498,940) writes 185 "
            "instead of the CLI's 186 and why case_0007 keeps two red pixels at "
            "251 plus the top-left border at 0."
        ),
    }


def kirakira_stage_values_action() -> dict[str, Any]:
    return {
        "request_id": "kirakira_fun_181150790_stage_values_20260620",
        "plugin_area": "OLMKiraKira FUN_181150790 stage-value runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMKiraKira single-ray Software case "
            "kk_vertical_len50_brightness1_strength100 through FUN_181150790. "
            "Record both warpAffine calls' Mat headers, dsize, affine matrix "
            "values, ROI/copy rectangles, selected boxFilter branch, and float "
            "witness values before/after center-copy, forward warp, each of the "
            "three horizontal boxFilter passes, rotate-back, final center-copy, "
            "FUN_18114fd90 aggregation, and merge-mode-1 compose."
        ),
        "stop_condition": (
            "Return enough values to decide whether the remaining KiraKira "
            "residual is caused by Windows AVX2 boxFilter numeric behavior, "
            "warpAffine Mat/ROI placement, final centered copy, ray aggregation, "
            "or merge-mode compose."
        ),
    }


def kirakira_deep_stage_values_action() -> dict[str, Any]:
    return {
        "request_id": "kirakira_fun_181150790_deep_stage_values_20260621",
        "plugin_area": "OLMKiraKira FUN_181150790 deep stage-value runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMKiraKira single-ray Software case "
            "kk_vertical_len50_brightness1_strength100 through FUN_181150790, "
            "using the included witness plan at "
            "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/"
            "witness_plan.md. Capture the same three witness pixels at source/"
            "temp/ray coordinates: center (source 960,540 temp 962,962), "
            "ray_length_up (source 960,490 temp 962,912), and ray_length_right "
            "(source 1010,540 temp 1012,962). For each witness, record float "
            "values after center-copy, after forward warp, after each of the "
            "three boxFilter passes, after rotate-back, and after final "
            "center-copy. Also record forward/back matrices, ROI/copy rects, "
            "Mat headers/steps/data pointers, selected boxFilter branch for "
            "each pass, FUN_18114fd90 aggregation values, and merge-mode-1 "
            "compose values at the listed compose samples."
        ),
        "stop_condition": (
            "Return concrete float/byte witness values or an exact failed "
            "breakpoint/watchpoint reason. Wrapper hit counts, branch names, or "
            "`not isolated` placeholders are not enough; those were already "
            "captured and classified as trace-too-sparse."
        ),
    }


def kirakira_forward_warp_box_input_action() -> dict[str, Any]:
    return {
        "request_id": "kirakira_forward_warp_box_input_20260621",
        "plugin_area": "OLMKiraKira forward-warp / boxFilter input follow-up",
        "mode": "external-trace",
        "command": (
            "Follow up the answered_partial deep KiraKira trace. Use the same "
            "single-ray Software case kk_vertical_len50_brightness1_strength100 "
            "and the same witness plan coordinates. Do not recapture broad PNGs. "
            "Capture only the missing first-divergence inputs: values after "
            "center-copy before forward warp, values immediately after the "
            "forward warp call, and values immediately before and after the "
            "first horizontal boxFilter pass for center/ray_length_up/"
            "ray_length_right. Also record the forward warpAffine matrix, dsize, "
            "source/destination Mat headers, ROI/copy rects, selected "
            "boxFilter branch, ksize/anchor/normalize/borderType, and the "
            "boxFilter source/destination Mat headers for pass 1."
        ),
        "stop_condition": (
            "Return typed float values for the three witnesses or the exact "
            "failed breakpoint/watchpoint reason. The goal is to classify the "
            "first divergence as center-copy, forward-warp, boxFilter input, or "
            "boxFilter pass-1 numeric behavior. Wrapper hit counts alone are "
            "not sufficient."
        ),
    }


def kirakira_boxfilter_pass1_microprobe_action() -> dict[str, Any]:
    return {
        "request_id": "kirakira_boxfilter_pass1_microprobe_20260622",
        "plugin_area": "OLMKiraKira first boxFilter AVX2 microprobe",
        "mode": "external-trace",
        "command": (
            "Follow up `kirakira_forward_warp_box_input_20260621`. Use the same "
            "single-ray Software case `kk_vertical_len50_brightness1_strength100` "
            "and the same first horizontal boxFilter pass. Do not recapture broad "
            "PNGs. The prior focused trace proved the forward warp matrix, temp "
            "geometry, source ROI/copy rect, boxFilter args "
            "`ksize=(50,1), anchor=(-1,-1), normalize=true, borderType=4`, and "
            "`before_box_1 == after_forward_warp` at the traced points. The "
            "remaining divergence starts inside or immediately around pass 1: "
            "after pass 1 Windows is brighter than local by roughly center "
            "`+0.00765908`, up `+0.00722814`, right `+0.00512678`. For the "
            "center `(temp 962,962)`, ray_length_up `(962,912)`, and "
            "ray_length_right `(1012,962)` witnesses, capture the actual "
            "pass-1 source row window used by Windows/OpenCV AVX2: resolved "
            "source x range after `BORDER_REFLECT_101`, the 50 contributing "
            "float samples or compact sum/min/max/hash plus enough edge samples "
            "to reconstruct it, the raw normalized sum before store, the stored "
            "float after pass 1, and the Mat data pointer/step for src and dst. "
            "If you can break in `FUN_1812e39d0`, also record the vector/scalar "
            "path name or nearest offset and accumulator precision."
        ),
        "stop_condition": (
            "A satisfactory answer must decide whether the first pass mismatch "
            "is caused by a different contributing window, different border "
            "reflection, different accumulator precision/store, or a different "
            "Mat/address stage. Do not return only wrapper args; those already "
            "match."
        ),
    }


def kirakira_aggregation_compose_bt709_action() -> dict[str, Any]:
    return {
        "request_id": "kirakira_aggregation_compose_bt709_20260624",
        "plugin_area": "OLMKiraKira aggregation / merge-mode compose after BT.709 ray-helper match",
        "mode": "external-trace",
        "command": (
            "Trace OLMKiraKira single-ray Software case "
            "kk_vertical_len50_brightness1_strength100 after the BT.709 seed "
            "reconciliation. Do not re-trace boxFilter/window/warp unless needed "
            "to reach the requested functions; the Mac BT.709 trace already "
            "matches Windows through box pass 1/2/3, rotate-back, and final "
            "center-copy within float print precision. Capture FUN_18114fd90 "
            "aggregation inputs and outputs for center/source points, then capture "
            "merge-mode-1 screen compose inputs/outputs and final byte/PNG-facing "
            "values. Focus on center (960,540), ray_length_up (960,490), "
            "ray_length_right (1010,540), and the vertical-case residual hotspot "
            "(934,118), where Windows reference is [131,131,131,255] and the "
            "local BT.709 candidate is [145,145,145,255]. If time permits, also "
            "sample the overall largest BT.709 Software residual from the "
            "rotation13 case at (1098,202), Windows [112,112,112,255] versus "
            "local [46,46,46,255]."
        ),
        "stop_condition": (
            "Return concrete float and byte witness values for aggregation and "
            "compose, or the exact breakpoint/watchpoint failure reason. Do not "
            "answer with wrapper hit counts or already-known ray-helper facts."
        ),
    }


def smoother2_no_key_grid_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_no_key_grid_runtime_trace_20260619",
        "plugin_area": "OLMSmoother2 no-key grid runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 case sm2_no_key_s100_r3 at the listed residual "
            "pixels. Record FUN_18000c280 switch index, cardinal dispatcher "
            "descriptors/keys, the d520/dbd0/d230/d800 scan helper returns that "
            "feed those keys, the FUN_180010550 p1/p2/p3 index inputs plus "
            "idx=7 context values for each "
            "scan helper, every FUN_1800104d0 append src/rgba/weight/count, "
            "FUN_18000ab00 composite inputs/output, FUN_18000b120 output, and "
            "FUN_1800036e0 final sRGB/writeback values. Compare against the Mac "
            "baseline logs in refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/."
        ),
        "stop_condition": (
            "Return enough values to decide whether the Mac port is missing a "
            "0.2 duplicate sample, using the wrong cardinal span formula, or "
            "matching the polygon but differing in final color/writeback. If the "
            "append sequence differs, the scan helper return values should point "
            "to the first mismatching descriptor/key."
        ),
    }


def smoother2_legacy_key_gamma_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_key_gamma_runtime_trace_20260620",
        "plugin_area": "OLMSmoother2 legacy key/gamma runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 legacy key/gamma AE-exact failures at the listed "
            "top-edge witness pixels. Focus on case_0001, case_0002, case_0003, "
            "and case_0010. Record parameter struct values, Color Key active/"
            "invert decisions, gamma/sRGB decode/encode decisions, class-plane "
            "bytes, pre/post FUN_1800036e0 writeback values, and final RGBA. "
            "Compare against the AE-host failure report in "
            "refs/reports/ae_host_validation_20260620_1425/"
            "ae_pixel_olmsmoother2_legacy_20260619/reports/."
        ),
        "stop_condition": (
            "Return enough values to decide whether the 0/7 legacy failures are "
            "caused by Color Key mask polarity, premultiply/unpremultiply, gamma "
            "setup, class-plane generation, or final writeback. Do not continue "
            "no-key grid tuning from this package."
        ),
    }


def smoother2_legacy_writeback_extract_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_writeback_extract_20260620",
        "plugin_area": "OLMSmoother2 legacy writeback full-log extraction",
        "mode": "external-trace",
        "command": (
            "Do not rerun the all-plugin dense trace first. Use the existing "
            "Windows full CDB log from the live attempt if available: "
            "C:\\Users\\optim\\Documents\\Codex\\2026-06-11\\files-mentioned-by-the-user-olm\\work\\"
            "live_attempt_smoother2_legacy_20260620\\cdb_console.txt. Extract "
            "the complete CDB output around both "
            "HIT_FUN_1800036e0_writeback_candidate hits, including the marker, "
            "register dump, stack dump, call stack, and at least 120 lines before "
            "and after each hit. Also extract a compact window around the first "
            "few adjacent HIT_FUN_180010550_candidate and "
            "HIT_FUN_18000c280_switch_candidate hits in the same render. If the "
            "full log is no longer available, rerun only "
            "ae_pixel_olmsmoother2_legacy_20260619 case_0001 with breakpoints "
            "that log full registers/stack for OLMSmoother2+0x36e0, but limit "
            "the run to the first 20 writeback-candidate hits."
        ),
        "stop_condition": (
            "Return the actual register/stack values for the two "
            "OLMSmoother2+0x36e0 hits, or an exact statement that the full log "
            "was unavailable and a rerun failed. The previous return only kept "
            "the hit markers/counts; this request is successful only if the "
            "writeback-hit values are present."
        ),
    }


def smoother2_legacy_u8_writer_trace_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_u8_writer_trace_20260620",
        "plugin_area": "OLMSmoother2 legacy 8bpc writer/runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace the 8bpc output writer for OLMSmoother2 legacy cases. The "
            "previous +0x36e0 request failed because +0x36e0 is the float writer "
            "FUN_1800036e0 and did not execute for the 8bpc AE pixel validation "
            "run. For this 8bpc request, arm OLMSmoother2+0x3370 "
            "(FUN_180003370) and the wrapper OLMSmoother2+0x3d00 "
            "(FUN_180003d00). Run ae_pixel_olmsmoother2_legacy_20260619, "
            "starting with case_0001. On the first 20 hits at +0x3370, log the "
            "marker, registers, call stack, dq @rsp L24, dd/dq of the pointers "
            "passed as param_5/param_6/param_7/param_8/param_9 where safe, and "
            "if possible the current x/y loop locals, FUN_18000cce0 output "
            "floats {a,r,g,b}, gamma branch, premultiply branch, and final "
            "packed 8bpc bytes written by FUN_180003370."
        ),
        "stop_condition": (
            "Return direct +0x3370 hit values that show the 8bpc legacy writer "
            "input/output for at least case_0001, or an exact failed-breakpoint "
            "reason. Do not reuse the failed +0x36e0 result as an answer."
        ),
    }


def smoother2_legacy_u8_pixel_trace_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_u8_pixel_trace_20260620",
        "plugin_area": "OLMSmoother2 legacy 8bpc per-pixel writer trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 legacy case_0001 at the known high-diff pixel "
            "(x=712,y=406). The prior u8 writer trace proved that the active "
            "8bpc writer is OLMSmoother2+0x3370 / FUN_180003370. Now set "
            "conditional breakpoints inside that function, not at entry: "
            "OLMSmoother2+0x3510 immediately after CALL FUN_18000cce0, "
            "OLMSmoother2+0x35ad before final scaling/packing, and "
            "OLMSmoother2+0x360e immediately before MOV dword ptr [RSI],EAX. "
            "Use the local loop coordinates at [RSP+0x34] for x and [RSP+0x38] "
            "for y, and only log when x==712 and y==406. At +0x3510 record "
            "[RSP+0x48], [RSP+0x4c], [RSP+0x50], [RSP+0x54] as floats/hex "
            "(FUN_18000cce0 output r,g,b,a), RBP/p8 parameter flags including "
            "[RBP] and byte [RBP+0x19], RBX/p9 gamma context including "
            "[RBX+0x10], and the call stack. At +0x35ad record XMM6/XMM7/XMM8/"
            "XMM1 before multiply by 255/add 0.5. At +0x360e record EAX, RSI, "
            "the destination dword before write, and the packed output bytes. "
            "Expected/reference pixel is RGBA [207,207,207,207]; current Mac/"
            "candidate pixel is RGBA [106,106,106,135]."
        ),
        "stop_condition": (
            "Return direct values for case_0001 pixel (712,406) at +0x3510 and "
            "+0x360e, or an exact failed conditional-breakpoint reason. This "
            "request is successful only if the per-pixel float and packed byte "
            "values are present."
        ),
    }


def smoother2_legacy_cce0_pixel_trace_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_cce0_pixel_trace_20260621",
        "plugin_area": "OLMSmoother2 legacy FUN_18000cce0 target-pixel composite trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 legacy case_0001 at high-diff pixel (x=712,y=406), "
            "moving upstream from the proven 8bpc writer. The previous per-pixel "
            "writer trace captured final packed store EAX=c8c8c887 at +0x3610, "
            "which explains the failing candidate PNG [106,106,106,135] after "
            "AE premultiplication. Now capture the composite output that feeds "
            "that writer. Set a breakpoint at OLMSmoother2+0xcce0 "
            "(FUN_18000cce0) and only log when dwo(@r9)==0x2c8 and "
            "dwo(@r9+4)==0x196. At that target hit, log RCX/RDX/R8/R9, "
            "dd @r9 L2, dq @rdx L8, dq @r8 L8, dq poi(@rsp+0x20) L16, and "
            "dq poi(@rsp+0x28) L8 if safe. Then arm a one-shot breakpoint at "
            "OLMSmoother2+0x3510 for the immediate return to the u8 writer, and "
            "log [RSP+0x48], [RSP+0x4c], [RSP+0x50], [RSP+0x54] as float/hex, "
            "plus RBP flags ([RBP], byte [RBP+0x19]) and RBX+0x10. If direct "
            "conditional code breakpoints are too slow, use the successful "
            "entry-command/data-watch approach from the previous return to first "
            "restrict to the target output world, then capture the first matching "
            "FUN_18000cce0 call on the same render."
        ),
        "stop_condition": (
            "Return the target-pixel FUN_18000cce0 input pointers and the "
            "+0x3510 returned floats for case_0001 (712,406), or an exact failed "
            "breakpoint reason. Do not repeat only the final packed EAX value; "
            "that is already known as c8c8c887."
        ),
    }


def smoother2_legacy_cce0_internals_trace_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_cce0_internals_replay_from_writer_trace_20260621",
        "plugin_area": "OLMSmoother2 legacy FUN_18000cce0 internal composite trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 legacy case_0001 at target pixel (x=712,y=406) "
            "inside FUN_18000cce0. The previous return proved the final writer "
            "is not the source of the residual: cce0 produced floats "
            "[0.57797289, 0.57797289, 0.57797289, 0.52794117], the u8 writer "
            "packed EAX=c8c8c887 (A/R/G/B [135,200,200,200]), and the PNG "
            "candidate [106,106,106,135] follows from AE premultiplication. "
            "Five internals attempts are now failed_partial. Positive facts are "
            "strong: the fallback data-watch path repeatedly catches the target "
            "write at OLMSmoother2+0x3610, with stack xy (0x2c8,0x196), cce0 "
            "return floats [0.57797289,0.57797289,0.57797289,0.52794117], and "
            "packed EAX=c8c8c887. Negative facts are also strong: +0x34b0 did "
            "not match the computed target addresses, +0x350b @rsi==$t3 did "
            "not hit, and +0x350b @rdi==0x2c8 && @r14==0x196 did not hit in "
            "the retained run. Therefore do not spend another run only trying "
            "to pre-break at +0x350b. Instead use the reliable target write at "
            "+0x3610 as the anchor. When the target write/watchpoint hits, dump "
            "the full writer frame: dq @rsp L80, dd @rsp L160, all nonvolatile "
            "registers, xmm6/xmm7/xmm8/xmm1, [rsp+0x34..0x58], [rsp+0x60..0x98], "
            "and pointer previews for RBX/RBP/R13/R15/RDX/RSI. Reconstruct the "
            "FUN_18000cce0 call arguments from the same writer frame: for the "
            "FUN_180003370 path these are RCX=&[rsp+0x48], RDX=&[rsp+0x80], "
            "R8=&[rsp+0x60], R9=&[rsp+0x34], stack param5=RBX, stack param6=RBP. "
            "If safe in CDB, call or simulate a second invocation of "
            "OLMSmoother2+0xcce0 with those exact arguments into a scratch "
            "output buffer and single-step/break through +0xcd5f,+0xcddb,"
            "+0xcdfd,+0xce02,+0xce2e,+0xce4c,+0xce4f to capture c280/bb10/"
            "c0d0/ab00/b120 stage values. If calling back into the plugin is "
            "unsafe, do not force it; instead return the reconstructed argument "
            "block and a clear reason why replay was skipped. Also record the "
            "return address/callsite evidence from the stack so we can explain "
            "why +0x350b did not behave as a stable pre-call breakpoint."
        ),
        "stop_condition": (
            "Return target-pixel cce0 internals for case_0001 (712,406) captured "
            "either by replaying FUN_18000cce0 from the reliable +0x3610 writer "
            "frame or by returning a complete reconstructed cce0 argument block "
            "with enough stack/register data to replay locally. A satisfactory "
            "answer includes c280 polygon count/vertices or exact c280 failure "
            "reason, before/after values for bb10/c0d0/ab00/b120, and final "
            "cce0 floats. If replay is skipped as unsafe, return the reason and "
            "the complete argument/stack dump; do not return only the known "
            "EAX=c8c8c887 store."
        ),
    }


def smoother2_legacy_current_aex_residuals_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_current_aex_residuals_trace_20260621",
        "plugin_area": "OLMSmoother2 legacy current-AEX residual trace",
        "mode": "external-trace",
        "command": (
            "Trace the imported Windows AE 2026 Software current-AEX recapture "
            "`smoother2_legacy_full_current_aex_recapture_20260621`. Do not use "
            "the retired 20260605 legacy PNGs as expected output. First classify "
            "input ownership by tracing one exact control and one residual case: "
            "`legacy_case_0002_current_aex` (AE-saved before-frame CLI exact), "
            "`legacy_case_0004_current_aex` (localized residual), and "
            "`legacy_case_0012_gamma5_red_blue_current_aex` (gamma residual). "
            "Primary witness pixels from the Mac diff are: 0004 `(501,1055)` "
            "Windows `[159,95,95,255]` vs Mac `[65,65,65,255]`, and 0012 "
            "`(500,877)` Windows `[9,9,9,255]` vs Mac `[176,112,112,255]`. "
            "Use 0002 as an exact control; a harmless exact-control sample is "
            "`(500,877)` or any nonzero source pixel that reaches the same path. "
            "For each case, record the source pixel as loaded by AE/effect input, "
            "the value after any unpremultiply stage, key-filter result, class "
            "plane byte around a high-diff witness, FUN_18000cce0 output floats "
            "if reached, gamma/sRGB branch state, and final 8bpc writer value. "
            "Use the included IR and current-AEX manifest to pick concrete "
            "witness pixels from the local diff reports; prefer pixels with "
            "max residual, not broad wrapper hit counts."
        ),
        "stop_condition": (
            "Return concrete per-case witness values that decide whether the "
            "remaining residual is caused by AE input premultiply/unpremultiply "
            "semantics, key-mask/class-plane differences, gamma path setup, or "
            "final writeback. If a breakpoint cannot be isolated, return the "
            "exact failed condition and the closest successful address/register "
            "state."
        ),
    }


def smoother2_legacy_current_aex_polygon_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_current_aex_polygon_stepover_trace_20260621",
        "plugin_area": "OLMSmoother2 legacy current-AEX cce0 step-over/polygon trace",
        "mode": "external-trace",
        "command": (
            "Follow up the writer-backtrack trace for "
            "`smoother2_legacy_full_current_aex_recapture_20260621`. Do not "
            "recapture broad PNGs. The previous return is internally useful "
            "but its JSON summary under-reported one key fact: for "
            "`legacy_case_0004_current_aex` at `(501,1055)`, the direct "
            "`@rsp+0x34/@rsp+0x38` filter DID hit `OLMSmoother2+0x350b`. "
            "At that hit, `r9=[rsp+0x34]`, `[rsp+0x34]=0x1f5`, "
            "`[rsp+0x38]=0x41f`, `rcx=[rsp+0x48]`, `rdx=[rsp+0x80]`, "
            "`r8=[rsp+0x60]`, and the pre-call result buffer at `rcx` held "
            "`[0x3f483078,0x3ace85ef,0x3ace85ef,0x3f800000]` "
            "(`0.78198957,0.0015756468,0.0015756468,1.0`). The script then "
            "armed internal breakpoints but did not capture `+0x3510` or "
            "c280 internals, apparently stopping again at the same callsite. "
            "Run a focused 0004-only trace. When `+0x350b` hits for "
            "`x=0x1f5,y=0x41f`, dump the same callsite args, then force the "
            "call to execute: either use `p`/step-over to reach `+0x3510` and "
            "dump `[rsp+0x48..0x54]` as hex/floats, or step into/continue with "
            "working breakpoints at `+0xc280`, `+0xc50a`, `+0x104d0`, and "
            "`+0xc7dd`. Do not quit immediately after arming breakpoints. "
            "Return the actual cce0 output after the call and, if reached, "
            "c280 switch index, polygon count, append source coordinates, "
            "vertex RGBA floats, weights, and helper offsets. Treat `0012` as "
            "secondary; the prior run did not reach its target before AE hit "
            "an access violation at `OLMSmoother2+0x98f2`."
        ),
        "stop_condition": (
            "A satisfactory answer for this round is 0004-focused: it must "
            "include either (A) the `+0x3510` post-cce0 result floats for "
            "`(501,1055)` plus any c280/polygon facts reached, or (B) a "
            "concrete debugger reason why the already observed `+0x350b` hit "
            "cannot be stepped over/into. Do not return only the existing "
            "callsite dump; the missing proof is what happens after executing "
            "that exact call."
        ),
    }


def smoother2_current_aex_f270_witness_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_current_aex_f270_witness_trace_20260621",
        "plugin_area": "OLMSmoother2 current-AEX f270/e170/e3a0 witness trace",
        "mode": "external-trace",
        "command": (
            "Trace only the current-AEX Software recapture "
            "`smoother2_legacy_full_current_aex_recapture_20260621` with the "
            "current installed OLMSmoother2 AEX. Do not use retired legacy PNGs "
            "or broad merged trace templates. Primary case: "
            "`legacy_case_0012_gamma5_red_blue_current_aex`, target pixel "
            "`(91,841)`. Mac CLI builds `idx=105`, enters cardinal6 with "
            "`desc=(91,841,1,91,843,5)` / `key=50`, reads `e170` bits "
            "`A(x,y-1)=1, R(x-1,y)=0, A(x,y)=0 -> c=2`, then `f270` emits "
            "source `(91,840)` through `e3a0` with weight `0.35632184`. "
            "Windows reference at the same pixel is `[0,0,0,0]`, Mac CLI is "
            "`[90,90,90,91]`. Capture enough runtime state to decide which of "
            "these diverges in Windows: c280 switch index, cardinal6 desc/key, "
            "e170 input bits and return code, f270 taken/not-taken, e3a0 "
            "trapezoid args/result, append source coordinate/RGBA/weight, final "
            "polygon count, FUN_18000cce0 input/output floats, and final writer "
            "u8 RGBA. Secondary case: `legacy_case_0004_current_aex`, pixel "
            "`(1903,519)`, where Mac has `idx=208`, transparent center, polygon "
            "count 0, output `[0,0,0,0]`, while Windows reference is "
            "`[103,103,103,113]`; capture c280 index and whether any helper "
            "append occurs. The 2026-06-24 neighborhood report shows these two "
            "centers are opposite failures: case 0012 is a local false-positive "
            "semi-transparent append where Windows stays transparent, while "
            "case 0004 is a local false-negative transparent passthrough where "
            "Windows emits semi-transparent output. Also record the strongest "
            "neighboring deltas for context: 0012 has nearby deltas at "
            "`(91,840)`, `(92,841)`, `(91,842)`; 0004 has nearby deltas at "
            "`(1903,518)`, `(1904,518)`, `(1901,519)`, `(1901,520)`."
        ),
        "stop_condition": (
            "A satisfactory answer must classify both center-pixel mismatches. "
            "For 0012, choose one of: different c280 index, different cardinal6 "
            "desc/key, different e170 bits/code, f270/e3a0 not emitted, same "
            "emit but cce0/writeback suppresses it, or trace failure with exact "
            "failed breakpoint/address. For 0004, choose one of: different c280 "
            "index, helper append emitted where Mac emits none, cce0 nonzero "
            "fallback before passthrough, same polygon but different blend, or "
            "trace failure with exact failed breakpoint/address. Do not return "
            "only final writer values; those are already known."
        ),
    }


def smoother2_current_aex_writer_frame_followup_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_current_aex_writer_frame_followup_trace_20260625",
        "plugin_area": "OLMSmoother2 current-AEX writer-frame cce0 producer trace",
        "mode": "external-trace",
        "command": (
            "Trace only the current-AEX Software recapture "
            "`smoother2_legacy_full_current_aex_recapture_20260621` with the "
            "current installed OLMSmoother2 AEX. This follows up the "
            "2026-06-25 neighborhood return: final writer watchpoints hit for "
            "`legacy_case_0012_gamma5_red_blue_current_aex` pixel `(91,841)` "
            "and `legacy_case_0004_current_aex` pixel `(1903,519)`, but the "
            "`OLMSmoother2+0x350b` `@r9 == target_xy` predicate did not hit. "
            "Do not repeat that `@r9`-only coordinate predicate as the primary "
            "proof. Use the reliable final writer watchpoint/output-address "
            "anchor from `FUN_180003370` instead. At writer entry "
            "`OLMSmoother2+0x3370`, compute all three candidate target output "
            "addresses from the three output worlds exactly as in the previous "
            "writer trace, arm write watchpoints on all three, and stop when "
            "the watched address is written at `OLMSmoother2+0x3610`. For each "
            "target writer stop, dump: module base, the watched address, "
            "full registers, full stack around `@rsp-0xa0..@rsp+0x1e0`, "
            "`@rsi-0x40..@rsi+0x80`, and `r12/r13/r15/rbp` pointee windows. "
            "Then reconstruct the same `FUN_18000cce0` call frame from the "
            "writer stack. In `FUN_180003370`, decomp shows the call as "
            "`FUN_18000cce0(&local_f0,&local_b8,&local_d8,&local_104,param_8,"
            "param_9)`; immediately after cce0 and before gamma/premultiply, "
            "the stack contains `local_104=x`, `local_100=y`, and "
            "`local_f0/local_ec/local_e8/local_e4` result floats. The previous "
            "writer dumps show these local values still visible near the "
            "writer stop, e.g. for 0012 stack dwords near the stop include "
            "`x=0x5b`, `y=0x349`, floats `1,1,1,1`, and for 0004 include "
            "`x=0x76f`, `y=0x207`, floats approximately "
            "`0.80824906,0.80824906,0.80824906,0.44156867`. Confirm these "
            "locations explicitly. If possible, set a one-shot breakpoint at "
            "the return address of the exact cce0 call in the same writer "
            "frame, rather than filtering `+0x350b` by `@r9`. If live "
            "backtracking is too risky, return a complete reconstructed "
            "argument block for local analysis and a concrete reason why the "
            "exact cce0 callsite cannot be isolated."
        ),
        "stop_condition": (
            "A satisfactory answer must classify both center-pixel mismatches "
            "or provide exact failure evidence. For 0012, report whether cce0 "
            "already returns `[1,1,1,1]` / transparent packed output from an "
            "empty/suppressed polygon, or whether an upstream append exists "
            "and is later suppressed. For 0004, report whether cce0 already "
            "returns approximately `[0.808249,0.808249,0.808249,0.441569]` "
            "and identify the producer: c280 switch index, helper append, "
            "fallback, or alternate path. Do not return only final writer "
            "bytes; those are already known."
        ),
    }


def distancegradation_field_prep_action() -> dict[str, Any]:
    return {
        "request_id": "olmdistancegradation_field_prep_runtime_trace_20260619",
        "plugin_area": "OLMDistanceGradation distance field / Constant interpolation runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMDistanceGradation cases 0020, 0022, and 0029 around the "
            "distance-field construction and FUN_181170870 compose path. Record "
            "the field Mat/AE-world RGBA values consumed by compose, the "
            "Constant-mode binarization point, blur input/output field values, "
            "OpenCV/helper distanceTransform args, min/max normalization facts, "
            "GaussianBlur args for case_0029, and final compose values at the "
            "listed witness pixels."
        ),
        "stop_condition": (
            "Return enough values to decide whether Constant mode binarizes the "
            "field upstream for all non-blur cases, only background cases, or "
            "only blur cases, and which channel(s) carry the normalized distance "
            "field into FUN_181170870."
        ),
    }


def distancegradation_16bpc_case0026_x_witness_action() -> dict[str, Any]:
    return {
        "request_id": "olmdistancegradation_16bpc_case0026_x_witness_20260628",
        "plugin_area": "OLMDistanceGradation 16bpc Power/background ramp field/X witness",
        "mode": "external-trace",
        "command": (
            "Trace OLMDistanceGradation normalized Software 16bpc "
            "olmdistancegradation_extended__case_0026. Focus on row y=0, "
            "x=0..14, especially x=3..14. Record the 16bpc field-world pixel "
            "or Mat value consumed by FUN_181170480 before invert/interpolation, "
            "then the X values after Invert=1 and Power interpolation, plus the "
            "final RGBA16 write. Compare against "
            "refs/conformance/olmdistancegradation_16bpc_case0026_analysis_20260628.md."
        ),
        "stop_condition": (
            "Return enough values to decide whether Windows ramps before "
            "FUN_181170480 compose (field-prep/normalization ownership) or only "
            "inside FUN_181170480 after invert/power interpolation. Placeholder "
            "wrapper hits or final PNG values alone are not enough."
        ),
    }


def distancegradation_layer_no_bg_source_ownership_action() -> dict[str, Any]:
    return {
        "request_id": "olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629",
        "plugin_area": "OLMDistanceGradation 16bpc Layer/no-bg source ownership witness",
        "mode": "external-trace",
        "command": (
            "Trace OLMDistanceGradation normalized Software 16bpc "
            "olmdistancegradation_extended__case_0012 and case_0016. Focus on the "
            "Layer render path with Use Background Color=0 where Windows and Mac "
            "share output alpha but disagree on RGB magnitude. Record the source/input "
            "pixel actually consumed by FUN_181170480, the field/X values, alpha base, "
            "the source-layer RGB/alpha values used by the compose branch, any "
            "premultiply or unpremultiply step, the output floats before 16bpc writeback, "
            "and the final RGBA16 at the listed witness pixels."
        ),
        "stop_condition": (
            "Return enough values to decide whether Windows derives Layer/no-bg RGB from "
            "straight source color times output alpha, from already-premultiplied source, "
            "or from another ownership rule. Final PNG values alone are not enough."
        ),
    }


def radialblur_dense_action() -> dict[str, Any]:
    return {
        "request_id": "olmradialblur_dense_sampler_trace_20260620",
        "plugin_area": "OLMRadialBlur dense sampler/scatter/writeback trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMRadialBlur representative Zoom, Rotation, and Inner cases. "
            "Record effective parameters, center/angle/radius normalization, "
            "sampler coordinates, scatter span/count, weight accumulation, "
            "normalization denominator, pre-writeback floats, and final bytes "
            "at residual witness pixels. Include the already known Inner "
            "span-31 fact as a sanity check, but focus on remaining sampler/"
            "prepass/writeback residuals."
        ),
        "stop_condition": (
            "Return enough per-pixel values to classify RadialBlur residuals as "
            "sampler coordinate, scatter/span, normalization, border handling, "
            "or writeback differences before further implementation tuning."
        ),
    }


def radialblur_residual_witness_action() -> dict[str, Any]:
    return {
        "request_id": "olmradialblur_zoom_tiny_rotation_residual_witness_20260622",
        "plugin_area": "OLMRadialBlur Zoom writeback and tiny Rotation validity witness",
        "mode": "external-trace",
        "command": (
            "Trace only the two classified RadialBlur residuals from "
            "`refs/reports/olmradialblur_residual_clusters_20260622_011750/`. "
            "For Zoom `case_0009`, focus on the max=1 alpha/RGB one-step "
            "residual at `(6,0)` and nearby scattered +1 alpha pixels: record "
            "the sampled polar/pre-output RGBA, normalization denominator, "
            "pre-writeback float/hex, final byte conversion operation, and final "
            "stored RGBA. For tiny Rotation `case_0010`, focus on the high-max "
            "witness `(1614,6)` where Windows is white and the Mac candidate is "
            "black while alpha stays 255: record inverse-sampler source/polar "
            "coordinates, validity/border decision, source/polar RGBA, "
            "normalization denominator, pre-writeback float/hex, and final "
            "stored RGBA. Do not return broad PNGs; these two witnesses are "
            "intended to separate writeback/alpha-normalization from sampler/"
            "validity misses."
        ),
        "stop_condition": (
            "Return enough typed values to classify Zoom as writeback, "
            "alpha-normalization, or sampler; and tiny Rotation as inverse "
            "sampler coordinate, validity/border, normalization, or writeback. "
            "If a breakpoint fails, return the exact failed address/condition "
            "and the closest available pre-output/final writer values."
        ),
    }


def radialblur_inner_cell_witness_action() -> dict[str, Any]:
    return {
        "request_id": "olmradialblur_inner_cell_witness_trace_20260625",
        "plugin_area": "OLMRadialBlur Inner FUN_180001c90 typed per-cell witness",
        "mode": "external-trace",
        "command": (
            "Trace the OLMRadialBlur Inner cases selected in "
            "`refs/reports/olmradialblur_inner_witness_plan_20260625/witness_plan.md`. "
            "Do not return broad PNGs and do not tune from the global candidate "
            "matrix. For `rb_inner_only_strength_large` and `rb_inner_quality_1`, "
            "capture typed values at the FUN_180001c90 scatter/helper level for "
            "one representative residual cell each: resolved span, span gate, "
            "table index, table divisor, loop bound, source polar row/column, "
            "destination polar row/column, border/underflow decision, gaussian "
            "or table weight, accumulated RGBA numerator, denominator, and the "
            "post-scatter value consumed by writeback. If those two witnesses do "
            "not explain the split, also capture `rb_inner_edgefade_only` with "
            "prepass alpha/factor plane values before FUN_180001c90."
        ),
        "stop_condition": (
            "Return enough typed per-cell evidence to decide whether Inner needs "
            "a family-specific circular wrap, loop-minus-one, table-span-minus-one, "
            "or prepass correction. If a breakpoint/watchpoint fails, return the "
            "exact function address, condition, case_id, pixel/cell, and closest "
            "available local variables instead of marking the request complete."
        ),
    }


def directionalblur_dense_action() -> dict[str, Any]:
    return {
        "request_id": "olmdirectionalblur_dense_sampler_trace_20260620",
        "plugin_area": "OLMDirectionalBlur dense sampler/writeback trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMDirectionalBlur representative Software cases through the "
            "directional sampler kernel. Record parameter normalization, angle/"
            "distance conversion, loop bounds, sample coordinates/order, border "
            "mode, per-sample weights, accumulation denominator, pre-writeback "
            "floats, and final bytes at high-diff witness pixels."
        ),
        "stop_condition": (
            "Return enough values to decide whether the remaining gap is angle "
            "normalization, sample count/range, border behavior, accumulation, "
            "or byte writeback. Do not request broad PNG sweeps without these "
            "kernel facts."
        ),
    }


def directionalblur_residual_witness_action() -> dict[str, Any]:
    return {
        "request_id": "olmdirectionalblur_angle0_diagonal_residual_witness_20260622",
        "plugin_area": "OLMDirectionalBlur angle-0 rowdriver and diagonal rotate-path residual witness",
        "mode": "external-trace",
        "command": (
            "Trace only the two classified OLMDirectionalBlur residual witnesses "
            "from `refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/`. "
            "Do not recapture broad PNGs and do not tune from the candidate matrix. "
            "Use the 8bpc Software reference cases that feed the local "
            "`rotated-aex-full-choreo` probe. For angle-0/front-only `case_0001`, "
            "focus on `(494,169)` where Windows reference is `[164,0,0,255]` and "
            "the local candidate is `[0,0,0,255]`. Record parameter normalization "
            "(front/back strength, angle, Size Variation, Edge Fade, Sharp Tail, "
            "Noise), A/B buffer coordinates for this output pixel, rowdriver/group "
            "membership, validity/alpha side-channel values, accumulation numerator/"
            "denominator, pre-writeback floats/hex, and final stored RGBA. For the "
            "diagonal rotate-path `case_0005`, focus on `(507,367)` where Windows "
            "reference is `[1,0,0,255]` and the local candidate is `[252,0,0,255]`. "
            "Record the same facts plus rotate sampler source coordinates/order, "
            "border/validity decision, group-size or opacity gating, and any "
            "normalize/divide step before final writeback. If the exact coordinate "
            "condition is too slow, first log the nearest high-diff row/diagonal "
            "component and return the exact condition that failed."
        ),
        "stop_condition": (
            "Return enough typed values to classify `case_0001` as rowdriver/group "
            "membership, valid-alpha side-channel, normalization, or writeback; and "
            "`case_0005` as rotate sampler coordinates, border/validity, group-size/"
            "opacity gating, normalization, or writeback. A satisfactory answer has "
            "per-pixel stage values for both witnesses, or a precise failed "
            "breakpoint/watchpoint reason with the closest successful stage."
        ),
    }


def toondilate_dense_action() -> dict[str, Any]:
    return {
        "request_id": "olmtoondilate_dense_chamfer_trace_20260620",
        "plugin_area": "OLMToonDilate light binary-grounding trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMToonDilate exact 8bpc Software cases lightly to confirm "
            "the binary-grounded kernel: threshold/matte setup, two-pass chamfer "
            "or distance propagation order, Chebyshev/chamfer neighborhood, "
            "semi-alpha RGB premultiply behavior, clamp, and final writeback at "
            "a few edge witness pixels."
        ),
        "stop_condition": (
            "Return a compact proof that the current AE-exact ToonDilate model "
            "matches Windows AEX constants, pass order, alpha/RGB handling, and "
            "writeback. This is conformance evidence, not an active tuning task."
        ),
    }


def dense_all_actions() -> list[dict[str, Any]]:
    return [
        smoother2_legacy_key_gamma_action(),
        colorkey_edge_action(),
        distancegradation_field_prep_action(),
        olmblur_repeat_threshold_action(),
        kirakira_stage_values_action(),
        radialblur_dense_action(),
        directionalblur_dense_action(),
        toondilate_dense_action(),
        smoother2_no_key_grid_action(),
    ]


def dense_live_followup_actions() -> list[dict[str, Any]]:
    actions = dense_all_actions()
    for action in actions:
        action = action
        action["command"] = (
            "LIVE TRACE FOLLOW-UP ONLY. Do not satisfy this request by merging "
            "old RETURN_RUNTIME_TRACE_TEMPLATE.json files or replacing nulls "
            "with not-isolated strings. Capture new debugger/runtime evidence. "
            + str(action.get("command", ""))
        )
        action["stop_condition"] = (
            str(action.get("stop_condition", ""))
            + " Return direct witness values or the exact failed breakpoint/watchpoint attempt; "
            "do not mark the request complete from static notes alone."
        )
    return actions


def selected_actions(snapshot: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    if profile == "dense-all":
        return dense_all_actions()
    if profile == "dense-live-followup":
        return dense_live_followup_actions()
    if profile == "colorkey-edge":
        return [colorkey_edge_action()]
    if profile == "colorkey-16bpc-case0009":
        return [colorkey_16bpc_case0009_action()]
    if profile == "olmblur-repeat-threshold":
        return [olmblur_repeat_threshold_action()]
    if profile == "kirakira-stage-values":
        return [kirakira_stage_values_action()]
    if profile == "kirakira-stage-values-deep":
        return [kirakira_deep_stage_values_action()]
    if profile == "kirakira-forward-warp-box-input":
        return [kirakira_forward_warp_box_input_action()]
    if profile == "kirakira-boxfilter-pass1-microprobe":
        return [kirakira_boxfilter_pass1_microprobe_action()]
    if profile == "kirakira-aggregation-compose-bt709":
        return [kirakira_aggregation_compose_bt709_action()]
    if profile == "radialblur-residual-witness":
        return [radialblur_residual_witness_action()]
    if profile == "radialblur-inner-cell-witness":
        return [radialblur_inner_cell_witness_action()]
    if profile == "directionalblur-residual-witness":
        return [directionalblur_residual_witness_action()]
    if profile == "smoother2-no-key-grid":
        return [smoother2_no_key_grid_action()]
    if profile == "smoother2-legacy-key-gamma":
        return [smoother2_legacy_key_gamma_action()]
    if profile == "smoother2-legacy-writeback-extract":
        return [smoother2_legacy_writeback_extract_action()]
    if profile == "smoother2-legacy-u8-writer-trace":
        return [smoother2_legacy_u8_writer_trace_action()]
    if profile == "smoother2-legacy-u8-pixel-trace":
        return [smoother2_legacy_u8_pixel_trace_action()]
    if profile == "smoother2-legacy-cce0-pixel-trace":
        return [smoother2_legacy_cce0_pixel_trace_action()]
    if profile == "smoother2-legacy-cce0-internals-trace":
        return [smoother2_legacy_cce0_internals_trace_action()]
    if profile == "smoother2-legacy-current-aex-residuals":
        return [smoother2_legacy_current_aex_residuals_action()]
    if profile == "smoother2-legacy-current-aex-polygon":
        return [smoother2_legacy_current_aex_polygon_action()]
    if profile == "smoother2-current-aex-f270-witness":
        return [smoother2_current_aex_f270_witness_action()]
    if profile == "smoother2-current-aex-writer-frame-followup":
        return [smoother2_current_aex_writer_frame_followup_action()]
    if profile == "distancegradation-field-prep":
        return [distancegradation_field_prep_action()]
    if profile == "distancegradation-layer-no-bg-source-ownership":
        return [distancegradation_layer_no_bg_source_ownership_action()]
    if profile == "distancegradation-16bpc-case0026-x-witness":
        return [distancegradation_16bpc_case0026_x_witness_action()]
    return runtime_actions(snapshot)


def package_manifest(root: Path, snapshot: dict[str, Any], profile: str) -> dict[str, Any]:
    actions = selected_actions(snapshot, profile)
    return {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "profile": profile,
        "packaged_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "repo_root_name": root.name,
        "runtime_actions": [
            {
                "request_id": action.get("request_id"),
                "plugin_area": action.get("plugin_area"),
                "mode": action.get("mode"),
                "command": action.get("command"),
                "stop_condition": action.get("stop_condition"),
            }
            for action in actions
        ],
        "entrypoint": str(TRACE_NOTE),
    }


def build_readme(manifest: dict[str, Any]) -> str:
    actions = manifest["runtime_actions"]
    live_followup = manifest.get("profile") == "dense-live-followup"
    lines = [
        "# OLM Runtime Trace Request Package",
        "",
        "This zip is for the Windows machine / Windows Codex session.",
        "It asks for debugger or exact-library primitive facts, not another PNG render batch.",
        "",
        f"Entrypoint: `{TRACE_NOTE}`",
        "",
        "Priority order:",
        "",
    ]
    if live_followup:
        lines.extend(
            [
                "Important: this is a live-trace follow-up package.",
                "",
                "- Do not answer by merging older trace return zips.",
                "- Do not replace requested values with `not isolated` just to make JSON non-null.",
                "- For each item, either capture direct CDB/WinDbg/runtime values or record the exact breakpoint/watchpoint attempt that failed.",
                "- Fewer complete cases are better than many placeholder-filled cases.",
                "",
            ]
        )
    for index, action in enumerate(actions, start=1):
        lines.extend(
            [
                f"{index}. `{action['request_id']}`",
                f"   - Area: {action['plugin_area']}",
                f"   - Action: {action['command']}",
                f"   - Stop: {action['stop_condition']}",
                "",
            ]
        )
    lines.extend(
        [
            "Return exactly the trace values / primitive fact requested in the note.",
            "You can fill `RETURN_RUNTIME_TRACE_TEMPLATE.json` and zip it back as the return artifact.",
            "Do not tune implementation code from PNG residuals while answering this package.",
            "",
        ]
    )
    return "\n".join(lines)


def build_return_template(manifest: dict[str, Any]) -> dict[str, Any]:
    result_templates = []
    for action in manifest["runtime_actions"]:
        request_id = action.get("request_id")
        if request_id == "radialblur_inner_runtime_trace_20260618":
            observations: dict[str, Any] = {
                "case_id": "rb_inner_only_strength_small",
                "module_base": "0x...",
                "r8d_at_0x26e5": None,
                "rsp_0x138_dword_at_0x26e5": "0x...",
                "edx_at_0x26e5": None,
                "r9d_at_0x26e5": None,
                "source_alpha_raw_dword_rsp_0x48": "0x...",
                "span_gate_raw_dword_rsp_0x28": "0x...",
                "inner_offset_mode_dword_rcx_0x2c": None,
                "inner_base_span_dword_rcx_0x3a9ec": None,
                "ebp_after_0x1d18": None,
                "r14d_after_0x1d18": None,
                "eax_after_0x1d43_optional": None,
                "xmm7_after_0x1d43_optional": None,
            }
            summary = "Fill with the observed RadialBlur inner helper registers/stack values."
        elif request_id == "kirakira_opencv455_primitive_fact_20260618":
            observations = {
                "fun_181281260_first_boxfilter_branch": "FUN_1812e39d0 | FUN_1812d7c40 | FUN_181280fa0 | other",
                "branch_condition": "feature 0xb | feature 6 | neither | unknown",
                "filter_constructors": "RowSum<float,double>/ColumnSum<double,float> equivalent | SIMD equivalent | other",
                "microprobe_opencv_version": "4.5.5 | not run",
                "microprobe_mean_diff_case_0001_optional": None,
                "microprobe_mean_diff_case_0002_optional": None,
                "microprobe_mean_diff_case_0003_optional": None,
            }
            summary = "Fill with the observed KiraKira OpenCV 4.5.5 primitive branch/fact."
        elif request_id == "colorkey_edge_runtime_trace_20260619":
            observations = {
                "effect": "OLM Color Key",
                "module_base": "0x...",
                "fun_1800094b0_hit": True,
                "ctx_0x28_edge_thin_direction_or_mode": None,
                "ctx_0x2c_edge_blur_direction": None,
                "ctx_0x40_edge_amount_raw_float": "0x...",
                "ctx_0x44_distance_type": None,
                "ctx_0x48_edge_blur_amount_raw_float": "0x...",
                "edge_thin_erode_cases": [
                    {
                        "case_id": "case_0005",
                        "witness": {"x": 34, "y": 0},
                        "reason": "top-edge erode alpha polarity; current C++ transparent, Windows opaque",
                        "initial_matched_or_keep_matte": None,
                        "distance_seed_input": None,
                        "distance_after_transform": None,
                        "ctx_amount_decoded_float": None,
                        "branch_condition_observed": "dist <= amount | dist < amount | dist > adjusted_limit | other",
                        "edge_thin_output_matte_or_alpha": None,
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0006",
                        "witness": {"x": 34, "y": 0},
                        "reason": "paired color-keep polarity; current C++ opaque, Windows transparent",
                        "initial_matched_or_keep_matte": None,
                        "distance_seed_input": None,
                        "distance_after_transform": None,
                        "ctx_amount_decoded_float": None,
                        "branch_condition_observed": "dist <= amount | dist < amount | dist > adjusted_limit | other",
                        "edge_thin_output_matte_or_alpha": None,
                        "final_output_rgba": [None, None, None, None],
                    },
                ],
                "edge_blur_samples": [
                    {
                        "case_id": "case_0008",
                        "x": 1111,
                        "y": 628,
                        "reason": "RGB/alpha contour residual; Python max-diff neighborhood",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0008",
                        "x": 464,
                        "y": 0,
                        "reason": "top-edge alpha residual; C++ max-diff neighborhood",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0009",
                        "x": 1116,
                        "y": 136,
                        "reason": "known high-diff neighborhood from normalized Software case_0009",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_thin_output_value": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0009",
                        "x": 1699,
                        "y": 7,
                        "reason": "top-edge/background neighborhood sanity sample",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_thin_output_value": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                ],
                "positive_edge_thin_copy_condition_observed": "dist <= amount | dist < amount | other",
                "edge_blur_distance_dispatch_observed": "1->FUN_180006e20,2->FUN_180005d60,3->FUN_180007ec0 | other",
                "edge_blur_apply_formula_summary": "",
            }
            summary = "Fill with ColorKey Edge Thin/Edge Blur ctx and sample trace values."
        elif request_id == "colorkey_16bpc_case0009_runtime_trace_20260626":
            observations = {
                "effect": "OLM Color Key",
                "request_id": "olm_bitdepth_16bpc_normalized_exact_20260625",
                "case_id": "olmcolorkey__case_0009",
                "module_base": "0x...",
                "ctx_fields": {
                    "bit_depth_or_source_format_field": None,
                    "ctx_0x3c_force_lower_precision": None,
                    "ctx_0x40_raw_float": "0x...",
                    "ctx_0x44_distance_type": None,
                    "ctx_0x48_raw_float": "0x...",
                },
                "witnesses": [
                    {
                        "x": 1110,
                        "y": 149,
                        "role": "largest residual component representative; opaque black kept by Mac, removed by Windows",
                        "core_lab76_matched_byte": None,
                        "post_core_pre_dilate_temp_matte_byte": None,
                        "positive_edge_thin_seed_byte_optional": None,
                        "distance_value_consumed": None,
                        "amount_or_limit_value_compared": None,
                        "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                        "post_dilate_matte_byte": None,
                        "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "x": 1213,
                        "y": 785,
                        "role": "second-largest representative; current Mac witness sits only 8px from nearest naive hit",
                        "core_lab76_matched_byte": None,
                        "post_core_pre_dilate_temp_matte_byte": None,
                        "positive_edge_thin_seed_byte_optional": None,
                        "distance_value_consumed": None,
                        "amount_or_limit_value_compared": None,
                        "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                        "post_dilate_matte_byte": None,
                        "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "x": 369,
                        "y": 95,
                        "role": "third-largest representative; far-from-hit opaque black witness",
                        "core_lab76_matched_byte": None,
                        "post_core_pre_dilate_temp_matte_byte": None,
                        "positive_edge_thin_seed_byte_optional": None,
                        "distance_value_consumed": None,
                        "amount_or_limit_value_compared": None,
                        "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                        "post_dilate_matte_byte": None,
                        "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "x": 1503,
                        "y": 57,
                        "role": "fourth-largest representative near top region",
                        "core_lab76_matched_byte": None,
                        "post_core_pre_dilate_temp_matte_byte": None,
                        "positive_edge_thin_seed_byte_optional": None,
                        "distance_value_consumed": None,
                        "amount_or_limit_value_compared": None,
                        "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                        "post_dilate_matte_byte": None,
                        "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "x": 668,
                        "y": 945,
                        "role": "fifth-largest representative; far-from-hit opaque black witness",
                        "core_lab76_matched_byte": None,
                        "post_core_pre_dilate_temp_matte_byte": None,
                        "positive_edge_thin_seed_byte_optional": None,
                        "distance_value_consumed": None,
                        "amount_or_limit_value_compared": None,
                        "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                        "post_dilate_matte_byte": None,
                        "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "x": 1699,
                        "y": 7,
                        "role": "optional top-edge sanity witness",
                        "core_lab76_matched_byte": None,
                        "post_core_pre_dilate_temp_matte_byte": None,
                        "positive_edge_thin_seed_byte_optional": None,
                        "distance_value_consumed": None,
                        "amount_or_limit_value_compared": None,
                        "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                        "post_dilate_matte_byte": None,
                        "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                        "final_output_rgba": [None, None, None, None],
                    },
                ],
                "control_pixel_optional": {
                    "x": None,
                    "y": None,
                    "role": "definitely-kept control pixel from the same frame",
                    "core_lab76_matched_byte": None,
                    "post_core_pre_dilate_temp_matte_byte": None,
                    "positive_edge_thin_seed_byte_optional": None,
                    "distance_value_consumed": None,
                    "amount_or_limit_value_compared": None,
                    "copy_condition_observed": "dist <= amount | dist < amount | adjusted-limit | other",
                    "post_dilate_matte_byte": None,
                    "frame_edge_neighbors_treated_as": "inside | outside | mixed | unknown",
                    "final_output_rgba": [None, None, None, None],
                },
            }
            summary = "Fill with narrow 16bpc ColorKey case_0009 ctx/seed/dilate witness values."
        elif request_id == "olmblur_repeat_threshold_runtime_trace_20260619":
            observations = {
                "effect": "OLM Blur",
                "module_base": "0x...",
                "cases": [
                    {
                        "case_id": "case_0006",
                        "legacy": 0,
                        "repeat": 10,
                        "bias_direction": 1,
                        "residual_pixels": [
                            {
                                "x": 498,
                                "y": 940,
                                "windows_reference_rgba": [185, 0, 0, 255],
                                "mac_cli_candidate_rgba": [186, 0, 0, 255],
                                "cli_pre_writeback_rgb_hex": ["0x1.73p+7", "0x1.44a3c6p-4", "0x1.44a3c6p-4"],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "aex_writeback_operation": "floorf(value + 0.5) | cvt/trunc | other",
                                "aex_final_rgba": [None, None, None, None],
                            }
                        ],
                        "radius_path_fact": "confirm decay is powf but per-iteration radius uses pow(double,double) and float sigma",
                        "accumulation_order_notes": "",
                    },
                    {
                        "case_id": "case_0007",
                        "legacy": 1,
                        "repeat": 10,
                        "bias_direction": 1,
                        "residual_pixels": [
                            {
                                "x": 0,
                                "y": 0,
                                "windows_reference_rgba": [0, 0, 0, 255],
                                "mac_cli_candidate_rgba": [1, 1, 1, 255],
                                "cli_pre_writeback_rgb_hex": [None, None, None],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "legacy_border_sample_included": None,
                                "legacy_all_same_state": None,
                                "aex_final_rgba": [None, None, None, None],
                            },
                            {
                                "x": 488,
                                "y": 941,
                                "windows_reference_rgba": [251, 0, 0, 255],
                                "mac_cli_candidate_rgba": [250, 0, 0, 255],
                                "cli_pre_writeback_rgb_hex": [None, None, None],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "legacy_border_sample_included": None,
                                "legacy_all_same_state": None,
                                "aex_final_rgba": [None, None, None, None],
                            },
                            {
                                "x": 488,
                                "y": 942,
                                "windows_reference_rgba": [251, 0, 0, 255],
                                "mac_cli_candidate_rgba": [250, 0, 0, 255],
                                "cli_pre_writeback_rgb_hex": [None, None, None],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "legacy_border_sample_included": None,
                                "legacy_all_same_state": None,
                                "aex_final_rgba": [None, None, None, None],
                            },
                        ],
                        "negative_probes_to_avoid": [
                            "initializing all_same from -1 worsened case_0007 to max=16 / 21px",
                            "including border coordinate 0 worsened case_0007 to max=15 / 5412px",
                        ],
                    },
                ],
            }
            summary = "Fill with OLMBlur residual pre-writeback/writeback and Legacy border trace facts."
        elif request_id == "kirakira_fun_181150790_stage_values_20260620":
            observations = {
                "effect": "OLM Kira Kira",
                "module_base": "0x...",
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "reference_case_path_hint": (
                    "refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira/"
                    "kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
                ),
                "known_facts_to_keep": {
                    "first_boxfilter_branch": "FUN_1812e39d0 / AVX2",
                    "boxfilter_args": {
                        "ksize": [50, 1],
                        "anchor": [-1, -1],
                        "normalize": True,
                        "border_type": 4,
                    },
                    "warpaffine_flags": "INTER_LINEAR, no WARP_INVERSE_MAP, BORDER_CONSTANT zero",
                    "temp_extent_rule": "truncate after +4.0 then clamp to at least source size + 4",
                },
                "fun_181150790_entry": {
                    "src_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "tmp1_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "tmp2_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "ray_length": None,
                    "angle_degrees_or_radians": None,
                    "affine_forward_matrix": [None, None, None, None, None, None],
                    "affine_back_matrix": [None, None, None, None, None, None],
                    "forward_dsize": [None, None],
                    "back_dsize": [None, None],
                    "source_roi_rect": [None, None, None, None],
                    "final_copy_rect": [None, None, None, None],
                },
                "witness_pixels": [
                    {
                        "label": "source_seed_center",
                        "xy": [960, 540],
                        "source_xy": [960, 540],
                        "tmp1_xy": [None, None],
                        "tmp2_xy": [None, None],
                        "ray_xy": [960, 540],
                        "before_center_copy_float": None,
                        "after_center_copy_tmp1_float": None,
                        "after_forward_warp_tmp2_float": None,
                        "after_box_1_float": None,
                        "after_box_2_float": None,
                        "after_box_3_float": None,
                        "after_rotate_back_tmp1_float": None,
                        "after_final_center_copy_ray_float": None,
                    },
                    {
                        "label": "vertical_ray_peak_or_first_nonzero",
                        "xy": [960, 490],
                        "source_xy": [960, 490],
                        "tmp1_xy": [None, None],
                        "tmp2_xy": [None, None],
                        "ray_xy": [960, 490],
                        "before_center_copy_float": None,
                        "after_center_copy_tmp1_float": None,
                        "after_forward_warp_tmp2_float": None,
                        "after_box_1_float": None,
                        "after_box_2_float": None,
                        "after_box_3_float": None,
                        "after_rotate_back_tmp1_float": None,
                        "after_final_center_copy_ray_float": None,
                    },
                    {
                        "label": "current_residual_hotspot_optional",
                        "xy": [None, None],
                        "source_xy": [None, None],
                        "tmp1_xy": [None, None],
                        "tmp2_xy": [None, None],
                        "ray_xy": [None, None],
                        "windows_reference_rgba": [None, None, None, None],
                        "mac_cli_candidate_rgba": [None, None, None, None],
                        "ray_float_before_aggregation": None,
                        "aggregation_output_float_rgba": [None, None, None, None],
                        "final_merge_rgba": [None, None, None, None],
                    },
                ],
                "boxfilter_calls": [
                    {
                        "index": 1,
                        "selected_branch": "FUN_1812e39d0 | other",
                        "src_mat_header": {},
                        "dst_mat_header": {},
                        "sample_before_after": [],
                    },
                    {
                        "index": 2,
                        "selected_branch": "FUN_1812e39d0 | other",
                        "src_mat_header": {},
                        "dst_mat_header": {},
                        "sample_before_after": [],
                    },
                    {
                        "index": 3,
                        "selected_branch": "FUN_1812e39d0 | other",
                        "src_mat_header": {},
                        "dst_mat_header": {},
                        "sample_before_after": [],
                    },
                ],
                "aggregation_and_compose": {
                    "fun_18114fd90_inputs": {
                        "brightness": None,
                        "strength": None,
                        "ray_scalar_or_gain": None,
                    },
                    "fun_18114fd90_sample_outputs": [],
                    "merge_mode_1_sample_inputs_outputs": [],
                },
            }
            summary = "Fill with KiraKira FUN_181150790 stage values and aggregation/compose witnesses."
        elif request_id == "kirakira_fun_181150790_deep_stage_values_20260621":
            observations = {
                "effect": "OLM Kira Kira",
                "module_base": "0x...",
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "included_local_baseline": (
                    "refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/"
                    "witness_plan.json"
                ),
                "known_facts_to_keep": {
                    "first_boxfilter_branch": "FUN_1812e39d0 / AVX2",
                    "boxfilter_args": {
                        "ksize": [50, 1],
                        "anchor": [-1, -1],
                        "normalize": True,
                        "border_type": 4,
                    },
                    "warpaffine_flags": "INTER_LINEAR, no WARP_INVERSE_MAP, BORDER_CONSTANT zero",
                    "temp_size": [1924, 1924],
                    "copy_origin_expected": [2, 422],
                    "center_expected": [962.0, 962.0],
                    "forward_matrix_local": [
                        6.123234262925839e-17,
                        1.0,
                        -1.1368683772161603e-13,
                        -1.0,
                        6.123234262925839e-17,
                        1924.0,
                    ],
                    "back_matrix_local": [
                        6.123234262925839e-17,
                        -1.0,
                        1924.0,
                        1.0,
                        6.123234262925839e-17,
                        -1.1368683772161603e-13,
                    ],
                },
                "windows_fun_181150790_entry": {
                    "src_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "tmp1_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "tmp2_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "ray_length": None,
                    "angle_degrees_or_radians": None,
                    "affine_forward_matrix": [None, None, None, None, None, None],
                    "affine_back_matrix": [None, None, None, None, None, None],
                    "source_roi_rect": [None, None, None, None],
                    "final_copy_rect": [None, None, None, None],
                },
                "stage_witnesses": [
                    {
                        "label": "center",
                        "source_xy": [960, 540],
                        "temp_xy": [962, 962],
                        "local_expected": {
                            "seed": 0.11764706671237946,
                            "after_center_copy": 0.11764706671237946,
                            "after_forward_warp": 0.11764706671237946,
                            "after_box_1": 0.7871310114860535,
                            "after_box_2": 0.7226850986480713,
                            "after_box_3": 0.7102346420288086,
                            "after_rotate_back": 0.7102346420288086,
                            "after_final_center_copy": 0.7102346420288086,
                        },
                        "windows_observed": {},
                    },
                    {
                        "label": "ray_length_up",
                        "source_xy": [960, 490],
                        "temp_xy": [962, 912],
                        "local_expected": {
                            "seed": 0.7799215912818909,
                            "after_center_copy": 0.7799215912818909,
                            "after_forward_warp": 0.11764706671237946,
                            "after_box_1": 0.7714077830314636,
                            "after_box_2": 0.6957992315292358,
                            "after_box_3": 0.7070566415786743,
                            "after_rotate_back": 0.7545762062072754,
                            "after_final_center_copy": 0.7545762062072754,
                        },
                        "windows_observed": {},
                    },
                    {
                        "label": "ray_length_right",
                        "source_xy": [1010, 540],
                        "temp_xy": [1012, 962],
                        "local_expected": {
                            "seed": 0.11764706671237946,
                            "after_center_copy": 0.11764706671237946,
                            "after_forward_warp": 0.11764706671237946,
                            "after_box_1": 0.3080717623233795,
                            "after_box_2": 0.39996397495269775,
                            "after_box_3": 0.4451564848423004,
                            "after_rotate_back": 0.7070566415786743,
                            "after_final_center_copy": 0.7070566415786743,
                        },
                        "windows_observed": {},
                    },
                ],
                "aggregation_and_compose": {
                    "center_local_expected": {
                        "source_rgba": [0.11764705926179886, 0.11764705926179886, 0.11764705926179886, 1.0],
                        "glow_rgba": [1.0, 1.0, 1.0, 0.44034549593925476],
                        "out_rgba_float": [0.5061872005462646, 0.5061872005462646, 0.5061872005462646, 1.0],
                        "out_rgba_u8": [129, 129, 129, 255],
                    },
                    "windows_observed_samples": [],
                },
                "first_divergence_classification": (
                    "center-copy | forward-warp | box-filter-pass-1 | box-filter-pass-2 | "
                    "box-filter-pass-3 | rotate-back | final-copy | aggregation | compose | unknown"
                ),
            }
            summary = "Fill with deep KiraKira per-stage witness values and first-divergence classification."
        elif request_id == "kirakira_aggregation_compose_bt709_20260624":
            observations = {
                "effect": "OLM Kira Kira",
                "module_base": "0x...",
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "why_this_trace": (
                    "BT.709 local trace matches Windows through box pass 1/2/3, "
                    "rotate-back, and final center-copy within 1e-5. Remaining "
                    "PNG residual should be isolated in aggregation, merge-mode "
                    "compose, or final quantization/export."
                ),
                "known_facts_to_keep": {
                    "channel_2_seed_luma": "BT.709",
                    "ray_helper_status": "matches Windows within float print precision for captured vertical witness",
                    "boxfilter_branch": "FUN_1812e39d0 / AVX2",
                    "boxfilter_args": {
                        "ksize": [50, 1],
                        "anchor": [-1, -1],
                        "normalize": True,
                        "border_type": 4,
                    },
                    "merge_mode_1_model_under_test": "screen source RGB with glow RGB*glow_alpha; preserve source alpha",
                },
                "local_bt709_expected": {
                    "center": {
                        "source_xy": [960, 540],
                        "ray_values": {
                            "after_final_center_copy": 0.7189121246337891,
                        },
                        "aggregation_and_compose": {
                            "source_rgba": [0.11764705926179886, 0.11764705926179886, 0.11764705926179886, 1.0],
                            "glow_rgba": [1.0, 1.0, 1.0, 0.44572553038597107],
                            "out_rgba_float": [0.5109343528747559, 0.5109343528747559, 0.5109343528747559, 1.0],
                            "out_rgba_u8": [130, 130, 130, 255],
                        },
                    },
                    "ray_length_up": {
                        "source_xy": [960, 490],
                        "ray_values": {
                            "after_final_center_copy": 0.7683287858963013,
                        },
                    },
                    "ray_length_right": {
                        "source_xy": [1010, 540],
                        "ray_values": {
                            "after_final_center_copy": 0.715643584728241,
                        },
                    },
                },
                "fun_18114fd90_aggregation": {
                    "entry": {
                        "brightness_or_param_10": None,
                        "glow_opacity": None,
                        "source_opacity": None,
                        "output_buffer": "0x...",
                        "width": None,
                        "height": None,
                    },
                    "sample_outputs": [
                        {
                            "label": "center",
                            "source_xy": [960, 540],
                            "ray_inputs": [None, None, None, None, None],
                            "layer_alphas_after_clamp": [None, None, None, None, None],
                            "pre_normalize_rgba": [None, None, None, None],
                            "post_normalize_glow_rgba": [None, None, None, None],
                        }
                    ],
                },
                "merge_mode_1_compose": {
                    "sample_inputs_outputs": [
                        {
                            "label": "center",
                            "source_xy": [960, 540],
                            "source_rgba_float": [None, None, None, None],
                            "glow_rgba_float": [None, None, None, None],
                            "glow_after_opacity_rgba_float": [None, None, None, None],
                            "composed_rgba_float": [None, None, None, None],
                            "pre_writeback_rgba_float": [None, None, None, None],
                            "final_writeback_or_png_rgba": [None, None, None, None],
                        }
                    ],
                },
                "residual_hotspots": [
                    {
                        "label": "primary_vertical_case_hotspot",
                        "case_id": "kk_vertical_len50_brightness1_strength100",
                        "source_xy": [934, 118],
                        "windows_reference_rgba": [131, 131, 131, 255],
                        "mac_bt709_candidate_rgba": [145, 145, 145, 255],
                        "delta_candidate_minus_windows": [14, 14, 14, 0],
                        "aggregation_glow_rgba_float": [None, None, None, None],
                        "compose_output_rgba_float": [None, None, None, None],
                        "final_writeback_or_png_rgba": [None, None, None, None],
                    },
                    {
                        "label": "optional_global_software_hotspot",
                        "case_id": "kk_diagonal_len50_rotation13",
                        "source_xy": [1098, 202],
                        "windows_reference_rgba": [112, 112, 112, 255],
                        "mac_bt709_candidate_rgba": [46, 46, 46, 255],
                        "delta_candidate_minus_windows": [-66, -66, -66, 0],
                        "aggregation_glow_rgba_float": [None, None, None, None],
                        "compose_output_rgba_float": [None, None, None, None],
                        "final_writeback_or_png_rgba": [None, None, None, None],
                    },
                ],
                "directly_observed_vs_inferred": {
                    "directly_observed": [],
                    "static_or_decomp_inferred": [],
                    "not_isolated": [],
                },
            }
            summary = "Fill with KiraKira BT.709 aggregation/compose/final quantization witnesses."
        elif request_id == "kirakira_forward_warp_box_input_20260621":
            observations = {
                "effect": "OLM Kira Kira",
                "module_base": "0x...",
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "supersedes_request": "kirakira_fun_181150790_deep_stage_values_20260621",
                "previous_first_concrete_divergence": {
                    "stage": "after_box_1",
                    "point": "center",
                    "windows_minus_local": 0.00765908,
                },
                "known_facts_to_keep": {
                    "first_boxfilter_branch": "FUN_1812e39d0 / AVX2",
                    "boxfilter_args": {
                        "ksize": [50, 1],
                        "anchor": [-1, -1],
                        "normalize": True,
                        "border_type": 4,
                    },
                    "warpaffine_flags": "INTER_LINEAR, no WARP_INVERSE_MAP, BORDER_CONSTANT zero",
                    "temp_size": [1924, 1924],
                    "copy_origin_expected": [2, 422],
                    "center_expected": [962.0, 962.0],
                },
                "forward_warp": {
                    "matrix": [None, None, None, None, None, None],
                    "dsize": [None, None],
                    "src_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "dst_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "source_roi_rect": [None, None, None, None],
                    "copy_origin": [None, None],
                },
                "boxfilter_pass_1": {
                    "selected_branch": "FUN_1812e39d0 | other",
                    "ksize": [None, None],
                    "anchor": [None, None],
                    "normalize": None,
                    "border_type": None,
                    "src_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "dst_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                },
                "witnesses": [
                    {
                        "label": "center",
                        "source_xy": [960, 540],
                        "temp_xy": [962, 962],
                        "local_expected": {
                            "after_center_copy": 0.11764706671237946,
                            "after_forward_warp": 0.11764706671237946,
                            "before_box_1": 0.11764706671237946,
                            "after_box_1": 0.7871310114860535,
                        },
                        "windows_observed": {
                            "after_center_copy": None,
                            "after_forward_warp": None,
                            "before_box_1": None,
                            "after_box_1": None,
                        },
                    },
                    {
                        "label": "ray_length_up",
                        "source_xy": [960, 490],
                        "temp_xy": [962, 912],
                        "local_expected": {
                            "after_center_copy": 0.7799215912818909,
                            "after_forward_warp": 0.11764706671237946,
                            "before_box_1": 0.11764706671237946,
                            "after_box_1": 0.7714077830314636,
                        },
                        "windows_observed": {
                            "after_center_copy": None,
                            "after_forward_warp": None,
                            "before_box_1": None,
                            "after_box_1": None,
                        },
                    },
                    {
                        "label": "ray_length_right",
                        "source_xy": [1010, 540],
                        "temp_xy": [1012, 962],
                        "local_expected": {
                            "after_center_copy": 0.11764706671237946,
                            "after_forward_warp": 0.11764706671237946,
                            "before_box_1": 0.11764706671237946,
                            "after_box_1": 0.3080717623233795,
                        },
                        "windows_observed": {
                            "after_center_copy": None,
                            "after_forward_warp": None,
                            "before_box_1": None,
                            "after_box_1": None,
                        },
                    },
                ],
                "first_divergence_classification": (
                    "center-copy | forward-warp | boxfilter-input | boxfilter-pass-1 | unknown"
                ),
                "failed_breakpoint_or_watchpoint_reason": None,
            }
            summary = "Fill with the missing KiraKira forward-warp / boxFilter pass-1 input witness values."
        elif request_id == "kirakira_boxfilter_pass1_microprobe_20260622":
            observations = {
                "effect": "OLM Kira Kira",
                "module_base": "0x...",
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "supersedes_request": "kirakira_forward_warp_box_input_20260621",
                "known_facts_to_keep": {
                    "first_boxfilter_branch": "FUN_1812e39d0 / OpenCV 4.5.5 AVX2",
                    "local_boxfilter_window_plan": (
                        "refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.json"
                    ),
                    "boxfilter_args": {
                        "ksize": [50, 1],
                        "anchor": [-1, -1],
                        "normalize": True,
                        "border_type": 4,
                    },
                    "before_box_1_matches_after_forward_warp": True,
                    "local_expected_after_box_1": {
                        "center": 0.7871310114860535,
                        "ray_length_up": 0.7714077830314636,
                        "ray_length_right": 0.3080717623233795,
                    },
                    "known_windows_minus_local_after_box_1": {
                        "center": 0.00765908,
                        "ray_length_up": 0.00722814,
                        "ray_length_right": 0.00512678,
                    },
                },
                "boxfilter_pass_1": {
                    "breakpoint_or_probe_site": "FUN_1812e39d0 | wrapper | failed",
                    "selected_path_or_nearest_offset": None,
                    "accumulator_precision": "float|double|integer|SIMD-lane|unknown",
                    "src_mat": {
                        "rows": None,
                        "cols": None,
                        "type": None,
                        "step": None,
                        "data": "0x...",
                    },
                    "dst_mat": {
                        "rows": None,
                        "cols": None,
                        "type": None,
                        "step": None,
                        "data": "0x...",
                    },
                },
                "witnesses": [
                    {
                        "label": "center",
                        "temp_xy": [962, 962],
                        "local_after_box_1": 0.7871310114860535,
                        "local_input_window": {
                            "anchor_x": 25,
                            "x_range_unbordered": [937, 986],
                            "mean": 0.7871310114860535,
                        },
                        "windows_after_box_1": None,
                        "resolved_source_x_range_after_border": [None, None],
                        "border_reflect101_indices_or_formula": None,
                        "contributing_samples_float": [],
                        "sample_summary": {
                            "count": None,
                            "sum": None,
                            "min": None,
                            "max": None,
                            "hash": None,
                        },
                        "normalized_sum_before_store": None,
                        "stored_float_after_pass_1": None,
                    },
                    {
                        "label": "ray_length_up",
                        "temp_xy": [962, 912],
                        "local_after_box_1": 0.7714077830314636,
                        "local_input_window": {
                            "anchor_x": 25,
                            "x_range_unbordered": [937, 986],
                            "mean": 0.7714077830314636,
                        },
                        "windows_after_box_1": None,
                        "resolved_source_x_range_after_border": [None, None],
                        "border_reflect101_indices_or_formula": None,
                        "contributing_samples_float": [],
                        "sample_summary": {
                            "count": None,
                            "sum": None,
                            "min": None,
                            "max": None,
                            "hash": None,
                        },
                        "normalized_sum_before_store": None,
                        "stored_float_after_pass_1": None,
                    },
                    {
                        "label": "ray_length_right",
                        "temp_xy": [1012, 962],
                        "local_after_box_1": 0.3080717623233795,
                        "local_input_window": {
                            "anchor_x": 25,
                            "x_range_unbordered": [987, 1036],
                            "mean": 0.3080717623233795,
                        },
                        "windows_after_box_1": None,
                        "resolved_source_x_range_after_border": [None, None],
                        "border_reflect101_indices_or_formula": None,
                        "contributing_samples_float": [],
                        "sample_summary": {
                            "count": None,
                            "sum": None,
                            "min": None,
                            "max": None,
                            "hash": None,
                        },
                        "normalized_sum_before_store": None,
                        "stored_float_after_pass_1": None,
                    },
                ],
                "classification": (
                    "different-window | border-reflect101 | accumulator-precision | "
                    "store-rounding | different-mat-stage | failed-to-isolate"
                ),
                "failure_if_any": None,
            }
            summary = "Fill with OLMKiraKira first boxFilter pass contributing-window microprobe facts."
        elif request_id == "olmradialblur_zoom_tiny_rotation_residual_witness_20260622":
            observations = {
                "effect": "OLM RadialBlur",
                "module_base": "0x...",
                "residual_cluster_report": (
                    "refs/reports/olmradialblur_residual_clusters_20260622_011750/residual_clusters.md"
                ),
                "cases": [
                    {
                        "case_id": "case_0009",
                        "path": "Zoom no-inner/no-noise",
                        "local_classification": "scattered one-step alpha/writeback residual",
                        "witness": {
                            "x": 6,
                            "y": 0,
                            "reference_rgba": [20, 3, 3, 254],
                            "mac_candidate_rgba": [20, 3, 3, 255],
                            "signed_delta_candidate_minus_reference": [0, 0, 0, 1],
                        },
                        "aex_sampler_or_polar_xy": None,
                        "aex_validity_or_border_decision": None,
                        "aex_source_or_polar_rgba_float": [None, None, None, None],
                        "aex_normalization_denominator": None,
                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                        "aex_writeback_operation": "round|floor(x+0.5)|trunc|cvt|other",
                        "aex_final_rgba_u8": [None, None, None, None],
                        "classification": "writeback | alpha-normalization | sampler | unresolved",
                    },
                    {
                        "case_id": "case_0010",
                        "path": "tiny Rotation",
                        "local_classification": "localized high-max RGB miss, not pure rounding",
                        "witness": {
                            "x": 1614,
                            "y": 6,
                            "reference_rgba": [255, 255, 255, 255],
                            "mac_candidate_rgba": [0, 0, 0, 255],
                            "signed_delta_candidate_minus_reference": [-255, -255, -255, 0],
                        },
                        "aex_inverse_sampler_input_xy": None,
                        "aex_polar_or_source_xy": None,
                        "aex_validity_or_border_decision": None,
                        "aex_source_or_polar_rgba_float": [None, None, None, None],
                        "aex_normalization_denominator": None,
                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                        "aex_writeback_operation": "round|floor(x+0.5)|trunc|cvt|other",
                        "aex_final_rgba_u8": [None, None, None, None],
                        "classification": "inverse-sampler | validity-border | normalization | writeback | unresolved",
                    },
                ],
                "failed_breakpoint_or_watchpoint_reason": None,
            }
            summary = "Fill with focused OLMRadialBlur Zoom/tiny Rotation residual witness facts."
        elif request_id == "olmdirectionalblur_angle0_diagonal_residual_witness_20260622":
            observations = {
                "effect": "OLM DirectionalBlur",
                "module_base": "0x...",
                "residual_cluster_report": (
                    "refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/residual_clusters.md"
                ),
                "candidate_under_test": "rotated-aex-full-choreo",
                "cases": [
                    {
                        "case_id": "case_0001",
                        "path": "angle-0/front-only",
                        "local_classification": "broad RGB residual; candidate misses red band while alpha matches",
                        "witness": {
                            "x": 494,
                            "y": 169,
                            "reference_rgba": [164, 0, 0, 255],
                            "mac_candidate_rgba": [0, 0, 0, 255],
                            "signed_delta_candidate_minus_reference": [-164, 0, 0, 0],
                        },
                        "aex_parameter_normalization": {
                            "angle": None,
                            "front_strength": None,
                            "back_strength": None,
                            "size_variation": None,
                            "edge_fade": None,
                            "sharp_tail": None,
                            "noise": None,
                        },
                        "aex_output_to_ab_buffer_xy": None,
                        "aex_rowdriver_or_group_membership": None,
                        "aex_validity_or_alpha_side_channel": None,
                        "aex_accumulation_numerator_rgba_float_or_hex": [None, None, None, None],
                        "aex_accumulation_denominator": None,
                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                        "aex_final_rgba_u8": [None, None, None, None],
                        "classification": "rowdriver-group | valid-alpha-side-channel | normalization | writeback | unresolved",
                    },
                    {
                        "case_id": "case_0005",
                        "path": "diagonal rotate-path",
                        "local_classification": "localized high-max RGB inversion; candidate overshoots red while alpha mostly matches",
                        "witness": {
                            "x": 507,
                            "y": 367,
                            "reference_rgba": [1, 0, 0, 255],
                            "mac_candidate_rgba": [252, 0, 0, 255],
                            "signed_delta_candidate_minus_reference": [251, 0, 0, 0],
                        },
                        "aex_parameter_normalization": {
                            "angle": None,
                            "front_strength": None,
                            "back_strength": None,
                            "size_variation": None,
                            "edge_fade": None,
                            "sharp_tail": None,
                            "noise": None,
                        },
                        "aex_output_to_ab_buffer_xy": None,
                        "aex_rotate_sampler_source_coordinates_order": [],
                        "aex_border_or_validity_decision": None,
                        "aex_group_size_or_opacity_gate": None,
                        "aex_accumulation_numerator_rgba_float_or_hex": [None, None, None, None],
                        "aex_accumulation_denominator": None,
                        "aex_pre_writeback_rgba_float_or_hex": [None, None, None, None],
                        "aex_final_rgba_u8": [None, None, None, None],
                        "classification": "rotate-sampler | border-validity | group-size-opacity | normalization | writeback | unresolved",
                    },
                ],
                "failed_breakpoint_or_watchpoint_reason": None,
            }
            summary = "Fill with focused OLMDirectionalBlur angle-0/diagonal residual witness facts."
        elif request_id == "olmsmoother2_no_key_grid_runtime_trace_20260619":
            observations = {
                "effect": "OLM Smoother v2",
                "module_base": "0x...",
                "case_id": "sm2_no_key_s100_r3",
                "reference_case_path_hint": (
                    "refs/win_references/20260605_extra/OLMSmoother2/"
                    "smoother2_no_key_grid_20260606__software__fr24__sm2_no_key_s100_r3.png"
                ),
                "pixels": [
                    {
                        "x": 211,
                        "y": 139,
                        "mac_cli_idx": "0x10",
                        "mac_cli_candidate_rgba": [203, 66, 66, 255],
                        "windows_reference_rgba": [212, 68, 68, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x1e",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [210, 139], "weight": 0.40000001},
                                {"src": [210, 139], "weight": 0.2},
                            ],
                        },
                    },
                    {
                        "x": 215,
                        "y": 145,
                        "mac_cli_idx": "0x08",
                        "mac_cli_candidate_rgba": [54, 34, 34, 255],
                        "windows_reference_rgba": [46, 32, 32, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x14",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [216, 145], "weight": 0.32000002},
                                {"src": [216, 145], "weight": 0.2},
                            ],
                        },
                    },
                    {
                        "x": 991,
                        "y": 139,
                        "mac_cli_idx": "0x10",
                        "mac_cli_candidate_rgba": [212, 194, 57, 255],
                        "windows_reference_rgba": [221, 202, 59, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x1e",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [990, 139], "weight": 0.40000001},
                                {"src": [990, 139], "weight": 0.2},
                            ],
                        },
                    },
                    {
                        "x": 995,
                        "y": 145,
                        "mac_cli_idx": "0x08",
                        "mac_cli_candidate_rgba": [56, 53, 33, 255],
                        "windows_reference_rgba": [47, 45, 32, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x14",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [996, 145], "weight": 0.32000002},
                                {"src": [996, 145], "weight": 0.2},
                            ],
                        },
                    },
                ],
                "requested_for_each_pixel": {
                    "fun_18000c280_switch_idx": None,
                    "cardinal3_descriptor_and_key": None,
                    "cardinal12_descriptor_and_key": None,
                    "scan_helpers": {
                        "FUN_180010820": {
                            "d520_return_xy_class": [None, None, None],
                            "d520_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "dbd0_return_xy_class": [None, None, None],
                            "dbd0_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "FUN_1800101e0_key": None,
                        },
                        "FUN_1800105f0": {
                            "d230_return_xy_class": [None, None, None],
                            "d230_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "d800_return_xy_class": [None, None, None],
                            "d800_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "FUN_18000fbf0_key": None,
                        },
                    },
                    "append_sequence": [
                        {
                            "src_xy": [None, None],
                            "sample_rgba_float_hex": [None, None, None, None],
                            "weight_float_hex": None,
                            "count_before": None,
                        }
                    ],
                    "composite": {
                        "center_rgba_float_hex": [None, None, None, None],
                        "total_weight_hex": None,
                        "output_before_b120_hex": [None, None, None, None],
                    },
                    "post_b120_rgba_float_hex": [None, None, None, None],
                    "writeback": {
                        "pre_srgb_rgb_hex": [None, None, None],
                        "post_srgb_rgb_hex": [None, None, None],
                        "final_rgba_8bit": [None, None, None, None],
                    },
                },
            }
            summary = "Fill with OLMSmoother2 no-key grid per-pixel polygon/composite/writeback trace facts."
        elif request_id == "olmsmoother2_legacy_key_gamma_runtime_trace_20260620":
            observations = {
                "effect": "OLM Smoother v2",
                "module_base": "0x...",
                "reference_report_hint": (
                    "refs/reports/ae_host_validation_20260620_1425/"
                    "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
                ),
                "cases": [
                    {
                        "case_id": "case_0001",
                        "reason": (
                            "Color Key disabled; alpha matches at witnesses but RGB is much lower "
                            "in the Mac candidate, so writeback/premultiply/gamma ownership is suspect."
                        ),
                        "expected_params": {
                            "enable_color_key": 0,
                            "invert_color_key": 0,
                            "smoothness": 100,
                            "extra_smooth": 0,
                            "smooth_range": 2,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [25, 25, 25, 75], "windows_reference_rgba": [75, 75, 75, 75]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [44, 44, 44, 106], "windows_reference_rgba": [106, 106, 106, 106]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [25, 25, 25, 75], "windows_reference_rgba": [75, 75, 75, 75]},
                        ],
                    },
                    {
                        "case_id": "case_0002",
                        "reason": (
                            "Color Key enabled + invert; Mac candidate zeros top-edge pixels where "
                            "Windows keeps nonzero RGBA."
                        ),
                        "expected_params": {
                            "enable_color_key": 1,
                            "invert_color_key": 1,
                            "smoothness": 100,
                            "extra_smooth": 0,
                            "smooth_range": 2,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [0, 0, 0, 0], "windows_reference_rgba": [75, 75, 75, 75]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [0, 0, 0, 0], "windows_reference_rgba": [106, 106, 106, 106]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [0, 0, 0, 0], "windows_reference_rgba": [75, 75, 75, 75]},
                        ],
                    },
                    {
                        "case_id": "case_0003",
                        "reason": (
                            "Color Key enabled without invert and Smoothness=0; Mac candidate keeps "
                            "nonzero pixels where Windows writes transparent black."
                        ),
                        "expected_params": {
                            "enable_color_key": 1,
                            "invert_color_key": 0,
                            "smoothness": 0,
                            "extra_smooth": 0,
                            "smooth_range": 2,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [106, 106, 106, 106], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                        ],
                    },
                    {
                        "case_id": "case_0010",
                        "reason": (
                            "Color Key + Extra Smooth/Gamma-range stress; Mac candidate keeps top-edge "
                            "pixels where Windows writes transparent black."
                        ),
                        "expected_params": {
                            "enable_color_key": 1,
                            "invert_color_key": 0,
                            "smoothness": 100,
                            "extra_smooth": 40,
                            "smooth_range": 22,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [106, 106, 106, 106], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                        ],
                    },
                ],
                "requested_for_each_case": {
                    "parameter_struct": {
                        "enable_color_key": None,
                        "color_key_rgba_or_packed": None,
                        "invert_color_key": None,
                        "smoothness": None,
                        "extra_smooth": None,
                        "smooth_range": None,
                        "smoother_version": None,
                        "gamma_correction": None,
                        "num_gamma_colors": None,
                        "observed_flags_and_offsets": {},
                    },
                    "setup_and_keying": {
                        "input_pixel_rgba_before_effect": [None, None, None, None],
                        "after_any_unpremultiply_rgba": [None, None, None, None],
                        "active_palette_filter_hit": None,
                        "active_palette_filter_value": None,
                        "scalar_key_filter_hit": None,
                        "scalar_key_filter_value": None,
                        "invert_branch_taken": None,
                        "class_plane_byte_before_smoothing": None,
                        "class_plane_neighbors": [],
                    },
                    "smoothing_and_writeback": {
                        "fun_18000c280_switch_idx_if_hit": None,
                        "append_count_if_hit": None,
                        "before_FUN_1800036e0_rgba_float_hex": [None, None, None, None],
                        "gamma_or_srgb_decode_encode_steps": [],
                        "premultiply_or_unpremultiply_step": None,
                        "final_writeback_operation": "floorf(value+0.5) | trunc | cvt | other",
                        "final_rgba_8bit": [None, None, None, None],
                    },
                },
            }
            summary = "Fill with OLMSmoother2 legacy key/gamma setup, mask, gamma, and writeback trace facts."
        elif request_id == "olmdistancegradation_field_prep_runtime_trace_20260619":
            observations = {
                "effect": "OLM Distance Gradation",
                "module_base": "0x...",
                "cases": [
                    {
                        "case_id": "case_0020",
                        "reason": "Constant + background + Inside; removing compose-time Constant binarization worsens mean 0.0561 -> 6.9951",
                        "params": {
                            "invert": 0,
                            "in_out": 1,
                            "inside_threshold": 78,
                            "outside_threshold": 204,
                            "render_mode": 1,
                            "use_background_color": 1,
                            "interpolation_mode": 1,
                            "blur_mode": 1,
                            "blur_size": 0,
                        },
                        "pixels": [
                            {
                                "x": 951,
                                "y": 417,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                            {
                                "x": 952,
                                "y": 417,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                        ],
                    },
                    {
                        "case_id": "case_0022",
                        "reason": "Constant + background + Both with small thresholds; broad residual but old binarization still much closer than pass-through",
                        "params": {
                            "invert": 0,
                            "in_out": 3,
                            "inside_threshold": 36,
                            "outside_threshold": 11,
                            "render_mode": 1,
                            "use_background_color": 1,
                            "interpolation_mode": 1,
                            "blur_mode": 1,
                            "blur_size": 0,
                        },
                        "pixels": [
                            {
                                "x": 4,
                                "y": 0,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                            {
                                "x": 28,
                                "y": 0,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                        ],
                    },
                    {
                        "case_id": "case_0029",
                        "reason": "Constant + Blur; current binary-field-before-blur is guarded but not exact",
                        "params": {
                            "invert": 1,
                            "in_out": 1,
                            "inside_threshold": 158,
                            "outside_threshold": 13,
                            "render_mode": 1,
                            "use_background_color": 0,
                            "interpolation_mode": 1,
                            "blur_mode": 2,
                            "blur_size": 30,
                        },
                        "pixels": [
                            {
                                "x": 524,
                                "y": 783,
                                "windows_reference_rgba": [15, 0, 126, 135],
                                "mac_cli_candidate_rgba": [17, 0, 147, 158],
                            },
                            {
                                "x": 525,
                                "y": 783,
                                "windows_reference_rgba": [15, 0, 129, 138],
                                "mac_cli_candidate_rgba": [18, 0, 150, 161],
                            },
                        ],
                    },
                ],
                "requested_for_each_pixel": {
                    "source_input_rgba_8bit": [None, None, None, None],
                    "distance_field_before_constant_rgba_or_mat_values": [None, None, None, None],
                    "distance_field_after_constant_rgba_or_mat_values": [None, None, None, None],
                    "distance_field_after_blur_if_any": [None, None, None, None],
                    "field_world_pointer_rowbytes_dimensions": {
                        "pointer": None,
                        "rowbytes": None,
                        "width": None,
                        "height": None,
                    },
                    "distance_transform_call": {
                        "input_mat_type_size_channels": None,
                        "dist_type": None,
                        "mask_size": None,
                        "dst_type": None,
                    },
                    "threshold_and_normalization": {
                        "ui_threshold": None,
                        "threshold_clamp_before_minmax": None,
                        "actual_min": None,
                        "actual_max": None,
                        "normalization_denominator": None,
                        "denominator_source": "ui-threshold|actual-max|other",
                    },
                    "gaussian_blur_call_if_case_0029": {
                        "input_mat_type_size_channels": None,
                        "output_mat_type_size_channels": None,
                        "ksize": [None, None],
                        "sigma_x": None,
                        "sigma_y": None,
                        "border_type": None,
                        "anchor": [None, None],
                        "radius_source": "blur-size|scaled|constant-doubled|other",
                    },
                    "fun_181170870_field_pixel_bytes": [None, None, None, None],
                    "fun_181170870_X_before_invert": None,
                    "fun_181170870_X_after_invert": None,
                    "fun_181170870_X_after_interp": None,
                    "fun_181170870_alpha_base": None,
                    "fun_181170870_output_rgba_before_byte_cast": [None, None, None, None],
                    "final_rgba_8bit": [None, None, None, None],
                },
            }
            summary = "Fill with OLMDistanceGradation field-prep/Constant-mode runtime trace facts."
        elif request_id == "olmdistancegradation_16bpc_case0026_x_witness_20260628":
            observations = {
                "effect": "OLM Distance Gradation",
                "case_id": "olmdistancegradation_extended__case_0026",
                "module_base": "0x...",
                "function_focus": {
                    "compose16_callback": "FUN_181170480",
                    "known_binary_facts": [
                        "field scale uses 1/32768 and 32768 constants",
                        "Render Mode=1 selects Gradation Color",
                        "Use Background Color=1 mixes BG*(1-X)+Grad*X",
                    ],
                },
                "params": {
                    "invert": 1,
                    "in_out": 3,
                    "inside_threshold": 158,
                    "outside_threshold": 13,
                    "render_mode": 1,
                    "use_background_color": 1,
                    "gradation_color_rgba16": [7195, 0, 61165, 65535],
                    "background_color_rgba16": [65535, 0, 0, 65535],
                    "interpolation_mode": 4,
                    "power": 2.59740734100342,
                    "blur_mode": 1,
                    "blur_size": 0,
                },
                "witness_pixels": [
                    {
                        "x": x,
                        "y": 0,
                        "windows_reference_rgba16": reference,
                        "mac_candidate_rgba16": [7195, 0, 61165, 65535],
                        "inferred_windows_x": inferred_x,
                    }
                    for x, reference, inferred_x in [
                        (0, [7195, 0, 61165, 65535], 1.0),
                        (1, [7195, 0, 61165, 65535], 1.0),
                        (2, [7195, 0, 61165, 65535], 1.0),
                        (3, [18147, 0, 49681, 65535], 0.812259),
                        (4, [27731, 0, 39633, 65535], 0.647982),
                        (5, [36021, 0, 30941, 65535], 0.505879),
                        (6, [43085, 0, 23533, 65535], 0.38478),
                        (7, [49003, 0, 17331, 65535], 0.283361),
                        (8, [53849, 0, 12249, 65535], 0.200285),
                        (9, [57703, 0, 8209, 65535], 0.134229),
                        (10, [60657, 0, 5111, 65535], 0.083587),
                        (11, [62803, 0, 2861, 65535], 0.046802),
                        (12, [64241, 0, 1355, 65535], 0.022167),
                        (13, [65083, 0, 471, 65535], 0.007724),
                        (14, [65459, 0, 77, 65535], 0.001281),
                    ]
                ],
                "requested_for_each_pixel": {
                    "source_input_rgba16": [None, None, None, None],
                    "field_world_pointer_rowbytes_dimensions": {
                        "pointer": None,
                        "rowbytes": None,
                        "width": None,
                        "height": None,
                    },
                    "field_pixel_raw_rgba16_or_mat_channels_before_compose": [None, None, None, None],
                    "fun_181170480_X_before_invert": None,
                    "fun_181170480_X_after_invert": None,
                    "fun_181170480_X_after_power_interp": None,
                    "fun_181170480_background_rgba_float_or_16": [None, None, None, None],
                    "fun_181170480_gradation_rgba_float_or_16": [None, None, None, None],
                    "output_rgba_float_before_cvt": [None, None, None, None],
                    "final_rgba16": [None, None, None, None],
                },
                "branch_decision": {
                    "field_already_ramps_before_compose": None,
                    "compose_interpolation_creates_ramp_from_saturated_field": None,
                    "parameter_or_color_branch_mismatch": None,
                    "failed_breakpoint_or_watchpoint_reason": None,
                },
            }
            summary = "Fill with OLMDistanceGradation 16bpc case_0026 field/X witness facts."
        elif request_id == "olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629":
            observations = {
                "effect": "OLM Distance Gradation",
                "module_base": "0x...",
                "function_focus": {
                    "compose16_callback": "FUN_181170480",
                    "known_binary_facts": [
                        "Render Mode=2 selects source-layer RGB path",
                        "Use Background Color=0 keeps alpha = d_alpha * X in the current port",
                        "Current Mac candidate matches Windows alpha at the witness but RGB stays lower",
                    ],
                },
                "cases": [
                    {
                        "case_id": "olmdistancegradation_extended__case_0012",
                        "reason": (
                            "Layer/no-bg source ownership residual: alpha matches at the max witness "
                            "while Windows RGB is roughly doubled."
                        ),
                        "params": {
                            "invert": 0,
                            "in_out": 3,
                            "inside_threshold": 122,
                            "outside_threshold": 204,
                            "render_mode": 2,
                            "use_background_color": 0,
                            "interpolation_mode": 2,
                            "power": 1,
                            "blur_mode": 1,
                            "blur_size": 0,
                        },
                        "pixels": [
                            {
                                "x": 462,
                                "y": 7,
                                "source_input_rgba16": [16255, 16255, 16255, 32639],
                                "windows_reference_rgba16": [32371, 32371, 32371, 64997],
                                "mac_candidate_rgba16": [16121, 16121, 16121, 64997],
                            },
                            {
                                "x": 72,
                                "y": 8,
                                "source_input_rgba16": [16255, 16255, 16255, 32639],
                                "windows_reference_rgba16": [32371, 32371, 32371, 64997],
                                "mac_candidate_rgba16": [16121, 16121, 16121, 64997],
                            },
                        ],
                    },
                    {
                        "case_id": "olmdistancegradation_extended__case_0016",
                        "reason": (
                            "Sanity companion for the same residual family under Invert=1 / Inside; "
                            "Windows alpha again matches while RGB is higher."
                        ),
                        "params": {
                            "invert": 1,
                            "in_out": 1,
                            "inside_threshold": 0,
                            "outside_threshold": 204,
                            "render_mode": 2,
                            "use_background_color": 0,
                            "interpolation_mode": 2,
                            "power": 1,
                            "blur_mode": 1,
                            "blur_size": 0,
                        },
                        "pixels": [
                            {
                                "x": 106,
                                "y": 19,
                                "source_input_rgba16": [29125, 29125, 29125, 43689],
                                "windows_reference_rgba16": [29125, 29125, 29125, 43689],
                                "mac_candidate_rgba16": [19415, 19415, 19415, 43689],
                            }
                        ],
                    },
                ],
                "requested_for_each_pixel": {
                    "source_input_rgba16": [None, None, None, None],
                    "field_world_pointer_rowbytes_dimensions": {
                        "pointer": None,
                        "rowbytes": None,
                        "width": None,
                        "height": None,
                    },
                    "field_pixel_raw_rgba16_or_mat_channels_before_compose": [None, None, None, None],
                    "fun_181170480_X_before_invert": None,
                    "fun_181170480_X_after_invert": None,
                    "fun_181170480_X_after_interp": None,
                    "fun_181170480_alpha_base": None,
                    "fun_181170480_source_rgba_float_or_16_before_any_unpremultiply": [None, None, None, None],
                    "fun_181170480_source_rgba_after_any_unpremultiply": [None, None, None, None],
                    "fun_181170480_output_rgba_float_before_cvt": [None, None, None, None],
                    "final_rgba16": [None, None, None, None],
                },
                "branch_decision": {
                    "uses_straight_source_times_output_alpha": None,
                    "uses_premultiplied_source_directly": None,
                    "uses_other_source_ownership_rule": None,
                    "failed_breakpoint_or_watchpoint_reason": None,
                },
            }
            summary = "Fill with OLMDistanceGradation 16bpc Layer/no-bg source ownership witness facts."
        elif request_id == "olmsmoother2_legacy_writeback_extract_20260620":
            observations = {
                "existing_full_log_path_checked": (
                    "C:\\Users\\optim\\Documents\\Codex\\2026-06-11\\files-mentioned-by-the-user-olm\\work\\"
                    "live_attempt_smoother2_legacy_20260620\\cdb_console.txt"
                ),
                "full_log_available": None,
                "source": "existing-full-log|rerun|failed",
                "writeback_hits": [
                    {
                        "hit_index": 1,
                        "marker": "HIT_FUN_1800036e0_writeback_candidate",
                        "register_dump": None,
                        "call_stack": None,
                        "stack_dump_dq_rsp_l16": None,
                        "nearby_lines": None,
                        "decoded_notes": {
                            "candidate_case_id": None,
                            "candidate_pixel_xy": [None, None],
                            "pre_writeback_rgba_float_or_hex": [None, None, None, None],
                            "gamma_or_srgb_branch": None,
                            "premultiply_branch": None,
                            "final_rgba_or_argb": [None, None, None, None],
                        },
                    },
                    {
                        "hit_index": 2,
                        "marker": "HIT_FUN_1800036e0_writeback_candidate",
                        "register_dump": None,
                        "call_stack": None,
                        "stack_dump_dq_rsp_l16": None,
                        "nearby_lines": None,
                        "decoded_notes": {
                            "candidate_case_id": None,
                            "candidate_pixel_xy": [None, None],
                            "pre_writeback_rgba_float_or_hex": [None, None, None, None],
                            "gamma_or_srgb_branch": None,
                            "premultiply_branch": None,
                            "final_rgba_or_argb": [None, None, None, None],
                        },
                    },
                ],
                "adjacent_candidate_context": {
                    "fun_180010550_hits_near_writeback": None,
                    "fun_18000c280_hits_near_writeback": None,
                },
                "failure_if_any": None,
            }
            summary = "Extract the actual OLMSmoother2 legacy writeback-hit register/stack values from the full CDB log."
        elif request_id == "olmsmoother2_legacy_u8_writer_trace_20260620":
            observations = {
                "target_addresses": {
                    "u8_writer": "OLMSmoother2+0x3370 / FUN_180003370",
                    "u8_writer_wrapper": "OLMSmoother2+0x3d00 / FUN_180003d00",
                    "known_wrong_float_writer": "OLMSmoother2+0x36e0 / FUN_1800036e0",
                },
                "ae_request_id": "ae_pixel_olmsmoother2_legacy_20260619",
                "cases_traced": [],
                "u8_writer_hits": [
                    {
                        "hit_index": None,
                        "case_id": None,
                        "register_dump": None,
                        "call_stack": None,
                        "stack_dump_dq_rsp_l24": None,
                        "decoded_loop": {
                            "x": None,
                            "y": None,
                            "width": None,
                            "height": None,
                        },
                        "fun_18000cce0_output_float_or_hex": {
                            "alpha": None,
                            "red": None,
                            "green": None,
                            "blue": None,
                        },
                        "gamma_or_srgb_branch": None,
                        "premultiply_branch": None,
                        "final_packed_8bpc_argb_or_rgba": [None, None, None, None],
                    }
                ],
                "wrapper_hits": [],
                "failure_if_any": None,
            }
            summary = "Fill with direct OLMSmoother2 +0x3370 8bpc writer runtime values."
        elif request_id == "olmsmoother2_legacy_u8_pixel_trace_20260620":
            observations = {
                "target": {
                    "case_id": "case_0001",
                    "x": 712,
                    "y": 406,
                    "expected_rgba": [207, 207, 207, 207],
                    "current_candidate_rgba": [106, 106, 106, 135],
                },
                "breakpoints": {
                    "after_fun_18000cce0": "OLMSmoother2+0x3510",
                    "pre_pack": "OLMSmoother2+0x35ad",
                    "pre_store": "OLMSmoother2+0x360e",
                    "coordinate_locals": {"x": "[RSP+0x34]", "y": "[RSP+0x38]"},
                },
                "after_fun_18000cce0": {
                    "hit": None,
                    "rsp_0x48_rgba_or_bgra_float_hex": [None, None, None, None],
                    "rbp_param8_flags": None,
                    "rbp_0x19_keep_premul_byte": None,
                    "rbx_param9_gamma_ctx": None,
                    "rbx_0x10_lut_ptr": None,
                    "register_dump": None,
                    "call_stack": None,
                },
                "pre_pack": {
                    "hit": None,
                    "xmm6": None,
                    "xmm7": None,
                    "xmm8": None,
                    "xmm1_alpha": None,
                    "register_dump": None,
                },
                "pre_store": {
                    "hit": None,
                    "eax_packed_dword": None,
                    "rsi_dest": None,
                    "dest_dword_before": None,
                    "packed_output_bytes": [None, None, None, None],
                    "register_dump": None,
                },
                "failure_if_any": None,
            }
            summary = "Fill with OLMSmoother2 case_0001 pixel (712,406) +0x3510/+0x360e writer values."
        elif request_id == "olmsmoother2_legacy_cce0_pixel_trace_20260621":
            observations = {
                "target": {
                    "case_id": "case_0001",
                    "x": 712,
                    "y": 406,
                    "expected_rgba": [207, 207, 207, 207],
                    "candidate_rgba": [106, 106, 106, 135],
                    "known_final_store_eax": "c8c8c887",
                    "known_final_store_argb": [135, 200, 200, 200],
                },
                "fun_18000cce0_entry": {
                    "hit": None,
                    "rcx_output_float_ptr": None,
                    "rdx_polygon_or_input_ptr": None,
                    "r8_plane_or_output_ptr": None,
                    "r9_xy_ptr": None,
                    "xy": [None, None],
                    "rdx_dump": None,
                    "r8_dump": None,
                    "param8_dump": None,
                    "param9_dump": None,
                    "register_dump": None,
                    "call_stack": None,
                },
                "u8_writer_after_cce0": {
                    "hit": None,
                    "rsp_0x48_to_0x54_float_hex": [None, None, None, None],
                    "interpreted_output_rgba_or_argb_float": [None, None, None, None],
                    "rbp_param8_flags": None,
                    "rbp_0x19_keep_premul_byte": None,
                    "rbx_0x10_lut_ptr": None,
                    "register_dump": None,
                },
                "failure_if_any": None,
            }
            summary = "Fill with target-pixel FUN_18000cce0 input and +0x3510 output floats."
        elif request_id in {
            "olmsmoother2_legacy_cce0_internals_trace_20260621",
            "olmsmoother2_legacy_cce0_internals_r9_callsite_trace_20260621",
            "olmsmoother2_legacy_cce0_internals_targetaddr_trace_20260621",
            "olmsmoother2_legacy_cce0_internals_multiaddr_probe_trace_20260621",
            "olmsmoother2_legacy_cce0_internals_t3_rsi_callsite_trace_20260621",
            "olmsmoother2_legacy_cce0_internals_replay_from_writer_trace_20260621",
        }:
            observations = {
                "target": {
                    "case_id": "case_0001",
                    "x": 712,
                    "y": 406,
                    "expected_rgba": [207, 207, 207, 207],
                    "candidate_rgba": [106, 106, 106, 135],
                    "known_cce0_output_float": [0.57797289, 0.57797289, 0.57797289, 0.52794117],
                    "known_writer_store_eax": "c8c8c887",
                },
                "trace_anchor": {
                    "primary_breakpoint": "OLMSmoother2+0x3610",
                    "primary_condition": "target output write/watchpoint for pixel (712,406), then reconstruct/replay cce0 args from the writer frame",
                    "why": (
                        "The multi-address probe proved $t3 receives the target final write "
                        "at +0x3610, while +0x34b0 and +0x350b pre-call anchors did not "
                        "catch the target in retained runs. Therefore this request starts "
                        "from the reliable writer frame and asks for replay/reconstruction."
                    ),
                },
                "previous_failed_partials": [
                    {
                        "request_id": "olmsmoother2_legacy_cce0_internals_trace_20260621",
                        "status": "failed_partial",
                        "useful_facts": [
                            "+0xcd5f reachable",
                            "RSI points to x/y dwords at +0xcd5f",
                            "read [RBP+0x90] at +0xcd5f because MOV R14,[RBP+0x90] has not executed yet",
                        ],
                    },
                    {
                        "request_id": "olmsmoother2_legacy_cce0_internals_r9_callsite_trace_20260621",
                        "status": "failed_partial",
                        "useful_facts": [
                            "+0x350b @r9 coordinate breakpoint was installed but did not hit",
                            "previous datwatch still proves target final write and stack xy after cce0",
                        ],
                    },
                    {
                        "request_id": "olmsmoother2_legacy_cce0_internals_targetaddr_trace_20260621",
                        "status": "failed_partial",
                        "useful_facts": [
                            "+0x3370 writer-entry target addresses were computed",
                            "+0x34b0 @rsi == @$t3 did not hit",
                        ],
                    },
                    {
                        "request_id": "olmsmoother2_legacy_cce0_internals_multiaddr_probe_trace_20260621",
                        "status": "failed_partial",
                        "useful_facts": [
                            "$t3 receives the target pixel write at OLMSmoother2+0x3610",
                            "candidate loop condition at +0x34b0 did not hit for $t1/$t2/$t3",
                            "latest $t3 was 00000272`2244a020",
                        ],
                    },
                    {
                        "request_id": "olmsmoother2_legacy_cce0_internals_t3_rsi_callsite_trace_20260621",
                        "status": "failed_partial",
                        "useful_facts": [
                            "+0x350b @rsi == @$t3 did not produce a pre-call hit",
                            "+0x350b @rdi==0x2c8 && @r14==0x196 also did not hit",
                            "the reliable target anchor remains the later +0x3610 writer/data-watch stop",
                        ],
                    },
                ],
                "writer_entry_target_address": {
                    "entry": "OLMSmoother2+0x3370",
                    "loop_target": "OLMSmoother2+0x3610",
                    "known_successful_final_write": "OLMSmoother2+0x3610",
                    "candidate_addr_registers": ["$t3"],
                    "hit_condition": "data watchpoint or exact writeback hit for target output address",
                    "latest_candidate_addresses": {
                        "$t1": "00000272`23535c20",
                        "$t2": "00000272`24c0a020",
                        "$t3": "00000272`2244a020",
                    },
                    "candidate_loop_hit": False,
                    "candidate_write_watch_hit": "HIT_T3_WRITE_WATCH",
                    "selected_output_world": "$t3",
                },
                "fun_18000cce0_entry": {
                    "hit": None,
                    "replay_from_writer_frame": None,
                    "rcx_output_float_ptr": None,
                    "rdx_source_descriptor": None,
                    "r8_work_descriptor": None,
                    "r9_xy_ptr": None,
                    "param5_context_ptr": None,
                    "param6_context": None,
                },
                "after_fun_18000c280": {
                    "hit": None,
                    "address": "OLMSmoother2+0xcd5f",
                    "polygon_count_local_58_or_r14": None,
                    "local_148_vertex_records": [],
                    "class_plane_or_switch_index_evidence": None,
                    "source_descriptor_local_168": None,
                    "work_descriptor_local_188": None,
                },
                "stage_values": {
                    "before_fun_18000bb10": None,
                    "after_fun_18000bb10": None,
                    "after_fun_18000c0d0": None,
                    "after_fun_18000ab00": None,
                    "after_fun_18000b120": None,
                    "final_before_store_to_param1": None,
                },
                "interpretation": {
                    "alpha_drop_source": None,
                    "rgb_source": None,
                    "candidate_fix": None,
                },
                "failure_if_any": None,
            }
            summary = "Fill with target-pixel FUN_18000cce0 polygon/stage internals."
        elif request_id == "olmsmoother2_legacy_current_aex_residuals_trace_20260621":
            observations = {
                "effect": "OLM Smoother v2",
                "reference_request_id": "smoother2_legacy_full_current_aex_recapture_20260621",
                "render_set": "software",
                "cases": [
                    {
                        "case_id": "legacy_case_0002_current_aex",
                        "why": "AE-saved before-frame CLI exact control for key-mask/input semantics.",
                        "witness_pixels": [
                            {
                                "x": 500,
                                "y": 877,
                                "note": "Exact-control probe point; if this pixel does not hit the interesting path, choose a nearby nonzero source pixel and report the substitute.",
                            }
                        ],
                    },
                    {
                        "case_id": "legacy_case_0004_current_aex",
                        "why": "Localized current-AEX residual after AE-saved before-frame input.",
                        "witness_pixels": [
                            {
                                "x": 501,
                                "y": 1055,
                                "windows_rgba": [159, 95, 95, 255],
                                "mac_cli_rgba": [65, 65, 65, 255],
                                "diff_rgba": [94, 30, 30, 0],
                            }
                        ],
                    },
                    {
                        "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
                        "why": "Gamma/current-AEX residual after AE-saved before-frame input.",
                        "witness_pixels": [
                            {
                                "x": 500,
                                "y": 877,
                                "windows_rgba": [9, 9, 9, 255],
                                "mac_cli_rgba": [176, 112, 112, 255],
                                "diff_rgba": [167, 103, 103, 0],
                            }
                        ],
                    },
                ],
                "requested_for_each_witness": {
                    "ae_input_pixel_rgba": [None, None, None, None],
                    "after_unpremultiply_rgba_float_hex": [None, None, None, None],
                    "key_filter": {
                        "active_palette_filter_hit": None,
                        "scalar_key_filter_hit": None,
                        "invert_branch_taken": None,
                        "key_match_or_distance": None,
                        "alpha_after_key": None,
                    },
                    "class_plane": {
                        "center_byte": None,
                        "neighbor_bytes": [],
                        "fun_18000c280_switch_idx_if_hit": None,
                    },
                    "composite": {
                        "fun_18000cce0_hit": None,
                        "fun_18000cce0_output_float_hex": [None, None, None, None],
                    },
                    "gamma_and_writeback": {
                        "gamma_mode_or_srgb_branch": None,
                        "pre_write_float_hex": [None, None, None, None],
                        "final_u8_rgba": [None, None, None, None],
                    },
                },
                "failure_if_any": None,
            }
            summary = "Fill with current-AEX OLMSmoother2 residual input/key/gamma/writeback trace facts."
        elif request_id in {
            "olmsmoother2_legacy_current_aex_polygon_trace_20260621",
            "olmsmoother2_legacy_current_aex_polygon_backtrack_trace_20260621",
            "olmsmoother2_legacy_current_aex_polygon_stepover_trace_20260621",
        }:
            observations = {
                "effect": "OLM Smoother v2",
                "reference_request_id": "smoother2_legacy_full_current_aex_recapture_20260621",
                "render_set": "software",
                "prior_writer_trace": {
                    "status": "answered_partial",
                    "conclusion": "input and final writer are captured; residual is upstream of 8bpc writer/PNG export",
                },
                "cases": [
                    {
                        "case_id": "legacy_case_0004_current_aex",
                        "witness": {
                            "x": 501,
                            "y": 1055,
                            "windows_final_rgba": [159, 95, 95, 255],
                            "windows_result_float_rgba_like": [0.34566423, 0.11387402, 0.11387402, 1.0],
                            "mac_final_rgba": [65, 65, 65, 255],
                            "mac_trace": {
                                "switch_idx": 192,
                                "polygon_count": 1,
                                "samples": [
                                    {
                                        "src_xy": [501, 1054],
                                        "rgba": [0.55834043, 0.55834043, 0.55834043, 1.0],
                                        "weight": 0.0875,
                                    }
                                ],
                                "after_b120": [0.05220960, 0.05220960, 0.05220960, 1.0],
                            },
                        },
                    },
                    {
                        "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
                        "witness": {
                            "x": 500,
                            "y": 877,
                            "windows_final_rgba": [9, 9, 9, 255],
                            "windows_result_float_rgba_like": [0.002731743, 0.002731743, 0.002731743, 1.0],
                            "mac_final_rgba": [176, 112, 112, 255],
                            "mac_trace": {
                                "switch_idx": 22,
                                "polygon_count": 3,
                                "samples": [
                                    {"src_xy": [499, 877], "rgba": [0.87136710, 0.0, 0.0, 1.0], "weight": 0.2},
                                    {"src_xy": [499, 878], "rgba": [0.97344530, 0.00151745, 0.00151745, 1.0], "weight": 0.1},
                                    {"src_xy": [500, 878], "rgba": [0.79910272, 0.79910272, 0.79910272, 1.0], "weight": 0.2},
                                ],
                                "after_b120": [0.43280423, 0.16133800, 0.16133800, 1.0],
                            },
                        },
                    },
                ],
                "requested_for_each_case": {
                    "class_plane_window": {
                        "center_xy": [None, None],
                        "window_radius": 2,
                        "bytes_per_pixel_order": "expected [left, top, top-left, top-right]; correct if wrong",
                        "values": [],
                    },
                    "c280_switch": {
                        "switch_index": None,
                        "raw_corner_bytes_or_bits": None,
                        "helper_offsets_called": [],
                    },
                    "polygon": {
                        "count": None,
                        "vertices": [
                            {
                                "src_xy": [None, None],
                                "rgba_float_hex": [None, None, None, None],
                                "rgba_float": [None, None, None, None],
                                "weight_float_hex": None,
                                "weight_float": None,
                                "append_helper_offset": None,
                            }
                        ],
                    },
                    "final_stage_check": {
                        "after_c280_before_bb10_float_rgba": [None, None, None, None],
                        "after_ab00_float_rgba": [None, None, None, None],
                        "after_b120_float_rgba": [None, None, None, None],
                    },
                    "failure_if_any": None,
                },
            }
            if request_id == "olmsmoother2_legacy_current_aex_polygon_stepover_trace_20260621":
                observations["requested_for_case_0004_stepover"] = {
                    "case_id": "legacy_case_0004_current_aex",
                    "target_xy": [501, 1055],
                    "known_hit": {
                        "breakpoint": "OLMSmoother2+0x350b",
                        "rsp_xy": ["0x1f5", "0x41f"],
                        "pre_call_rcx_result_buffer_float_hex": [
                            "0x3f483078",
                            "0x3ace85ef",
                            "0x3ace85ef",
                            "0x3f800000",
                        ],
                        "pre_call_rcx_result_buffer_float": [
                            0.78198957,
                            0.0015756468,
                            0.0015756468,
                            1.0,
                        ],
                    },
                    "required": {
                        "post_cce0_rsp_0x48_float_hex": [None, None, None, None],
                        "post_cce0_rsp_0x48_float": [None, None, None, None],
                        "c280_switch_index_if_reached": None,
                        "polygon_count_if_reached": None,
                        "append_records_if_reached": [],
                        "debugger_reason_if_stepover_failed": None,
                    },
                }
                summary = "Fill with 0004 +0x350b step-over/post-cce0 and c280/polygon facts."
            else:
                summary = "Fill with current-AEX OLMSmoother2 class-plane/switch/polygon facts for 0004 and 0012."
        elif request_id == "olmsmoother2_current_aex_f270_witness_trace_20260621":
            observations = {
                "effect": "OLM Smoother v2",
                "reference_request_id": "smoother2_legacy_full_current_aex_recapture_20260621",
                "render_set": "software",
                "primary_case": {
                    "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
                    "pixel": {"x": 91, "y": 841},
                    "windows_reference_rgba": [0, 0, 0, 0],
                    "mac_cli_rgba": [90, 90, 90, 91],
                    "neighborhood_context": {
                        "shape": "local-adds-semitransparent-output-where-windows-stays-transparent",
                        "strong_neighbor_deltas": [
                            {"xy": [91, 840], "windows_rgba": [172, 172, 172, 180], "mac_rgba": [203, 203, 203, 204]},
                            {"xy": [92, 841], "windows_rgba": [233, 233, 233, 237], "mac_rgba": [249, 249, 249, 252]},
                            {"xy": [91, 842], "windows_rgba": [0, 0, 0, 0], "mac_rgba": [20, 20, 20, 20]},
                        ],
                    },
                    "mac_current_path": {
                        "c280_idx": 105,
                        "cardinal6_desc": [91, 841, 1, 91, 843, 5],
                        "cardinal6_key": 50,
                        "e170_bits": {
                            "a_x_y_minus_1": 1,
                            "r_x_minus_1_y": 0,
                            "a_x_y": 0,
                        },
                        "e170_code": 2,
                        "f270_emits": True,
                        "e3a0_weight": 0.35632184,
                        "append_src": [91, 840],
                    },
                    "requested_windows_values": {
                        "c280_idx": None,
                        "cardinal6_desc": [None, None, None, None, None, None],
                        "cardinal6_key": None,
                        "e170_bits": {
                            "a_x_y_minus_1": None,
                            "r_x_minus_1_y": None,
                            "a_x_y": None,
                        },
                        "e170_code": None,
                        "f270_hit": None,
                        "f270_emits": None,
                        "e3a0_args": {
                            "scale_m": None,
                            "scale_h": None,
                            "trap_width": None,
                            "trap_pos": None,
                            "trap_edge": None,
                            "weight": None,
                        },
                        "append": {
                            "hit": None,
                            "src_xy": [None, None],
                            "src_rgba_float": [None, None, None, None],
                            "weight": None,
                            "count_before": None,
                            "count_after": None,
                        },
                        "cce0": {
                            "hit": None,
                            "center_rgba_float": [None, None, None, None],
                            "polygon_count": None,
                            "output_rgba_float": [None, None, None, None],
                        },
                        "writer_u8_rgba": [None, None, None, None],
                        "classification": None,
                    },
                },
                "secondary_case": {
                    "case_id": "legacy_case_0004_current_aex",
                    "pixel": {"x": 1903, "y": 519},
                    "windows_reference_rgba": [103, 103, 103, 113],
                    "mac_cli_rgba": [0, 0, 0, 0],
                    "neighborhood_context": {
                        "shape": "windows-adds-semitransparent-output-where-local-passthrough-is-transparent",
                        "strong_neighbor_deltas": [
                            {"xy": [1903, 518], "windows_rgba": [161, 161, 161, 178], "mac_rgba": [191, 191, 191, 215]},
                            {"xy": [1904, 518], "windows_rgba": [221, 221, 221, 233], "mac_rgba": [212, 212, 212, 230]},
                            {"xy": [1901, 519], "windows_rgba": [10, 10, 10, 33], "mac_rgba": [14, 14, 14, 46]},
                            {"xy": [1901, 520], "windows_rgba": [9, 9, 9, 32], "mac_rgba": [13, 13, 13, 45]},
                        ],
                    },
                    "requested_windows_values": {
                        "c280_idx": None,
                        "polygon_count": None,
                        "append_events": [],
                        "cce0_output_rgba_float": [None, None, None, None],
                        "writer_u8_rgba": [None, None, None, None],
                        "classification": None,
                    },
                },
                "classification": None,
                "failure_if_any": None,
            }
            summary = "Fill with current-AEX f270/e170/e3a0 witness facts."
        else:
            observations = {
                "effect": action.get("plugin_area"),
                "module_base": "0x...",
                "ae_context": {
                    "ae_version": None,
                    "project_renderer_name": None,
                    "project_renderer_raw": None,
                    "bit_depth": None,
                    "color_management": None,
                },
                "cases": [
                    {
                        "case_id": None,
                        "parameters_ui": {},
                        "parameters_decoded_in_aex": {},
                        "witness_pixels": [
                            {
                                "x": None,
                                "y": None,
                                "input_rgba": [None, None, None, None],
                                "branch_or_dispatch": None,
                                "loop_bounds_or_sample_count": None,
                                "sample_order": [],
                                "intermediate_values": {},
                                "pre_writeback_rgba_float_hex": [None, None, None, None],
                                "writeback_operation": None,
                                "final_rgba": [None, None, None, None],
                            }
                        ],
                    }
                ],
                "directly_observed_vs_inferred": {
                    "directly_observed": [],
                    "static_or_decomp_inferred": [],
                    "not_isolated": [],
                },
            }
            summary = "Fill with dense input-to-output runtime trace facts for this plugin area."
        result_templates.append(
            {
                "request_id": request_id,
                "status": "answered",
                "summary": summary,
                "observations": observations,
            }
        )
    return {
        "kind": "olm_runtime_trace_result",
        "schema": 1,
        "results": result_templates,
    }


def checked_files(root: Path, profile: str) -> list[Path]:
    if profile in {
        "kirakira-stage-values-deep",
        "kirakira-forward-warp-box-input",
        "kirakira-boxfilter-pass1-microprobe",
        "kirakira-aggregation-compose-bt709",
    }:
        ensure_kirakira_deep_witness_plan(root)

    if profile in {"dense-all", "dense-live-followup"}:
        files = [
            TRACE_NOTE,
            Path("notes/WINDOWS_DENSE_TRACE_STRATEGY.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/IR_OLMColorKey_Edge.md"),
            Path("notes/IR_OLMDistanceGradation.md"),
            Path("notes/IR_OLMBlur.md"),
            Path("notes/IR_OLMKiraKira.md"),
            Path("notes/IR_OLMRadialBlur.md"),
            Path("notes/IR_OLMDirectionalBlur.md"),
            Path("notes/IR_OLMToonDilate.md"),
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/OLMColorKey_ASM_FACTS.md"),
            Path("notes/OLMKiraKira_ASM_FACTS.md"),
            Path("notes/OLMRadialBlur_ASM_FACTS.md"),
            Path("notes/OLMDirectionalBlur_ASM_FACTS.md"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
        ]
    elif profile == "colorkey-edge":
        files = [
            TRACE_NOTE,
            *COLORKEY_SUPPORTING_NOTES,
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0005_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0006_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0008_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0009_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/diff.json"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/diff.csv"),
        ]
    elif profile == "colorkey-16bpc-case0009":
        files = [
            TRACE_NOTE,
            *COLORKEY_SUPPORTING_NOTES,
            *COLORKEY_16BPC_CASE0009_SUPPORTING_FILES,
        ]
    elif profile == "olmblur-repeat-threshold":
        files = [
            TRACE_NOTE,
            *OLMBLUR_SUPPORTING_NOTES,
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/case_0006_trace.log"),
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/case_0007_trace.log"),
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/diff.json"),
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/diff.csv"),
        ]
    elif profile == "kirakira-stage-values":
        files = [
            TRACE_NOTE,
            *KIRAKIRA_STAGE_SUPPORTING_NOTES,
            Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
            Path("refs/reference_requests/kirakira_strength0_brightness_20260614.json"),
        ]
    elif profile == "kirakira-stage-values-deep":
        files = [
            TRACE_NOTE,
            *KIRAKIRA_STAGE_SUPPORTING_NOTES,
            Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
            Path("refs/reference_requests/kirakira_strength0_brightness_20260614.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md"),
        ]
    elif profile == "kirakira-forward-warp-box-input":
        files = [
            TRACE_NOTE,
            *KIRAKIRA_STAGE_SUPPORTING_NOTES,
            Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md"),
            Path("refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json"),
            Path("refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.json"),
            Path("refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.md"),
            Path(
                "refs/reports/kirakira_deep_stage_values_20260621/"
                "runtime_trace_comparisons/olmkirakira_deep_stage_values.md"
            ),
            Path(
                "refs/reports/kirakira_deep_stage_values_20260621/"
                "runtime_trace_comparisons/olmkirakira_deep_stage_values.json"
            ),
        ]
    elif profile == "kirakira-boxfilter-pass1-microprobe":
        files = [
            TRACE_NOTE,
            *KIRAKIRA_STAGE_SUPPORTING_NOTES,
            Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md"),
            Path("refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json"),
            Path("refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.json"),
            Path("refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.md"),
            Path(
                "refs/reports/kirakira_deep_stage_values_20260621/"
                "runtime_trace_comparisons/olmkirakira_deep_stage_values.md"
            ),
            Path("refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.md"),
            Path("refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.json"),
        ]
    elif profile == "kirakira-aggregation-compose-bt709":
        files = [
            TRACE_NOTE,
            *KIRAKIRA_STAGE_SUPPORTING_NOTES,
            Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json"),
            Path("refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/README.md"),
            Path("refs/reports/olmkirakira_remeasure_20260624_bt709_software/reports/diff.json"),
            Path("refs/reports/olmkirakira_remeasure_20260624_bt709_software/reports/diff.csv"),
            Path(
                "refs/reports/runtime_trace_comparisons/"
                "olmkirakira_deep_stage_values_20260624_bt709.md"
            ),
            Path(
                "refs/reports/runtime_trace_comparisons/"
                "olmkirakira_deep_stage_values_20260624_bt709.json"
            ),
            Path(
                "refs/reports/runtime_trace_comparisons/"
                "olmkirakira_boxfilter_pass1_microprobe_20260624.md"
            ),
            Path(
                "refs/reports/runtime_trace_comparisons/"
                "olmkirakira_boxfilter_pass1_microprobe_20260624.json"
            ),
        ]
    elif profile == "radialblur-residual-witness":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMRadialBlur.md"),
            Path("notes/OLMRadialBlur_ASM_FACTS.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/olmradialblur_residual_clusters_20260622_011750/residual_clusters.md"),
            Path("refs/reports/olmradialblur_residual_clusters_20260622_011750/residual_clusters.json"),
        ]
    elif profile == "radialblur-inner-cell-witness":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMRadialBlur.md"),
            Path("notes/OLMRadialBlur_ASM_FACTS.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/conformance/olmradialblur_8bpc_decision.json"),
            Path("refs/conformance/olmradialblur_8bpc_decision.md"),
            Path("refs/reference_requests/radialblur_inner_20260605.json"),
            Path("refs/reports/olmradialblur_inner_witness_plan_20260625/witness_plan.json"),
            Path("refs/reports/olmradialblur_inner_witness_plan_20260625/witness_plan.md"),
            Path("refs/reports/olmradialblur_inner_candidate_matrix_20260622_002848/summary.json"),
            Path("refs/reports/olmradialblur_inner_candidate_matrix_20260622_002848/candidate_matrix.csv"),
        ]
    elif profile == "directionalblur-residual-witness":
        files = [
            TRACE_NOTE,
            *DIRECTIONALBLUR_SUPPORTING_NOTES,
        ]
    elif profile == "smoother2-no-key-grid":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/OLMSmoother2_FORECAST_AUDIT_20260619.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_211_139.log"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_215_145.log"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_991_139.log"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_995_145.log"),
        ]
    elif profile == "smoother2-legacy-key-gamma":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.csv"
            ),
        ]
    elif profile == "smoother2-legacy-current-aex-residuals":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reference_requests/smoother2_legacy_full_current_aex_recapture_20260621.json"),
            Path(
                "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
                "OLMSmootherv2/reference_manifest.json"
            ),
            Path(
                "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
                "OLMSmootherv2/WINDOWS_RECAPTURE_SUMMARY.md"
            ),
        ]
    elif profile == "smoother2-legacy-current-aex-polygon":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reference_requests/smoother2_legacy_full_current_aex_recapture_20260621.json"),
            Path(
                "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
                "OLMSmootherv2/reference_manifest.json"
            ),
            Path(
                "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
                "OLMSmootherv2/WINDOWS_RECAPTURE_SUMMARY.md"
            ),
        ]
    elif profile == "smoother2-legacy-writeback-extract":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/dense_live_followup_20260620/runtime_trace_summary_dense_live_followup_20260620_213031.md"),
            Path("refs/reports/dense_live_followup_20260620/runtime_trace_summary_dense_live_followup_20260620_213031.json"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
        ]
    elif profile == "smoother2-legacy-u8-writer-trace":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/smoother2_legacy_writeback_extract_20260620/runtime_trace_summary_smoother2_legacy_writeback_extract_20260620_231855.md"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
        ]
    elif profile == "smoother2-legacy-u8-pixel-trace":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/smoother2_legacy_u8_writer_trace_20260620/runtime_trace_summary_smoother2_legacy_u8_writer_trace_20260620_233427.md"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
        ]
    elif profile == "smoother2-legacy-cce0-pixel-trace":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/smoother2_legacy_u8_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_u8_pixel_trace_20260621_0040.md"),
            Path("refs/reports/smoother2_legacy_u8_pixel_trace_20260621/cdb_console_final_entrycmd_utf16.txt"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
        ]
    elif profile == "smoother2-legacy-cce0-internals-trace":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_cce0_pixel_trace_20260621_0145.md"),
            Path("refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/runtime_trace_summary_smoother2_legacy_cce0_pixel_trace_20260621_0145.json"),
            Path("refs/reports/smoother2_legacy_cce0_pixel_trace_20260621/cdb_console_final_datwatch_utf16.txt"),
            Path("refs/reports/runtime_trace_summary.md"),
            Path(
                "refs/returns/windows/20260621_011845_smoother2_cce0_internals/"
                "olm_runtime_trace_smoother2_legacy_cce0_internals_trace_20260621_011845_return_windows.zip"
            ),
            Path(
                "refs/returns/windows/20260621_022708_smoother2_cce0_internals_r9_callsite/"
                "olm_runtime_trace_smoother2_legacy_cce0_internals_r9_callsite_20260621_022708_return_windows.zip"
            ),
            Path(
                "refs/returns/windows/20260621_025613_smoother2_cce0_internals_targetaddr/"
                "olm_runtime_trace_smoother2_legacy_cce0_internals_targetaddr_20260621_025613_return_windows.zip"
            ),
            Path(
                "refs/returns/windows/20260621_031230_smoother2_cce0_internals_multiaddr_probe/"
                "olm_runtime_trace_smoother2_legacy_cce0_internals_multiaddr_probe_20260621_031230_return_windows.zip"
            ),
            Path(
                "refs/returns/windows/20260621_032645_smoother2_cce0_internals_t3_rsi_callsite/"
                "olm_runtime_trace_smoother2_legacy_cce0_internals_t3_rsi_callsite_20260621_032645_return_windows.zip"
            ),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
        ]
    elif profile == "smoother2-current-aex-f270-witness":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.md"),
            Path("refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.json"),
            Path("refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.md"),
            Path("refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.json"),
            Path("refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.md"),
            Path("refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.json"),
            Path("refs/reference_requests/smoother2_legacy_full_current_aex_recapture_20260621.json"),
            Path(
                "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
                "OLMSmootherv2/reference_manifest.json"
            ),
        ]
    elif profile == "smoother2-current-aex-writer-frame-followup":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/conformance/olmsmoother2_current_aex_8bpc_decision.md"),
            Path("refs/conformance/olmsmoother2_current_aex_8bpc_decision.json"),
            Path("refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.md"),
            Path("refs/reports/olmsmoother2_current_aex_proof_plan_20260625/proof_plan.json"),
            Path("refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.md"),
            Path("refs/reports/olmsmoother2_witness_neighborhood_20260624/neighborhood.json"),
            Path("refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.md"),
            Path("refs/reports/olmsmoother2_current_aex_witness_contract_20260624/witness_contract.json"),
            Path("refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.md"),
            Path("refs/reports/olmsmoother2_current_aex_decision_matrix_20260624/decision_matrix.json"),
            Path("refs/reference_requests/smoother2_legacy_full_current_aex_recapture_20260621.json"),
            Path(
                "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
                "OLMSmootherv2/reference_manifest.json"
            ),
        ]
    elif profile == "distancegradation-field-prep":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMDistanceGradation.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("notes/PORTING_BOARD.md"),
        ]
    elif profile == "distancegradation-layer-no-bg-source-ownership":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMDistanceGradation.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/conformance/olmdistancegradation_16bpc_representative_witnesses_20260629.md"),
            Path("refs/conformance/olmdistancegradation_16bpc_representative_witnesses_20260629.json"),
            Path("refs/conformance/olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.md"),
            Path("refs/conformance/olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.json"),
            Path(
                "handoff/ae_pixel_validation_20260618/requests/"
                "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/reference_manifest.json"
            ),
        ]
    elif profile == "distancegradation-16bpc-case0026-x-witness":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMDistanceGradation.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/conformance/olmdistancegradation_16bpc_case0026_analysis_20260628.md"),
            Path("refs/conformance/olmdistancegradation_16bpc_case0026_analysis_20260628.json"),
            Path(
                "refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/"
                "bitdepth16_olmdistancegradation_extended_exact/reports/ae_pixel_16bpc_extended_exact.json"
            ),
            Path(
                "handoff/ae_pixel_validation_20260618/requests/"
                "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/reference_manifest.json"
            ),
        ]
    else:
        files = [TRACE_NOTE, *DEFAULT_REQUESTS, *SUPPORTING_NOTES]
    missing = [path for path in files if not (root / path).exists()]
    if missing:
        raise FileNotFoundError("missing package input(s): " + ", ".join(str(path) for path in missing))
    return files


def main() -> int:
    args = parse_args()
    root = repo_root()
    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = root / "refs" / "runtime_trace_packages" / f"olm_runtime_trace_requests_{stamp}.zip"
    elif not output.is_absolute():
        output = root / output

    try:
        files = checked_files(root, args.profile)
        snapshot = next_actions_snapshot(root)
        manifest = package_manifest(root, snapshot, args.profile)
        if not manifest["runtime_actions"]:
            return fail("next_reference_actions.py produced no runtime trace actions")

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README_RUNTIME_TRACE.md", build_readme(manifest))
            archive.writestr(
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                json.dumps(build_return_template(manifest), indent=2, sort_keys=True),
            )
            archive.writestr("runtime_trace_package_manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            archive.writestr("next_reference_actions_snapshot.json", json.dumps(snapshot, indent=2, sort_keys=True))
            for path in files:
                archive.write(root / path, path.as_posix())
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))

    print(f"[OK] runtime trace package: {output}")
    for action in manifest["runtime_actions"]:
        print(f"- {action['request_id']}: {action['plugin_area']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
