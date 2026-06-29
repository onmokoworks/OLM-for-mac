#!/usr/bin/env python3
"""Package a focused Windows action bundle and publish it to the share."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--focus",
        choices=["smoother-priority", "blur-kirakira", "pending-runtime", "priority4-runtime", "secondary-runtime"],
        required=True,
        help="Bundle focus to package and publish.",
    )
    parser.add_argument(
        "--share-root",
        type=Path,
        default=Path("/Volumes/onmk/olm_pr"),
        help="Shared exchange root. Defaults to /Volumes/onmk/olm_pr",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only package locally and print the publish command.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()

    package_proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "package_windows_action_bundle.py"),
            "--focus",
            args.focus,
        ],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(package_proc.stdout, end="" if package_proc.stdout.endswith("\n") else "\n")

    output_path: Path | None = None
    for line in package_proc.stdout.splitlines():
        prefix = "[OK] Windows action bundle: "
        if line.startswith(prefix):
            output_path = Path(line[len(prefix):].strip())
            break
    if output_path is None or not output_path.is_file():
        raise SystemExit("failed to determine packaged bundle path")

    publish_cmd = [
        str(root / "scripts" / "publish_windows_request_to_share.sh"),
        str(output_path),
    ]
    if args.dry_run:
        print("[DRY-RUN] publish command:")
        print(" ".join(shlex.quote(part) for part in publish_cmd))
        return 0

    env = dict(os.environ)
    env["OLM_PR_SHARE_ROOT"] = str(args.share_root)
    publish_proc = subprocess.run(
        publish_cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    print(publish_proc.stdout, end="" if publish_proc.stdout.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
