#!/usr/bin/env python3
"""Validate the actual-AEX forward-warp contract evidence."""

import argparse
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


def cpp_float(value: float) -> str:
    return f"{value.hex()}f"


def compile_forward_warp_fixture(root: Path, report: dict) -> list[str]:
    compiler = shutil.which("clang++") or shutil.which("c++")
    assert compiler, "no local C++ compiler found"
    source = (root / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    begin = "// OLMKIRAKIRA_FORWARD_WARP_HELPERS_BEGIN"
    end = "// OLMKIRAKIRA_FORWARD_WARP_HELPERS_END"
    assert source.count(begin) == source.count(end) == 1
    helpers = source[source.index(begin) + len(begin):source.index(end)]
    call = report["forward_warp_contract"]["calls"][0]
    src = [value for row in call["src"]["mat"]["values_f32"] for value in row]
    matrix = call["transform"]["decoded_by_mat_depth"]
    width = call["dsize"]["width"]
    height = call["dsize"]["height"]
    angle = 5.0
    assert matrix == [
        0.9961946980917455, 0.08715574274765817, -0.28792124102965855,
        -0.08715574274765817, 0.9961946980917455, 0.4055193990433523,
    ]
    harness = f"""
#include <cmath>
#include <cstdio>
#include <vector>
using A_long = long;
{helpers}
int main() {{
    const std::vector<float> input = {{{', '.join(cpp_float(value) for value in src)}}};
    const std::vector<float> output = WarpGetRotDirect(
        input, {width}, {height}, {width}, {height}, {width} * 0.5, {height} * 0.5, {angle.hex()});
    for (float value : output) {{
        unsigned word;
        static_assert(sizeof(word) == sizeof(value), "float32 required");
        __builtin_memcpy(&word, &value, sizeof(word));
        std::printf("%08x\\n", word);
    }}
}}
"""
    with tempfile.TemporaryDirectory(prefix="olmkirakira-forward-warp-") as tmp:
        tmp_path = Path(tmp)
        cpp = tmp_path / "fixture.cpp"
        binary = tmp_path / "fixture"
        cpp.write_text(harness, encoding="utf-8")
        subprocess.run([compiler, "-std=c++17", "-O2", str(cpp), "-o", str(binary)], check=True)
        proc = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
    return proc.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=Path("refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = args.json if args.json.is_absolute() else root / args.json
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["schema"] == "olmkirakira-mode3-forward-warp-contract-actual-aex/1"
    assert report["status"] == "captured_forward_warp_contract"
    calls = report["forward_warp_contract"]["calls"]
    assert len(calls) == 1
    first = calls[0]
    assert first["rip"] == "0x181297ac0"
    assert first["dsize"] == {"height": 7, "packed": "0x700000009", "source": "R9", "width": 9}
    assert first["optional_stack_args"]["interpolation_flags"] == 1
    assert first["optional_stack_args"]["border_mode"] == 0
    assert first["optional_stack_args"]["border_value_pointer"] != "0x0"
    assert first["src"]["object"] == first["dst"]["object"]
    assert first["src"]["mat"]["data"] == first["dst"]["mat"]["data"]
    assert first["transform"]["mat"]["depth_code"] == 6
    assert first["transform"]["decoded_by_mat_depth"] == [0.9961946980917455, 0.08715574274765817, -0.28792124102965855, -0.08715574274765817, 0.9961946980917455, 0.4055193990433523]
    assert first["src"]["mat"]["values_f32"]
    assert first["dst"]["mat"]["values_f32"]
    assert report["ray_population_capture"]["roi_after_copy"][0]["temp_a"]["values_f32"] != report["ray_population_capture"]["warp_after"][0]["temp_a"]["values_f32"]
    assert any(value != 0.0 for row in report["ray_population_capture"]["warp_after"][0]["temp_a"]["values_f32"] for value in row)
    sidecar = report["forward_warp_sidecar"]
    assert sidecar["status"] == "ok"
    assert sidecar["cv2"] == "4.5.5"
    assert sidecar["exact_words"] == sidecar["total_words"] == 63
    assert sidecar["max_abs"] == 0.0
    expected_values = [
        value
        for row in report["ray_population_capture"]["warp_after"][0]["temp_a"]["values_f32"]
        for value in row
    ]
    expected_words = [struct.pack("<f", value).hex() for value in expected_values]
    expected_words = [word[6:8] + word[4:6] + word[2:4] + word[0:2] for word in expected_words]
    actual_words = compile_forward_warp_fixture(root, report)
    mismatches = [
        (index, expected, actual)
        for index, (expected, actual) in enumerate(zip(expected_words, actual_words))
        if expected != actual
    ]
    assert len(actual_words) == len(expected_words) == 63
    assert not mismatches, f"Mac forward warp differs at {len(mismatches)}/63 words: {mismatches[:8]}"
    print("[OK] OLMKiraKira Mode 3 forward-warp contract and Mac helper match 63/63 words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
