#!/usr/bin/env python3
"""Smoke test for the natural case0012 class-plane producer checkpoint."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_classplane_natural_caller_20260717.py"
EXPECTED = "PASS_MAC_NATURAL_CLASSPLANE_CALLER_WITH_EXACT_LIVE_INPUT_BOUNDARY"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_classplane_natural_") as temp:
        output_json = Path(temp) / "result.json"
        output_md = Path(temp) / "result.md"
        run = subprocess.run([
            sys.executable, str(PROBE), "--output-json", str(output_json), "--output-md", str(output_md),
        ], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        result = json.loads(output_json.read_text(encoding="utf-8"))
        markdown = output_md.read_text(encoding="utf-8")

    natural = result["natural_checkpoint"]
    assert result["verdict"] == EXPECTED
    assert natural["generated_window_exact"] is True
    assert natural["full_rectangle_populated"] is True
    assert natural["worker_entries"] == 1
    assert natural["classifier_entries"] == 256
    assert natural["c280_from_generated_plane"]["count"] == 1
    assert result["live_boundary"]["ada0_or_ae10_input_checkpoints_in_returns"] == 0
    assert "FUN_18000ada0 entry" in result["live_boundary"]["exact_next_checkpoint"]
    assert "No production correctness or AE exact claim" in markdown
    print("PASS: natural ada0/ac00/ae10 class-plane checkpoint and live-input boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
