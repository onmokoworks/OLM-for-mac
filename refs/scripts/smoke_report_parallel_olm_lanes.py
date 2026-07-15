#!/usr/bin/env python3
"""Smoke-test the parallel lane report generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_subject(repo: Path):
    scripts_dir = repo / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        import report_parallel_olm_lanes as subject  # type: ignore
    finally:
        sys.path.pop(0)
    return subject


def main() -> int:
    subject = load_subject(ROOT)
    with tempfile.TemporaryDirectory(prefix="olm_parallel_lane_layout_") as tmpdir:
        tmp = Path(tmpdir)
        split_share = tmp / "split" / "olm_pr"
        (split_share / "new" / "mac_requests").mkdir(parents=True)
        (split_share / "new" / "windows_processing").mkdir(parents=True)
        (split_share / "new" / "mac_returns").mkdir(parents=True)
        with mock.patch.object(subject, "SHARE_ROOT", split_share):
            split_report = subject.build_report()
        assert split_report["share_new"] == "new/mac_requests"
        assert all(
            row["stages"]["shared_exchange"]["path"].startswith("new/mac_requests/")
            for row in split_report["bitdepth_lanes"]
        )
        assert all(str(split_share) not in row["stages"]["shared_exchange"]["path"] for row in split_report["bitdepth_lanes"])

        legacy_share = tmp / "legacy" / "olm_pr"
        (legacy_share / "new").mkdir(parents=True)
        with mock.patch.object(subject, "SHARE_ROOT", legacy_share):
            legacy_report = subject.build_report()
        assert legacy_report["share_new"] == "new"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out_json = tmp / "parallel_lane_report.json"
        out_md = tmp / "parallel_lane_report.md"
        proc = subprocess.run(
            [
                "python3",
                "scripts/report_parallel_olm_lanes.py",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stderr, end="")
            return proc.returncode
        data = json.loads(out_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olm_parallel_lane_report":
            print("unexpected report kind", file=sys.stderr)
            return 1
        if len(data.get("bitdepth_lanes", [])) < 3:
            print("missing bitdepth lanes", file=sys.stderr)
            return 1
        if len(data.get("provenance_lanes", [])) < 3:
            print("missing provenance lanes", file=sys.stderr)
            return 1
        if not out_md.exists():
            print("missing markdown output", file=sys.stderr)
            return 1
        if str(subject.SHARE_ROOT) in out_json.read_text(encoding="utf-8"):
            print("unexpected absolute share path in report JSON", file=sys.stderr)
            return 1
        if str(subject.SHARE_ROOT) in out_md.read_text(encoding="utf-8"):
            print("unexpected absolute share path in report markdown", file=sys.stderr)
            return 1
    print("[OK] parallel lane report smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
