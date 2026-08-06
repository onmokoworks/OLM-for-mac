#!/usr/bin/env python3
"""Production PF16 compose/store vs retained actual-AEX case0023 triplet."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/emulation/fixtures/distancegradation_compose_case0023_triplet"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads((FIXTURE / "manifest.json").read_text())
    assert manifest["provenance"]["oracle"] == "unicorn-aex"
    assert manifest["provenance"]["binary_sha256"] == "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
    names = ["field_agrb16.bin", "refcon.bin", "output_triplet_agrb16.bin"]
    descriptors = [manifest["intermediates"][0]["descriptor"], manifest["raw_param_block"]["descriptor"], manifest["output"]["descriptor"]]
    for name, descriptor in zip(names, descriptors):
        assert sha256(FIXTURE / name) == descriptor["sha256"]

    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_") as temp:
        binary = Path(temp) / "triplet"
        compile_result = subprocess.run([
            "clang++", "-std=c++17", "-O0", "-Wall", "-Wextra", "-pedantic",
            "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
            str(ROOT / "tools/emulation/dg_case0023_triplet_production_harness_20260805.cpp"),
            str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(binary),
        ], text=True, capture_output=True)
        assert compile_result.returncode == 0, compile_result.stderr
        run = subprocess.run([str(binary), *(str(FIXTURE / name) for name in names)], text=True, capture_output=True)
        assert run.returncode == 0, run.stderr
        lines = [line for line in run.stdout.splitlines() if line.startswith("PASS ")]
        assert len(lines) == 3, lines
        assert "AGRB16=32768,0,3598,30583" in lines[0]
        assert all("AGRB16=32768,0,32768,0" in line for line in lines[1:])
        print(run.stdout, end="")
    print("PASS_OLMDISTANCEGRADATION_CASE0023_PRODUCTION_PF16_EXACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
