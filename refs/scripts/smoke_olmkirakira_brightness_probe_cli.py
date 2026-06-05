#!/usr/bin/env python3
"""Measure the unresolved OLMKiraKira Brightness/Strength=0 path.

This smoke is intentionally red. case_0003 has Brightness Gain=9.4 and
Strength multiplier=0, but the Windows reference still emits dense white
KiraKira rays. The probe keeps that discrepancy reproducible while the vtable
and source/glow routing are still being reverse engineered.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMKiraKira"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmkirakira_brightness_probe_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmkirakira_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 --gain-scale 0.72 "
        "--ray-mode axis-rotate --compose-mode aex-premul "
        "--scale-mode aex --filter-border mirror "
        "--auto-length-scale --comp-width 1920"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0003",
        "--expected-effect",
        "OLM Kira Kira",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
