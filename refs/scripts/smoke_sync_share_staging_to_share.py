#!/usr/bin/env python3
"""Smoke-test scripts/sync_share_staging_to_share.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    helper = root / "scripts" / "sync_share_staging_to_share.py"

    with tempfile.TemporaryDirectory(prefix="olm_sync_stage_smoke_") as tmp:
        tmp_root = Path(tmp)
        staging_dir = tmp_root / "stage"
        share_root = tmp_root / "olm_pr"
        (share_root / "new").mkdir(parents=True)
        (share_root / "old").mkdir(parents=True)
        staging_dir.mkdir(parents=True)

        zip_file = staging_dir / "request.zip"
        readme_file = staging_dir / "README.txt"
        note_file = staging_dir / "note.md"
        zip_file.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
        readme_file.write_text("hello\n", encoding="utf-8")
        note_file.write_text("note\n", encoding="utf-8")

        dry = subprocess.run(
            [
                sys.executable,
                str(helper),
                "--staging-dir",
                str(staging_dir),
                "--share-root",
                str(share_root),
                "--dry-run",
            ],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        data = json.loads(dry.stdout)
        assert data["files"][0].endswith("request.zip")
        assert any(path.endswith("README.txt") for path in data["files"])

        old_existing = share_root / "new" / "old_pending.zip"
        old_existing.write_bytes(b"old")

        run = subprocess.run(
            [
                sys.executable,
                str(helper),
                "--staging-dir",
                str(staging_dir),
                "--share-root",
                str(share_root),
            ],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if "[OK] synced staging directory" not in run.stdout:
            raise AssertionError("sync output missing success marker")
        new_dir = share_root / "new"
        assert (new_dir / "request.zip").is_file()
        assert (new_dir / "README.txt").is_file()
        assert (new_dir / "note.md").is_file()
        archived = list((share_root / "old").glob("*__old_pending.zip"))
        assert archived, "old pending file was not archived"

    print("[OK] sync_share_staging_to_share smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
