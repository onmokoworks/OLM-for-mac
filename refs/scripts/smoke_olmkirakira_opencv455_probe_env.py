#!/usr/bin/env python3
"""Check the local OpenCV 4.5.5 probe environment for OLMKiraKira.

This is intentionally lightweight: it does not create the venv or install
packages. Use setup_olmkirakira_opencv455_probe_env.sh for that.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_PYTHON = Path("/tmp/olm_cv455_probe_venv/bin/python")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python",
        default=os.environ.get("OLM_PROBE_PYTHON", str(DEFAULT_PYTHON)),
        help="probe Python executable (default: OLM_PROBE_PYTHON or /tmp/olm_cv455_probe_venv/bin/python)",
    )
    parser.add_argument(
        "--require",
        action="store_true",
        help="fail when the probe environment is missing instead of reporting SKIP",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    python = Path(args.python).expanduser()
    setup_hint = "refs/scripts/setup_olmkirakira_opencv455_probe_env.sh"

    if not python.exists():
        message = f"missing OLMKiraKira OpenCV probe Python: {python}"
        if args.require:
            print(f"[FAIL] {message}; run {setup_hint}", file=sys.stderr)
            return 1
        print(f"[SKIP] {message}; run {setup_hint}")
        return 0

    check = (
        "import cv2, json, numpy as np, sys; "
        "print(json.dumps({"
        "'python': sys.executable, "
        "'cv2': cv2.__version__, "
        "'numpy': np.__version__"
        "}, sort_keys=True))"
    )
    result = subprocess.run(
        [str(python), "-c", check],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        print(
            f"[FAIL] {python} could not import cv2/numpy; run {setup_hint}",
            file=sys.stderr,
        )
        print(result.stderr, file=sys.stderr)
        return result.returncode

    versions = json.loads(result.stdout)
    if versions["cv2"] != "4.5.5":
        print(
            f"[FAIL] expected cv2 4.5.5, got {versions['cv2']} from {versions['python']}",
            file=sys.stderr,
        )
        return 1
    if not versions["numpy"].startswith("1.26."):
        print(
            f"[FAIL] expected numpy 1.26.x, got {versions['numpy']} from {versions['python']}",
            file=sys.stderr,
        )
        return 1

    print(
        "[OK] OLMKiraKira OpenCV probe env: "
        f"python={versions['python']} cv2={versions['cv2']} numpy={versions['numpy']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
