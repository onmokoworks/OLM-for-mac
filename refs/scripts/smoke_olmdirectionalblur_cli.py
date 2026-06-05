#!/usr/bin/env python3
"""Run the experimental OLMDirectionalBlur slice against the first probe case.

This smoke is expected to report DIFF. The current CLI is a measurement
scaffold for front-only/no-noise DirectionalBlur reconstruction.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMDirectionalBlur"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmdirectionalblur_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmdirectionalblur_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--algorithm direct --angle-sign -1 --sample-sign -1 "
        "--strength-scale auto --rgb-normalize front-strength"
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
        "--case-id",
        "case_0004",
        "--case-id",
        "case_0005",
        "--expected-effect",
        "OLM DirectionalBlur",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
