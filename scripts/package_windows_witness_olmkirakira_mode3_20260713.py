#!/usr/bin/env python3
"""Compile the real common-core OLMKiraKira Mode 3 live-Gaussian witness."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "refs/windows_witness_specs/olmkirakira_mode3_live_gaussian_20260713/witness-spec.json"
PACKAGE = ROOT / "refs/runtime_trace_packages/windows_witness_olmkirakira_mode3_20260713"
ARCHIVE = PACKAGE.with_suffix(".zip")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    zip_path = args.zip_path if args.zip_path.is_absolute() else ROOT / args.zip_path
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.windows_witness.compile",
            str(SPEC),
            "--output-dir",
            str(output_dir),
            "--zip",
            str(zip_path),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)
    print(json.dumps({"status": "ok", "compiler": "tools.windows_witness.compile", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
