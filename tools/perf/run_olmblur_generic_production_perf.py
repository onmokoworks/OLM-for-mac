#!/usr/bin/env python3
"""Release-like OLMBlur generic-lane HD/UHD driver."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "tests/test_olmblur_generic_beta_sanitizers_20260820.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("olmblur_generic_driver", WRAPPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", choices=("hd", "uhd"), required=True)
    args = parser.parse_args()
    driver = load_wrapper()
    with tempfile.TemporaryDirectory(prefix="olmblur-perf-") as raw:
        run = driver.run_probe(driver.compile_probe(Path(raw), False), args.geometry)
    print(run.stdout, end="")
    if run.stderr:
        print(run.stderr, end="", file=__import__("sys").stderr)
    cases = []
    for line in run.stdout.splitlines():
        if not line.startswith("GENERIC "):
            continue
        words = line.split()
        cases.append({
            "case": words[1], "depth": int(words[2].split("=")[1]),
            "dimensions": [int(value) for value in words[3].split("x")],
            "legacy": int(words[4].split("=")[1]),
            "status": "passed" if "ok=1" in words else "failed",
        })
    print("OLM_PERF_CASES_JSON=" + json.dumps(cases, separators=(",", ":")))
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
