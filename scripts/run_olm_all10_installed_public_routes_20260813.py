#!/usr/bin/env python3
"""Run the lightweight, AE-free all-ten installed public-route checkpoint."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    (sys.executable, "tools/emulation/audit_olm_all10_current_source_installed_authority_20260813.py"),
    (sys.executable, "-m", "unittest", "tests.test_olm_all10_current_source_installed_authority_20260813"),
    (sys.executable, "tools/emulation/test_olm_all10_current_installed_public_routes_20260813.py"),
    (sys.executable, "-m", "unittest", "tests.test_olm_all10_current_installed_public_routes_20260813"),
)


def main() -> int:
    for command in COMMANDS:
        run = subprocess.run(command, cwd=ROOT)
        if run.returncode:
            return run.returncode
    print("PASS_OLM_ALL10_INSTALLED_PUBLIC_ROUTES_LIGHTWEIGHT_AE_FREE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
