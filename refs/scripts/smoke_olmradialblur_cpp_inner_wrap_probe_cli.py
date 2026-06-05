#!/usr/bin/env python3
"""Run C++ OLMRadialBlur inner angle-wrap probes.

This is intentionally red. It tests FUN_180001c90's inner-direction wrap, where
the decomp appears to move a negative angle wrap to the next radius row.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, mode: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--inner-source-scatter-prepass "
        "--inner-prepass-mode tail-gather "
        "--inner-prepass-span-mode edge-fade "
        "--inner-prepass-weight-mode row-span "
        "--inner-scatter-rgb-mode prepass-premul "
        "--inner-scatter-seed-mode source "
        f"--inner-wrap-mode {mode}"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0011",
        "--case-id",
        "case_0012",
        "--case-id",
        "case_0013",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
    ]
    print(f"\n=== inner-wrap={mode} ===", flush=True)
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    rc = 0
    for mode in ("circular", "aex-next-row"):
        result = run_probe(root, mode, Path(f"/tmp/olmradialblur_cpp_inner_wrap_probe_{mode}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
