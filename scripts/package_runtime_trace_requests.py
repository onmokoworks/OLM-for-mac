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
OLMBLUR_SUPPORTING_NOTES = [
    Path("notes/IR_OLMBlur.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("notes/AE_HOST_VALIDATION_20260618.md"),
    Path("notes/PORTING_BOARD.md"),
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
            "olmblur-repeat-threshold",
            "kirakira-stage-values",
            "kirakira-stage-values-deep",
            "smoother2-no-key-grid",
            "smoother2-legacy-key-gamma",
            "smoother2-legacy-writeback-extract",
            "smoother2-legacy-u8-writer-trace",
            "smoother2-legacy-u8-pixel-trace",
            "smoother2-legacy-cce0-pixel-trace",
            "smoother2-legacy-cce0-internals-trace",
            "distancegradation-field-prep",
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
    if profile == "olmblur-repeat-threshold":
        return [olmblur_repeat_threshold_action()]
    if profile == "kirakira-stage-values":
        return [kirakira_stage_values_action()]
    if profile == "kirakira-stage-values-deep":
        return [kirakira_deep_stage_values_action()]
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
    if profile == "distancegradation-field-prep":
        return [distancegradation_field_prep_action()]
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
    if profile == "kirakira-stage-values-deep":
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
    elif profile == "distancegradation-field-prep":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMDistanceGradation.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("notes/PORTING_BOARD.md"),
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
