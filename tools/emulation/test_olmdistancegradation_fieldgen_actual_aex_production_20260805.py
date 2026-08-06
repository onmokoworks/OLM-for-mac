#!/usr/bin/env python3
"""Production field helper vs retained actual-AEX FUN_181174760 fixture."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = [
    (ROOT / "tools/emulation/fixtures/distancegradation_fieldgen_synthetic_17x11", 3, 1),
    (ROOT / "tools/emulation/fixtures/distancegradation_fieldgen_synthetic_17x11_threshold4_param8_0", 4, 0),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    names = ["input_mask_u8.bin", "call_params_le_i32.bin", "field_f32.bin"]
    for fixture, _threshold, _param8 in FIXTURES:
        manifest = json.loads((fixture / "manifest.json").read_text())
        assert manifest["provenance"]["oracle"] == "unicorn-aex"
        assert manifest["provenance"]["function"] == "0x181174760"
        assert manifest["provenance"]["binary_sha256"] == "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
        descriptors = [manifest["world"]["descriptor"], manifest["raw_param_block"]["descriptor"], manifest["output"]["descriptor"]]
        for name, descriptor in zip(names, descriptors):
            assert digest(fixture / name) == descriptor["sha256"]

    with tempfile.TemporaryDirectory(prefix="olmdg_fieldgen_") as temp:
        binary = Path(temp) / "fieldgen"
        compiled = subprocess.run([
            "clang++", "-std=c++17", "-O0", "-Wall", "-Wextra", "-pedantic",
            "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
            str(ROOT / "tools/emulation/dg_fieldgen_actual_aex_production_harness_20260805.cpp"),
            str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(binary),
        ], text=True, capture_output=True)
        assert compiled.returncode == 0, compiled.stderr
        for fixture, threshold, param8 in FIXTURES:
            run = subprocess.run([str(binary), *(str(fixture / name) for name in names)], text=True, capture_output=True)
            assert run.returncode == 0, run.stderr
            assert f"PASS full_field words=187 mismatches=0 threshold={threshold} constant={param8}" in run.stdout
            assert len([line for line in run.stdout.splitlines() if line.startswith("PASS i=")]) == 7
            print(run.stdout, end="")
    print("PASS_OLMDISTANCEGRADATION_FIELDGEN_ACTUAL_AEX_PRODUCTION_EXACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
