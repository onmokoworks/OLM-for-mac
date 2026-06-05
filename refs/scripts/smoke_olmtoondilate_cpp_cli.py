#!/usr/bin/env python3
"""Smoke-test the C++ OLMToonDilate CLI against Windows refs."""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmtoondilate_cpp_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMToonDilate/olmtoondilate_cli" '
        '--input "{input}" --params "{params}" --output "{output}" --comp-width 1920'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir", str(run_dir),
        "--case-id", "case_0001",
        "--case-id", "case_0002",
        "--case-id", "case_0003",
        "--expected-effect", "OLM Toon Dilate",
        "--command", command,
        "--max-diff", "255",
        "--mean-diff", "3.1",
        "--nonzero-px-percent", "1.7",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
