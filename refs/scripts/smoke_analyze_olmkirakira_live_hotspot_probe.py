#!/usr/bin/env python3
"""Smoke-test the OLMKiraKira live hotspot probe analyzer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    probe_dir = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260703_r3"
    result_json = Path("/tmp/olm_ae_single_case_20260703_141656/AE_SINGLE_CASE_RESULT.json")
    if not result_json.exists():
        print("skipping smoke: live AE probe result missing", file=sys.stderr)
        return 0
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out_json = tmp / "report.json"
        out_md = tmp / "report.md"
        proc = subprocess.run(
            [
                "python3",
                "scripts/analyze_olmkirakira_live_hotspot_probe.py",
                "--result-json",
                str(result_json),
                "--reference-png",
                str(probe_dir / "expected/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"),
                "--debug-neighborhood-json",
                str(probe_dir / "kirakira_neighborhood.json"),
                "--installed-binary",
                str(Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"),
                "--built-binary",
                str(ROOT / "mac/OLMKiraKira/Mac/build/Debug/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"),
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
        if data.get("kind") != "olmkirakira_live_hotspot_probe":
            print("unexpected report kind", file=sys.stderr)
            return 1
        if data.get("center_pixels", {}).get("exported_png_rgba8", [None])[0] is None:
            print("missing exported center pixel", file=sys.stderr)
            return 1
    print("[OK] OLMKiraKira live hotspot probe smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
