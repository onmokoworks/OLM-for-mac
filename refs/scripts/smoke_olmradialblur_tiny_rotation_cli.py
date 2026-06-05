#!/usr/bin/env python3
"""Regression guard for the smallest OLMRadialBlur Rotation slice.

case_0010 is Rotation / outer Strength=4 / no inner / no noise. The current
polar-grid port is not pixel-exact, but after the AEX-style Strength-1 tail
mapping it is close enough to guard as a green near-match.
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

    run_dir = Path("/tmp/olmradialblur_tiny_rotation_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmradialblur_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" --algorithm polar'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0010",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "0.02",
        "--nonzero-px-percent",
        "1.7",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
