#!/usr/bin/env python3
"""Exercise the current release layout contract without building Xcode bundles."""
from pathlib import Path
import subprocess
import sys

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    raise SystemExit(subprocess.call([sys.executable, "-B", str(root / "tests/test_release_package_layout.py")]))
