#!/usr/bin/env python3
"""Measure the OLMSmoother2 C++ CLI against the 20260605 Windows refs.

This is an expected-red measurement smoke for now. It proves the new
OLMSmoother2 reference set can drive the mac port outside After Effects and
keeps the current residual visible while the class-plane/polygon/smoother core
is refined. The Color Key + Invert active-palette path is already
disasm-confirmed and near-green on case_0002.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260605_extra" / "OLMSmoother2"
    cli = root / "cli" / "OLMSmoother2" / "olmsmoother2_cli"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1
    if not cli.exists():
        print(f"missing CLI binary (run build_olmsmoother2_cli.sh): {cli}", file=sys.stderr)
        return 1

    run_dir = Path("/tmp/olmsmoother2_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMSmoother2/olmsmoother2_cli" '
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
        "--case-id", "case_0004",
        "--expected-effect", "OLM Smoother v2",
        "--command", command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
