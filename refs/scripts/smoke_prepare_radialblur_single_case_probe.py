#!/usr/bin/env python3
"""Smoke test for prepare_radialblur_single_case_probe.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_probe_smoke_") as tmp:
        out_dir = Path(tmp) / "probe"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "prepare_radialblur_single_case_probe.py"),
                "--case-id",
                "case_0009",
                "--output-dir",
                str(out_dir),
            ],
            cwd=ROOT,
            check=True,
        )
        req = json.loads((out_dir / "request_manifest.json").read_text(encoding="utf-8"))
        ref = json.loads((out_dir / "reference_manifest.json").read_text(encoding="utf-8"))
        plan = json.loads((out_dir / "OLMRADIALBLUR_PROBE_PLAN.json").read_text(encoding="utf-8"))
        assert req["cases"][0]["id"] == "case_0009"
        assert ref["cases"][0]["id"] == "case_0009"
        assert "OLMRADIALBLUR_DEBUG_POINTS" in plan["suggested_run_command"]
        assert (out_dir / "input" / "case_0009_before_effects.png").exists()
        assert (out_dir / "expected" / "case_0009.png").exists()
    print("[OK] prepare_radialblur_single_case_probe smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
