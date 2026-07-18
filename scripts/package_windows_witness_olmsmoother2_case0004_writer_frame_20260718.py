#!/usr/bin/env python3
"""Compile the same-run OLMSmoother2 case_0004 writer-frame witness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.windows_witness.compiler import compile_witness  # noqa: E402

SPEC = ROOT / "refs/windows_witness_specs/olmsmoother2_case0004_writer_frame_20260718/witness-spec.json"
OUTPUT_DIR = ROOT / "refs/runtime_trace_packages/windows_witness_olmsmoother2_case0004_writer_frame_20260718"
OUTPUT_ZIP = OUTPUT_DIR.with_suffix(".zip")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=OUTPUT_ZIP)
    args = parser.parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    zip_path = args.zip_path if args.zip_path.is_absolute() else ROOT / args.zip_path
    package, archive = compile_witness(SPEC, output_dir, zip_path)
    print(json.dumps({"status": "ok", "package": str(package), "zip": str(archive)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
