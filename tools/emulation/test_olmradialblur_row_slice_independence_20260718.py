#!/usr/bin/env python3
"""Regression test for the fail-closed RadialBlur row-slice proof."""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmradialblur_row_slice_independence_20260718.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("radial_row_audit", AUDIT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    audit = load_audit_module()
    assert audit.row_ranges(49, 4, [(0, 2), (2, 4)])['disjoint'] is True
    for invalid in ([(0, 3), (2, 4)], [(0, 1), (3, 4)], [(1, 4)]):
        try:
            audit.row_ranges(49, 4, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid partition accepted: {invalid}")
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory)
        result = subprocess.run(
            [
                sys.executable,
                str(AUDIT),
                "--output-json",
                str(out / "report.json"),
                "--output-md",
                str(out / "report.md"),
            ],
            check=False,
        )
        assert result.returncode == 0, result.returncode
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        assert report["status"] == "pass_row_slice_independence_with_two_phase_barrier"
        assert report["production_source_changed"] is False
        assert report["parallel_runner_started"] is False
        assert all(report["gates"].values()), report["gates"]
        assert report["partition_contract"]["disjoint"] is True
        assert report["partition_contract"]["complete"] is True
        assert report["abi"]["b150"]["shared_reduction"] is False
        assert report["abi"]["a9d0"]["shared_reduction"] is False
        text = (out / "report.md").read_text(encoding="utf-8")
        assert "B150-all-then-join-A9D0-all-then-join" in text or "Run `FUN_18000b150`" in text
    print("PASS_OLMRADIALBLUR_ROW_SLICE_INDEPENDENCE_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
