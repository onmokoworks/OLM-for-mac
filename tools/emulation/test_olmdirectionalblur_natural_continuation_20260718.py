#!/usr/bin/env python3
"""Fail-closed regression test for the 20260718 continuation harness."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_olmdirectionalblur_natural_continuation_20260718.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_continuation_smoke_") as name:
        progress = Path(name) / "progress.json"
        report_md = Path(name) / "progress.md"
        command = [sys.executable, str(RUNNER), "--progress", str(progress), "--report-md", str(report_md)]
        first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if first.returncode != 0:
            raise AssertionError(f"fresh bounded run crashed: {first.stderr[-2000:]}")
        first_report = json.loads(progress.read_text(encoding="utf-8"))
        if first_report["status"] not in {"pass", "blocked"}:
            raise AssertionError("invalid fail-closed status")
        if first_report["fail_closed"] != {
            "production_source_edited": False,
            "windows_values_fabricated": False,
            "png_tuning": False,
            "ae_exact_claim": False,
        }:
            raise AssertionError("fail-closed flags drifted")
        state = first_report["checkpoint_state"]
        if first_report["status"] == "pass":
            if state["final_blocker"] is not None:
                raise AssertionError("pass report must have final_blocker=null")
            if state["initial_fixture_blocker_before_explicit_continuation"] != "pre-render-return":
                raise AssertionError("initial fixture blocker was not preserved as an initial observation")
        elif state["final_blocker"] is None:
            raise AssertionError("blocked report must identify a final blocker")
        resume = subprocess.run(command + ["--resume"], cwd=ROOT, capture_output=True, text=True)
        if resume.returncode != 0:
            raise AssertionError(f"replay resume refused or crashed: {resume.stderr[-2000:]}")
        resumed = json.loads(progress.read_text(encoding="utf-8"))
        if resumed["provenance"] != first_report["provenance"]:
            raise AssertionError("resume changed provenance")
        if resumed["checkpoint_state"]["first_missing"] != first_report["checkpoint_state"]["first_missing"]:
            raise AssertionError("resume changed blocker classification")
        if not report_md.exists() or "FACT" not in report_md.read_text(encoding="utf-8"):
            raise AssertionError("FACT/INFERENCE report was not written")
    print("PASS_OLMDIRECTIONALBLUR_NATURAL_CONTINUATION_FAIL_CLOSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
