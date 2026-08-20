#!/usr/bin/env python3
"""Build and run the production EffectMain harness at one explicit size/depth."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from test_olmsmoother_v1_generic_classic_beta_20260820 import HARNESS


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", choices=("8", "16", "both"), required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--input-padding", type=int, default=18)
    parser.add_argument("--output-padding", type=int, default=34)
    parser.add_argument("--tolerance", type=int, default=255)
    parser.add_argument("--use-key", action="store_true")
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0 or not 0 <= args.tolerance <= 255:
        parser.error("positive dimensions and tolerance 0..255 are required")

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-perf-") as tmp:
        source = Path(tmp) / "production.cpp"
        binary = Path(tmp) / "production"
        source.write_text(HARNESS)
        subprocess.run([
            "clang++", "-std=c++17", "-O2",
            "-I", str(ROOT / "cli/OLMSmoother/shim"), "-I", str(ROOT),
            str(source), "-o", str(binary),
        ], cwd=ROOT, check=True)
        depths = ("8", "16") if args.depth == "both" else (args.depth,)
        for depth in depths:
            command = [
                str(binary), f"pf{depth}", str(args.width), str(args.height),
                str(args.input_padding), str(args.output_padding), str(args.tolerance),
            ]
            if args.use_key:
                command.append("key")
            run = subprocess.run(command, cwd=ROOT)
            if run.returncode:
                return run.returncode
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
