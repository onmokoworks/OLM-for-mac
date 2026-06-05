#!/usr/bin/env python3
"""Run OLMRadialBlur Zoom Offset/Size-Variation reference cases.

This is a near-match guard for cases 3-5. Size Variation is still explicitly
ignored by the CLI, so this smoke protects the current Zoom/Offset baseline
without claiming that Size Variation is implemented.
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

    run_dir = Path("/tmp/olmradialblur_zoom_offset_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmradialblur_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--algorithm zoom-polar --ignore-size-variation"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0003",
        "--case-id",
        "case_0004",
        "--case-id",
        "case_0005",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
        "--max-diff",
        "8",
        "--mean-diff",
        "0.05",
        "--nonzero-px-percent",
        "16.0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
