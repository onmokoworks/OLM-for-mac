#!/usr/bin/env python3
"""Report whether pending Windows reference requests have matching returned refs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from verify_reference_request_result import (
    case_is_required_render_set,
    case_matches_request,
    case_request_id,
    effect_matches,
    file_exists,
    load_json,
    render_set_id,
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
    return parser.parse_args()


def required_case_ids(request: dict[str, Any]) -> list[str]:
    return [
        case["id"]
        for case in request.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("id"), str) and not case.get("optional")
    ]


def expected_required_sets(request: dict[str, Any]) -> list[set[str]]:
    expected = []
    for item in request.get("render_sets", []):
        if not isinstance(item, dict) or not item.get("required"):
            continue
        label = item.get("id")
        gpu_name = item.get("project_gpu_accel_type.current_name")
        values = {value for value in (label, gpu_name) if isinstance(value, str) and value}
        if values:
            expected.append(values)
    return expected


def derive_source_case_id(case: dict[str, Any]) -> str | None:
    source_case_id = case.get("source_case_id")
    if isinstance(source_case_id, str) and source_case_id:
        return source_case_id
    case_id = case.get("id")
    if not isinstance(case_id, str):
        return None
    match = re.search(r"(?:case_|existing_)(\d{4})", case_id)
    if not match:
        return None
    return f"case_{match.group(1)}"


def count_params_full_cases(request: dict[str, Any]) -> int:
    return sum(
        1
        for case in request.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("params_full"), list) and len(case["params_full"]) > 0
    )


def count_linked_cases(request: dict[str, Any]) -> int:
    return sum(
        1
        for case in request.get("cases", [])
        if isinstance(case, dict) and derive_source_case_id(case)
    )


def package_time_pinning_summary(request_path: Path) -> dict[str, Any]:
    request = load_json(request_path)
    total_cases = len([case for case in request.get("cases", []) if isinstance(case, dict)])
    linked_cases = count_linked_cases(request)
    current_full = count_params_full_cases(request)
    packaged_full = current_full

    materializer = request_path.parents[2] / "scripts" / "materialize_linked_request_params.py"
    # Fast paths:
    # - no linked/source-backed cases means packaging cannot add params_full
    # - already fully pinned means a staging materialization would be redundant
    if linked_cases == 0 or current_full == total_cases or total_cases == 0:
        packaged_full = current_full
    elif materializer.exists():
        with tempfile.TemporaryDirectory(prefix="olm_request_pincheck_") as tmp_dir:
            staged = Path(tmp_dir) / request_path.name
            shutil.copy2(request_path, staged)
            subprocess.run(
                [sys.executable, str(materializer), "--write", str(staged)],
                cwd=request_path.parents[2],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            packaged = load_json(staged)
            packaged_full = count_params_full_cases(packaged)

    return {
        "total_cases": total_cases,
        "linked_cases": linked_cases,
        "current_params_full_cases": current_full,
        "packaged_params_full_cases": packaged_full,
        "current_fully_pinned": current_full == total_cases and total_cases > 0,
        "packaged_fully_pinned": packaged_full == total_cases and total_cases > 0,
    }


def relevant_manifest_cases(request: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    req_cases = set(required_case_ids(request))
    return [
        case
        for case in manifest.get("cases", [])
        if isinstance(case, dict) and case_matches_request(case, request, req_cases)
    ]


def manifest_case_ids(cases: list[dict[str, Any]]) -> set[str]:
    return {
        case_id
        for case in cases
        for case_id in [case_request_id(case)]
        if case_id
    }


def manifest_render_sets(cases: list[dict[str, Any]], manifest: dict[str, Any]) -> set[str]:
    return {
        render_set
        for case in cases
        for render_set in [render_set_id(case, manifest)]
        if render_set
    }


def manifest_files_ok(
    manifest_path: Path,
    manifest: dict[str, Any],
    cases: list[dict[str, Any]],
    required_sets: list[set[str]],
) -> bool:
    root = manifest_path.parent
    check_cases = [
        case
        for case in cases
        if case_is_required_render_set(case, manifest, required_sets)
    ]
    for case in check_cases:
        if not file_exists(root, case.get("frame")):
            return False
        if not file_exists(root, case.get("before_effects_frame")):
            return False
    return True


def score_request(
    request: dict[str, Any],
    manifests: list[tuple[Path, dict[str, Any]]],
    *,
    request_path: Path | None = None,
) -> dict[str, Any]:
    req_cases = set(required_case_ids(request))
    req_sets = expected_required_sets(request)
    candidates = []
    for manifest_path, manifest in manifests:
        if not effect_matches(request, manifest):
            continue
        relevant_cases = relevant_manifest_cases(request, manifest)
        if not relevant_cases:
            continue
        found_cases = manifest_case_ids(relevant_cases)
        found_sets = manifest_render_sets(relevant_cases, manifest)
        missing_cases = sorted(req_cases - found_cases)
        missing_sets = [
            sorted(values)
            for values in req_sets
            if values and not (values & found_sets)
        ]
        files_ok = manifest_files_ok(manifest_path, manifest, relevant_cases, req_sets)
        complete = not missing_cases and not missing_sets and files_ok
        candidates.append(
            {
                "manifest": str(manifest_path),
                "complete": complete,
                "matched_cases": len(req_cases & found_cases),
                "required_cases": len(req_cases),
                "missing_cases": missing_cases,
                "observed_render_sets": sorted(found_sets),
                "missing_render_sets": missing_sets,
                "files_ok": files_ok,
            }
        )

    complete = [candidate for candidate in candidates if candidate["complete"]]
    if complete:
        status = "covered"
        best = complete[0]
    elif candidates:
        status = "partial"
        best = max(candidates, key=lambda item: item["matched_cases"])
    else:
        status = "pending"
        best = None

    row = {
        "request_id": request["request_id"],
        "effect": request.get("effect", {}).get("name", ""),
        "required_cases": len(req_cases),
        "status": status,
        "best": best,
    }
    if request_path is not None:
        row["request_file"] = str(request_path)
        row["pinning"] = package_time_pinning_summary(request_path)
    return row


def load_status_rows(request_dir: Path, reference_dir: Path) -> list[dict[str, Any]]:
    request_paths = sorted(request_dir.glob("*.json"))
    manifest_paths = sorted(reference_dir.glob("**/reference_manifest.json"))
    manifests = [(path, load_json(path)) for path in manifest_paths]
    return [score_request(load_json(path), manifests, request_path=path) for path in request_paths]


def main() -> int:
    args = parse_args()
    rows = load_status_rows(args.requests, args.references)

    if args.json:
        print(json.dumps({"requests": rows}, indent=2, sort_keys=True))
        return 0

    print("reference request status")
    for row in rows:
        best = row["best"] or {}
        detail = ""
        if row["status"] == "covered":
            detail = f" -> {best.get('manifest')}"
        elif row["status"] == "partial":
            detail = (
                f" -> {best.get('matched_cases', 0)}/{row['required_cases']} cases, "
                f"missing render sets={best.get('missing_render_sets', [])}"
            )
        pinning = row.get("pinning") or {}
        if pinning:
            detail += (
                f" | pinning current={pinning.get('current_params_full_cases', 0)}/{pinning.get('total_cases', 0)} "
                f"packaged={pinning.get('packaged_params_full_cases', 0)}/{pinning.get('total_cases', 0)}"
            )
        print(
            f"- {row['request_id']}: {row['status']} "
            f"({row['required_cases']} required cases, {row['effect']}){detail}"
        )

    pending = [row["request_id"] for row in rows if row["status"] != "covered"]
    if pending:
        print("\npending package command:")
        print("python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
