#!/usr/bin/env python3
"""Gate the bounded Mode-3 9x7 length family against actual AEX output."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / "tools/emulation/test_kirakira_gaussian.cpp"
CORE = ROOT / "core/kirakira_gaussian.h"
LENGTHS = (3, 5, 7, 9)
FIXTURES = {
    3: ROOT / "refs/conformance/olmkirakira_mode3_gaussian_9x7_length3_actual_aex_20260810.json",
    5: ROOT / "refs/conformance/olmkirakira_mode3_gaussian_crt_initialized_actual_aex_20260805.json",
    7: ROOT / "refs/conformance/olmkirakira_mode3_gaussian_9x7_length7_actual_aex_20260810.json",
    9: ROOT / "refs/conformance/olmkirakira_mode3_gaussian_9x7_length9_actual_aex_20260810.json",
}
EXPECTED_AEX_SHA256 = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"


def normalized_words(values: list[str]) -> list[str]:
    return [f"0x{int(value, 16):08x}" for value in values]


def main() -> int:
    core = CORE.read_text(encoding="utf-8")
    assert "length == 3 || length == 5 || length == 7 || length == 9 || length == 50" in core

    with tempfile.TemporaryDirectory(prefix="olmkirakira_mode3_9x7_family_") as td:
        executable = Path(td) / "kirakira_gaussian"
        subprocess.run(["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)], check=True)
        result = {}
        for length in LENGTHS:
            report = json.loads(FIXTURES[length].read_text(encoding="utf-8"))
            assert report["status"] == "captured"
            assert report["execution"]["aex_sha256"] == EXPECTED_AEX_SHA256
            assert report["execution"]["input_shape"] == [7, 9]
            assert report["execution"]["length"] == length
            assert report["execution"]["return_hit_count"] == 1
            inputs = report["entry_capture"][0]["input_array"]["mat"]["words_u32"]
            expected = report["output_capture"]["output_array_after"]["mat"]["words_u32"]
            assert len(inputs) == len(expected) == 63
            lines = subprocess.check_output(
                [str(executable), "--crt-initialized-actual-aex-oracle", "9", "7", str(length)],
                input="\n".join(inputs) + "\n",
                text=True,
            ).splitlines()
            actual = [line.split()[1] for line in lines]
            assert normalized_words(actual) == normalized_words(expected)
            result[length] = hashlib.sha256(
                b"".join(struct.pack("<I", int(word, 16)) for word in expected)
            ).hexdigest()

    assert len(set(result.values())) == len(LENGTHS)
    print("PASS_OLMKIRAKIRA_MODE3_9X7_LENGTH_FAMILY_ACTUAL_AEX_20260810 " +
          " ".join(f"length{length}={digest[:12]}" for length, digest in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
