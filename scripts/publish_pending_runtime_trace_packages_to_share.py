#!/usr/bin/env python3
"""Publish pending runtime trace packages to the shared Windows exchange folder."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--share-root",
        type=Path,
        default=Path("/Volumes/onmk/olm_pr"),
        help="Shared exchange root. Defaults to /Volumes/onmk/olm_pr",
    )
    parser.add_argument(
        "--pending-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "pending_runtime_trace_packages.json",
        help="Pending runtime trace package report JSON.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of pending packages to publish. 0 means all pending packages.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected packages without touching the share.",
    )
    return parser.parse_args()


def load_pending_rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("kind") != "pending_runtime_trace_packages":
        raise ValueError(f"unexpected pending-runtime JSON: {path}")
    rows = data.get("requests")
    if not isinstance(rows, list):
        raise ValueError(f"missing requests list in: {path}")
    pending = [row for row in rows if isinstance(row, dict) and row.get("status") == "pending"]
    pending.sort(key=lambda row: (int(row.get("priority") or 999999), str(row.get("request_id") or "")))
    return pending


def build_queue_readme(rows: list[dict], generated_at: str) -> str:
    lines = [
        "Pending runtime trace request queue",
        "",
        f"Generated at: {generated_at}",
        "",
        "Priority order:",
    ]
    for row in rows:
        lines.extend(
            [
                f"- [{row.get('priority')}] {row.get('request_id')}",
                f"  package: {Path(str(row.get('package') or '')).name}",
                f"  plugin area: {row.get('plugin_area') or ''}",
                f"  stop condition: {row.get('stop_condition') or ''}",
                "",
            ]
        )
    lines.extend(
        [
            "Mac-side intake after return:",
            "- python3 scripts/list_olm_return_candidates.py /Volumes/onmk/olm_pr/new ~/Downloads",
            "- python3 scripts/intake_latest_windows_return_from_share.py --share-root /Volumes/onmk/olm_pr",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    rows = load_pending_rows(args.pending_json)
    if args.limit > 0:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("no pending runtime trace packages to publish")

    packages: list[Path] = []
    for row in rows:
        package = root / str(row["package"])
        if not package.is_file():
            raise SystemExit(f"missing package: {package}")
        packages.append(package)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "share_root": str(args.share_root),
                    "count": len(rows),
                    "requests": rows,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    timestamp = subprocess.run(
        ["date", "+%Y%m%d_%H%M%S"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="olm_publish_pending_runtime_") as tmp:
        tmp_root = Path(tmp)
        readme = tmp_root / f"{timestamp}__olm_pending_runtime_trace_queue__README.txt"
        readme.write_text(build_queue_readme(rows, timestamp), encoding="utf-8")

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
        cmd = [str(root / "scripts" / "publish_windows_request_to_share.sh")]
        cmd.extend(str(package) for package in packages)
        cmd.append(str(readme))
        proc = subprocess.run(
            cmd,
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )
        print(proc.stdout.rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
