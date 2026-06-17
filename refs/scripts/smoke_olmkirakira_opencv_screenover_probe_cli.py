#!/usr/bin/env python3
"""Run OLMKiraKira OpenCV two-temp probe with current screen-over composition.

This is a measurement probe, not a green byte-match gate. It requires a Python
with cv2; set OLM_PROBE_PYTHON to a venv containing opencv-python-headless.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    reference = root / "refs" / "win_references" / "olm_reference_return_windows_20260614" / "OLMKiraKira"
    if not reference.exists():
        print(f"missing Windows reference directory: {reference}", file=sys.stderr)
        return 1

    python = os.environ.get("OLM_PROBE_PYTHON", sys.executable)
    cv2_check = subprocess.run(
        [python, "-c", "import cv2; print(cv2.__version__)"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if cv2_check.returncode != 0:
        print(
            f"missing cv2 for {python}; set OLM_PROBE_PYTHON to an environment with opencv-python",
            file=sys.stderr,
        )
        print(cv2_check.stderr, file=sys.stderr)
        return cv2_check.returncode
    print(f"cv2: {cv2_check.stdout.strip()}")

    run_dir = Path("/tmp/olmkirakira_opencv_screenover_probe")
    if run_dir.exists():
        shutil.rmtree(run_dir)

    command = (
        f'"{python}" "refs/scripts/olmkirakira_cli.py" '
        '--input "{input}" --params "{params}" --output "{output}" '
        "--seed-mode aex --falloff box3 --gain-scale 0.62 "
        "--ray-mode opencv-two-temp --compose-mode aex-screen-over "
        "--scale-mode aex-screen-over --auto-length-scale --comp-width 1920 "
        "--zero-ray-skip"
    )
    args = [
        sys.executable,
        str(root / "refs" / "scripts" / "run_reference_test.py"),
        str(reference),
        "--run-dir",
        str(run_dir),
        "--expected-effect",
        "OLM Kira Kira",
        "--max-diff",
        "80",
        "--mean-diff",
        "2.0",
        "--nonzero-px-percent",
        "100",
        "--command",
        command,
    ]
    return subprocess.run(args, cwd=root).returncode


if __name__ == "__main__":
    raise SystemExit(main())
