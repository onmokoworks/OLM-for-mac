#!/usr/bin/env python3
"""Validate and package Windows AE reference render requests.

The output zip is meant to be handed to the Windows machine/Codex session that
renders additional AE references. It contains the request README plus selected
JSON request specs, preserving paths under refs/reference_requests/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="REQUEST_JSON",
        help="Package only this request JSON basename or path. May be repeated.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to /tmp/olm_reference_requests_YYYYMMDD.zip.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_requests(request_dir: Path, only: list[str]) -> list[Path]:
    all_requests = sorted(request_dir.glob("*.json"))
    if not only:
        return all_requests

    selected: list[Path] = []
    by_name = {path.name: path for path in all_requests}
    by_stem = {path.stem: path for path in all_requests}
    for item in only:
        candidate = Path(item)
        if candidate.exists():
            selected.append(candidate.resolve())
        elif item in by_name:
            selected.append(by_name[item])
        elif item in by_stem:
            selected.append(by_stem[item])
        else:
            known = ", ".join(path.name for path in all_requests)
            raise SystemExit(f"unknown request {item!r}; known: {known}")

    return sorted(dict.fromkeys(selected))


def validate_request(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON must be an object")
    request_id = data.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("missing non-empty request_id")
    if not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("missing non-empty cases list")
    if not isinstance(data.get("manifest_requirements"), list):
        raise ValueError("missing manifest_requirements list")
    return data


def main() -> int:
    args = parse_args()
    root = repo_root()
    request_dir = root / "refs" / "reference_requests"
    requests = resolve_requests(request_dir, args.only)
    if not requests:
        print(f"no request JSON files found in {request_dir}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d")
        output = Path("/tmp") / f"olm_reference_requests_{stamp}.zip"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    validated: list[tuple[Path, dict]] = []
    for request in requests:
        try:
            validated.append((request, validate_request(request)))
        except Exception as exc:  # noqa: BLE001 - show path-specific validation error.
            print(f"invalid request {request}: {exc}", file=sys.stderr)
            return 1

    readme = request_dir / "README.md"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if readme.exists():
            zf.write(readme, readme.relative_to(root))
        for request, _data in validated:
            zf.write(request, request.relative_to(root))

    print(f"wrote {output}")
    for request, data in validated:
        print(f"- {request.name}: {data['request_id']} ({len(data['cases'])} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
