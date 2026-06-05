#!/usr/bin/env python3
"""Run OLMDirectionalBlur Python back-blur probes.

This intentionally red measurement ignores Noise Variation so the direct
Python scaffold can exercise the front+back scatter parameters in cases that
currently have no clean back-only Windows reference.
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

    run_dir = Path("/tmp/olmdirectionalblur_back_probe_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmdirectionalblur_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--algorithm direct --direction both --ignore-noise-variation "
        "--angle-sign -1 --sample-sign -1 --strength-scale auto "
        "--rgb-normalize total-strength"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0006",
        "--case-id",
        "case_0007",
        "--case-id",
        "case_0008",
        "--case-id",
        "case_0009",
        "--expected-effect",
        "OLM DirectionalBlur",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
