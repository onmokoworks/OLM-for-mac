#!/usr/bin/env python3
"""Smoke-test project-local Windows Send First staging materialization."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    pending_path = ROOT / "refs" / "reports" / "pending_runtime_trace_packages.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    rows = [row for row in pending.get("requests", []) if isinstance(row, dict) and row.get("status") == "pending"]
    rows.sort(key=lambda row: (int(row.get("priority") or 999999), str(row.get("request_id") or "")))
    with tempfile.TemporaryDirectory(prefix="olm_windows_send_first_stage_smoke_") as tmp:
        staging_dir = Path(tmp) / "stage"
        subprocess.run(
            [
                sys.executable,
                "scripts/materialize_windows_send_first_staging.py",
                "--staging-dir",
                str(staging_dir),
            ],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        readme = (staging_dir / "README.md").read_text(encoding="utf-8")
        if not rows:
            assert "No pending runtime trace packages" in readme
            assert not list(staging_dir.glob("*.zip"))
            print("[OK] Windows Send First staging materializer smoke passed")
            return 0
        row = rows[0]
        package_path = ROOT / row["package"]
        staged_zip = staging_dir / package_path.name
        assert staged_zip.is_file()
        assert sha256(staged_zip) == sha256(package_path)
        assert str(row["request_id"]) in readme
        assert package_path.name in readme
        assert sha256(package_path) in readme
        assert str(row.get("stop_condition") or "") in readme
    print("[OK] Windows Send First staging materializer smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
