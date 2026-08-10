#!/usr/bin/env python3
"""Fail closed when a proposed public tree contains private analysis material."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PREFIXES = (
    "refs/upstream_official/",
    "refs/win_references/",
    "refs/windows_returns/",
    "refs/mac_validation_runs/",
    "refs/runtime_trace_support/",
)
PRIVATE_SUFFIXES = (".aex", ".dmp")
ABSOLUTE_PATH_PATTERNS = (
    re.compile(rb"/Users/[A-Za-z0-9._-]+/"),
    re.compile(rb"[A-Za-z]:\\Users\\[^\\\r\n]+\\"),
)
SECRET_PATTERNS = (
    ("private key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(rb"\bgh[opusr]_[A-Za-z0-9_]{30,}\b")),
    ("AWS access key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
)


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    return [p.decode("utf-8", "surrogateescape") for p in result.stdout.split(b"\0") if p]


def inspect_bytes(label: str, data: bytes, errors: list[str]) -> None:
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(data):
            errors.append(f"{label}: possible {name}")
    for pattern in ABSOLUTE_PATH_PATTERNS:
        if pattern.search(data):
            errors.append(f"{label}: workstation-specific absolute path")


def audit(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in tracked_files(root):
        normalized = PurePosixPath(rel).as_posix()
        path = root / rel
        if normalized.startswith(PRIVATE_PREFIXES):
            errors.append(f"{rel}: private evidence directory")
        if normalized.lower().endswith(PRIVATE_SUFFIXES):
            errors.append(f"{rel}: proprietary/private binary type")
        try:
            data = path.read_bytes()
        except (OSError, MemoryError) as exc:
            errors.append(f"{rel}: cannot inspect ({exc})")
            continue
        inspect_bytes(rel, data, errors)
        if zipfile.is_zipfile(path):
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        member_name = PurePosixPath(member.filename).as_posix()
                        if member_name.lower().endswith(PRIVATE_SUFFIXES):
                            errors.append(f"{rel}!{member_name}: private binary in archive")
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append(f"{rel}: cannot inspect zip ({exc})")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="report findings but exit successfully for the private analysis repo",
    )
    args = parser.parse_args()
    errors = audit(args.root.resolve())
    if errors:
        print(f"PUBLIC_AUDIT_FAIL findings={len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 0 if args.report_only else 1
    print("PUBLIC_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
