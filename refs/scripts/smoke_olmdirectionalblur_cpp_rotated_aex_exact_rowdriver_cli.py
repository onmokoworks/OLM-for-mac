#!/usr/bin/env python3
"""Run OLMDirectionalBlur C++ exact row-driver probe.

This intentionally red diagnostic combines the A/B full choreography,
FUN_180001000-shaped row prepass, and FUN_1800013e0-shaped source-driven
scatter helper in one measurement.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, reference: Path, algorithm: str, run_dir: Path) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMDirectionalBlur/olmdirectionalblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        f"--algorithm {algorithm} "
        "--angle-sign -1 --sample-sign 1 --strength-scale auto"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0001",
        "--case-id",
        "case_0005",
        "--expected-effect",
        "OLM DirectionalBlur",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMDirectionalBlur"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmdirectionalblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    probes = [
        ("rotated-aex-full-choreo", Path("/tmp/olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_full")),
        ("rotated-aex-exact-scatter-helper", Path("/tmp/olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_scatter")),
        ("rotated-aex-exact-rowdriver", Path("/tmp/olmdirectionalblur_cpp_rotated_aex_exact_rowdriver")),
    ]

    rc = 0
    for algorithm, run_dir in probes:
        print(f"\n=== algorithm={algorithm} ===", flush=True)
        result = run_probe(root, reference, algorithm, run_dir)
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
