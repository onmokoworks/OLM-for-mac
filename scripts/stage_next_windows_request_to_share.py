#!/usr/bin/env python3
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
        "--scan-path",
        action="append",
        default=[],
        help="Extra path to pass to print_next_olm_action.py. Can be specified multiple times.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be published without touching the share.",
    )
    return parser.parse_args()


def load_next_action(root: Path, scan_paths: list[str]) -> dict:
    cmd = [sys.executable, str(root / "scripts" / "print_next_olm_action.py")]
    if scan_paths:
        cmd.extend(scan_paths)
    else:
        cmd.extend([str(Path.home() / "Downloads"), "/tmp"])
    cmd.append("--json")
    proc = subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    data = json.loads(proc.stdout)
    if not isinstance(data, dict):
        raise ValueError("next action output must be a JSON object")
    decision = data.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("missing decision in next action output")
    return decision


def build_readme(decision: dict, target_path: Path) -> str:
    request_id = target_path.stem
    command = decision.get("command", "")
    reason = decision.get("reason", "")
    action = decision.get("action", "")
    lines = [
        f"Action: {action}",
        "",
        f"Target file: {target_path.name}",
        "",
        "Why this is next:",
        f"- {reason}",
        "",
        "What Windows should do:",
        f"- Run/use: {target_path.name}",
    ]
    if command:
        lines.extend(["", "Requested operation:", f"- {command}"])
    if isinstance(decision.get("target"), dict):
        target = decision["target"]
        path = target.get("path")
        if path:
            lines.extend(["", "Repo-side target path:", f"- {path}"])
    lines.extend(["", f"Derived request id hint: {request_id}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = repo_root()
    decision = load_next_action(root, args.scan_path)
    target = decision.get("target")
    if not isinstance(target, dict) or not isinstance(target.get("path"), str):
        raise SystemExit("next action did not include a publishable target path")
    target_path = Path(target["path"])
    if not target_path.is_file():
        raise SystemExit(f"target path not found: {target_path}")
    if target_path.suffix.lower() != ".zip":
        raise SystemExit(f"target path is not a zip file: {target_path}")

    timestamp = subprocess.run(
        ["date", "+%Y%m%d_%H%M%S"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    staged_zip_name = f"{timestamp}__{target_path.name}"
    staged_readme_name = f"{timestamp}__{target_path.stem}__README.txt"

    if args.dry_run:
        print(json.dumps({
            "share_root": str(args.share_root),
            "target_zip": str(target_path),
            "staged_zip_name": staged_zip_name,
            "staged_readme_name": staged_readme_name,
            "decision": decision,
        }, indent=2, ensure_ascii=False))
        return 0

    with tempfile.TemporaryDirectory(prefix="olm_share_stage_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        staged_zip = tmp_root / staged_zip_name
        staged_readme = tmp_root / staged_readme_name
        staged_zip.write_bytes(target_path.read_bytes())
        staged_readme.write_text(build_readme(decision, target_path), encoding="utf-8")

        path_entries = [
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
            "/opt/homebrew/bin",
            str(Path.home() / ".local/bin"),
        ]
        env = os.environ.copy()
        env["OLM_PR_SHARE_ROOT"] = str(args.share_root)
        env["PATH"] = ":".join(path_entries)
        proc = subprocess.run(
            [str(root / "scripts" / "publish_windows_request_to_share.sh"), str(staged_zip), str(staged_readme)],
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
