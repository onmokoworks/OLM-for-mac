#!/usr/bin/env python3
"""Run the OLMRadialBlur Zoom no-noise slice.

This is a near-match regression guard for Blur Type=1 case_0009. The remaining
max=1 residual is 8-bit rounding / alpha-floor level, not a gross algorithm
gap.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmradialblur_zoom_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmradialblur_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" --algorithm zoom-polar'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0009",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
        "--max-diff",
        "1",
        "--mean-diff",
        "0.01",
        "--nonzero-px-percent",
        "2.1",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
