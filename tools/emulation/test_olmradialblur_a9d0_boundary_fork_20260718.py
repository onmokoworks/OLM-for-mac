#!/usr/bin/env python3
"""Regression checks for the dated A9D0 boundary-fork proof."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/run_olmradialblur_a9d0_boundary_fork_20260718.py"
REPORT = ROOT / "refs/conformance/olmradialblur_a9d0_boundary_fork_20260718.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("radial_boundary_fork_20260718", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    runner = load_runner()
    assert runner.half_open_partition(3, 5, 8) == [(3, 5), (5, 8)]
    for invalid in ((3, 3, 8), (3, 9, 8), (8, 5, 3)):
        try:
            runner.half_open_partition(*invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid partition accepted: {invalid}")
    assert runner.non_overlapping({"a": (0, 4), "b": (4, 9)})
    assert not runner.non_overlapping({"a": (0, 5), "b": (4, 9)})

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "pass_boundary_fork_prepared"
    assert report["protected_pid_interactions"] == 0
    assert report["source_unchanged"] is True
    assert all(report["gates"].values()), report["gates"]
    assert report["bounded_proof"]["merge"]["serial_vs_two_slice_heap_equal"] is True
    assert report["bounded_proof"]["normalization_reached"] is True
    assert report["contract"]["caller_return"] == runner.A9D0_RETURN
    assert report["contract"]["caller_ebx"] == report["contract"]["caller_count"]
    for item in report["full_fork"]["slices"]:
        assert Path(item["checkpoint"]).is_file()
        assert runner.file_sha256(Path(item["checkpoint"])) == item["sha256"]
    print("PASS_OLMRADIALBLUR_A9D0_BOUNDARY_FORK_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
