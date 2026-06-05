#!/usr/bin/env python3
"""Validate an AE host validation result JSON returned from a Mac plug-in test."""

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
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def require_bool_or_null(value: object, field: str, allow_incomplete: bool) -> bool:
    if isinstance(value, bool):
        return True
    return allow_incomplete and value is None


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.result.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - command-line validator should show exact failure.
        return fail(f"could not read JSON: {exc}")

    if data.get("kind") != "olm_ae_host_validation_result":
        return fail("kind must be 'olm_ae_host_validation_result'")

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
        if not isinstance(entry.get("returned_artifacts", []), list):
            return fail(f"{name}.returned_artifacts must be a list")

    missing = [name for name in EXPECTED_PLUGINS if name not in by_name]
    extra = [name for name in by_name if name not in EXPECTED_PLUGINS]
    if missing:
        return fail(f"missing plugin entries: {', '.join(missing)}")
    if extra:
        return fail(f"unknown plugin entries: {', '.join(extra)}")

    if not args.allow_incomplete:
        failed = [
            name
            for name, entry in by_name.items()
            if not (entry["loaded"] and entry["applied"] and entry["render_succeeded"])
        ]
        if failed:
            return fail(f"plugins not fully passing load/apply/render: {', '.join(failed)}")

    print(f"[OK] {args.result}: {len(plugins)} plugin validation entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
