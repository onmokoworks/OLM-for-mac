#!/usr/bin/env python3
"""Regression test for the fail-closed A9D0 row-slice harness."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_olmradialblur_a9d0_row_slice_acceleration_20260718.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("radial_a9d0_slice", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    assert runner.row_partition(4, [(0, 2), (2, 4)]) == {
        "height": 4,
        "slices": [[0, 2], [2, 4]],
        "complete": True,
        "disjoint": True,
    }
    for invalid in ([(0, 3), (2, 4)], [(0, 1), (3, 4)], [(1, 4)]):
        try:
            runner.row_partition(4, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid partition accepted: {invalid}")

    checkpoint = Path("/tmp/olm_radial_case0009_workers_progress6_20260718.aexcp")
    if not checkpoint.is_file():
        raise AssertionError(f"required natural checkpoint missing: {checkpoint}")
    with tempfile.TemporaryDirectory(prefix="olm_radial_a9d0_slice_test_") as directory:
        out = Path(directory)
        result = subprocess.run(
            [
                "python3",
                str(RUNNER),
                "--copy-dir",
                str(out / "copy"),
                "--output-json",
                str(out / "report.json"),
                "--output-md",
                str(out / "report.md"),
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        assert report["status"] == "blocked_fail_closed_checkpoint_not_safe_for_a9d0_replay"
        assert report["a9d0_invoked"] is False
        assert report["derived_checkpoint_emitted"] is False
        assert report["protected_pid_stopped"] is False
        assert report["source_unchanged_after_copy"] is True
        assert report["gates"]["checkpoint_copy_hash_equal"] is True
        assert report["checkpoint_classification"]["rip"] == "0x18000af9a"
        assert any("not an A9D0 entry" in reason for reason in report["checkpoint_classification"]["reasons"])
        assert (out / "copy" / "natural_checkpoint6_copy.aexcp").is_file()
        markdown = (out / "report.md").read_text(encoding="utf-8")
        assert "No A9D0 execution" in markdown or "not an A9D0 entry" in markdown
    print("PASS_OLMRADIALBLUR_A9D0_ROW_SLICE_FAIL_CLOSED_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
