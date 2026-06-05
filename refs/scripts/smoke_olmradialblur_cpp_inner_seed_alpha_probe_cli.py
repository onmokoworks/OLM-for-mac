#!/usr/bin/env python3
"""Run C++ OLMRadialBlur inner seed-alpha probes.

This is intentionally red. It separates FUN_180002780's accumulation seed
alpha from FUN_1800024c0's scatter source RGB mode.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, seed_alpha: str, scatter_rgb: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--inner-source-scatter-prepass "
        "--inner-prepass-mode tail-gather "
        "--inner-prepass-span-mode strength "
        "--inner-prepass-weight-mode row-span "
        f"--inner-scatter-rgb-mode {scatter_rgb} "
        "--inner-scatter-seed-mode source "
        f"--inner-seed-alpha-mode {seed_alpha}"
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
    print(f"\n=== seed-alpha={seed_alpha} scatter-rgb={scatter_rgb} ===", flush=True)
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
    probes = [
        ("input", "straight"),
        ("prepass", "straight"),
        ("input", "prepass-premul"),
        ("prepass", "prepass-premul"),
    ]
    for seed_alpha, scatter_rgb in probes:
        result = run_probe(
            root,
            seed_alpha,
            scatter_rgb,
            Path(f"/tmp/olmradialblur_cpp_inner_seed_alpha_probe_{seed_alpha}_{scatter_rgb}"),
        )
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
