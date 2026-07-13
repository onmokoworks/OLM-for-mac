#!/usr/bin/env python3
"""Verify the binary-grounded, behavior-preserving Mode 3/4 boundary."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI_SOURCE = ROOT / "cli" / "OLMKiraKira" / "main.cpp"
MAC_SOURCE = ROOT / "mac" / "OLMKiraKira" / "OLMKiraKira.cpp"


def main() -> int:
    cli = CLI_SOURCE.read_text(encoding="utf-8")
    mac = MAC_SOURCE.read_text(encoding="utf-8")
    required = (
        "FUN_181272ec0 (GaussianBlur)",
        "recursive/separable body",
        "do not substitute PNG-tuned math here",
    )
    for source_name, source in (("CLI", cli), ("Mac", mac)):
        for marker in required:
            if marker not in source:
                raise SystemExit(f"{source_name} missing boundary marker: {marker}")

    build = ROOT / "refs" / "scripts" / "build_olmkirakira_cli.sh"
    subprocess.run([str(build)], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    smoke = ROOT / "refs" / "scripts" / "smoke_olmkirakira_blur_mode_dispatch.py"
    result = subprocess.run([str(smoke)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout, end="")
        print(result.stderr, end="")
        return result.returncode
    print("[PASS] Mode 3/4 remain explicitly narrowed to the Mode 2 scaffold")
    print("[PASS] Existing Mode 1/2 dispatch regression remains green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
