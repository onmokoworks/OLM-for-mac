#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_tiny_rotation_support_envelope.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmrb_tiny_rotation_support_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmradialblur_tiny_rotation_support_envelope.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmradialblur_tiny_rotation_support_envelope"
        assert report["witness_xy"] == [1614, 6]
        assert report["positive_cluster_rows"] == [843]
        assert report["positive_cluster_angles"] == [1601, 1602]
        assert report["summary_counts"]["outputs_with_direct_cluster_visibility"] == 3
        assert report["summary_counts"]["witness_has_direct_cluster_visibility"] is False
        visible = {tuple(row["xy"]): row for row in report["outputs"] if row["can_directly_see_cluster"]}
        assert (1612, 6) in visible
        assert (1613, 6) in visible
        assert (1614, 7) in visible
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMRadialBlur tiny Rotation Support Envelope Audit",
            "(1614, 6)",
            "(1612, 6)",
            "(1613, 6)",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMRadialBlur tiny Rotation support envelope smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
