#!/usr/bin/env python3
"""Publish a staged Windows exchange directory to the mounted share."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_staging_dir(root: Path) -> Path | None:
    staging_root = root / "refs" / "share_staging"
    if not staging_root.is_dir():
        return None
    candidates = [path for path in staging_root.iterdir() if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--staging-dir",
        type=Path,
        default=default_staging_dir(root),
        help="Staged handoff directory to publish. Defaults to the newest refs/share_staging/* directory.",
    )
    parser.add_argument(
        "--share-root",
        type=Path,
        default=Path("/Volumes/onmk/olm_pr"),
        help="Mounted Windows exchange root. Defaults to /Volumes/onmk/olm_pr",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the files that would be published without touching the share.",
    )
    return parser.parse_args()


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def staged_files(staging_dir: Path) -> list[Path]:
    files = [path for path in staging_dir.iterdir() if path.is_file()]
    files.sort(key=lambda path: (path.suffix.lower() != ".zip", path.name))
    return files


def main() -> int:
    args = parse_args()
    root = repo_root()
    staging_dir = args.staging_dir
    if staging_dir is None:
        raise SystemExit("no staging directory found under refs/share_staging")
    if not staging_dir.is_dir():
        raise SystemExit(f"staging directory not found: {staging_dir}")

    files = staged_files(staging_dir)
    if not files:
        raise SystemExit(f"staging directory is empty: {staging_dir}")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "share_root": str(args.share_root),
                    "staging_dir": display_path(root, staging_dir),
                    "files": [display_path(root, path) for path in files],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if not args.share_root.is_dir():
        raise SystemExit(
            f"share root not available: {args.share_root}\n"
            f"staged files remain in: {display_path(root, staging_dir)}"
        )

    env = os.environ.copy()
    env["OLM_PR_SHARE_ROOT"] = str(args.share_root)
    path_entries = [
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
        "/opt/homebrew/bin",
        str(Path.home() / ".local/bin"),
    ]
    env["PATH"] = ":".join(path_entries)
    proc = subprocess.run(
        [str(root / "scripts" / "publish_windows_request_to_share.sh"), *[str(path) for path in files]],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    print(proc.stdout.rstrip())
    print(f"[OK] synced staging directory: {display_path(root, staging_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
