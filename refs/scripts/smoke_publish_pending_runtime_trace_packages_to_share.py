#!/usr/bin/env python3
"""Smoke-test scripts/publish_pending_runtime_trace_packages_to_share.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_zip(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "publish_pending_runtime_trace_packages_to_share.py"

    with tempfile.TemporaryDirectory(prefix="olm_publish_pending_runtime_smoke_") as tmp:
        tmp_root = Path(tmp)
        share_root = tmp_root / "olm_pr"
        new_dir = share_root / "new"
        old_dir = share_root / "old"
        new_dir.mkdir(parents=True)
        old_dir.mkdir(parents=True)

        pkg_dir = tmp_root / "pkgs"
        pkg_dir.mkdir()
        pkg1 = pkg_dir / "req_01.zip"
        pkg2 = pkg_dir / "req_02.zip"
        write_zip(pkg1, {"hello.txt": "one\n"})
        write_zip(pkg2, {"hello.txt": "two\n"})
        (new_dir / "stale.zip").write_text("old\n", encoding="utf-8")

        pending_json = tmp_root / "pending.json"
        pending_json.write_text(
            json.dumps(
                {
                    "kind": "pending_runtime_trace_packages",
                    "schema": 1,
                    "requests": [
                        {
                            "request_id": "req_b",
                            "status": "pending",
                            "priority": 20,
                            "package": str(pkg2),
                            "plugin_area": "Second request",
                            "stop_condition": "stop B",
                        },
                        {
                            "request_id": "req_a",
                            "status": "pending",
                            "priority": 10,
                            "package": str(pkg1),
                            "plugin_area": "First request",
                            "stop_condition": "stop A",
                        },
                        {
                            "request_id": "req_done",
                            "status": "answered",
                            "priority": 1,
                            "package": str(pkg1),
                            "plugin_area": "Answered request",
                            "stop_condition": "done",
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        dry = run(
            [
                sys.executable,
                str(script),
                "--share-root",
                str(share_root),
                "--pending-json",
                str(pending_json),
                "--dry-run",
            ],
            root,
        )
        dry_data = json.loads(dry.stdout)
        assert dry_data["count"] == 2
        assert dry_data["requests"][0]["request_id"] == "req_a"
        assert dry_data["requests"][1]["request_id"] == "req_b"

        proc = run(
            [
                sys.executable,
                str(script),
                "--share-root",
                str(share_root),
                "--pending-json",
                str(pending_json),
            ],
            root,
        )
        assert "[OK] published:" in proc.stdout
        new_files = sorted(path.name for path in new_dir.iterdir() if path.is_file())
        assert "req_01.zip" in new_files
        assert "req_02.zip" in new_files
        assert any(name.endswith("__README.txt") for name in new_files)
        archived = {path.name for path in old_dir.iterdir() if path.is_file()}
        assert any(name.endswith("stale.zip") for name in archived)

        proc_limit = run(
            [
                sys.executable,
                str(script),
                "--share-root",
                str(share_root),
                "--pending-json",
                str(pending_json),
                "--limit",
                "1",
            ],
            root,
        )
        assert "[OK] published:" in proc_limit.stdout
        new_files = sorted(path.name for path in new_dir.iterdir() if path.is_file())
        assert "req_01.zip" in new_files
        assert "req_02.zip" not in new_files

    with tempfile.TemporaryDirectory(prefix="olm_publish_pending_runtime_split_smoke_") as tmp:
        tmp_root = Path(tmp)
        share_root = tmp_root / "olm_pr"
        mac_requests = share_root / "new" / "mac_requests"
        windows_processing = share_root / "new" / "windows_processing"
        mac_returns = share_root / "new" / "mac_returns"
        old_dir = share_root / "old"
        mac_requests.mkdir(parents=True)
        windows_processing.mkdir(parents=True)
        mac_returns.mkdir(parents=True)
        old_dir.mkdir(parents=True)

        pkg_dir = tmp_root / "pkgs"
        pkg_dir.mkdir()
        pkg = pkg_dir / "req_split.zip"
        write_zip(pkg, {"hello.txt": "split\n"})
        (mac_requests / "stale_request.zip").write_text("old\n", encoding="utf-8")
        timestamp = subprocess.run(
            ["date", "+%Y%m%d_%H%M%S"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        collision = old_dir / f"{timestamp}__stale_request.zip"
        collision.write_text("keep existing archive\n", encoding="utf-8")
        (windows_processing / "in_progress.zip").write_text("keep\n", encoding="utf-8")
        (mac_returns / "returned.zip").write_text("keep\n", encoding="utf-8")

        pending_json = tmp_root / "pending.json"
        pending_json.write_text(
            json.dumps(
                {
                    "kind": "pending_runtime_trace_packages",
                    "schema": 1,
                    "requests": [
                        {
                            "request_id": "req_split",
                            "status": "pending",
                            "priority": 1,
                            "package": str(pkg),
                            "plugin_area": "Split request",
                            "stop_condition": "stop split",
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        proc = run(
            [
                sys.executable,
                str(script),
                "--share-root",
                str(share_root),
                "--pending-json",
                str(pending_json),
            ],
            root,
        )
        assert "[OK] published:" in proc.stdout
        assert "new/mac_requests" in proc.stdout
        request_files = sorted(path.name for path in mac_requests.iterdir() if path.is_file())
        assert "req_split.zip" in request_files
        readme_name = next(name for name in request_files if name.endswith("__README.txt"))
        readme_text = (mac_requests / readme_name).read_text(encoding="utf-8")
        assert "new/mac_returns" in readme_text
        assert "/Volumes/" not in readme_text
        archived = {path.name for path in old_dir.iterdir() if path.is_file()}
        assert any(name.endswith("stale_request.zip") for name in archived)
        assert collision.read_text(encoding="utf-8") == "keep existing archive\n"
        assert len([name for name in archived if name.endswith("stale_request.zip")]) == 2
        assert (windows_processing / "in_progress.zip").is_file()
        assert (mac_returns / "returned.zip").is_file()

    print("[OK] publish pending runtime trace packages to share smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
