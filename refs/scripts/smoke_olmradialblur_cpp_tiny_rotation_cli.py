#!/usr/bin/env python3
"""Regression guard for the C++ OLMRadialBlur smallest Rotation slice."""

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

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmradialblur_cpp_tiny_rotation_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0010",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "0.02",
        "--nonzero-px-percent",
        "1.7",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
