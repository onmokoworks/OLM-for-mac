#!/usr/bin/env python3
"""Self-contained smoke for the fail-closed case0012 c280 boundary probe."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SOURCE = ROOT / "tools/emulation/smoother2_case0012_c280_post_division_adapter_20260717.cpp"
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_post_division_boundary_20260717.py"
EXPECTED = "BLOCKED_CASE0012_POST_DIVISION_C280_NEIGHBOR_SEAM"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_c280_boundary_smoke_") as temp:
        work = Path(temp)
        adapter = work / "adapter"
        report = work / "report.json"
        build_command = [
            "clang++", "-std=c++17", "-O2",
            "-I", "cli/OLMSmoother2/shim",
            "-I", "mac/OLMSmoother2",
            str(ADAPTER_SOURCE), "-o", str(adapter),
        ]
        build = subprocess.run(build_command, cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr

        run_command = [
            sys.executable, str(PROBE),
            "--adapter", str(adapter),
            "--output", str(report),
        ]
        run = subprocess.run(run_command, cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 2, run.stdout + run.stderr
        result = json.loads(report.read_text(encoding="utf-8"))

    assert result["verdict"] == EXPECTED
    assert result["differential"] == {
        "c280_count_equal": True,
        "c280_vertices_equal": True,
        "cce0_rgba_equal_1e-6": True,
    }
    blocker = result["blocker"]
    assert "Only center, previous, and left class pixels are retained" in blocker
    assert "All other class bytes were zero-filled" in blocker
    assert "cannot localize the live post-division c280 seam" in blocker
    print("PASS: blocked case0012 c280 boundary smoke is fail-closed")
    print("build: " + " ".join(build_command))
    print("run: " + " ".join(run_command))
    print("probe exit: 2")
    print("verdict: " + result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
