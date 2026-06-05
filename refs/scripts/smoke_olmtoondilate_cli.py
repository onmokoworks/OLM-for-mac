#!/usr/bin/env python3
"""Smoke-test the OLMToonDilate CLI against Windows refs (cases 1-3).

These cases vary only Search Radius (13, 13, 27) and render resolution. The CLI
reproduces the decomp's Chebyshev-chamfer dilation with nearest-opaque colour;
a small boundary residual remains versus the current references (it scales with
radius). ADBE Force CPU GPU=1 is not a render-path indicator; compare CUDA vs
Software renders via a separately recorded project_gpu_accel_type field. See
notes/PORTING_BOARD.md.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmtoondilate_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmtoondilate_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" --comp-width 1920'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir", str(run_dir),
        "--case-id", "case_0001",
        "--case-id", "case_0002",
        "--case-id", "case_0003",
        "--expected-effect", "OLM Toon Dilate",
        "--command", command,
        # Regression-guard bounds: the CPU port matches the current reference
        # to within ~1.6% of pixels (case_0003, R=27). max-diff is 255 because
        # the residual is binary-alpha boundary flips. This asserts "no worse
        # than the documented boundary gap", not pixel-exactness.
        "--max-diff", "255",
        "--mean-diff", "4.0",
        "--nonzero-px-percent", "1.7",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
