#!/usr/bin/env python3
"""Run OLMSmoother2 source/class plane split diagnostics.

This intentionally red probe checks whether the remaining no-key case_0001
residual comes from class-plane generation and FUN_1800104d0 sample reads using
different frame-setup timing planes.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROBES = (
    "none",
    "sample-pre-setup",
    "class-pre-setup",
    "sample-pre-gamma",
    "class-pre-gamma",
)


def run_probe(root: Path, mode: str, run_dir: Path) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMSmoother2/olmsmoother2_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        f"--plane-split-mode {mode}"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(root / "refs" / "win_references" / "20260605_extra" / "OLMSmoother2"),
        "--run-dir", str(run_dir),
        "--case-id", "case_0001",
        "--expected-effect", "OLM Smoother v2",
        "--command", command,
    ]
    return subprocess.run(args, cwd=root).returncode


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260605_extra" / "OLMSmoother2"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmsmoother2_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    rc = 0
    for mode in PROBES:
        print(f"\n=== plane-split-mode={mode} ===", flush=True)
        result = run_probe(root, mode, Path(f"/tmp/olmsmoother2_plane_split_probe_{mode}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
