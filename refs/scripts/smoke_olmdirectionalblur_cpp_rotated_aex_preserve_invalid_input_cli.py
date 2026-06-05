#!/usr/bin/env python3
"""Run OLMDirectionalBlur C++ AEX preserve-invalid-input probe.

This intentionally red diagnostic keeps the centered source canvas in the first
rotate destination when the AEX-shaped rotate helper would skip an invalid
sample. It tests whether input-rotate invalid-pixel destination ownership is a
meaningful contributor to the current front-only residual.
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

    run_dir = Path("/tmp/olmdirectionalblur_cpp_rotated_aex_preserve_invalid_input_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMDirectionalBlur/olmdirectionalblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--algorithm rotated-aex-preserve-invalid-input "
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
        "case_0005",
        "--expected-effect",
        "OLM DirectionalBlur",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
