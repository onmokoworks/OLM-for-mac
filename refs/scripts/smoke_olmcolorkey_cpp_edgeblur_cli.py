#!/usr/bin/env python3
"""Smoke-test the C++ OLMColorKey Edge Blur/Lab76 exploratory slice."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmcolorkey_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmcolorkey_cpp_edgeblur_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMColorKey/olmcolorkey_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0008",
        "--case-id",
        "case_0009",
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "1.55",
        "--nonzero-px-percent",
        "50.0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
