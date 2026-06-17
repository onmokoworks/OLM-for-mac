#!/usr/bin/env python3
"""Measure the OLMKiraKira Strength=0 Brightness half-gain path."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "olm_reference_return_windows_recapture_20260615" / "OLMKiraKira"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmkirakira_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmkirakira_brightness_probe_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMKiraKira/olmkirakira_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 --gain-scale 0.62 "
        "--ray-mode axis-rotate --compose-mode aex-screen-over "
        "--filter-border mirror "
        "--auto-length-scale --comp-width 1920"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Kira Kira",
        "--max-diff",
        "1",
        "--mean-diff",
        "0.04",
        "--nonzero-px-percent",
        "6.2",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
