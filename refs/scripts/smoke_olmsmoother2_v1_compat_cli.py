#!/usr/bin/env python3
"""Green compatibility gate for OLMSmoother2 forced-v1 mode.

It runs the v2 plug-in's `Smoother Version = 1` path against the standalone
OLMSmoother v1 references. The residual is tiny compared with the standalone
v1 port's current over-triggering, so this guards the preferred migration path
before spending more reverse-engineering time on OLMSmoother v1.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "20260604_olm" / "OLMSmoother"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmsmoother2_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode

    run_dir = Path("/tmp/olmsmoother2_v1_compat_smoke")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        '"cli/OLMSmoother2/olmsmoother2_cli" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--force-version 1"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Smoother",
        "--command",
        command,
        "--max-diff",
        "124",
        "--mean-diff",
        "0.021",
        "--nonzero-px-percent",
        "0.33",
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
