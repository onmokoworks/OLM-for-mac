#!/usr/bin/env python3
"""Gate the bounded Mode-3 production leaf against the CRT-initialized AEX."""

from __future__ import annotations

import json
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_crt_initialized_actual_aex_20260805.json"
DISPATCH = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_crt_initialized_dispatch_actual_aex_20260805.json"
CPP = ROOT / "tools/emulation/test_kirakira_gaussian.cpp"
MAC = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
EXPECTED_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"


def f32_word(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def main() -> int:
    output = json.loads(OUTPUT.read_text(encoding="utf-8"))
    dispatch = json.loads(DISPATCH.read_text(encoding="utf-8"))
    assert output["status"] == dispatch["status"] == "captured"
    assert output["execution"]["aex_sha256"] == EXPECTED_SHA
    assert output["execution"]["input_shape"] == [7, 9]
    assert output["execution"]["length"] == 5
    assert output["execution"]["sigma_x"] == 2.5
    assert len(output["manual_crt_initializers_diagnostic"]["callbacks"]) == 50

    generator = dispatch["evidence"]["coefficient_generators"][0]
    assert generator["entry"] == {"r8_count": 21, "xmm3_sigma_f64": 2.5}
    kernel_words = [f32_word(value) for value in generator["return"]["values_f64"]]
    assert kernel_words == [
        "0x38608900", "0x39805403", "0x3a79fee4", "0x3b4f80f3", "0x3c12c4ad",
        "0x3cb0ebf9", "0x3d35bcab", "0x3d9f14bb", "0x3ded5228", "0x3e16d8d6",
        "0x3e23691e", "0x3e16d8d6", "0x3ded5228", "0x3d9f14bb", "0x3d35bcab",
        "0x3cb0ebf9", "0x3c12c4ad", "0x3b4f80f3", "0x3a79fee4", "0x39805403",
        "0x38608900",
    ]

    inputs = output["entry_capture"][0]["input_array"]["mat"]["words_u32"]
    expected = output["output_capture"]["output_array_after"]["mat"]["words_u32"]
    assert len(inputs) == len(expected) == 63
    with tempfile.TemporaryDirectory(prefix="olmkirakira_mode3_crt_exact_") as td:
        executable = Path(td) / "kirakira_gaussian"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)], check=True)
        lines = subprocess.check_output(
            [str(executable), "--crt-initialized-actual-aex-oracle"],
            text=True,
            input="\n".join(inputs) + "\n",
        ).splitlines()
    actual = [f"0x{int(line.split()[1], 16):08x}" for line in lines]
    assert actual == expected

    mac = MAC.read_text(encoding="utf-8")
    assert "mode3_gaussian_admitted(rw, rh, length)" in mac
    assert "prepare_actual_aex_nonfused(length)" in mac
    print("PASS_OLMKIRAKIRA_MODE3_CRT_INITIALIZED_EXACT_BOUNDARY_20260805 words=63 max_ulp=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
