#!/usr/bin/env python3
"""Validate a returned Windows AE reference render result against a request JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="refs/reference_requests/*.json")
    parser.add_argument(
        "result",
        type=Path,
        help="Returned reference folder or reference_manifest.json",
    )
    parser.add_argument(
        "--allow-missing-optional-render-sets",
        action="store_true",
        help="Do not fail when optional render sets such as CUDA are absent.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def resolve_manifest(path: Path) -> Path:
    if path.is_dir():
        return path / "reference_manifest.json"
    return path


def nested_get(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def find_value(data: Any, key: str) -> Any:
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = find_value(value, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_value(value, key)
            if found is not None:
                return found
    return None


def effect_matches(request: dict[str, Any], manifest: dict[str, Any]) -> bool:
    expected = request.get("effect", {})
    if not isinstance(expected, dict):
        return True
    expected_names = {expected.get("name"), expected.get("match_name")} - {None, ""}
    if not expected_names:
        return True

    manifest_text = json.dumps(
        {
            "effect": manifest.get("effect"),
            "requests": manifest.get("requests"),
            "layer": manifest.get("layer"),
            "cases": [
                {
                    "effect": case.get("effect"),
                    "selected_effect": case.get("selected_effect"),
                    "selected_layer_effects": case.get("selected_layer_effects"),
                    "effects": case.get("effects"),
                }
                for case in manifest.get("cases", [])
                if isinstance(case, dict)
            ],
        },
        ensure_ascii=False,
    )
    return any(name in manifest_text for name in expected_names)


def case_request_id(case: dict[str, Any]) -> str | None:
    for key in ("request_case_id", "source_case_id", "id"):
        value = case.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def request_id_value(request: dict[str, Any]) -> str | None:
    value = request.get("request_id")
    return value if isinstance(value, str) and value else None


def case_matches_request(case: dict[str, Any], request: dict[str, Any], request_case_ids: set[str]) -> bool:
    req_id = request_id_value(request)
    case_req_id = case.get("request_id")
    if req_id and isinstance(case_req_id, str):
        return case_req_id == req_id
    case_id = case_request_id(case)
    return bool(case_id and case_id in request_case_ids)


def render_set_id(case: dict[str, Any], manifest: dict[str, Any]) -> str | None:
    for source in (case, manifest):
        for key in ("render_set", "render_set_id"):
            value = source.get(key) if isinstance(source, dict) else None
            if isinstance(value, str) and value:
                return value
        gpu = nested_get(source, "project_gpu_accel_type.current_name")
        if isinstance(gpu, str) and gpu:
            return gpu
        gpu = find_value(source, "project_gpu_accel_type")
        if isinstance(gpu, dict):
            current_name = gpu.get("current_name")
            if isinstance(current_name, str) and current_name:
                return current_name
    return None


def file_exists(root: Path, value: Any) -> bool:
    return isinstance(value, str) and bool(value) and (root / value).exists()


def case_is_required_render_set(
    case: dict[str, Any],
    manifest: dict[str, Any],
    expected_required_sets: list[set[str]],
) -> bool:
    if not expected_required_sets:
        return True
    observed = render_set_id(case, manifest)
    return bool(observed and any(observed in values for values in expected_required_sets))


def main() -> int:
    args = parse_args()
    request_path = args.request.resolve()
    manifest_path = resolve_manifest(args.result.resolve())
    root = manifest_path.parent

    if not request_path.exists():
        return fail(f"request not found: {request_path}")
    if not manifest_path.exists():
        return fail(f"reference_manifest.json not found: {manifest_path}")

    try:
        request = load_json(request_path)
        manifest = load_json(manifest_path)
    except Exception as exc:  # noqa: BLE001 - command-line validator should be direct.
        return fail(str(exc))

    request_cases = request.get("cases")
    manifest_cases = manifest.get("cases")
    if not isinstance(request_cases, list) or not request_cases:
        return fail("request has no cases")
    if not isinstance(manifest_cases, list) or not manifest_cases:
        return fail("result manifest has no cases")
    if not effect_matches(request, manifest):
        return fail("manifest does not appear to contain the requested effect")

    request_case_id_set = {
        case["id"]
        for case in request_cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    relevant_cases = [
        case
        for case in manifest_cases
        if isinstance(case, dict) and case_matches_request(case, request, request_case_id_set)
    ]
    if not relevant_cases:
        return fail("manifest has no cases for the requested request_id/case ids")

    by_request_case: dict[str, list[dict[str, Any]]] = {}
    for case in relevant_cases:
        if not isinstance(case, dict):
            return fail("manifest cases must be objects")
        case_id = case_request_id(case)
        if case_id:
            by_request_case.setdefault(case_id, []).append(case)

    required_case_ids = [
        case["id"]
        for case in request_cases
        if isinstance(case, dict) and isinstance(case.get("id"), str) and not case.get("optional")
    ]
    missing_cases = [case_id for case_id in required_case_ids if case_id not in by_request_case]
    if missing_cases:
        return fail(f"missing required request cases: {', '.join(missing_cases)}")

    render_sets = request.get("render_sets", [])
    expected_required_sets = []
    expected_optional_sets = []
    if isinstance(render_sets, list):
        for item in render_sets:
            if not isinstance(item, dict):
                continue
            label = item.get("id") or item.get("project_gpu_accel_type.current_name")
            gpu_name = item.get("project_gpu_accel_type.current_name")
            acceptable = {value for value in (label, gpu_name) if isinstance(value, str) and value}
            if item.get("required"):
                expected_required_sets.append(acceptable)
            elif not args.allow_missing_optional_render_sets:
                expected_optional_sets.append(acceptable)

    observed_render_sets = {
        value
        for case in relevant_cases
        if isinstance(case, dict)
        for value in [render_set_id(case, manifest)]
        if value
    }

    for acceptable in expected_required_sets + expected_optional_sets:
        if acceptable and not (acceptable & observed_render_sets):
            return fail(
                "missing render set: "
                + " or ".join(sorted(acceptable))
                + f" (observed: {', '.join(sorted(observed_render_sets)) or 'none'})"
            )

    missing_frames = []
    missing_before = []
    missing_gpu = []
    cases_to_check_files = relevant_cases
    if args.allow_missing_optional_render_sets:
        cases_to_check_files = [
            case
            for case in relevant_cases
            if case_is_required_render_set(case, manifest, expected_required_sets)
        ]

    for case in cases_to_check_files:
        if not isinstance(case, dict):
            continue
        case_id = case.get("id", case.get("request_case_id", "<unknown>"))
        if not file_exists(root, case.get("frame")):
            missing_frames.append(str(case_id))
        if not file_exists(root, case.get("before_effects_frame")):
            missing_before.append(str(case_id))
        if render_set_id(case, manifest) is None:
            missing_gpu.append(str(case_id))

    if missing_frames:
        return fail(f"missing output PNG files for cases: {', '.join(missing_frames[:12])}")
    if missing_before:
        return fail(f"missing before_effects_frame PNG files for cases: {', '.join(missing_before[:12])}")
    if missing_gpu:
        return fail(f"missing project_gpu_accel_type/render_set metadata for cases: {', '.join(missing_gpu[:12])}")

    print(
        f"[OK] {manifest_path}: {len(required_case_ids)} required request cases, "
        f"{len(relevant_cases)} matching rendered cases, render_sets={','.join(sorted(observed_render_sets))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
