#!/usr/bin/env python3
"""Validate an AE host validation result JSON returned from a Mac plug-in test.

By default this checks that a completed AE-host result is well-formed and
actionable, even if one or more plug-ins failed on the host. Add
--require-all-pass when the command should be a release gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


EXPECTED_PLUGINS = [
    "ColorKeep",
    "OLMBlur",
    "OLMColorKey",
    "OLMDirectionalBlur",
    "OLMRadialBlur",
    "OLMKiraKira",
    "OLMToonDilate",
    "OLMDistanceGradation",
    "OLMSmoother",
    "OLMSmoother2",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="AE_VALIDATION_RESULT JSON file")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Accept null per-plugin booleans while checking schema and names.",
    )
    parser.add_argument(
        "--require-all-pass",
        action="store_true",
        help="Fail if any plug-in did not load, apply, and render successfully.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def require_bool_or_null(value: object, field: str, allow_incomplete: bool) -> bool:
    if isinstance(value, bool):
        return True
    return allow_incomplete and value is None


def require_string(data: dict, field: str, allow_empty: bool) -> str | None:
    value = data.get(field)
    if not isinstance(value, str):
        return f"{field} must be a string"
    if not allow_empty and not value:
        return f"{field} must be non-empty"
    return None


def require_top_level_metadata(data: dict, allow_incomplete: bool) -> str | None:
    for field in ("package_configuration", "ae_version", "macos_version", "machine", "install_path", "notes"):
        problem = require_string(data, field, allow_incomplete or field == "notes")
        if problem:
            return problem

    gpu = data.get("project_gpu_accel_type")
    if not isinstance(gpu, dict):
        return "project_gpu_accel_type must be an object"
    problem = require_string(gpu, "current_name", allow_incomplete)
    if problem:
        return f"project_gpu_accel_type.{problem}"
    raw = gpu.get("raw")
    if not (isinstance(raw, int) or (allow_incomplete and raw is None)):
        return "project_gpu_accel_type.raw must be an integer"

    clean = data.get("clean_ae_launch_after_install")
    if not require_bool_or_null(clean, "clean_ae_launch_after_install", allow_incomplete):
        return "clean_ae_launch_after_install must be boolean"
    return None


def artifact_entries_ok(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(isinstance(item, (str, dict)) for item in value)


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.result.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - command-line validator should show exact failure.
        return fail(f"could not read JSON: {exc}")

    if data.get("kind") != "olm_ae_host_validation_result":
        return fail("kind must be 'olm_ae_host_validation_result'")

    metadata_problem = require_top_level_metadata(data, args.allow_incomplete)
    if metadata_problem:
        return fail(metadata_problem)

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        return fail("plugins must be a list")

    by_name = {}
    for entry in plugins:
        if not isinstance(entry, dict):
            return fail("each plugin entry must be an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            return fail("each plugin entry needs a non-empty name")
        if name in by_name:
            return fail(f"duplicate plugin entry: {name}")
        by_name[name] = entry

        for field in ("loaded", "applied", "render_succeeded"):
            if not require_bool_or_null(entry.get(field), field, args.allow_incomplete):
                return fail(f"{name}.{field} must be boolean")
        for field in ("effect_menu_name", "error"):
            problem = require_string(entry, field, True)
            if problem:
                return fail(f"{name}.{problem}")
        if not artifact_entries_ok(entry.get("returned_artifacts", [])):
            return fail(f"{name}.returned_artifacts must be a list of strings or objects")

    missing = [name for name in EXPECTED_PLUGINS if name not in by_name]
    extra = [name for name in by_name if name not in EXPECTED_PLUGINS]
    if missing:
        return fail(f"missing plugin entries: {', '.join(missing)}")
    if extra:
        return fail(f"unknown plugin entries: {', '.join(extra)}")

    incomplete = [
        name
        for name, entry in by_name.items()
        if any(entry[field] is None for field in ("loaded", "applied", "render_succeeded"))
    ]
    failed = [
        name
        for name, entry in by_name.items()
        if any(entry[field] is False for field in ("loaded", "applied", "render_succeeded"))
    ]
    if failed and not args.allow_incomplete:
        for name in failed:
            entry = by_name[name]
            if not entry.get("error") and not entry.get("returned_artifacts"):
                return fail(f"{name} failed validation but has no error or returned_artifacts")

    not_passing = failed + incomplete
    if not_passing and args.require_all_pass:
        return fail(f"plugins not fully passing load/apply/render: {', '.join(not_passing)}")

    print(f"[OK] {args.result}: {len(plugins)} plugin validation entries")
    if failed:
        print(f"[WARN] plugins not fully passing load/apply/render: {', '.join(failed)}")
    if incomplete:
        print(f"[INFO] incomplete plugin validation entries: {', '.join(incomplete)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
