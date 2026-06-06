#!/usr/bin/env python3
"""Validate a Windows reference request package zip."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

from check_reference_request_status import load_status_rows


HANDOFF_NAME = "refs/reference_requests/WIN_CODEX_HANDOFF.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="zip produced by package_reference_requests.py")
    parser.add_argument(
        "--expect-pending",
        action="store_true",
        help="Require packaged request IDs to equal the current uncovered requests.",
    )
    parser.add_argument(
        "--requests",
        type=Path,
        default=Path("refs/reference_requests"),
        help="Request JSON directory used for --expect-pending.",
    )
    parser.add_argument(
        "--references",
        type=Path,
        default=Path("refs/win_references"),
        help="Imported Windows references used for --expect-pending.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json_bytes(name: str, data: bytes) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name}: top-level JSON must be an object")
    return value


def request_id_from_json(name: str, data: bytes) -> str:
    value = load_json_bytes(name, data)
    request_id = value.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError(f"{name}: missing non-empty request_id")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{name}: missing non-empty cases")
    return request_id


def packaged_request_ids(package: Path) -> list[str]:
    if not package.exists():
        raise ValueError(f"package not found: {package}")
    if not zipfile.is_zipfile(package):
        raise ValueError(f"not a zip file: {package}")
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        if HANDOFF_NAME not in names:
            raise ValueError(f"missing {HANDOFF_NAME}")
        request_names = sorted(
            name
            for name in names
            if name.startswith("refs/reference_requests/")
            and name.endswith(".json")
            and Path(name).name != "README.json"
        )
        if not request_names:
            raise ValueError("package contains no request JSON files")
        ids = [request_id_from_json(name, archive.read(name)) for name in request_names]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate request_id values in package")
    return sorted(ids)


def current_pending_ids(requests: Path, references: Path) -> list[str]:
    rows = load_status_rows(requests, references)
    return sorted(row["request_id"] for row in rows if row["status"] != "covered")


def main() -> int:
    args = parse_args()
    try:
        ids = packaged_request_ids(args.package.resolve())
        if args.expect_pending:
            expected = current_pending_ids(args.requests, args.references)
            if ids != expected:
                return fail(
                    "packaged requests do not match pending requests: "
                    f"packaged={ids} pending={expected}"
                )
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))

    print(f"[OK] {args.package}: {len(ids)} reference request(s)")
    for request_id in ids:
        print(f"- {request_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
