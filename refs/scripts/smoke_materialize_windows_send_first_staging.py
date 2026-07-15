#!/usr/bin/env python3
"""Smoke-test project-local Windows Send First staging materialization."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_subject(repo: Path):
    scripts_dir = repo / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        import materialize_windows_send_first_staging as subject  # type: ignore
    finally:
        sys.path.pop(0)
    return subject


def main() -> int:
    subject = load_subject(ROOT)
    pending_path = ROOT / "refs" / "reports" / "pending_runtime_trace_packages.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    rows = [row for row in pending.get("requests", []) if isinstance(row, dict) and row.get("status") == "pending"]
    rows.sort(key=lambda row: (int(row.get("priority") or 999999), str(row.get("request_id") or "")))
    synthetic_row = {
        "request_id": "split_readme",
        "plugin_area": "Split README",
        "stop_condition": "stop here",
    }
    with tempfile.TemporaryDirectory(prefix="olm_windows_send_first_readme_layout_") as tmp:
        tmp_path = Path(tmp)
        split_share = tmp_path / "split" / "olm_pr"
        (split_share / "new" / "mac_requests").mkdir(parents=True)
        (split_share / "new" / "windows_processing").mkdir(parents=True)
        (split_share / "new" / "mac_returns").mkdir(parents=True)
        with mock.patch.object(subject, "DEFAULT_SHARE_ROOT", split_share):
            split_readme = subject.build_readme(
                synthetic_row,
                tmp_path / "external" / "req_split.zip",
                "abc123",
            )
        assert "new/mac_requests/req_split.zip" in split_readme
        assert str(split_share) not in split_readme
        assert "external/req_split.zip" not in split_readme
        assert "- Source: `req_split.zip`" in split_readme

        legacy_share = tmp_path / "legacy" / "olm_pr"
        (legacy_share / "new").mkdir(parents=True)
        with mock.patch.object(subject, "DEFAULT_SHARE_ROOT", legacy_share):
            legacy_readme = subject.build_readme(
                synthetic_row,
                Path("refs/runtime_trace_packages/req_legacy.zip"),
                "def456",
            )
        assert "new/req_legacy.zip" in legacy_readme
        assert "new/mac_requests/req_legacy.zip" not in legacy_readme

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
        assert str(ROOT) not in readme
    print("[OK] Windows Send First staging materializer smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
