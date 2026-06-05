#!/usr/bin/env python3
"""Smoke-test the OLMBlur C++ CLI against all Windows refs.

The current CPU CLI is exact for cases 1/2/4 and within max-diff 1 for the
remaining high-radius or legacy cases. This smoke test guards that known PNG /
rounding-level residual while keeping the expected effect name honest.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMBlur"
    cli = root / "cli" / "OLMBlur" / "olmblur_cli"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1
    if not cli.exists():
        print(f"missing CLI binary (run build_olmblur_cli.sh): {cli}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmblur_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMBlur/olmblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir", str(run_dir),
        "--expected-effect", "OLM Blur",
        "--command", command,
        "--max-diff", "1",
        "--mean-diff", "0.01",
        "--nonzero-px-percent", "3.0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
