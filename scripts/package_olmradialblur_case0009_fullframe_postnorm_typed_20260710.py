#!/usr/bin/env python3
"""Build the one-shot Windows full-frame RadialBlur typed witness package."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


REQUEST = "olmradialblur_case0009_fullframe_postnorm_typed_20260710"
PROFILE = "radialblur-case0009-fullframe-postnorm-typed"
CONTRACT = Path("refs/conformance/olmradialblur_case0009_fullframe_postnorm_typed_contract_20260710.md")
SUPPORT = Path("refs/runtime_trace_support/olmradialblur_zoom_case0009_final_plane_typed_20260710")
PAYLOAD = (
    Path("scripts/ae_render_single_case.jsx"),
    Path("scripts/run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1"),
    Path("tools/emulation/probe_radialblur_final_plane_small.py"),
    Path("refs/conformance/aex_cpu_fixture_template_result_20260710.md"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/request_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/reference_manifest.json"),
    Path("handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701/input/case_0009_before_effects.png"),
)


def return_template() -> dict:
    def point(role: str, xy: list[int], reference: list[int]) -> dict:
        return {
            "role": role,
            "xy": xy,
            "reference_rgba8": reference,
            "observed_rgba8": None,
            "inverse_sample_xy": [None, None],
            "cells": [
                {
                    "slot": slot,
                    "cell_id": None,
                    "angle_index": None,
                    "radius_index": None,
                    "address": None,
                    "bilinear_weight": None,
                    "accum_rgba_f32": [None, None, None, None],
                    "denom_f32": None,
                    "valid_f32": None,
                    "final_rgba_f32": [None, None, None, None],
                }
                for slot in ("00", "10", "01", "11")
            ],
            "final_alpha_sum": None,
            "pre_byte_alpha": None,
            "hook_liveness": None,
            "evidence_artifact": None,
            "failed_reason": None,
        }

    return {
        "kind": "olm_runtime_trace_result",
        "schema": 1,
        "results": [{
            "request_id": REQUEST,
            "status": "answered_partial",
            "summary": "Fill from one Windows AE Software full-frame case_0009 run.",
            "observations": {
                "classification": "answered | answered_partial | failed_partial",
                "effect": "OLM RadialBlur",
                "case_id": "case_0009",
                "run_id": None,
                "hook_or_watchpoint": "0x180005d99 post-normalization boundary",
                "geometry": {"width": 1920, "height": 1080, "mode": "full-frame"},
                "points": [
                    point("primary", [7, 0], [21, 3, 3, 254]),
                    point("control", [8, 0], [21, 3, 3, 255]),
                    point("control", [24, 0], [21, 3, 3, 255]),
                ],
                "same_run": True,
                "producer_b150": {
                    "hook_offset": "0xb150", "row_range": [None, None], "width": None,
                    "context": None, "source_rgba": None, "source_scalar": None,
                    "scale_plane": None, "accum_rgba": None, "alpha_plane": None,
                    "outer_span": None, "inner_span": None,
                    "target_scale_f32": {}, "target_source_alpha_f32": {},
                },
                "console_artifact": None,
                "failed_reason": None,
            },
        }],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(
        "refs/runtime_trace_packages/olm_runtime_trace_radialblur_case0009_fullframe_postnorm_typed_20260710.zip"
    ))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else root / args.output
    required = [root / CONTRACT, root / SUPPORT / "final_plane_hook_fragment.cdb.template"]
    required += [root / path for path in PAYLOAD]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("missing package input:\n" + "\n".join(missing))

    manifest = {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "profile": PROFILE,
        "entrypoint": CONTRACT.as_posix(),
        "repo_root_name": root.name,
        "runtime_actions": [{
            "request_id": REQUEST,
            "plugin_area": "OLMRadialBlur Zoom case_0009 full-frame post-normalization typed witness",
            "mode": "external-trace",
            "command": "Run exactly one Windows AE Software full-frame case_0009 render under CDB; capture the target-row FUN_18000b150 producer inputs at +0xb150 and the post-normalization cells at +0x5d99/+0x5e5b/+0x5e6d for (7,0), (8,0), and (24,0).",
            "stop_condition": "answered only when the +0xb150 scale/source-alpha producer values and all three final-plane rows are complete and bound to the same run; otherwise return the exact failure reason and artifact.",
        }],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("runtime_trace_package_manifest.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("RETURN_RUNTIME_TRACE_TEMPLATE.json", json.dumps(return_template(), indent=2) + "\n")
        archive.write(root / CONTRACT, CONTRACT.as_posix())
        archive.write(root / SUPPORT / "final_plane_hook_fragment.cdb.template", "artifacts/final_plane_hook_fragment.cdb.template")
        for path in PAYLOAD:
            target = "artifacts/" + path.name if path.name.startswith("run_olmradialblur") else path.as_posix()
            archive.write(root / path, target)
    print(f"[OK] runtime trace package: {output}")
    print(f"- {REQUEST}: one-shot Windows full-frame post-normalization typed witness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
