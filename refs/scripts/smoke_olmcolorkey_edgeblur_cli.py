#!/usr/bin/env python3
"""Smoke-test the exploratory OLMColorKey Edge Blur slice (cases 8-9).

This is a regression guard for the partially reconstructed Edge Blur/Lab76
path, not an exactness claim. See notes/PORTING_BOARD.md.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmcolorkey_edgeblur_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmcolorkey_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir", str(run_dir),
        "--case-id", "case_0008",
        "--case-id", "case_0009",
        "--expected-effect", "OLM Color Key",
        "--command", command,
        "--max-diff", "255",
        "--mean-diff", "1.26",
        "--nonzero-px-percent", "50.0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
