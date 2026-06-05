#!/usr/bin/env python3
"""Run the Python OLM Distance Gradation CLI against stable green cases."""

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

    run_dir = Path("/tmp/olmdistancegradation_basic_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

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
        "--case-id",
        "case_0006",
        "--case-id",
        "case_0007",
        "--case-id",
        "case_0015",
        "--case-id",
        "case_0017",
        "--case-id",
        "case_0018",
        "--case-id",
        "case_0019",
        "--expected-effect",
        "OLM Distance Gradation",
        "--command",
        command,
        "--max-diff",
        "7",
        "--mean-diff",
        "0.11",
        "--nonzero-px-percent",
        "22.0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
