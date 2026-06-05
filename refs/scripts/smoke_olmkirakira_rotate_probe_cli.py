#!/usr/bin/env python3
"""Run OLMKiraKira Python rotation interpolation probes.

This intentionally red measurement captures the mixed evidence around
SciPy cubic rotation. It improves cases 1/2 but worsens the Strength=0 case,
so it should not replace the current C++/Mac bilinear scaffold.
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

    run_dir = Path("/tmp/olmkirakira_rotate_probe_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmkirakira_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 --gain-scale 0.72 "
        "--ray-mode axis-rotate --compose-mode aex-premul "
        "--scale-mode aex --filter-border mirror "
        "--auto-length-scale --comp-width 1920 "
        "--rotate-order 3 --rotate-prefilter"
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
        "case_0003",
        "--expected-effect",
        "OLM Kira Kira",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
