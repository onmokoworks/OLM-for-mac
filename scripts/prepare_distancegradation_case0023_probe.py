#!/usr/bin/env python3
"""Prepare a single-case OLMDistanceGradation case_0023 AE probe request."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


CASE_ID = "olmdistancegradation_extended__case_0023"
DEFAULT_POINTS = "1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request-dir",
        type=Path,
        default=root / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "handoff" / "ae_pixel_validation_20260618" / "requests" / "ae_single_distancegradation_case0023_probe_20260701",
    )
    parser.add_argument("--points", default=DEFAULT_POINTS)
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


def main() -> int:
    args = parse_args()
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
    req_copy["request_id"] = "ae_single_distancegradation_case0023_probe_20260701"
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
        "Use with run_ae_single_case.py and OLM_DG_DEBUG_POINTS.",
    ]
    (out_dir / "request_manifest.json").write_text(
        json.dumps(req_copy, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    plan = {
        "kind": "olmdistancegradation_case0023_probe_plan",
        "case_id": CASE_ID,
        "request_dir": str(out_dir),
        "debug_points_spec": args.points,
        "suggested_run_command": (
            "python3 scripts/run_ae_single_case.py "
            f"--request-dir {out_dir} --case-id {CASE_ID} "
            f"--output-dir /tmp/olmdg_case0023_probe_20260701 "
            f"--ae-env OLM_DG_DEBUG_DUMP_PATH=/tmp/olmdg_case0023_probe_20260701/field_debug.txt "
            f"--ae-env OLM_DG_DEBUG_POINTS={args.points}"
        ),
    }
    (out_dir / "OLMDG_CASE0023_PROBE_PLAN.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"request_dir={out_dir}")
    print(f"debug_points={args.points}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
