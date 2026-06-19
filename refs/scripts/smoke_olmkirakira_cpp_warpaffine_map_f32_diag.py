#!/usr/bin/env python3
"""Verify the OLMKiraKira C++ WarpAffine map1/map2 diagnostic."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    build = subprocess.run([str(root / "refs" / "scripts" / "build_olmkirakira_cli.sh")], cwd=root)
    if build.returncode != 0:
        return build.returncode
    return subprocess.run(
        [str(root / "cli" / "OLMKiraKira" / "olmkirakira_cli"), "--diag-warpaffine-map-f32"],
        cwd=root,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
