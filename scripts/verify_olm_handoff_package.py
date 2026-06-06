#!/usr/bin/env python3
"""Validate an OLM port handoff zip before sending it to another machine."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="zip produced by scripts/package_olm_handoff.sh")
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def has_macos_metadata(package: Path) -> str | None:
    with zipfile.ZipFile(package) as archive:
        for name in archive.namelist():
            parts = Path(name).parts
            if "__MACOSX" in parts:
                return name
            if any(part.startswith("._") for part in parts):
                return name
            if any(part == ".DS_Store" for part in parts):
                return name
    return None


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def single_root(root: Path) -> Path:
    children = [path for path in root.iterdir() if path.is_dir()]
    if len(children) != 1:
        raise ValueError(f"package must contain one top-level directory, found {len(children)}")
    return children[0]


def verify_reference_zip(path: Path) -> str | None:
    if not path.exists():
        return f"reference request zip missing: {path}"
    if not zipfile.is_zipfile(path):
        return f"reference request package is not a zip: {path.name}"
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    if "refs/reference_requests/WIN_CODEX_HANDOFF.md" not in names:
        return "reference request package missing WIN_CODEX_HANDOFF.md"
    request_jsons = [
        name
        for name in names
        if name.startswith("refs/reference_requests/") and name.endswith(".json")
    ]
    if not request_jsons:
        return "reference request package contains no request JSON files"
    return None


def verify_reference_zip_pending(repo: Path, path: Path) -> int:
    verifier = repo / "refs" / "scripts" / "verify_reference_request_package.py"
    proc = subprocess.run(
        [sys.executable, str(verifier), str(path), "--expect-pending"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc.returncode


def verify_mac_zip(repo: Path, path: Path) -> int:
    verifier = repo / "scripts" / "verify_mac_plugin_package.py"
    proc = subprocess.run(
        [sys.executable, str(verifier), str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc.returncode


def verify_next_actions(path: Path) -> str | None:
    if not path.exists():
        return f"next reference actions JSON missing: {path}"
    try:
        data = load_json(path)
    except ValueError as exc:
        return str(exc)
    for key in ("covered_actions", "partial", "pending"):
        if not isinstance(data.get(key), list):
            return f"next reference actions JSON .{key} must be a list"
    if "next_action" not in data:
        return "next reference actions JSON missing .next_action"
    pending_actions = data.get("pending_actions")
    if not isinstance(pending_actions, list):
        return "next reference actions JSON .pending_actions must be a list"
    for index, action in enumerate([*pending_actions, *data.get("covered_actions", [])]):
        if not isinstance(action, dict):
            return f"next reference action #{index} must be an object"
        for key in (
            "request_id",
            "plugin_area",
            "mode",
            "write_scope",
            "smoke_command",
            "agent_prompt",
            "copy_paste_prompt",
        ):
            if not isinstance(action.get(key), str) or not action[key]:
                return f"next reference action #{index}.{key} must be a non-empty string"
        if not isinstance(action.get("read_files"), list):
            return f"next reference action #{index}.read_files must be a list"
        if not isinstance(action.get("read_files_resolved"), list):
            return f"next reference action #{index}.read_files_resolved must be a list"
    return None


def main() -> int:
    args = parse_args()
    package = args.package.resolve()
    repo = Path(__file__).resolve().parents[1]
    if not package.exists():
        return fail(f"package not found: {package}")
    if not zipfile.is_zipfile(package):
        return fail(f"not a zip file: {package}")

    metadata_entry = has_macos_metadata(package)
    if metadata_entry:
        return fail(f"package contains macOS metadata entry: {metadata_entry}")

    with tempfile.TemporaryDirectory(prefix="olm_handoff_pkg_verify_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(tmp_path)
        try:
            root = single_root(tmp_path)
            manifest = load_json(root / "manifest.json")
        except Exception as exc:  # noqa: BLE001
            return fail(str(exc))

        if manifest.get("kind") != "olm_port_handoff_package":
            return fail("manifest.kind must be 'olm_port_handoff_package'")
        for key in ("configuration", "source_root", "created_at"):
            if not isinstance(manifest.get(key), str) or not manifest[key]:
                return fail(f"manifest.{key} must be a non-empty string")
        git_commit = manifest.get("git_commit")
        if not isinstance(git_commit, str) or not git_commit:
            return fail("manifest.git_commit must be a non-empty string")
        if git_commit != "unknown" and len(git_commit) != 40:
            return fail("manifest.git_commit must be a 40-character hash or 'unknown'")
        if not isinstance(manifest.get("git_dirty"), bool):
            return fail("manifest.git_dirty must be a boolean")
        if not (root / "README.md").exists():
            return fail("README.md missing")

        ref_zip = manifest.get("reference_requests_zip")
        mac_zip = manifest.get("mac_plugins_zip")
        next_actions_json = manifest.get("next_reference_actions_json")
        if not isinstance(ref_zip, str) or not ref_zip:
            return fail("manifest.reference_requests_zip must be a non-empty string")
        if not isinstance(mac_zip, str) or not mac_zip:
            return fail("manifest.mac_plugins_zip must be a non-empty string")
        if not isinstance(next_actions_json, str) or not next_actions_json:
            return fail("manifest.next_reference_actions_json must be a non-empty string")

        reference_problem = verify_reference_zip(root / ref_zip)
        if reference_problem:
            return fail(reference_problem)
        if verify_reference_zip_pending(repo, root / ref_zip) != 0:
            return fail("nested reference request package failed verification")
        next_actions_problem = verify_next_actions(root / next_actions_json)
        if next_actions_problem:
            return fail(next_actions_problem)
        if verify_mac_zip(repo, root / mac_zip) != 0:
            return fail("nested Mac plugin package failed verification")

    print(f"[OK] {package}: OLM handoff package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
