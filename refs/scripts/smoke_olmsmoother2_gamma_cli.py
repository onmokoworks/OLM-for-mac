#!/usr/bin/env python3
"""Green regression gate for OLMSmoother2 Gamma Colors cases.

Cases 10-12 exercise the disasm-confirmed FUN_18000bb10/FUN_18000a9c0
Gamma Colors path. This guards the Win setter fact that Gamma Colors are not
the frame-level FUN_180002930 alpha palette.
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

    run_dir = Path("/tmp/olmsmoother2_gamma_smoke")
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
        "--case-id", "case_0010",
        "--case-id", "case_0011",
        "--case-id", "case_0012",
        "--expected-effect", "OLM Smoother v2",
        "--command", command,
        "--max-diff", "170",
        "--mean-diff", "0.11",
        "--nonzero-px-percent", "0.51",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
