#!/usr/bin/env python3
"""Run RadialBlur C++ Inner Edge Fade factor-buffer probes on extra refs.

This is intentionally red. It uses the 20260605 extra RadialBlur references
where Inner Edge Fade is nonzero but Size Variation is still zero, so the
`FUN_180002780` factor buffer can be checked without the unsupported Size
Variation path.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


CASES = ("case_0024", "case_0025", "case_0027")


def run_probe(root: Path, mode: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260605_extra" / "OLMRadialBlur_img2"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--inner-source-scatter-prepass "
        "--inner-prepass-mode tail-gather "
        "--inner-prepass-span-mode edge-fade "
        "--inner-prepass-weight-mode aex-alpha "
        f"--inner-prepass-factor-mode {mode} "
        "--inner-scatter-rgb-mode prepass-premul "
        "--inner-scatter-seed-mode source"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
    ]
    for case_id in CASES:
        args.extend(["--case-id", case_id])
    print(f"\n=== inner-edgefade-factor-mode={mode} ===", flush=True)
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260605_extra" / "OLMRadialBlur_img2"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    rc = 0
    for mode in ("alpha", "one", "valid"):
        result = run_probe(root, mode, Path(f"/tmp/olmradialblur_cpp_inner_edgefade_factor_probe_{mode}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
