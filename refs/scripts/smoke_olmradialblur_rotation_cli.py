#!/usr/bin/env python3
"""Run the experimental OLMRadialBlur Rotation slice against outer-only cases.

This smoke is expected to report DIFF until the full polar-grid/two-pass AEX
algorithm is ported. It is intentionally not tolerance-gated green, but it now
uses the AEX-shaped polar-grid experiment rather than the older direct sampler.
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

    run_dir = Path("/tmp/olmradialblur_rotation_smoke")
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
        "case_0001",
        "--case-id",
        "case_0002",
        "--case-id",
        "case_0010",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
