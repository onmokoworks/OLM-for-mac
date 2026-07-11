#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path("/tmp/olmsmoother2_fullchain_diff")
ADAPTER = BUILD / "port_adapter"
RESULT = ROOT / "refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json"

BUILD.mkdir(parents=True, exist_ok=True)
compile_cmd = [
    "clang++", "-std=c++17", "-O2", "-Wall", "-Wextra",
    f"-I{ROOT / 'cli/OLMSmoother2/shim'}",
    f"-I{ROOT / 'mac/OLMSmoother2/Mac'}",
    str(ROOT / "tools/emulation/smoother2_fullchain_port_adapter.cpp"),
    "-o", str(ADAPTER),
]
subprocess.run(compile_cmd, check=True, cwd=ROOT)
subprocess.run([
    "python3", str(ROOT / "tools/emulation/test_smoother2_fullchain_diff.py"),
    "--adapter", str(ADAPTER), "--output", str(RESULT),
], check=True, cwd=ROOT)
print("PASS smoother2 fullchain local differential")
print(f"result={RESULT}")

