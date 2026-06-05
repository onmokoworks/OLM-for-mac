#!/usr/bin/env python3
"""Smoke-test the C++ OLMColorKey CLI RGB and Edge Thin slices."""

import shutil
import subprocess
import sys
from pathlib import Path


def run_group(root, reference, run_dir, case_ids, *threshold_args):
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMColorKey/olmcolorkey_cli" '
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

    rc = subprocess.run([str(root / "refs" / "scripts" / "build_olmcolorkey_cli.sh")], cwd=root).returncode
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_cpp_rgb_smoke"),
        ["case_0001", "case_0002", "case_0003", "case_0004"],
    )
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_cpp_edgethin_exact_smoke"),
        ["case_0007"],
    )
    if rc != 0:
        return rc

    return run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_cpp_edgethin_residual_smoke"),
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
