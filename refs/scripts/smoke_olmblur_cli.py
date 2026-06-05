#!/usr/bin/env python3
"""Smoke-test the OLMBlur C++ CLI against all Windows refs.

The current CPU CLI is exact for cases 1/2/4 and within max-diff 1 for the
remaining high-radius or legacy cases. Keep those gates separate so exact cases
cannot regress inside the residual tolerance.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_group(root: Path, reference: Path, run_dir: Path, case_ids: list[str], *threshold_args: str) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMBlur/olmblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Blur",
        "--command",
        command,
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])
    args.extend(threshold_args)
    return subprocess.run(args, cwd=root).returncode


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMBlur"
    cli = root / "cli" / "OLMBlur" / "olmblur_cli"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1
    if not cli.exists():
        print(f"missing CLI binary (run build_olmblur_cli.sh): {cli}", file=sys.stderr)
        return 1

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmblur_exact_smoke"),
        ["case_0001", "case_0002", "case_0004"],
    )
    if rc != 0:
        return rc

    return run_group(
        root,
        reference,
        Path("/tmp/olmblur_residual_smoke"),
        ["case_0003", "case_0005", "case_0006", "case_0007"],
        "--max-diff",
        "1",
        "--mean-diff",
        "0.01",
        "--nonzero-px-percent",
        "3.0",
    )


if __name__ == "__main__":
    raise SystemExit(main())
