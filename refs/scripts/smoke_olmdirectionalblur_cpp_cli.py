#!/usr/bin/env python3
"""Run the C++ OLMDirectionalBlur direct probe against front-only/no-noise cases.

This is an intentionally red measurement scaffold. The C++ CLI mirrors the
current Python direct/front-strength probe so future reverse-engineering passes
can iterate faster.
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

    run_dir = Path("/tmp/olmdirectionalblur_cpp_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMDirectionalBlur/olmdirectionalblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--angle-sign -1 --sample-sign -1 "
        "--strength-scale auto --rgb-normalize front-strength"
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
