#!/usr/bin/env python3
"""Run the C++ OLMDirectionalBlur rotated/front-strength preserve-alpha probe.

This intentionally red measurement combines the rotated-buffer scaffold with
the direct probe's front-strength RGB denominator, while preserving input alpha
on rotate-back. It is a small positive split for front-only cases, not a
validated AEX port.
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

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmdirectionalblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmdirectionalblur_cpp_rotated_front_strength_preserve_alpha_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMDirectionalBlur/olmdirectionalblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--algorithm rotated-front-strength-preserve-alpha "
        "--angle-sign -1 --sample-sign 1 --strength-scale auto"
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
