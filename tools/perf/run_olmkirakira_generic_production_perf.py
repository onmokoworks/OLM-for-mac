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
CASES = (
    {"mode": "box", "tuple_index": 0, "tuple_name": "m1_h7_r0",
     "horizontal_length": 7, "rotation_degrees": 0.0},
    {"mode": "approximated_gaussian", "tuple_index": 3,
     "tuple_name": "m2_h7_ramp_r0",
     "horizontal_length": 7, "rotation_degrees": 0.0},
    {"mode": "gaussian_length50", "tuple_index": 7,
     "tuple_name": "m3_h50_r0",
     "horizontal_length": 50, "rotation_degrees": 0.0},
    {"mode": "exponential", "tuple_index": 9,
     "tuple_name": "m4_highlight_r3",
     "horizontal_length": 0, "rotation_degrees": 0.0},
    {"mode": "gaussian_length300", "tuple_index": None,
     "tuple_name": "m3_ui_length",
     "horizontal_length": 300, "rotation_degrees": 1.0},
)
RSS = re.compile(r"^\s*(\d+)\s+maximum resident set size\s*$", re.MULTILINE)
GENERIC_ROW = re.compile(
    r"^GENERIC tuple=(\S+) length=(-?\d+) rotation=(-?\d+(?:\.\d+)?) "
    r"depth=(\d+) size=(\d+)x(\d+) ok=([01]) content=(\S+) "
    r"callbacks=(\d+/\d+/\d+/\d+)$"
)


def parse_peak_rss(stderr: str) -> int | None:
    matches = RSS.findall(stderr)
    if len(matches) != 1:
        return None
    value = int(matches[0])
    return value if value > 0 else None


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
        for case in CASES:
            for depth in (8, 16, 32):
                if case["tuple_index"] is None:
                    harness_args = [
                        "--single-mode3-length", str(depth), str(width), str(height),
                        str(case["horizontal_length"]), str(case["rotation_degrees"]),
                    ]
                else:
                    harness_args = [
                        "--single", str(case["tuple_index"]), str(depth),
                        str(width), str(height),
                    ]
                started = time.monotonic()
                run = subprocess.run([
                    "/usr/bin/time", "-lp", str(executable), *harness_args,
                ], cwd=ROOT, text=True, capture_output=True)
                peak_rss = parse_peak_rss(run.stderr)
                generic_rows = [
                    parsed for line in run.stdout.splitlines()
                    if (parsed := GENERIC_ROW.fullmatch(line)) is not None
                ]
                completed_contract = (
                    run.returncode == 0 and len(generic_rows) == 1 and
                    peak_rss is not None
                )
                if completed_contract:
                    parsed = generic_rows[0]
                    completed_contract = (
                        parsed.group(1) == case["tuple_name"] and
                        int(parsed.group(2)) == case["horizontal_length"] and
                        float(parsed.group(3)) == case["rotation_degrees"] and
                        int(parsed.group(4)) == depth and
                        int(parsed.group(5)) == width and
                        int(parsed.group(6)) == height and
                        parsed.group(7) == "1" and parsed.group(8) == "full" and
                        parsed.group(9) == "1/1/1/0"
                    )
                row = {
                    "mode": case["mode"], "depth_bpc": depth,
                    "tuple": case["tuple_name"],
                    "dimensions": [width, height],
                    "horizontal_length": case["horizontal_length"],
                    "rotation_degrees": case["rotation_degrees"],
                    "wall_seconds": round(time.monotonic() - started, 6),
                    "peak_rss_bytes": peak_rss,
                    "returncode": run.returncode,
                    "content_bounds": "full",
                    "callback_shape": "1/1/1/0",
                    "workload": "Smart plus two Classic production renders with parity/determinism checks",
                    "classic_smart_parity": completed_contract,
                    "deterministic": completed_contract,
                    "independent_strides": completed_contract,
                    "input_span_unchanged": completed_contract,
                    "output_padding_unchanged": completed_contract,
                    "output_active_changed": completed_contract,
                }
                cases.append(row)
                if not completed_contract:
                    print(run.stdout)
                    print(run.stderr)
                    return run.returncode or 65
        print("OLM_PERF_CASES_JSON=" + json.dumps(cases, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
