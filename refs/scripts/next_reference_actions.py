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
    "smoother2_no_key_grid_20260606",
    "olmcolorkey_replace_colorspace_20260606",
    "directionalblur_context_scale_20260606",
    "kirakira_single_ray_20260606",
    "radialblur_inner_size_variation_20260606",
    "radialblur_inner_20260605",
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
        "reason": "Most isolated blocker: v2 key/gamma paths are guarded and no-key case_0001 is the remaining residual.",
        "command": "python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py",
        "agent": "Spawn/read OLMSmoother2 no-key explorer after the grid smoke groups Smoothness and Smooth Range.",
        "agent_prompt": "Read notes/OLMSmoother2_ASM_FACTS.md, refs/reference_requests/smoother2_no_key_grid_20260606.json, cli/OLMSmoother2/, and refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py. Do not edit. Run or inspect the no-key grid smoke output, group residuals by Smoothness and Smooth Range, and report the smallest objdump/IR-backed parent action for no-key v2.",
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
        "reason": "Unblocks Replace and non-RGB color-space promotion that current black-key refs cannot prove.",
        "command": "python3 refs/scripts/smoke_olmcolorkey_replace_colorspace_request_cli.py",
        "agent": "Spawn/read OLMColorKey Replace/color-space explorer, then implement the smallest RGB Replace/no-edge slice first.",
        "agent_prompt": "Read refs/reference_requests/olmcolorkey_replace_colorspace_20260606.json, refs/scripts/audit_olmcolorkey_manifest.py, refs/scripts/olmcolorkey_cli.py, cli/OLMColorKey/, rust/olmcolorkey_cli/, and mac/OLMColorKey/. Do not edit. Compare the returned cases against current RGB/Edge Thin/Edge Blur coverage and identify the smallest reference-backed Replace or color-space slice to implement first.",
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
        "reason": "Unblocks render-context scale, premul/straight RGB, and alpha ownership for DirectionalBlur.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id directionalblur_context_scale_20260606 --expected-effect 'OLM DirectionalBlur' --build-script refs/scripts/build_olmdirectionalblur_cli.sh --command '\"cli/OLMDirectionalBlur/olmdirectionalblur_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\" --algorithm rotated-aex-full-choreo --angle-sign -1 --sample-sign 1 --strength-scale auto'",
        "agent": "Spawn/read OLMDirectionalBlur explorer to reconcile manifest/context scale with the A/B buffer IR.",
        "agent_prompt": "Read notes/IR_OLMDirectionalBlur.md, notes/OLMDirectionalBlur_ASM_FACTS.md, refs/reference_requests/directionalblur_context_scale_20260606.json, cli/OLMDirectionalBlur/, and the directional smoke scripts. Do not edit. Use the returned manifest/context-scale and non-opaque alpha cases to decide whether the current A/B buffer IR needs render-scale, premul, or alpha side-channel changes.",
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
        "reason": "Unblocks ray order, angle table, helper scalar, and crop/canvas behavior for KiraKira.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id kirakira_single_ray_20260606 --expected-effect 'OLM Kira Kira' --build-script refs/scripts/build_olmkirakira_cli.sh --command '\"cli/OLMKiraKira/olmkirakira_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\" --seed-mode aex --falloff box3 --gain-scale 0.72 --ray-mode axis-rotate --compose-mode aex-premul --filter-border mirror --auto-length-scale --comp-width 1920'",
        "agent": "Spawn/read OLMKiraKira explorer to isolate vertical/horizontal, diagonal, and scalar behavior in that order.",
        "agent_prompt": "Read notes/OLMKiraKira_ASM_FACTS.md, notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md, refs/reference_requests/kirakira_single_ray_20260606.json, cli/OLMKiraKira/, and refs/scripts/smoke_olmkirakira*.py. Do not edit. Use the single-ray returned cases to separate ray order, angle table, helper scalar, crop/canvas, and axis fast-path behavior.",
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
        "reason": "Unblocks nonzero Size Variation and alpha cases for the +0x40/+0x50 Inner plane semantics.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id radialblur_inner_size_variation_20260606 --expected-effect 'OLM RadialBlur' --build-script refs/scripts/build_olmradialblur_cli.sh --command '\"cli/OLMRadialBlur/olmradialblur_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\" --inner-source-scatter-prepass --ignore-size-variation'",
        "agent": "Spawn/read OLMRadialBlur Inner explorer to compare only a small set of +0x40/+0x50 hypotheses.",
        "agent_prompt": "Read notes/OLMRadialBlur_RE.md, notes/OLMRadialBlur_ASM_FACTS.md, refs/reference_requests/radialblur_inner_size_variation_20260606.json, cli/OLMRadialBlur/, and the Inner/EdgeFade smoke scripts. Do not edit. Use nonzero Size Variation and alpha cases to isolate +0x40 span/gate and +0x50 prepass factor semantics before proposing any implementation change.",
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
        "reason": "Secondary Inner request; process after the size-variation request unless it is the only covered RadialBlur return.",
        "command": "python3 refs/scripts/smoke_reference_request_cli_probe.py --request-id radialblur_inner_20260605 --expected-effect 'OLM RadialBlur' --build-script refs/scripts/build_olmradialblur_cli.sh --command '\"cli/OLMRadialBlur/olmradialblur_cli\" --input \"{input}\" --params \"{params}\" --output \"{output}\" --inner-source-scatter-prepass'",
        "agent": "Use as supporting evidence for the OLMRadialBlur Inner explorer.",
        "agent_prompt": "Read notes/OLMRadialBlur_RE.md, notes/OLMRadialBlur_ASM_FACTS.md, refs/reference_requests/radialblur_inner_20260605.json, cli/OLMRadialBlur/, and the Inner smoke scripts. Do not edit. Treat this as supporting Inner evidence and compare it with the size-variation request if both are covered.",
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
            f"Workspace: /Users/onmk/Documents/Projects/Personal/OLM as",
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
        agent_prompt = (
            f"Pending reference request: {request_id}. Do not edit and do not tune from current PNG residuals. "
            f"First read {prior_refs} to avoid restating old audits. "
            f"Then read the listed files, report only new stop-line deltas, audit whether the stop condition still holds, "
            f"and report the exact first action after this request is imported. "
            f"Original post-import prompt: {agent_prompt}"
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
    covered = sorted([row for row in rows if row.get("status") == "covered"], key=priority_key)
    partial = sorted([row for row in rows if row.get("status") == "partial"], key=priority_key)
    pending = sorted([row for row in rows if row.get("status") == "pending"], key=priority_key)
    actions = [action_for(row) for row in covered]
    pending_actions = [action_for(row, covered=False) for row in pending]
    data = {
        "next_action": actions[0] if actions else None,
        "covered_actions": actions,
        "pending_actions": pending_actions,
        "partial": partial,
        "pending": [row.get("request_id") for row in pending],
    }

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
        pending_action_list = [action_for(row, covered=False) for row in pending]
        for pending_action in pending_action_list:
            print(f"- {pending_action['request_id']}: {pending_action['plugin_area']} ({pending_action['mode']})")
        first_pending = pending_action_list[0]
        print("\nnext pending subagent")
        print(f"- request: {first_pending['request_id']} ({first_pending['effect']})")
        print(f"- plugin area: {first_pending['plugin_area']}")
        print(f"- unblock: {first_pending['unblock_request']}")
        print(f"- stop: {first_pending['stop_condition']}")
        print(f"- smoke after import: {first_pending['smoke_command']}")
        print(f"- read files: {', '.join(first_pending['read_files'])}")
        print(f"- subagent prompt: {first_pending['agent_prompt']}")
        print(f"- copy-paste prompt: next_reference_actions.py --json | .pending_actions[0].copy_paste_prompt")
        print("\npending subagent dispatch JSON:")
        print("python3 refs/scripts/next_reference_actions.py --json")
        print("\npending package command:")
        print("python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending_20260606.zip")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
