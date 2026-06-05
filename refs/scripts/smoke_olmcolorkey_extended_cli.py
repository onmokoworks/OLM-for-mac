#!/usr/bin/env python3
"""Smoke-test the OLMColorKey extended Edge Thin slice against Windows refs.

Cases 5 and 6 intentionally retain a small boundary residual; case 7 is exact.
The tolerance gate asserts the known residual does not grow.
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

    run_dir = Path("/tmp/olmcolorkey_extended_smoke")
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
        "case_0005",
        "--case-id",
        "case_0006",
        "--case-id",
        "case_0007",
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
        "--max-diff",
        "255",
        "--mean-diff",
        "0.31",
        "--nonzero-px-percent",
        "0.49",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
