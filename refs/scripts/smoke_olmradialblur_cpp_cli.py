#!/usr/bin/env python3
"""Run the C++ OLMRadialBlur Zoom Offset slice.

This guards the current C++ port of the no-noise Zoom polar kernel. Size
Variation is still explicitly ignored, matching the Python exploratory guard.
"""

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

    run_dir = Path("/tmp/olmradialblur_cpp_zoom_offset_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--ignore-size-variation"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0003",
        "--case-id",
        "case_0004",
        "--case-id",
        "case_0005",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
        "--max-diff",
        "8",
        "--mean-diff",
        "0.01",
        "--nonzero-px-percent",
        "16.0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
