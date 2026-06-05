#!/usr/bin/env python3
"""Smoke-test the OLMSmoother C++ CLI against Windows refs (cases 1-3).

Builds nothing; assumes cli/OLMSmoother/olmsmoother_cli exists
(refs/scripts/build_olmsmoother_cli.sh). These cases use Use Color Key=0,
Do Smooth Range=6, 8bpc. NOTE: ADBE Force CPU GPU=1 is not a render-path
indicator; compare CUDA vs Software renders via a separately recorded
project_gpu_accel_type field. The CLI runs the CPU MLAA path ported from the
Windows .aex, so exact agreement is not expected yet — see notes/PORTING_BOARD.md.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMSmoother"
    cli = root / "cli" / "OLMSmoother" / "olmsmoother_cli"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1
    if not cli.exists():
        print(f"missing CLI binary (run build_olmsmoother_cli.sh): {cli}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmsmoother_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMSmoother/olmsmoother_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir", str(run_dir),
        "--case-id", "case_0001",
        "--case-id", "case_0002",
        "--case-id", "case_0003",
        "--expected-effect", "OLM Smoother",
        "--command", command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
