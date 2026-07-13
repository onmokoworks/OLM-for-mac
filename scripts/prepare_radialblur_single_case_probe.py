#!/usr/bin/env python3
"""Prepare a single-case OLMRadialBlur AE probe request."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DEFAULT_POINTS = {
    "case_0009": ";".join(f"{x},0" for x in range(32)),
    "case_0010": "1614,6;1613,6;1615,6;1614,5;1614,7;1610,6;1611,6;1612,6;1616,6;1617,6;1618,6",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur",
    )
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_single_radialblur_case_0009_probe_20260701",
    )
    parser.add_argument("--points", default=None)
    return parser.parse_args()


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


def main() -> int:
    args = parse_args()
    reference_dir = args.reference_dir.resolve()
    manifest = load_manifest(reference_dir / "reference_manifest.json")
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

    ref_copy = dict(manifest)
    ref_copy["cases"] = [case]
    project = dict(ref_copy.get("project") or {})
    if "bits_per_channel" not in project:
        project["bits_per_channel"] = 8
    ref_copy["project"] = project
    (out_dir / "reference_manifest.json").write_text(
        json.dumps(ref_copy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    effect = case["effects"][0]
    request_manifest = {
        "kind": "olm_ae_pixel_validation_request",
        "request_id": f"ae_single_radialblur_{args.case_id}_probe_20260701",
        "created_at": "2026-07-01T00:00:00Z",
        "reference_manifest": "reference_manifest.json",
        "reference_profile": "windows-software-single-case",
        "effect_name": effect["name"],
        "effect_match_name": effect["match_name"],
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
            "Single-case OLMRadialBlur probe request.",
            "Use with run_ae_single_case.py and OLMRADIALBLUR_DEBUG_POINTS.",
        ],
    }
    (out_dir / "request_manifest.json").write_text(
        json.dumps(request_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    points = args.points or DEFAULT_POINTS.get(args.case_id, "")
    plan = {
        "kind": "olmradialblur_single_case_probe_plan",
        "reference_dir": str(reference_dir),
        "request_dir": str(out_dir),
        "case_id": args.case_id,
        "debug_points_spec": points,
        "suggested_run_command": (
            "python3 scripts/run_ae_single_case.py "
            f"--request-dir {out_dir} --case-id {args.case_id} "
            f"--output-dir /tmp/{args.case_id}_radialblur_probe_20260701 "
            f"--ae-env OLMRADIALBLUR_DEBUG_DUMP_PATH=/tmp/{args.case_id}_radialblur_probe_20260701/radialblur_debug.log "
            f"--ae-env OLMRADIALBLUR_DEBUG_POINTS={points}"
        ),
        "suggested_analysis_command": (
            "python3 scripts/analyze_radialblur_debug_points.py "
            f"/tmp/{args.case_id}_radialblur_probe_20260701/radialblur_debug.log "
            f"--output-json {out_dir / 'radialblur_debug_points.json'} "
            f"--output-md {out_dir / 'radialblur_debug_points.md'}"
        ),
    }
    (out_dir / "OLMRADIALBLUR_PROBE_PLAN.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"request_dir={out_dir}")
    print(f"debug_points={points}")
    print(f"plan_json={out_dir / 'OLMRADIALBLUR_PROBE_PLAN.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
