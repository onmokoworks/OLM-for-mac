#!/usr/bin/env python3
"""Exact C++ OLMToonDilate check against normalized Windows AE Software refs."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = (
        root
        / "refs"
        / "reports"
        / "ae_host_validation_20260618_232926"
        / "normalized_refs"
        / "OLMToonDilate"
    )
    if not reference.exists():
        print(f"missing normalized Windows Software reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = root / "refs" / "reports" / "ae_host_validation_20260618_232926" / "smoke_runs" / "olmtoondilate_cpp_exact"
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMToonDilate/olmtoondilate_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Toon Dilate",
        "--command",
        command,
        "--max-diff",
        "0",
        "--mean-diff",
        "0",
        "--nonzero-px-percent",
        "0",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
