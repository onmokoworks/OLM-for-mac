#!/usr/bin/env python3
"""Smoke-test the Rust OLMColorKey CLI RGB, Edge Thin, and Edge Blur slices."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_group(root: Path, reference: Path, run_dir: Path, case_ids: list[str], *threshold_args: str) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMColorKey/olmcolorkey_rust_cli" '
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


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    rc = subprocess.run([str(root / "refs" / "scripts" / "build_olmcolorkey_rust_cli.sh")], cwd=root).returncode
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_rgb_smoke"),
        ["case_0001", "case_0002", "case_0003", "case_0004"],
    )
    if rc != 0:
        return rc

    rc = run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_edgethin_smoke"),
        ["case_0005", "case_0006", "case_0007"],
        "--max-diff",
        "255",
        "--mean-diff",
        "0.31",
        "--nonzero-px-percent",
        "0.49",
    )
    if rc != 0:
        return rc

    return run_group(
        root,
        reference,
        Path("/tmp/olmcolorkey_rust_edgeblur_smoke"),
        ["case_0008", "case_0009"],
        "--max-diff",
        "255",
        "--mean-diff",
        "1.55",
        "--nonzero-px-percent",
        "50.0",
    )


if __name__ == "__main__":
    raise SystemExit(main())
