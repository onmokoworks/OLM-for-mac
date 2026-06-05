#!/usr/bin/env python3
"""Run C++ OLMRadialBlur inner prepass mode probes.

This is intentionally red. It compares the current simple source-scatter
prepass against a first-pass FUN_180002780-style two-direction tail gather.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, mode: str, span_mode: str, weight_mode: str, rgb_mode: str, seed_mode: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--inner-source-scatter-prepass "
        f"--inner-prepass-mode {mode} "
        f"--inner-prepass-span-mode {span_mode} "
        f"--inner-prepass-weight-mode {weight_mode} "
        f"--inner-scatter-rgb-mode {rgb_mode} "
        f"--inner-scatter-seed-mode {seed_mode}"
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
    print(
        f"\n=== inner-prepass-mode={mode} span={span_mode} weight={weight_mode} rgb={rgb_mode} seed={seed_mode} ===",
        flush=True,
    )
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
        ("simple", "strength", "row-span", "straight", "source"),
        ("tail-gather", "strength", "row-span", "straight", "source"),
        ("tail-gather", "strength", "aex-alpha", "straight", "source"),
        ("tail-gather", "offset", "row-span", "straight", "source"),
        ("tail-gather", "edge-fade", "row-span", "straight", "source"),
        ("tail-gather", "offset", "row-span", "prepass-premul", "source"),
        ("tail-gather", "strength", "aex-alpha", "prepass-premul", "source"),
        ("tail-gather", "edge-fade", "row-span", "prepass-premul", "source"),
        ("tail-gather", "strength", "row-span", "prepass-premul", "none"),
        ("tail-gather", "strength", "aex-alpha", "prepass-premul", "none"),
        ("tail-gather", "edge-fade", "row-span", "prepass-premul", "none"),
    ]
    for mode, span_mode, weight_mode, rgb_mode, seed_mode in probes:
        result = run_probe(
            root,
            mode,
            span_mode,
            weight_mode,
            rgb_mode,
            seed_mode,
            Path(f"/tmp/olmradialblur_cpp_inner_prepass_mode_probe_{mode}_{span_mode}_{weight_mode}_{rgb_mode}_{seed_mode}"),
        )
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
