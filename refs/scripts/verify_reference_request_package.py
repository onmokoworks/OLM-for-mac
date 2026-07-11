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
REQUIRED_32BPC_COMPARE_POLICY_PATH = "refs/conformance/bitdepth_32bpc_compare_policy_20260703.md"


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
    validate_request_contract(name, value)
    return request_id


def validate_request_contract(name: str, value: dict[str, Any]) -> None:
    request_id = value.get("request_id")
    scope = value.get("scope")
    if not isinstance(scope, dict):
        if isinstance(request_id, str) and request_id.startswith("olm_bitdepth_"):
            raise ValueError(f"{name}: missing scope object")
        return
    bit_depth = scope.get("bit_depth")
    if bit_depth not in {"16bpc", "32bpc"}:
        if isinstance(request_id, str) and request_id.startswith("olm_bitdepth_"):
            raise ValueError(f"{name}: unexpected scope.bit_depth={bit_depth!r}")
        return

    compare_policy = value.get("compare_policy")
    if not isinstance(compare_policy, dict):
        raise ValueError(f"{name}: missing compare_policy object")

    output_requirements = value.get("output_requirements")
    if not isinstance(output_requirements, dict):
        raise ValueError(f"{name}: missing output_requirements object")

    preferred_formats = output_requirements.get("preferred_formats")
    if not isinstance(preferred_formats, list) or not all(isinstance(item, str) and item for item in preferred_formats):
        raise ValueError(f"{name}: output_requirements.preferred_formats must be a non-empty string list")

    record_exact_format_used = output_requirements.get("record_exact_format_used")
    if not isinstance(record_exact_format_used, bool) or not record_exact_format_used:
        raise ValueError(f"{name}: output_requirements.record_exact_format_used must be true")

    if bit_depth == "32bpc":
        if compare_policy.get("path") != REQUIRED_32BPC_COMPARE_POLICY_PATH:
            raise ValueError(
                f"{name}: compare_policy.path must be {REQUIRED_32BPC_COMPARE_POLICY_PATH!r} for 32bpc"
            )
        if compare_policy.get("mode") != "float-preserving-required":
            raise ValueError(f"{name}: compare_policy.mode must be 'float-preserving-required' for 32bpc")
        if compare_policy.get("png_only_classification") != "probe-only":
            raise ValueError(f"{name}: compare_policy.png_only_classification must be 'probe-only' for 32bpc")
        if preferred_formats != ["exr"]:
            raise ValueError(f"{name}: output_requirements.preferred_formats must be ['exr'] for 32bpc")
        if output_requirements.get("png_only_classification") != "probe-only":
            raise ValueError(f"{name}: output_requirements.png_only_classification must be 'probe-only' for 32bpc")
        if output_requirements.get("float_preserving_required_for_ae_exact") is not True:
            raise ValueError(
                f"{name}: output_requirements.float_preserving_required_for_ae_exact must be true for 32bpc"
            )
    else:
        if compare_policy.get("mode") != "bitdepth-aware-integer-exact":
            raise ValueError(f"{name}: compare_policy.mode must be 'bitdepth-aware-integer-exact' for 16bpc")
        if preferred_formats != ["png"]:
            raise ValueError(f"{name}: output_requirements.preferred_formats must be ['png'] for 16bpc")
        if output_requirements.get("float_preserving_required_for_ae_exact") is not False:
            raise ValueError(
                f"{name}: output_requirements.float_preserving_required_for_ae_exact must be false for 16bpc"
            )


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
