#!/usr/bin/env python3
"""Run C++ OLMRadialBlur inner alpha accumulator probes.

This is intentionally red. It mirrors the Python `--inner-alpha-mode` probe in
the native CLI so Inner Blur alpha handling can be compared without manual
commands.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, mode: str, run_dir: Path) -> int:
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    command = (
        '"cli/OLMRadialBlur/olmradialblur_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        f"--inner-alpha-mode {mode}"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--case-id",
        "case_0011",
        "--case-id",
        "case_0012",
        "--case-id",
        "case_0013",
        "--expected-effect",
        "OLM RadialBlur",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmradialblur_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    rc = 0
    for mode in ("max", "sum", "outer", "inner", "input"):
        result = run_probe(root, mode, Path(f"/tmp/olmradialblur_cpp_inner_alpha_mode_probe_{mode}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
