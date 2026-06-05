#!/usr/bin/env python3
"""Run the C++ OLMDirectionalBlur AEX row-driver prepass probes.

These intentionally red measurements exercise a FUN_180001000-shaped alpha
prepass before the existing rotated row scatter, with and without the
caller-style copied-buffer initialization variant. They are diagnostic-only
and are not validated Mac plug-in paths.
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
    print(f"\n=== algorithm={algorithm} ===", flush=True)
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
        ("rotated-rowdriver-prepass", Path("/tmp/olmdirectionalblur_cpp_rotated_rowdriver_prepass_smoke")),
        ("rotated-rowdriver-prepass-init", Path("/tmp/olmdirectionalblur_cpp_rotated_rowdriver_prepass_init_smoke")),
    ]
    saw_diff = False
    for algorithm, run_dir in probes:
        result = run_probe(root, reference, algorithm, run_dir)
        if result == 0:
            return 0
        if result == 1:
            saw_diff = True
            continue
        return result
    return 1 if saw_diff else 0


if __name__ == "__main__":
    raise SystemExit(main())
