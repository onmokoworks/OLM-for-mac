#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zip_request_ids(path: Path) -> list[str]:
    if path.suffix.lower() != ".zip":
        return []
    request_ids: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith(".json"):
                    continue
                try:
                    data = json.loads(archive.read(name).decode("utf-8"))
                except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
                    continue
                request_id = data.get("request_id") if isinstance(data, dict) else None
                if isinstance(request_id, str) and request_id:
                    request_ids.append(request_id)
    except zipfile.BadZipFile:
        return []
    return request_ids


def load_pending_runtime_rows(root: Path) -> list[dict[str, Any]]:
    path = root / "refs" / "reports" / "pending_runtime_trace_packages.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = data.get("requests") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def resolve_request_metadata(root: Path, decision: dict, target_path: Path) -> dict[str, str]:
    target = decision.get("target")
    request_ids: list[str] = []
    if isinstance(target, dict):
        direct_request_id = target.get("request_id")
        if isinstance(direct_request_id, str) and direct_request_id:
            request_ids.append(direct_request_id)
        listed_request_ids = target.get("request_ids")
        if isinstance(listed_request_ids, list):
            request_ids.extend(
                request_id
                for request_id in listed_request_ids
                if isinstance(request_id, str) and request_id
            )
    direct_request_id = decision.get("request_id")
    if isinstance(direct_request_id, str) and direct_request_id:
        request_ids.append(direct_request_id)
    request_ids.extend(zip_request_ids(target_path))

    sha256 = file_sha256(target_path)
    target_name = target_path.name
    target_str = str(target_path)
    matched_row: dict[str, Any] | None = None
    pending_rows = load_pending_runtime_rows(root)
    for row in pending_rows:
        package = row.get("package")
        if not isinstance(package, str):
            continue
        if package == target_str or Path(package).name == target_name:
            matched_row = row
            break
    if matched_row is None and request_ids:
        request_id_set = set(request_ids)
        for row in pending_rows:
            if row.get("request_id") in request_id_set:
                matched_row = row
                break

    request_id = ""
    stop_condition = ""
    if matched_row is not None:
        request_id = str(matched_row.get("request_id") or "")
        stop_condition = str(matched_row.get("stop_condition") or "")
    if not request_id and request_ids:
        request_id = request_ids[0]
    if not stop_condition:
        stop_condition = str(decision.get("stop_condition") or "")
    return {
        "request_id": request_id,
        "sha256": sha256,
        "stop_condition": stop_condition,
    }


def build_readme(decision: dict, target_path: Path, metadata: dict[str, str]) -> str:
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
    if metadata.get("request_id"):
        lines.extend(["", f"Pending request id: {metadata['request_id']}"])
    lines.extend(["", f"Package SHA256: {metadata['sha256']}"])
    if metadata.get("stop_condition"):
        lines.extend(["", "Stop condition:", f"- {metadata['stop_condition']}"])
    return "\n".join(lines) + "\n"


def clear_staging_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_file():
            child.unlink()


def staged_package_path(decision: dict) -> Path | None:
    staged = decision.get("staged_package")
    if not isinstance(staged, dict):
        return None
    path = staged.get("path")
    if not isinstance(path, str) or not path:
        return None
    return Path(path)


def generated_package_from_decision(root: Path, decision: dict) -> Path | None:
    target = decision.get("target")
    if not isinstance(target, dict) or target.get("type") != "runtime_trace_package_profile":
        return None
    run_command = decision.get("run")
    if not isinstance(run_command, str) or not run_command.strip():
        return None
    argv = shlex.split(run_command)
    output_path: Path | None = None
    for index, arg in enumerate(argv):
        if arg == "--output" and index + 1 < len(argv):
            output_path = Path(argv[index + 1])
            break
        if arg.startswith("--output="):
            output_path = Path(arg.split("=", 1)[1])
            break
    if output_path is None:
        raise ValueError("runtime_trace_package_profile action is missing --output in run command")
    output_path = output_path if output_path.is_absolute() else root / output_path
    subprocess.run(argv, cwd=root, check=True, text=True)
    return output_path


def main() -> int:
    args = parse_args()
    root = repo_root()
    decision = load_next_action(root, args.scan_path)
    staged_path = staged_package_path(decision)
    await_actions = {
        "await-runtime-trace-return": ("runtime trace package", "Windows runtime trace"),
        "await-windows-reference-return": ("Windows reference request package", "Windows reference render"),
    }
    action = str(decision.get("action") or "")
    if action in await_actions and staged_path and staged_path.is_file():
        package_label, wait_label = await_actions[action]
        if args.dry_run:
            print(json.dumps({
                "share_root": str(args.share_root),
                "publishable": False,
                "already_staged": True,
                "reason": f"{package_label} is already staged; waiting for {wait_label} return",
                "staged_path": str(staged_path),
                "decision": decision,
            }, indent=2, ensure_ascii=False))
            return 0
        print(f"[OK] already staged: {staged_path}")
        print(f"[OK] waiting for {wait_label} return; not republishing")
        return 0
    target = decision.get("target")
    generated_target = generated_package_from_decision(root, decision)
    if generated_target is not None:
        target = {"path": str(generated_target)}
    if not isinstance(target, dict) or not isinstance(target.get("path"), str):
        if args.dry_run:
            print(json.dumps({
                "share_root": str(args.share_root),
                "publishable": False,
                "reason": "next action did not include a publishable target path",
                "decision": decision,
            }, indent=2, ensure_ascii=False))
            return 0
        clear_staging_dir(args.share_root / "new")
        print("nothing to publish: next action did not include a publishable target path")
        return 0
    target_path = Path(target["path"])
    if not target_path.is_file():
        if args.dry_run:
            print(json.dumps({
                "share_root": str(args.share_root),
                "publishable": False,
                "reason": f"target path not found: {target_path}",
                "decision": decision,
            }, indent=2, ensure_ascii=False))
            return 0
        clear_staging_dir(args.share_root / "new")
        print(f"nothing to publish: target path not found: {target_path}")
        return 0
    if target_path.suffix.lower() != ".zip":
        if args.dry_run:
            print(json.dumps({
                "share_root": str(args.share_root),
                "publishable": False,
                "reason": f"target path is not a zip file: {target_path}",
                "decision": decision,
            }, indent=2, ensure_ascii=False))
            return 0
        clear_staging_dir(args.share_root / "new")
        print(f"nothing to publish: target path is not a zip file: {target_path}")
        return 0
    metadata = resolve_request_metadata(root, decision, target_path)

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
            "request_id": metadata["request_id"],
            "sha256": metadata["sha256"],
            "stop_condition": metadata["stop_condition"],
            "decision": decision,
        }, indent=2, ensure_ascii=False))
        return 0

    with tempfile.TemporaryDirectory(prefix="olm_share_stage_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        staged_zip = tmp_root / staged_zip_name
        staged_readme = tmp_root / staged_readme_name
        staged_zip.write_bytes(target_path.read_bytes())
        staged_readme.write_text(build_readme(decision, target_path, metadata), encoding="utf-8")

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
