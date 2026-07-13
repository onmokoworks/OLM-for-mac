#!/usr/bin/env python3
"""Materialize the project-local Windows Send First staging directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PENDING = ROOT / "refs" / "reports" / "pending_runtime_trace_packages.json"
DEFAULT_STAGING_DIR = ROOT / "refs" / "share_staging" / "20260707_windows_send_first"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pending-json", type=Path, default=DEFAULT_PENDING)
    parser.add_argument("--staging-dir", type=Path, default=DEFAULT_STAGING_DIR)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pending(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def pending_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("requests")
    if not isinstance(rows, list):
        return []
    pending = [row for row in rows if isinstance(row, dict) and row.get("status") == "pending"]
    pending.sort(key=lambda row: (int(row.get("priority") or 999999), str(row.get("request_id") or "")))
    return pending


def clean_staging_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_file():
            child.unlink()


def build_readme(row: dict[str, Any], package_path: Path, package_hash: str) -> str:
    request_id = str(row.get("request_id") or "")
    context_value = row.get("hard_lane_context")
    if isinstance(context_value, dict):
        context = str(context_value.get("summary") or "")
        hard_note = str(context_value.get("note") or row.get("hard_lane_note") or "")
    else:
        context = str(context_value or "")
        hard_note = str(row.get("hard_lane_note") or "")
    acceptance = str(row.get("acceptance_note") or "")
    stop_condition = str(row.get("stop_condition") or "")
    why = str(row.get("why_needed") or row.get("plugin_area") or "")
    lines = [
        "# Windows Send First",
        "",
        "The authoritative selector is:",
        "",
        "```bash",
        "python3 scripts/print_next_olm_action.py ~/Downloads /tmp",
        "```",
        "",
        "This project-local staging folder is generated from",
        "`refs/reports/pending_runtime_trace_packages.json`.",
        "",
        "## Package",
        "",
        f"- Request: `{request_id}`",
        f"- File: `{package_path.name}`",
        f"- Source: `{package_path.as_posix()}`",
        f"- SHA-256: `{package_hash}`",
        "",
        "## Why This One",
        "",
        f"- {why}",
    ]
    if context:
        lines.extend(["", "## Hard Lane Context", "", context])
    if hard_note:
        lines.extend(["", "## Evidence Note", "", f"- `{hard_note}`"])
    if acceptance:
        lines.extend(["", "## Acceptance", "", f"- `{acceptance}`"])
    if stop_condition:
        lines.extend(["", "## Stop Condition", "", stop_condition])
    lines.extend(
        [
            "",
            "## Share Check",
            "",
            "```bash",
            f"test -f /Volumes/onmk/olm_pr/new/{package_path.name} \\",
            f"  && shasum -a 256 /Volumes/onmk/olm_pr/new/{package_path.name}",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    pending_path = args.pending_json if args.pending_json.is_absolute() else ROOT / args.pending_json
    staging_dir = args.staging_dir if args.staging_dir.is_absolute() else ROOT / args.staging_dir
    data = load_pending(pending_path)
    rows = pending_rows(data)
    clean_staging_dir(staging_dir)
    if not rows:
        (staging_dir / "README.md").write_text(
            "# Windows Send First\n\nNo pending runtime trace packages.\n",
            encoding="utf-8",
        )
        print(f"[OK] no pending runtime trace packages; wrote {staging_dir / 'README.md'}")
        return 0

    row = rows[0]
    package_rel = Path(str(row.get("package") or ""))
    package_path = package_rel if package_rel.is_absolute() else ROOT / package_rel
    if not package_path.is_file():
        raise FileNotFoundError(f"pending package not found: {package_path}")
    package_hash = sha256(package_path)
    staged_zip = staging_dir / package_path.name
    shutil.copy2(package_path, staged_zip)
    (staging_dir / "README.md").write_text(build_readme(row, package_rel, package_hash), encoding="utf-8")
    print(f"[OK] staged {row.get('request_id')} -> {staged_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
