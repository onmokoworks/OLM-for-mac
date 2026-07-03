#!/usr/bin/env python3
"""Prepare a single-case OLMKiraKira AE probe request and optional neighborhood plan."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=root / "refs" / "win_references" / "olm_reference_return_windows_20260614" / "OLMKiraKira",
    )
    parser.add_argument(
        "--case-id",
        default="kk_vertical_len50_brightness1_strength100",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_single_kirakira_hotspot_probe_20260701",
    )
    parser.add_argument("--center", default="934,118")
    parser.add_argument("--radius", type=int, default=1)
    parser.add_argument("--windows-target-u8", type=int, default=131)
    parser.add_argument("--bits-per-channel", type=int, default=8)
    return parser.parse_args()


def parse_xy(text: str) -> tuple[int, int]:
    x, y = text.split(",", 1)
    return int(x), int(y)


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    return data


def find_case(manifest: dict, case_id: str) -> dict:
    for case in manifest.get("cases", []):
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    raise KeyError(f"case not found: {case_id}")


def point_spec(center: tuple[int, int], radius: int) -> str:
    cx, cy = center
    parts = []
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            parts.append(f"{x},{y}")
    return ";".join(parts)


def main() -> int:
    args = parse_args()
    reference_dir = args.reference_dir.resolve()
    manifest_path = reference_dir / "reference_manifest.json"
    manifest = load_manifest(manifest_path)
    case = find_case(manifest, args.case_id)
    out_dir = args.output_dir.resolve()
    input_dir = out_dir / "input"
    expected_dir = out_dir / "expected"
    input_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

    before_name = case["before_effects_frame"]
    frame_name = case["frame"]
    shutil.copy2(reference_dir / before_name, input_dir / before_name)
    shutil.copy2(reference_dir / frame_name, expected_dir / frame_name)

    filtered_manifest = dict(manifest)
    project_meta = dict(filtered_manifest.get("project") or {})
    project_meta["bits_per_channel"] = int(args.bits_per_channel)
    filtered_manifest["project"] = project_meta
    filtered_manifest["cases"] = [case]
    (out_dir / "reference_manifest.json").write_text(
        json.dumps(filtered_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    request_manifest = {
        "kind": "olm_ae_pixel_validation_request",
        "request_id": f"ae_single_{args.case_id}",
        "created_at": "2026-07-01T00:00:00Z",
        "reference_manifest": "reference_manifest.json",
        "reference_profile": "windows-software-single-case",
        "effect_name": case["effects"][0]["name"],
        "effect_match_name": case["effects"][0]["match_name"],
        "input_dir": "input",
        "expected_dir": "expected",
        "candidate_dir_hint": "candidate",
        "gate_kind": "host_smoke_pixel_tolerance",
        "cases": [
            {
                "id": case["id"],
                "before_effects_frame": before_name,
                "frame": frame_name,
            }
        ],
        "threshold_groups": [
            {
                "name": "single_case_exact",
                "case_ids": [case["id"]],
                "max_diff": 0,
                "mean_diff": 0.0,
                "nonzero_px_percent": 0.0,
            }
        ],
        "notes": [
            "Single-case KiraKira hotspot probe request.",
            "Use with run_ae_single_case.py and OLMKIRAKIRA_DEBUG_POINTS.",
        ],
    }
    (out_dir / "request_manifest.json").write_text(
        json.dumps(request_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    center = parse_xy(args.center)
    spec = point_spec(center, args.radius)
    plan = {
        "kind": "olmkirakira_hotspot_probe_plan",
        "reference_dir": str(reference_dir),
        "request_dir": str(out_dir),
        "case_id": args.case_id,
        "center_xy": list(center),
        "radius": args.radius,
        "windows_target_u8": args.windows_target_u8,
        "debug_points_spec": spec,
        "suggested_run_command": (
            "python3 scripts/run_ae_single_case.py "
            f"--request-dir {out_dir} --case-id {args.case_id} "
            f"--ae-env OLMKIRAKIRA_DEBUG_DUMP_PATH={out_dir / 'kirakira_debug.log'} "
            f"--ae-env OLMKIRAKIRA_DEBUG_POINTS={spec}"
        ),
        "suggested_analysis_command": (
            "python3 scripts/analyze_kirakira_compose_debug_neighborhood.py "
            f"--debug-log {out_dir / 'kirakira_debug.log'} "
            f"--center {center[0]},{center[1]} --radius {args.radius} "
            f"--windows-target-u8 {args.windows_target_u8} "
            f"--output-json {out_dir / 'kirakira_neighborhood.json'} "
            f"--output-md {out_dir / 'kirakira_neighborhood.md'}"
        ),
    }
    (out_dir / "KIRAKIRA_HOTSPOT_PROBE_PLAN.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"request_dir={out_dir}")
    print(f"debug_points={spec}")
    print(f"plan_json={out_dir / 'KIRAKIRA_HOTSPOT_PROBE_PLAN.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
