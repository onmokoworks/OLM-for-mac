#!/usr/bin/env python3
"""Green regression gate for OLMSmoother2 key-path cases.

Cases 2-4 exercise the disasm-confirmed active-palette and scalar-key paths.
They are now near/exact against the Windows reference and should stay guarded
while the remaining no-key polygon/smoother residual in case_0001 is refined.
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

    run_dir = Path("/tmp/olmsmoother2_keypaths_smoke")
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
        "--case-id", "case_0002",
        "--case-id", "case_0003",
        "--case-id", "case_0004",
        "--expected-effect", "OLM Smoother v2",
        "--command", command,
        "--max-diff", "95",
        "--mean-diff", "0.022",
        "--nonzero-px-percent", "0.15",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
