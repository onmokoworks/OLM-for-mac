#!/usr/bin/env python3
"""Compile the common-core OLMSmoother2 legacy producer witness."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "refs/windows_witness_specs/olmsmoother2_legacy_key_producer_common_core_20260716/witness-spec.json"
DEFAULT_OUTPUT = ROOT / "refs/runtime_trace_packages/windows_witness_olmsmoother2_legacy_key_producer_common_core_20260716"
DEFAULT_ZIP = DEFAULT_OUTPUT.with_suffix(".zip")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args(argv)
    output = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    archive = args.zip_path if args.zip_path.is_absolute() else ROOT / args.zip_path
    completed = subprocess.run([sys.executable, "-m", "tools.windows_witness.compile", str(SPEC), "--output-dir", str(output), "--zip", str(archive)], cwd=ROOT, check=True, text=True, capture_output=True)
    result = json.loads(completed.stdout)
    print(json.dumps({"status": "ok", "compiler": "tools.windows_witness.compile", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
