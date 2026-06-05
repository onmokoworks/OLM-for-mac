#!/usr/bin/env python3
"""Run OLMKiraKira C++ boxFilter output-depth probes.

This intentionally red measurement checks whether repeated boxFilter ray
buffers are rounded to integer image depth between passes.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, box_output_depth: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMKiraKira"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMKiraKira/olmkirakira_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 --gain-scale 0.72 "
        "--ray-mode axis-rotate --compose-mode aex-premul "
        "--filter-border mirror --rotate-border constant "
        "--auto-length-scale --comp-width 1920 "
        f"--box-output-depth {box_output_depth}"
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
        "--expected-effect",
        "OLM Kira Kira",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMKiraKira"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmkirakira_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    rc = 0
    for box_output_depth in ("float", "u8-each", "u16-each"):
        result = run_probe(root, box_output_depth, Path(f"/tmp/olmkirakira_cpp_box_output_depth_probe_{box_output_depth}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
