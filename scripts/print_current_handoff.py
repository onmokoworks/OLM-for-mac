#!/usr/bin/env python3
"""Print the canonical OLM Windows/Mac handoff commands."""

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
    parser.add_argument(
        "--package",
        type=Path,
        help="Specific OLM handoff zip to print. When omitted, the newest valid handoff in the search dirs is used.",
    )
    parser.add_argument(
        "--search-dir",
        action="append",
        type=Path,
        default=[],
        help="Directory to search for olm_port_handoff*.zip. May be repeated; defaults to /tmp.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def verify_handoff(root: Path, package: Path) -> str | None:
    verifier = root / "scripts" / "verify_olm_handoff_package.py"
    proc = subprocess.run(
        [sys.executable, str(verifier), str(package)],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode == 0:
        return None
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else f"verify_olm_handoff_package.py exited {proc.returncode}"


def candidate_packages(search_dirs: list[Path]) -> list[Path]:
    candidates: list[Path] = []
    for search_dir in search_dirs:
        if not search_dir.exists() or not search_dir.is_dir():
            continue
        candidates.extend(search_dir.glob("olm_port_handoff*.zip"))
    return sorted(set(candidates), key=lambda path: path.stat().st_mtime, reverse=True)


def find_latest_valid_handoff(root: Path, search_dirs: list[Path]) -> tuple[Path | None, list[str]]:
    skipped: list[str] = []
    for candidate in candidate_packages(search_dirs):
        problem = verify_handoff(root, candidate)
        if problem is None:
            return candidate.resolve(), skipped
        skipped.append(f"{candidate}: {problem}")
    return None, skipped


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def package_manifest(package: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="olm_handoff_manifest_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(package) as archive:
            manifest_name = next(
                (name for name in archive.namelist() if name.endswith("/manifest.json")),
                None,
            )
            if manifest_name is None:
                return {}
            archive.extract(manifest_name, tmp_path)
        try:
            return json.loads((tmp_path / manifest_name).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - optional display metadata only.
            return {}


def package_json_entry(package: Path, entry_name: str) -> dict:
    if not entry_name:
        return {}
    with tempfile.TemporaryDirectory(prefix="olm_handoff_json_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(package) as archive:
            member = next(
                (name for name in archive.namelist() if name.endswith(f"/{entry_name}") or name == entry_name),
                None,
            )
            if member is None:
                return {}
            archive.extract(member, tmp_path)
        try:
            return json.loads((tmp_path / member).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - optional display metadata only.
            return {}


def main() -> int:
    args = parse_args()
    root = repo_root()
    search_dirs = [path.resolve() for path in args.search_dir] or [Path("/tmp")]

    skipped: list[str] = []
    if args.package:
        package = args.package.resolve()
        if not package.exists():
            return fail(f"package not found: {package}")
        problem = verify_handoff(root, package)
        if problem:
            return fail(f"package failed verification: {problem}")
    else:
        package, skipped = find_latest_valid_handoff(root, search_dirs)
        if package is None:
            searched = ", ".join(str(path) for path in search_dirs)
            return fail(f"no valid OLM handoff package found in: {searched}")

    manifest = package_manifest(package)
    next_actions_snapshot = manifest.get("next_reference_actions_json")
    if not isinstance(next_actions_snapshot, str):
        next_actions_snapshot = ""
    next_reference_dispatch = package_json_entry(package, next_actions_snapshot)
    git_commit = manifest.get("git_commit")
    if not isinstance(git_commit, str):
        git_commit = ""
    git_dirty = manifest.get("git_dirty")
    if not isinstance(git_dirty, bool):
        git_dirty = None

    windows_reference_zip = "/tmp/olm_reference_requests_pending_20260606.zip"
    commands = {
        "make_reference_zip": f"python3 refs/scripts/package_reference_requests.py --pending --output {windows_reference_zip}",
        "make_handoff_zip": f"scripts/package_olm_handoff.sh --output {package}",
        "verify_handoff_zip": f"python3 scripts/verify_olm_handoff_package.py {package}",
        "mac_import_windows_refs": (
            "python3 scripts/intake_olm_return.py path/to/returned_reference.zip "
            "--quick --dispatch-dir /tmp/olm_reference_dispatch"
        ),
        "mac_import_ae_host": "python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass",
        "mac_import_ae_host_all_pixels": (
            "python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip "
            "--require-all-pass --require-all-pixel-requests"
        ),
        "next_reference_dispatch_json": "python3 refs/scripts/next_reference_actions.py --json",
    }

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "handoff_package": str(package),
                    "skipped": skipped,
                    "handoff_contents": {
                        "next_reference_actions_json": next_actions_snapshot,
                        "next_reference_dispatch": next_reference_dispatch,
                        "git_commit": git_commit,
                        "git_dirty": git_dirty,
                    },
                    "commands": commands,
                    "windows_note": (
                        "Read refs/reference_requests/WIN_CODEX_HANDOFF.md inside the package. "
                        "Render SOFTWARE required sets first; CUDA sets are optional unless explicitly requested."
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    for line in skipped:
        print(f"[INFO] skipped candidate: {line}")
    print("OLM handoff")
    print(f"- send to Windows: {package}")
    if git_commit:
        dirty_suffix = " dirty" if git_dirty else ""
        print(f"- source commit: {git_commit}{dirty_suffix}")
    print("- Windows: read refs/reference_requests/WIN_CODEX_HANDOFF.md inside the zip")
    if next_actions_snapshot:
        print(f"- Subagents: read {next_actions_snapshot} inside the zip for dispatch snapshot")
    print("- Windows refs: render SOFTWARE required sets first; CUDA sets are optional")
    print("- AE host: run bundled Mac plugins and return AE_VALIDATION_RESULT*.json plus pixel PNGs")
    print("")
    print("Mac commands after return:")
    print(f"- Windows refs: {commands['mac_import_windows_refs']}")
    print(f"- AE host partial/current: {commands['mac_import_ae_host']}")
    print(f"- AE host all bundled pixel requests: {commands['mac_import_ae_host_all_pixels']}")
    print(f"- next subagent dispatch JSON: {commands['next_reference_dispatch_json']}")
    print("")
    print("Regenerate packages:")
    print(f"- pending refs only: {commands['make_reference_zip']}")
    print(f"- full handoff: {commands['make_handoff_zip']}")
    print(f"- verify handoff: {commands['verify_handoff_zip']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
