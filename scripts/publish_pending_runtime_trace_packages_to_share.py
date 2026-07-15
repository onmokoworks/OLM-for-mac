#!/usr/bin/env python3
"""Publish pending runtime trace packages to the shared Windows exchange folder."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import list_olm_return_candidates


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


def build_queue_readme(rows: list[dict], generated_at: str, *, return_scan_root: str) -> str:
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
            "Mac-side intake after return (replace <olm_pr> with the mounted exchange root):",
            f"- python3 scripts/list_olm_return_candidates.py {return_scan_root} ~/Downloads",
            "- python3 scripts/intake_latest_windows_return_from_share.py --share-root <olm_pr>",
            "",
        ]
    )
    return "\n".join(lines)


def archive_existing_files(source_dir: Path, old_dir: Path, timestamp: str) -> list[Path]:
    old_dir.mkdir(parents=True, exist_ok=True)
    archived: list[Path] = []
    for existing in sorted(source_dir.iterdir()):
        if not existing.is_file():
            continue
        target = old_dir / f"{timestamp}__{existing.name}"
        suffix = 2
        while target.exists():
            target = old_dir / f"{timestamp}__{suffix}__{existing.name}"
            suffix += 1
        shutil.move(str(existing), str(target))
        archived.append(target)
    return archived


def publish_files(files: list[Path], destination_dir: Path) -> list[Path]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    published: list[Path] = []
    for src in files:
        if not src.is_file():
            raise SystemExit(f"missing file: {src}")
        dest = destination_dir / src.name
        shutil.copy2(src, dest)
        published.append(dest)
    return published


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
    request_dir = list_olm_return_candidates.exchange_request_dir(args.share_root)
    return_label = list_olm_return_candidates.exchange_return_label(args.share_root)

    with tempfile.TemporaryDirectory(prefix="olm_publish_pending_runtime_") as tmp:
        tmp_root = Path(tmp)
        readme = tmp_root / f"{timestamp}__olm_pending_runtime_trace_queue__README.txt"
        readme.write_text(build_queue_readme(rows, timestamp, return_scan_root=return_label), encoding="utf-8")
        archived = archive_existing_files(request_dir, args.share_root / "old", timestamp)
        published = publish_files([*packages, readme], request_dir)
        for archived_path in archived:
            print(f"[INFO] archived old file: {archived_path}")
        for published_path in published:
            print(f"[OK] published: {published_path}")
        print("")
        print("Share state:")
        print(f"- new: {request_dir}")
        print(f"- old: {args.share_root / 'old'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
