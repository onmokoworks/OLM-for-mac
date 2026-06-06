#!/usr/bin/env python3
"""Print the next parent actions for Windows reference request coverage."""

from __future__ import annotations

import argparse
import json
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
    return parser.parse_args()


def priority_key(row: dict[str, Any]) -> tuple[int, str]:
    request_id = str(row.get("request_id", ""))
    try:
        index = PRIORITY.index(request_id)
    except ValueError:
        index = len(PRIORITY)
    return (index, request_id)


def action_for(row: dict[str, Any]) -> dict[str, Any]:
    request_id = str(row.get("request_id", ""))
    follow_up = FOLLOW_UPS.get(request_id, {})
    command = follow_up.get(
        "command",
        f"python3 refs/scripts/smoke_reference_requests_after_import.py --request {request_id}",
    )
    return {
        "request_id": request_id,
        "status": row.get("status"),
        "effect": row.get("effect"),
        "manifest": (row.get("best") or {}).get("manifest"),
        "plugin_area": follow_up.get("plugin_area", request_id),
        "mode": follow_up.get("mode", "explorer"),
        "read_files": follow_up.get("read_files", [f"refs/reference_requests/{request_id}.json"]),
        "write_scope": follow_up.get("write_scope", "none"),
        "reason": follow_up.get("reason", "No registered priority note."),
        "command": command,
        "smoke_command": command,
        "agent": follow_up.get("agent", "Inspect the covered manifest and update the relevant IR note."),
        "agent_prompt": follow_up.get(
            "agent_prompt",
            f"Read the request JSON and imported manifest for {request_id}. Do not edit. Report the current measured status, whether the stop condition is lifted, and one parent action backed by reference or IR evidence.",
        ),
    }


def main() -> int:
    args = parse_args()
    rows = load_status_rows(args.requests, args.references)
    covered = sorted([row for row in rows if row.get("status") == "covered"], key=priority_key)
    partial = sorted([row for row in rows if row.get("status") == "partial"], key=priority_key)
    pending = sorted([row for row in rows if row.get("status") == "pending"], key=priority_key)
    actions = [action_for(row) for row in covered]

    if args.json:
        print(
            json.dumps(
                {
                    "next_action": actions[0] if actions else None,
                    "covered_actions": actions,
                    "partial": partial,
                    "pending": [row.get("request_id") for row in pending],
                },
                indent=2,
                sort_keys=True,
            )
        )
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
        for row in pending:
            print(f"- {row['request_id']}")
        print("\npending package command:")
        print("python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending_20260606.zip")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
