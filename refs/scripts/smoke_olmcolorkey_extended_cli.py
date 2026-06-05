#!/usr/bin/env python3
"""Smoke-test the OLMColorKey extended Edge Thin slice against Windows refs.

Cases 5 and 6 intentionally retain a small boundary residual; case 7 is exact.
Keep case 7 in an exact gate so it cannot regress inside the residual
tolerance for cases 5 and 6.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_group(root: Path, reference: Path, run_dir: Path, case_ids: list[str], *threshold_args: str) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        'python3 "refs/scripts/olmcolorkey_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}"'
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Color Key",
        "--command",
        command,
    ]
    for case_id in case_ids:
        args.extend(["--case-id", case_id])
    args.extend(threshold_args)
    return subprocess.run(args, cwd=root).returncode


def main():
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_edgethin_exact_smoke"),
        ["case_0007"],
    )
    if rc != 0:
        return rc

    return run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_edgethin_residual_smoke"),
        ["case_0005", "case_0006"],
        "--max-diff",
        "255",
        "--mean-diff",
        "0.31",
        "--nonzero-px-percent",
        "0.49",
    )


if __name__ == "__main__":
    raise SystemExit(main())
