#!/usr/bin/env python3
"""O2 KiraKira generic production-entry HD/UHD performance driver."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
STRINGS_SOURCE = "mac/OLMKiraKira/OLMKiraKira_Strings.cpp"
HARNESS = ROOT / "tests/olmkirakira_generic_beta_sanitizer_harness.cpp"
GEOMETRIES = {"hd": (1920, 1080), "uhd": (3840, 2160)}
MODES = {"box": 0, "approximated_gaussian": 3, "gaussian": 7, "exponential": 9}
RSS = re.compile(r"^\s*(\d+)\s+maximum resident set size\s*$", re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", required=True, choices=GEOMETRIES)
    args = parser.parse_args()
    width, height = GEOMETRIES[args.geometry]
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="kirakira_production_perf_") as raw:
        executable = Path(raw) / "driver"
        build = subprocess.run([
            "clang++", "-std=c++20", "-arch", "arm64", "-O2", "-DNDEBUG",
            "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk, "-w",
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            "-I", str(ROOT), f'-DKIRA_SOURCE="{SOURCE}"',
            f'-DKIRA_STRINGS_SOURCE="{STRINGS_SOURCE}"', str(HARNESS),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"),
            "-framework", "Cocoa", "-o", str(executable),
        ], cwd=ROOT, text=True, capture_output=True)
        if build.returncode:
            print(build.stderr)
            return build.returncode
        cases = []
        for mode, tuple_index in MODES.items():
            for depth in (8, 16, 32):
                started = time.monotonic()
                run = subprocess.run([
                    "/usr/bin/time", "-lp", str(executable), "--single",
                    str(tuple_index), str(depth), str(width), str(height),
                ], cwd=ROOT, text=True, capture_output=True)
                match = RSS.search(run.stderr)
                row = {
                    "mode": mode, "depth_bpc": depth,
                    "dimensions": [width, height],
                    "wall_seconds": round(time.monotonic() - started, 6),
                    "peak_rss_bytes": int(match.group(1)) if match else None,
                    "returncode": run.returncode,
                    "workload": "Smart plus two Classic production renders with parity/determinism checks",
                }
                cases.append(row)
                if run.returncode:
                    print(run.stdout)
                    print(run.stderr)
                    return run.returncode
        print("OLM_PERF_CASES_JSON=" + json.dumps(cases, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
