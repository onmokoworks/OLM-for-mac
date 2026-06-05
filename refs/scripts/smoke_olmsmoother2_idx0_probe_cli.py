#!/usr/bin/env python3
"""Run OLMSmoother2 idx=0 four-corner diagnostic probes.

This intentionally red probe isolates the case_0001 residual dominated by
FUN_18000c280 switch index 0x00. It does not propose a production fix; it
measures whether suppressing or scaling only that dispatch explains the
remaining no-key/v2 residual.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run_probe(root: Path, mode: str, run_dir: Path) -> int:
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMSmoother2/olmsmoother2_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        f"--idx0-mode {mode}"
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
    for mode in ("none", "suppress", "half", "quarter"):
        print(f"\n=== idx0-mode={mode} ===", flush=True)
        result = run_probe(root, mode, Path(f"/tmp/olmsmoother2_idx0_probe_{mode}"))
        if result != 0:
            rc = result
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
