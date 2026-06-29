#!/usr/bin/env python3
"""Print the next parent actions for Windows reference request coverage."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any

from check_reference_request_status import load_status_rows


PRIORITY = [
    "radialblur_inner_size_variation_20260606",
    "radialblur_inner_20260605",
    "kirakira_single_ray_20260606",
    "directionalblur_context_scale_20260606",
    "olmcolorkey_replace_colorspace_20260606",
    "smoother2_no_key_grid_20260606",
]

RUNTIME_FOLLOW_UPS = [
    {
        "request_id": "radialblur_inner_runtime_trace_20260618",
        "requires_covered": [
            "radialblur_inner_20260605",
            "radialblur_inner_size_variation_20260606",
        ],
        "effect": "OLM RadialBlur",
        "plugin_area": "OLMRadialBlur Inner runtime trace",
        "mode": "external-trace",
        "read_files": [
            "notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md",
            "notes/OLMRadialBlur_ASM_FACTS.md",
            "notes/OLMRadialBlur_RE.md",
            "refs/reference_requests/radialblur_inner_20260605.json",
        ],
        "write_scope": "none",
        "reason": "Inner and Size Variation references are already covered; the remaining span-minus-one ambiguity needs a Windows debugger/register trace, not more PNG tuning.",
        "command": "Open notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md and trace OLMRadialBlur.aex+0x26e5 / +0x1c90 for rb_inner_only_strength_small.",
        "agent": "Send the runtime-trace request to the Windows machine before doing more RadialBlur Inner implementation tuning.",
        "agent_prompt": "Read notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md. Do not edit. On Windows, render rb_inner_only_strength_small under a debugger, break at OLMRadialBlur.aex+0x26e5, record R8D/[rsp+0x138]/span_gate/inner base span, step into +0x1c90, and record R14D after +0x1d18. Return only the trace values and whether R14D is 31 or 32.",
    },
    {
        "request_id": "kirakira_opencv455_primitive_fact_20260618",
        "requires_covered": [
            "kirakira_single_ray_20260606",
            "kirakira_strength0_brightness_20260614",
        ],
        "effect": "OLM Kira Kira",
        "plugin_area": "OLMKiraKira OpenCV 4.5.5 primitive fact",
        "mode": "external-trace",
        "read_files": [
            "notes/OLMKiraKira_ASM_FACTS.md",
            "notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md",
            "refs/reference_requests/kirakira_single_ray_20260606.json",
            "cli/OLMKiraKira/",
            "refs/scripts/smoke_olmkirakira*.py",
        ],
        "write_scope": "none",
        "reason": "Single-ray and strength0 refs are covered; broad ray-order/scalar/compose, Rect/dsize, map/remap split, baseline box accumulation, one-pixel crop, destructive same-Mat warpAffine aliasing, and broad OpenCV version drift hypotheses are rejected. Remaining work needs the selected Windows AVX2 OpenCV 4.5.5 FilterEngine branch or another stage-value primitive fact rather than another PNG-only toggle.",
        "command": "Open OLMKiraKira.aex in Ghidra or a debugger and identify which FUN_181281260 FilterEngine branch is used for the first boxFilter pass; baseline RowSum<float,double>/ColumnSum<double,float> and warpAffine alias clone are already pinned.",
        "agent": "Use KiraKira only for a fresh OpenCV 4.5.5/Ghidra primitive fact; do not add more high-level warp/box toggles from PNG residuals alone.",
        "agent_prompt": "Read notes/OLMKiraKira_ASM_FACTS.md. Do not edit unless assigned a bounded diagnostic. Mac can now reproduce OpenCV 4.5.5 arm64 probes via refs/scripts/setup_olmkirakira_opencv455_probe_env.sh, and those match the newer OpenCV probe metrics, so broad OpenCV version drift is not the answer. Same-Mat warpAffine alias destruction is rejected by the FUN_181297ac0 alias guard, and baseline CV_32F boxFilter uses RowSum<float,double>/ColumnSum<double,float>. Report only which FUN_181281260 optimized FilterEngine branch is selected on Windows, a concrete Windows AVX2/OpenCV 4.5.5 primitive fact for that branch, or a pre/post ray stage detail.",
    },
]

FOLLOW_UPS = {
    "smoother2_no_key_grid_20260606": {
        "plugin_area": "OLMSmoother2 no-key",
        "mode": "explorer",
        "read_files": [
            "notes/OLMSmoother2_ASM_FACTS.md",
            "refs/reference_requests/smoother2_no_key_grid_20260606.json",
            "cli/OLMSmoother2/",
            "refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py",
        ],
        "write_scope": "none",
        "reason": "No-key grid is near-exact to current Windows reference precision; remaining work is AE-host/Mac integration validation, not more PNG-only tuning.",
        "command": "python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py",
        "agent": "Do not spawn more no-key tuning work unless AE-host validation exposes a new Smoother2 mismatch.",
        "agent_prompt": "Read notes/OLMSmoother2_ASM_FACTS.md, refs/reference_requests/smoother2_no_key_grid_20260606.json, cli/OLMSmoother2/, and refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py. Do not edit. Treat the no-key grid as solved to current Windows reference precision unless you find contradictory objdump evidence; report only AE-host/Mac integration validation risks and any narrow writeback/quantization audit worth keeping.",
    },
    "olmcolorkey_replace_colorspace_20260606": {
        "plugin_area": "OLMColorKey Replace/color-space",
        "mode": "explorer",
        "read_files": [
            "refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json",
            "refs/scripts/audit_olmcolorkey_manifest.py",
            "refs/scripts/olmcolorkey_cli.py",
            "cli/OLMColorKey/",
            "rust/olmcolorkey_cli/",
            "mac/OLMColorKey/",
        ],
        "write_scope": "none",
        "reason": "Reference-backed non-RGB comparator parity is now promoted into Mac/Rust; remaining ColorKey work is AE-host validation plus separate Edge Thin/Blur residuals.",
        "command": "python3 refs/scripts/smoke_olmcolorkey_replace_colorspace_request_cli.py",
        "agent": "Use ColorKey next only for AE-host validation packaging or the known Edge Thin/Edge Blur residuals.",
        "agent_prompt": "Read refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json, refs/scripts/audit_olmcolorkey_manifest.py, refs/scripts/olmcolorkey_cli.py, cli/OLMColorKey/, rust/olmcolorkey_cli/, and mac/OLMColorKey/. Do not edit. Treat Replace and non-RGB comparator parity as promoted in C++/Mac/Rust for the returned 8-bit PNG references; report only AE-host validation packaging, 16/32-bit host risks, or the separate Edge Thin/Edge Blur residual action.",
    },
    "directionalblur_context_scale_20260606": {
        "plugin_area": "OLMDirectionalBlur",
        "mode": "explorer",
        "read_files": [
            "notes/IR_OLMDirectionalBlur.md",
            "notes/OLMDirectionalBlur_ASM_FACTS.md",
            "refs/reference_requests/directionalblur_context_scale_20260606.json",
            "cli/OLMDirectionalBlur/",
            "refs/scripts/smoke_olmdirectionalblur*.py",
        ],
        "write_scope": "none",
        "reason": "Returned refs reject frame-rate scaling and obvious alpha/RGB branch toggles; first rotate, 8bpc host callbacks, rowdriver ownership, and the final denom>0 guard now match the current CLI.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id directionalblur_context_scale_20260606 --expected-effect 'OLM DirectionalBlur' --build-script refs/scripts/build_olmdirectionalblur_cli.sh --command '\"cli/OLMDirectionalBlur/olmdirectionalblur_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\" --algorithm rotated-aex-exact-rowdriver --angle-sign -1 --sample-sign 1 --strength-scale auto'",
        "agent": "Park DirectionalBlur unless a fresh binary fact appears; do not spend active PNG-tuning time here.",
        "agent_prompt": "Read notes/IR_OLMDirectionalBlur.md, notes/OLMDirectionalBlur_ASM_FACTS.md, refs/reference_requests/directionalblur_context_scale_20260606.json, cli/OLMDirectionalBlur/, and the directional smoke scripts. Do not edit. Treat ctx+0x11c/0x120 as PF_InData.downsample_x.num/den and treat straight RGB, binary alpha, denom-alpha rotate-back, plain rotate sampling, first-rotate invalid handling, 8bpc host populate/output callbacks, rowdriver ownership, and final denom>0 normalization as rejected or mirrored unless you find contradictory objdump evidence. Report only a new concrete binary-backed difference; otherwise keep this parked behind RadialBlur/KiraKira.",
    },
    "kirakira_single_ray_20260606": {
        "plugin_area": "OLMKiraKira",
        "mode": "explorer",
        "read_files": [
            "notes/OLMKiraKira_ASM_FACTS.md",
            "notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md",
            "refs/reference_requests/kirakira_single_ray_20260606.json",
            "cli/OLMKiraKira/",
            "refs/scripts/smoke_olmkirakira*.py",
        ],
        "write_scope": "none",
        "reason": "Returned single-ray refs close the broad ray-order/scalar gap, and the Ghidra/subagent/local-OpenCV audits now reject the naive Rect/copy/dsize, simple boxFilter argument, same-Mat alias, and broad OpenCV version-drift hypotheses. Remaining KiraKira work needs a fresh Windows AVX2/OpenCV 4.5.5 primitive fact, not more high-level PNG tuning.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id kirakira_single_ray_20260606 --expected-effect 'OLM Kira Kira' --build-script refs/scripts/build_olmkirakira_cli.sh --command '\"cli/OLMKiraKira/olmkirakira_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\" --seed-mode aex --falloff box3 --gain-scale 0.62 --ray-mode axis-rotate --compose-mode aex-screen-over --filter-border mirror --warp-mode aex-two-temp --auto-length-scale --comp-width 1920'",
        "agent": "Park KiraKira behind RadialBlur unless a fresh binary/OpenCV 4.5.5 fact appears; do not add more high-level warp/box toggles from PNG residuals alone.",
        "agent_prompt": "Read notes/OLMKiraKira_ASM_FACTS.md, notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md, refs/reference_requests/kirakira_single_ray_20260606.json, cli/OLMKiraKira/, and refs/scripts/smoke_olmkirakira*.py. Do not edit. Treat ray order, angle table, fd90 scalar non-use, compose, strength0 brightness scale, +4.0 temp extents, centered Rect/copy/dsize packing, simple boxFilter ksize/anchor/border/normalize, map/remap fixed-point split, baseline double box accumulation, one-pixel final-copy offsets, destructive same-Mat warpAffine aliasing, and broad OpenCV 4.5.5-vs-newer drift as separated or rejected by existing refs/asm. Report only a new concrete Windows AVX2 OpenCV 4.5.5 optimized FilterEngine/boxFilter branch fact, pre/post ray detail, or a single debugger/objdump diagnostic.",
    },
    "radialblur_inner_size_variation_20260606": {
        "plugin_area": "OLMRadialBlur Inner/EdgeFade",
        "mode": "explorer",
        "read_files": [
            "notes/OLMRadialBlur_RE.md",
            "notes/OLMRadialBlur_ASM_FACTS.md",
            "refs/reference_requests/radialblur_inner_size_variation_20260606.json",
            "cli/OLMRadialBlur/",
            "refs/scripts/smoke_olmradialblur*inner*.py",
        ],
        "write_scope": "none",
        "reason": "Ghidra-backed Inner source-scatter/prepass, Quality/5 span scaling, AEX next-row inner wrap, and Edge Fade prepass tables are now default in the C++ CLI; Windows runtime trace confirms the small-span witness resolves to effective span 31, so the span-31 population is now the default. Remaining residual needs sampler/prepass/writeback evidence, not another span trace.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id radialblur_inner_size_variation_20260606 --expected-effect 'OLM RadialBlur' --build-script refs/scripts/build_olmradialblur_cli.sh --command '\"cli/OLMRadialBlur/olmradialblur_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\"'",
        "agent": "Park RadialBlur unless a new binary fact explains the remaining residual or a bounded Edge Fade audit is assigned.",
        "agent_prompt": "Read notes/OLMRadialBlur_RE.md, notes/OLMRadialBlur_ASM_FACTS.md, refs/reports/runtime_trace_summary.md, refs/reference_requests/radialblur_inner_size_variation_20260606.json, refs/reference_requests/radialblur_inner_20260605.json, cli/OLMRadialBlur/, and the Inner/EdgeFade smoke scripts. Do not edit unless assigned a bounded patch. Treat max/denom writeback, Quality/5 span scaling, AEX next-row inner wrap, FUN_1800024c0 dynamic offset, FUN_180002780 Edge Fade prepass ownership, and runtime-confirmed small-span effective length 31 as promoted to the C++ CLI default. Do not request the same 32-vs-31 trace again. Report only a new concrete binary-backed sampler/prepass/writeback explanation or a narrow Edge Fade audit.",
    },
    "radialblur_inner_20260605": {
        "plugin_area": "OLMRadialBlur Inner/EdgeFade",
        "mode": "explorer",
        "read_files": [
            "notes/OLMRadialBlur_RE.md",
            "notes/OLMRadialBlur_ASM_FACTS.md",
            "refs/reference_requests/radialblur_inner_20260605.json",
            "cli/OLMRadialBlur/",
            "refs/scripts/smoke_olmradialblur*inner*.py",
        ],
        "write_scope": "none",
        "reason": "Primary full Inner software return: promoted default now uses source-scatter+Quality/5+AEX next-row wrap+Edge-Fade prepass plus runtime-confirmed span-31 population for the small witness. Residual remains nonzero, so continue from binary-grounded sampler/prepass/writeback facts.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id radialblur_inner_20260605 --expected-effect 'OLM RadialBlur' --build-script refs/scripts/build_olmradialblur_cli.sh --command '\"cli/OLMRadialBlur/olmradialblur_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\"'",
        "agent": "Use as the main full-Inner evidence set for the OLMRadialBlur Inner explorer.",
        "agent_prompt": "Read notes/OLMRadialBlur_RE.md, notes/OLMRadialBlur_ASM_FACTS.md, refs/reports/runtime_trace_summary.md, refs/reference_requests/radialblur_inner_20260605.json, refs/reference_requests/radialblur_inner_size_variation_20260606.json, cli/OLMRadialBlur/, and the Inner smoke scripts. Do not edit unless assigned a bounded patch. Treat current default, source-scatter+Quality/5+AEX next-row+Edge-Fade prepass, runtime-confirmed span-31 population, loop-minus-one, table-span-minus-one, and dynamic-offset aex-row metrics as recorded in the notes. Do not revisit broad final-denominator toggles or the already-answered 32-vs-31 trace; focus on remaining sampler/prepass/writeback residuals.",
    },
}

PRIOR_AUDIT_REFS = [
    "notes/SUBAGENT_ASSIGNMENTS.md",
    "notes/PROGRESS_MATRIX.md",
    "notes/PARALLEL_IR_AUDIT_20260606.md",
]


def resolved_read_files(read_files: list[str]) -> list[str]:
    resolved: list[str] = []
    for path in read_files:
        if any(char in path for char in "*?[]"):
            matches = sorted(glob.glob(path))
            resolved.extend(matches or [path])
        else:
            resolved.append(path)
    return sorted(dict.fromkeys(resolved))


def read_file_patterns(read_files: list[str]) -> list[str]:
    return [path for path in read_files if any(char in path for char in "*?[]")]


def copy_paste_prompt(action: dict[str, Any]) -> str:
    read_files = "\n".join(f"- {path}" for path in action["read_files"])
    prior_refs = "\n".join(f"- {path}" for path in action["prior_audit_refs"])
    pattern_note = []
    if action["read_file_patterns"]:
        patterns = "\n".join(f"- {path}" for path in action["read_file_patterns"])
        pattern_note = [
            "",
            "Pattern note:",
            "Use the glob patterns above as focused smoke families; action.json also records read_files_resolved for exact expansion.",
            patterns,
        ]
    return "\n".join(
        [
            "Workspace: <repo-root>",
            "",
            f"Plugin area: {action['plugin_area']}",
            f"Request: {action['request_id']} ({action['status']})",
            f"Mode: {action['mode']}",
            f"Write scope: {action['write_scope']}",
            "",
            "Read first:",
            prior_refs,
            "",
            "Then read:",
            read_files,
            *pattern_note,
            "",
            f"First run or inspect: {action['smoke_command']}",
            f"Stop condition: {action['stop_condition']}",
            "",
            "Task:",
            action["agent_prompt"],
            "",
            "Return exactly:",
            "1. Current best-supported IR checkpoints.",
            "2. Exact measured status with commands or file references.",
            "3. Whether the stop condition still holds and what unblocks it.",
            "4. One parent action backed by objdump/decomp/IR/reference evidence.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--requests",
        type=Path,
        default=Path("refs/reference_requests"),
        help="Directory containing request JSON files.",
    )
    parser.add_argument(
        "--references",
        type=Path,
        default=Path("refs/win_references"),
        help="Directory containing imported Windows reference manifests.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--dispatch-dir",
        type=Path,
        default=None,
        help="Write index.json and per-action SUBAGENT.md/action.json files for sub-agent dispatch.",
    )
    return parser.parse_args()


def priority_key(row: dict[str, Any]) -> tuple[int, str]:
    request_id = str(row.get("request_id", ""))
    try:
        index = PRIORITY.index(request_id)
    except ValueError:
        index = len(PRIORITY)
    return (index, request_id)


def action_for(row: dict[str, Any], *, covered: bool = True) -> dict[str, Any]:
    request_id = str(row.get("request_id", ""))
    follow_up = FOLLOW_UPS.get(request_id, {})
    command = follow_up.get(
        "command",
        f"python3 refs/scripts/smoke_reference_requests_after_import.py --request {request_id}",
    )
    agent_prompt = follow_up.get(
        "agent_prompt",
        f"Read the request JSON and imported manifest for {request_id}. Do not edit. Report the current measured status, whether the stop condition is lifted, and one parent action backed by reference or IR evidence.",
    )
    if not covered:
        prior_refs = ", ".join(PRIOR_AUDIT_REFS)
        pinning = row.get("pinning") or {}
        pinning_note = ""
        if pinning:
            pinning_note = (
                f" Package-time pinning: current params_full "
                f"{pinning.get('current_params_full_cases', 0)}/{pinning.get('total_cases', 0)}, "
                f"packaged params_full {pinning.get('packaged_params_full_cases', 0)}/{pinning.get('total_cases', 0)}, "
                f"linked cases {pinning.get('linked_cases', 0)}."
            )
        agent_prompt = (
            f"Pending reference request: {request_id}. Do not edit and do not tune from current PNG residuals. "
            f"First read {prior_refs} to avoid restating old audits. "
            f"Then read the listed files, report only new stop-line deltas, audit whether the stop condition still holds, "
            f"and report the exact first action after this request is imported. "
            f"Original post-import prompt: {agent_prompt}{pinning_note}"
        )
    else:
        agent_prompt = f"First run or inspect: {command}. {agent_prompt}"

    stop_condition = (
        f"{request_id} is not covered yet; keep this slice read-only and stop before PNG-only implementation tuning."
        if not covered
        else f"{request_id} is covered; run the request smoke before proposing implementation changes."
    )

    read_files = follow_up.get("read_files", [f"refs/reference_requests/{request_id}.json"])
    action = {
        "request_id": request_id,
        "status": row.get("status"),
        "effect": row.get("effect"),
        "manifest": (row.get("best") or {}).get("manifest"),
        "pinning": row.get("pinning"),
        "plugin_area": follow_up.get("plugin_area", request_id),
        "mode": follow_up.get("mode", "explorer"),
        "read_files": read_files,
        "read_file_patterns": read_file_patterns(read_files),
        "read_files_resolved": resolved_read_files(read_files),
        "write_scope": follow_up.get("write_scope", "none"),
        "reason": follow_up.get("reason", "No registered priority note."),
        "stop_condition": stop_condition,
        "unblock_request": request_id,
        "prior_audit_refs": PRIOR_AUDIT_REFS,
        "command": command,
        "smoke_command": command,
        "agent": follow_up.get("agent", "Inspect the covered manifest and update the relevant IR note."),
        "agent_prompt": agent_prompt,
    }
    action["copy_paste_prompt"] = copy_paste_prompt(action)
    return action


def runtime_action_for(config: dict[str, Any]) -> dict[str, Any]:
    read_files = list(config["read_files"])
    action = {
        "request_id": config["request_id"],
        "status": "runtime-trace",
        "effect": config["effect"],
        "manifest": None,
        "plugin_area": config["plugin_area"],
        "mode": config["mode"],
        "read_files": read_files,
        "read_file_patterns": read_file_patterns(read_files),
        "read_files_resolved": resolved_read_files(read_files),
        "write_scope": config["write_scope"],
        "reason": config["reason"],
        "stop_condition": "Required references are covered; stop PNG-only implementation tuning until this runtime trace is answered.",
        "unblock_request": config["request_id"],
        "prior_audit_refs": PRIOR_AUDIT_REFS,
        "command": config["command"],
        "smoke_command": config["command"],
        "agent": config["agent"],
        "agent_prompt": config["agent_prompt"],
    }
    action["copy_paste_prompt"] = copy_paste_prompt(action)
    return action


def runtime_actions_for(covered_ids: set[str]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for config in RUNTIME_FOLLOW_UPS:
        if all(request_id in covered_ids for request_id in config["requires_covered"]):
            actions.append(runtime_action_for(config))
    return actions


def build_reference_action_data(rows: list[dict[str, Any]]) -> dict[str, Any]:
    covered = sorted([row for row in rows if row.get("status") == "covered"], key=priority_key)
    partial = sorted([row for row in rows if row.get("status") == "partial"], key=priority_key)
    pending = sorted([row for row in rows if row.get("status") == "pending"], key=priority_key)
    covered_ids = {str(row.get("request_id", "")) for row in covered}
    actions = runtime_actions_for(covered_ids) + [action_for(row) for row in covered]
    pending_actions = [action_for(row, covered=False) for row in pending]
    return {
        "next_action": actions[0] if actions else None,
        "covered_actions": actions,
        "pending_actions": pending_actions,
        "partial": partial,
        "pending": [row.get("request_id") for row in pending],
    }


def write_dispatch_dir(dispatch_dir: Path, data: dict[str, Any]) -> None:
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    (dispatch_dir / "index.json").write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    for bucket_name, actions in (
        ("covered", data["covered_actions"]),
        ("pending", data["pending_actions"]),
    ):
        bucket = dispatch_dir / bucket_name
        bucket.mkdir(parents=True, exist_ok=True)
        for index, action in enumerate(actions, start=1):
            action_dir = bucket / f"{index:02d}_{action['request_id']}"
            action_dir.mkdir(parents=True, exist_ok=True)
            (action_dir / "action.json").write_text(
                json.dumps(action, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            (action_dir / "SUBAGENT.md").write_text(
                action["copy_paste_prompt"] + "\n",
                encoding="utf-8",
            )


def main() -> int:
    args = parse_args()
    rows = load_status_rows(args.requests, args.references)
    data = build_reference_action_data(rows)
    actions = data["covered_actions"]
    partial = data["partial"]
    pending = [row for row in rows if row.get("status") == "pending"]

    if args.dispatch_dir:
        write_dispatch_dir(args.dispatch_dir, data)
        print(f"wrote subagent dispatch files: {args.dispatch_dir}", file=sys.stderr)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    if actions:
        print("next covered reference action")
        first = actions[0]
        print(f"- request: {first['request_id']} ({first['effect']})")
        print(f"- plugin area: {first['plugin_area']}")
        print(f"- manifest: {first['manifest']}")
        print(f"- why: {first['reason']}")
        print(f"- run: {first['command']}")
        print(f"- mode: {first['mode']}")
        print(f"- write scope: {first['write_scope']}")
        print(f"- read files: {', '.join(first['read_files'])}")
        print(f"- parent: {first['agent']}")
        print(f"- subagent prompt: {first['agent_prompt']}")
        print(f"- copy-paste prompt: next_reference_actions.py --json | .next_action.copy_paste_prompt")
        if len(actions) > 1:
            print("\nother covered requests, in priority order:")
            for action in actions[1:]:
                print(f"- {action['request_id']}: {action['command']}")
    else:
        print("no covered reference requests yet")

    if partial:
        print("\npartial requests:")
        for row in partial:
            best = row.get("best") or {}
            print(f"- {row['request_id']}: {best}")

    if pending:
        print("\npending requests:")
        pending_action_list = data["pending_actions"]
        for pending_action in pending_action_list:
            print(f"- {pending_action['request_id']}: {pending_action['plugin_area']} ({pending_action['mode']})")
        first_pending = pending_action_list[0]
        print("\nnext pending subagent")
        print(f"- request: {first_pending['request_id']} ({first_pending['effect']})")
        print(f"- plugin area: {first_pending['plugin_area']}")
        print(f"- unblock: {first_pending['unblock_request']}")
        print(f"- stop: {first_pending['stop_condition']}")
        if first_pending.get("pinning"):
            pinning = first_pending["pinning"]
            print(
                "- pinning: "
                f"current {pinning.get('current_params_full_cases', 0)}/{pinning.get('total_cases', 0)}, "
                f"packaged {pinning.get('packaged_params_full_cases', 0)}/{pinning.get('total_cases', 0)}, "
                f"linked {pinning.get('linked_cases', 0)}"
            )
        print(f"- smoke after import: {first_pending['smoke_command']}")
        print(f"- read files: {', '.join(first_pending['read_files'])}")
        print(f"- subagent prompt: {first_pending['agent_prompt']}")
        print(f"- copy-paste prompt: next_reference_actions.py --json | .pending_actions[0].copy_paste_prompt")
        print("\npending subagent dispatch JSON:")
        print("python3 refs/scripts/next_reference_actions.py --json")
        print("\npending package command:")
        print("python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending.zip")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
