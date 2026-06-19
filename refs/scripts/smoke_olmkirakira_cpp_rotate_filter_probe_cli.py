#!/usr/bin/env python3
"""Run OLMKiraKira C++ rotation filter probes.

This intentionally red measurement checks whether alternate portable
warpAffine interpolation approximations move the native CLI toward the
Windows reference.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, rotate_filter: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMKiraKira"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMKiraKira/olmkirakira_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 --gain-scale 0.72 "
        "--ray-mode axis-rotate --compose-mode aex-premul "
        "--filter-border mirror --auto-length-scale --comp-width 1920 "
        f"--rotate-filter {rotate_filter}"
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
    for rotate_filter in (
        "bilinear",
        "bicubic",
        "bilinear-fixed5",
        "bilinear-fixed5-u16",
        "bilinear-fixed1024-floor5",
        "bilinear-fixed1024-round5",
        "bilinear-fixed1024-round5-u16",
        "nearest-fixed1024-u16-byteoffset",
        "bilinear-fixed1024-opencvtab",
    ):
        result = run_probe(root, rotate_filter, Path(f"/tmp/olmkirakira_cpp_rotate_filter_probe_{rotate_filter}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
