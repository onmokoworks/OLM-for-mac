#!/usr/bin/env python3
"""Smoke-test OLMDistanceGradation representative witness analysis."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    with tempfile.TemporaryDirectory(prefix="olmdg_representative_witnesses_") as tmp:
        tmp_path = Path(tmp)
        summary_json = tmp_path / "summary.json"
        summary_md = tmp_path / "summary.md"
        subprocess.run(
            [
                sys.executable,
                "scripts/analyze_distancegradation_representative_witnesses.py",
                "--summary-json",
                str(summary_json),
                "--summary-md",
                str(summary_md),
            ],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        data = json.loads(summary_json.read_text(encoding="utf-8"))
        cases = {row["case_id"]: row for row in data["cases"]}
        case_0020 = cases["olmdistancegradation_extended__case_0020"]
        case_0012 = cases["olmdistancegradation_extended__case_0012"]
        assert case_0020["family"] == "constant-bg-binary-sparse-full-color"
        assert case_0020["changed_pixel_count"] == 1001
        assert case_0020["samples"][0]["delta"] == [58340, 0, -61165, 0]
        assert case_0012["family"] == "layer-no-bg-source-or-alpha-ownership"
        assert case_0012["changed_pixel_count"] == 25421
        assert case_0012["samples"][0]["delta"] == [-16250, -16250, -16250, 0]
        assert "Prefer case_0020 first" in summary_md.read_text(encoding="utf-8")
    print("[OK] DistanceGradation representative witness smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
