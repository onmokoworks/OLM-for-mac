#!/usr/bin/env python3
"""Production regression for the actual-AEX-absent PF32 Smart path."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/emulation/dg_pf32_smart_fail_closed_harness_20260810.cpp"

with tempfile.TemporaryDirectory(prefix="olmdg_pf32_smart_guard_") as raw:
    executable = Path(raw) / "probe"
    build = subprocess.run([
        "clang++", "-std=c++17", "-O0",
        "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
        str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"),
        "-o", str(executable),
    ], cwd=ROOT, capture_output=True, text=True)
    assert build.returncode == 0, build.stderr
    run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "PASS PF32 Smart fail-closed before host checkout"
print("PASS_OLMDISTANCEGRADATION_PF32_SMART_FAIL_CLOSED_20260810")
