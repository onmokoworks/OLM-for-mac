#!/usr/bin/env python3
"""Gate the length-9, 15x6 CRT-initialized actual-AEX Mode-3 fixture."""

from __future__ import annotations

import json
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_length9_15x6_crt_actual_aex_20260806.json"
DISPATCH = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_length9_15x6_crt_dispatch_actual_aex_20260806.json"
CPP = ROOT / "tools/emulation/test_kirakira_gaussian.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
EXPECTED_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"


def main() -> int:
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    dispatch = json.loads(DISPATCH.read_text(encoding="utf-8"))
    assert output["status"] == dispatch["status"] == "captured"
    assert output["execution"]["aex_sha256"] == EXPECTED_SHA
    assert output["execution"]["input_shape"] == [6, 15]
    assert output["execution"]["length"] == 9
    assert output["execution"]["sigma_x"] == 4.5
    assert output["execution"]["entry_hit_count"] == 1
    assert output["execution"]["return_hit_count"] == 1
    assert len(output["manual_crt_initializers_diagnostic"]["callbacks"]) == 50

    generator = dispatch["evidence"]["coefficient_generators"][0]
    assert generator["entry"] == {"r8_count": 37, "xmm3_sigma_f64": 4.5}
    kernel_words = [
        f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"
        for value in generator["return"]["values_f64"]
    ]
    assert len(kernel_words) == 37
    assert kernel_words == list(reversed(kernel_words))

    inputs = output["entry_capture"][0]["input_array"]["mat"]["words_u32"]
    expected = output["output_capture"]["output_array_after"]["mat"]["words_u32"]
    assert len(inputs) == len(expected) == 90
    with tempfile.TemporaryDirectory(prefix="olmkirakira_mode3_length9_exact_") as td:
        executable = Path(td) / "kirakira_gaussian"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)], check=True)
        lines = subprocess.check_output(
            [str(executable), "--crt-initialized-actual-aex-oracle", "15", "6", "9"],
            input="\n".join(inputs) + "\n",
            text=True,
        ).splitlines()
    actual = [f"0x{int(line.split()[1], 16):08x}" for line in lines]
    assert actual == expected

    mac = MAC.read_text(encoding="utf-8")
    assert "mode3_gaussian_admitted(rw, rh, length)" in mac
    print("PASS_OLMKIRAKIRA_MODE3_LENGTH9_15X6_EXACT_BOUNDARY_20260806 words=90 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
