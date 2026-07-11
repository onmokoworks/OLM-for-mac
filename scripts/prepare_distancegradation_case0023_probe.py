#!/usr/bin/env python3
"""Prepare a single-case OLMDistanceGradation case_0023 AE probe request."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


CASE_ID = "olmdistancegradation_extended__case_0023"
DEFAULT_POINTS = "1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    stamp = datetime.now().strftime("%Y%m%d")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request-dir",
        type=Path,
        default=root / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "refs" / "reports" / f"ae_single_case_distancegradation_case0023_mac_probe_{stamp}" / "request",
    )
    parser.add_argument("--points", default=DEFAULT_POINTS)
    parser.add_argument(
        "--plan-json",
        type=Path,
        default=root / "refs" / "conformance" / f"olmdistancegradation_case0023_mac_probe_plan_{stamp}.json",
    )
    parser.add_argument(
        "--plan-md",
        type=Path,
        default=root / "refs" / "conformance" / f"olmdistancegradation_case0023_mac_probe_plan_{stamp}.md",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    return data


def find_case(manifest: dict, case_id: str) -> dict:
    for case in manifest.get("cases", []):
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    raise KeyError(f"case not found: {case_id}")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def double_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_markdown(plan: dict) -> str:
    lines = [
        "# OLMDistanceGradation case_0023 Mac Probe Plan",
        "",
        f"- Case: `{plan['case_id']}`",
        f"- Request dir: `{plan['request_dir']}`",
        f"- Debug points: `{plan['debug_points_spec']}`",
        f"- Purpose: {plan['purpose']}",
        "",
        "## Commands",
        "",
    ]
    for command in plan["suggested_runs"]:
        lines.extend(
            [
                f"### {command['name']}",
                "",
                f"- Output dir: `{command['output_dir']}`",
                f"- Discriminator: {command['discriminator']}",
                "",
                "```bash",
                command["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
        ]
    )
    for item in plan["interpretation"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden", ""])
    for item in plan["forbidden_actions"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = repo_root()
    src_dir = args.request_dir.resolve()
    out_dir = args.output_dir.resolve()
    ref_manifest = load_json(src_dir / "reference_manifest.json")
    req_manifest = load_json(src_dir / "request_manifest.json")
    case = find_case(ref_manifest, CASE_ID)

    input_dir = out_dir / "input"
    expected_dir = out_dir / "expected"
    input_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    before_name = case["before_effects_frame"]
    frame_name = case["frame"]
    shutil.copy2(src_dir / req_manifest["input_dir"] / before_name, input_dir / before_name)
    shutil.copy2(src_dir / req_manifest["expected_dir"] / frame_name, expected_dir / frame_name)

    ref_copy = dict(ref_manifest)
    ref_copy["cases"] = [case]
    (out_dir / "reference_manifest.json").write_text(
        json.dumps(ref_copy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    req_copy = dict(req_manifest)
    req_copy["request_id"] = "ae_single_distancegradation_case0023_mac_probe_20260707"
    req_copy["reference_profile"] = "windows-software-single-case"
    req_copy["cases"] = [
        {
            "id": case["id"],
            "before_effects_frame": before_name,
            "frame": frame_name,
        }
    ]
    req_copy["threshold_groups"] = [
        {
            "name": "single_case_exact",
            "case_ids": [case["id"]],
            "max_diff": 0,
            "mean_diff": 0.0,
            "nonzero_px_percent": 0.0,
        }
    ]
    req_copy["notes"] = [
        "Single-case DistanceGradation case_0023 probe request.",
        "Use with run_ae_single_case.py, OLM_DG_DEBUG_DUMP_PATH, and OLM_DG_DEBUG_POINTS.",
        "2026-07-07 reference audit proves packaged/current Windows exact; this is a Mac AE source/output ownership probe, not a reference-stale probe.",
    ]
    (out_dir / "request_manifest.json").write_text(
        json.dumps(req_copy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    request_dir_rel = rel(root, out_dir)
    base_output = out_dir.parent
    suggested_runs = []
    for name, use_bg in [("bg_on", 1), ("bg_off", 0)]:
        output_dir = base_output / name
        output_dir_rel = rel(root, output_dir)
        debug_path = f"$(pwd)/{output_dir_rel}/field_debug.txt"
        shade_debug_path = f"$(pwd)/{output_dir_rel}/shade_debug.txt"
        suggested_runs.append(
            {
                "name": name,
                "use_background_color": use_bg,
                "output_dir": output_dir_rel,
                "discriminator": (
                    "If field/debug values match the source-model audit but exported pixels differ, suspect 16bpc host output/source ownership; "
                    "if alpha/raw_inside/field_x differs, suspect Mac AE source alpha or field-boundary ownership."
                ),
                "command": (
                    "python3 scripts/run_ae_single_case.py "
                    f"--request-dir {request_dir_rel} --case-id {CASE_ID} "
                    f"--output-dir {output_dir_rel} "
                    f"--param-override 'Use Background Color={use_bg}' "
                    f"--ae-env {double_quote('OLM_DG_DEBUG_DUMP_PATH=' + debug_path)} "
                    f"--ae-env {double_quote('OLM_DG_SHADE_DEBUG_PATH=' + shade_debug_path)} "
                    f"--ae-env {double_quote('OLM_DG_DEBUG_POINTS=' + args.points)}"
                ),
            }
        )

    plan = {
        "kind": "olmdistancegradation_case0023_probe_plan",
        "case_id": CASE_ID,
        "request_dir": request_dir_rel,
        "debug_points_spec": args.points,
        "purpose": (
            "Differentiate Mac AE source alpha / mask / field-boundary ownership from 16bpc host output packing "
            "for the remaining 73px case_0023 residual."
        ),
        "suggested_runs": suggested_runs,
        "interpretation": [
            "Compare alpha/raw_inside/raw_outside/inside_x/outside_x/field_x at (1699,7) and (415,393) against refs/conformance/olmdistancegradation_case0023_source_model_audit_20260707.md.",
            "If bg_on and bg_off debug fields are identical but PNG deltas differ only at output, keep the investigation on host/source/output ownership.",
            "If debug alpha or raw distance changes between runs, the remaining seam is source-world or mask provenance before compose.",
        ],
        "forbidden_actions": [
            "Do not retune compose_pixel from this probe; the 2026-07-07 compose witness already excludes the triplet compose/writeback path.",
            "Do not retune Both-mode cv::add / saturating-add field merge while AEX CPU simu and the Mac source-model audit match the live witnesses.",
            "Do not revive the old packaged-stale explanation; packaged/current Windows references are exact in the 2026-07-07 audit.",
        ],
    }
    args.plan_json.parent.mkdir(parents=True, exist_ok=True)
    args.plan_json.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.plan_md.parent.mkdir(parents=True, exist_ok=True)
    args.plan_md.write_text(render_markdown(plan), encoding="utf-8")
    (out_dir / "OLMDG_CASE0023_PROBE_PLAN.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "OLMDG_CASE0023_PROBE_PLAN.md").write_text(render_markdown(plan), encoding="utf-8")
    print(f"request_dir={out_dir}")
    print(f"debug_points={args.points}")
    print(f"plan_json={args.plan_json}")
    print(f"plan_md={args.plan_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
