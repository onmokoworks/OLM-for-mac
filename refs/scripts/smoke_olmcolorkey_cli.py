#!/usr/bin/env python3
"""Smoke-test the OLMColorKey RGB/binary-alpha CLI against Windows refs."""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmcolorkey_rgb_smoke")
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
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
