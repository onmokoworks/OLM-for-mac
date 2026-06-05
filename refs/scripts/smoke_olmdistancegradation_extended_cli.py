#!/usr/bin/env python3
"""Run extended OLM Distance Gradation non-blur reference coverage.

These cases cover the currently near-matching render-layer, background,
constant, sphere, and power interpolation paths. The blur case remains excluded
because it is still a large red measurement target.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmdistancegradation_extended_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    case_ids = [
        "case_0008",
        "case_0010",
        "case_0011",
        "case_0012",
        "case_0013",
        "case_0014",
        "case_0016",
        "case_0020",
        "case_0021",
        "case_0022",
        "case_0023",
        "case_0024",
        "case_0025",
        "case_0026",
        "case_0027",
        "case_0028",
    ]

    command = (
        'python3 "refs/scripts/olmdistancegradation_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Distance Gradation",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "0.72",
        "--nonzero-px-percent",
        "51.0",
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
