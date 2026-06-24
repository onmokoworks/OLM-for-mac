#!/usr/bin/env python3
"""Smoke-test scripts/analyze_radialblur_zoom_witness.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="olmradialblur_zoom_witness_") as tmp:
        out_dir = Path(tmp)
        output_json = out_dir / "audit.json"
        output_md = out_dir / "audit.md"
        proc = subprocess.run(
            [
                py,
                "scripts/analyze_radialblur_zoom_witness.py",
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode

        report = json.loads(output_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmradialblur_zoom_witness_audit":
            raise AssertionError("unexpected report kind")
        if report.get("case_id") != "case_0009" or report.get("xy") != [6, 0]:
            raise AssertionError("unexpected witness target")
        if report["local"]["local_floor_u8"] != [20, 3, 3, 255]:
            raise AssertionError("expected local floor u8 alpha to stay 255")
        if report["windows_trace"]["final_rgba_u8"] != [20, 3, 3, 254]:
            raise AssertionError("expected Windows final alpha witness to be 254")
        if report["deltas"]["local_floor_minus_windows_u8"] != [0, 0, 0, 1]:
            raise AssertionError("expected only alpha to differ by one")
        local_alpha = float(report["local"]["local_sample_float"][3])
        windows_alpha = float(report["windows_trace"]["pre_writeback_rgba_float"][3])
        if abs(local_alpha - 1.0) > 1e-8:
            raise AssertionError("expected local alpha to be clipped to 1.0")
        if not (0.9999998 < windows_alpha < 1.0):
            raise AssertionError("expected Windows alpha to be just below 1.0")
        if "not a writeback conversion rule" not in report["interpretation"]:
            raise AssertionError("expected writeback rule to be ruled out")
        markdown = output_md.read_text(encoding="utf-8")
        if "Delta u8: `[0, 0, 0, 1]`" not in markdown:
            raise AssertionError("expected Markdown to show alpha-only u8 delta")

    print("[OK] RadialBlur Zoom witness audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
