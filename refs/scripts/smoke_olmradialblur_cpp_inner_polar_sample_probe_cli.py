#!/usr/bin/env python3
"""Run C++ OLMRadialBlur Inner polar RGBA sampling probes.

This is intentionally red. It checks whether the AEX-style alpha-weighted RGBA
sampler used to populate the polar `+0xe` plane explains the remaining Inner
gap better than the current plain bilinear sampler.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROBES = ("plain", "aex-alpha")


def run_probe(root: Path, ref_dir: Path, case_ids: tuple[str, ...], label: str, mode: str) -> int:
    run_dir = Path(f"/tmp/olmradialblur_cpp_inner_polar_sample_probe_{label}_{mode}")
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--inner-source-scatter-prepass "
        "--inner-prepass-mode tail-gather "
        "--inner-prepass-span-mode edge-fade "
        "--inner-prepass-weight-mode aex-alpha "
        "--inner-prepass-factor-mode one "
        "--inner-scatter-rgb-mode prepass-premul "
        "--inner-scatter-seed-mode source "
        f"--polar-sample-mode {mode}"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(ref_dir),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])
    print(f"\n=== {label} polar-sample={mode} ===", flush=True)
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    old_ref = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    edge_ref = root / "refs" / "win_references" / "20260605_extra" / "OLMRadialBlur_img2"
    for ref in (old_ref, edge_ref):
        if not ref.exists():
            print(f"missing Windows reference directory: {ref}", file=sys.stderr)
            return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    rc = 0
    suites = (
        (old_ref, ("case_0011", "case_0012", "case_0013"), "old-inner"),
        (edge_ref, ("case_0024", "case_0025", "case_0027"), "edgefade"),
    )
    for ref_dir, case_ids, label in suites:
        for mode in PROBES:
            result = run_probe(root, ref_dir, case_ids, label, mode)
            if result != 0:
                rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
