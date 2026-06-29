#!/usr/bin/env python3
"""Smoke-test Windows share publish helpers."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def write_zip(path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, text in files.items():
            archive.writestr(name, text)


def main() -> int:
    root = repo_root()
    publish_script = root / "scripts" / "publish_windows_request_to_share.sh"
    stage_script = root / "scripts" / "stage_next_windows_request_to_share.py"

    with tempfile.TemporaryDirectory(prefix="olm_share_publish_smoke_") as tmp:
        tmp_root = Path(tmp)
        share_root = tmp_root / "olm_pr"
        new_dir = share_root / "new"
        old_dir = share_root / "old"
        new_dir.mkdir(parents=True)
        old_dir.mkdir(parents=True)

        stale_zip = new_dir / "stale_request.zip"
        stale_readme = new_dir / "stale_request__README.txt"
        write_zip(stale_zip, {"hello.txt": "old\n"})
        stale_readme.write_text("old readme\n", encoding="utf-8")

        outgoing_zip = tmp_root / "outgoing_request.zip"
        outgoing_note = tmp_root / "outgoing_request__README.txt"
        write_zip(outgoing_zip, {"payload.txt": "new\n"})
        outgoing_note.write_text("new readme\n", encoding="utf-8")

        env = os.environ.copy()
        env["OLM_PR_SHARE_ROOT"] = str(share_root)
        proc = run([str(publish_script), str(outgoing_zip), str(outgoing_note)], root, env=env)
        assert "[OK] published:" in proc.stdout
        assert (new_dir / outgoing_zip.name).exists()
        assert (new_dir / outgoing_note.name).exists()
        archived = {path.name for path in old_dir.iterdir() if path.is_file()}
        assert any(name.endswith("stale_request.zip") for name in archived)
        assert any(name.endswith("stale_request__README.txt") for name in archived)

        proc = run(
            [
                sys.executable,
                str(stage_script),
                "--share-root",
                str(share_root),
            ],
            root,
        )
        assert "[OK] published:" in proc.stdout
        new_files = sorted(path.name for path in new_dir.iterdir() if path.is_file())
        assert len(new_files) == 2
        assert new_files[0].endswith(".txt") or new_files[1].endswith(".txt")
        assert any(name.endswith(".zip") for name in new_files)
        assert any(name.endswith("__README.txt") for name in new_files)
        archived = {path.name for path in old_dir.iterdir() if path.is_file()}
        assert any(name.endswith(outgoing_zip.name) for name in archived)
        assert any(name.endswith(outgoing_note.name) for name in archived)

    print("[OK] Windows share publish smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
