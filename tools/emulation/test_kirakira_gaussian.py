#!/usr/bin/env python3
"""Compare the standalone C++ primitive with pinned OpenCV 4.5.5 words."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CPP = ROOT / "tools/emulation/test_kirakira_gaussian.cpp"
AEX_ORACLE = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json"
INPUT_WORDS = [
    0x00000000, 0x3F800000, 0xC0000000, 0x40400000, 0x40800000,
    0xC0A00000, 0x40C00000, 0x40E00000, 0xC1000000, 0x3DCCCCCD,
    0xBE4CCCCD, 0x3E99999A, 0xBEFAE148, 0x3F1C28F6, 0xBF4CCCCD,
    0x3F733333, 0xBF7D70A4,
]
LENGTHS = [1, 2, 5, 9, 17]


def ordered(bits: int) -> int:
    return (0xFFFFFFFF - bits) if bits & 0x80000000 else (bits + 0x80000000)


def reflect101(index: int, width: int) -> int:
    while index < 0 or index >= width:
        index = -index if index < 0 else 2 * width - index - 2
    return index


def double_accumulate(source: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    width = source.shape[1]
    radius = kernel.size // 2
    output = np.empty(width, dtype=np.float32)
    for x in range(width):
        output[x] = sum(
            float(kernel[k]) * float(source[0, reflect101(x + k - radius, width)])
            for k in range(kernel.size)
        )
    return output


def mismatch_count(left: np.ndarray, right: np.ndarray) -> int:
    return int(np.count_nonzero(left.view(np.uint32).reshape(-1) !=
                                right.view(np.uint32).reshape(-1)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    assert cv2.__version__ == "4.5.5", cv2.__version__
    source = np.array(INPUT_WORDS, dtype=np.uint32).view(np.float32).reshape(1, -1)
    evidence = json.loads(AEX_ORACLE.read_text(encoding="utf-8"))
    input_aex = evidence["entry_capture"][0]["input_array"]["mat"]["words_u32"]
    with tempfile.TemporaryDirectory(prefix="kirakira_gaussian_") as temporary:
        executable = Path(temporary) / "test_kirakira_gaussian"
        subprocess.run(
            ["c++", "-std=c++17", "-O2", str(CPP), "-o", str(executable)],
            cwd=ROOT, check=True,
        )
        lines = subprocess.check_output([str(executable)], cwd=ROOT, text=True).splitlines()
        aex_lines = subprocess.check_output(
            [str(executable), "--actual-aex-oracle"], cwd=ROOT, text=True,
            input="\n".join(input_aex) + "\n",
        ).splitlines()

    actual = {(int(length), int(x)): int(word, 16)
              for length, x, word in (line.split() for line in lines)}
    mismatches = []
    total = 0
    controls = {
        "gaussian_vs_sepfilter_float_kernel": 0,
        "gaussian_vs_sepfilter_double_kernel": 0,
        "float_coefficient_double_accumulation": 0,
        "double_coefficient_double_accumulation": 0,
        "float_kernel_vs_double_kernel_cast_to_float": 0,
    }
    for length in LENGTHS:
        sigma = length * 0.5
        kernel_size = 4 * length + 1
        kernel32 = cv2.getGaussianKernel(kernel_size, sigma, cv2.CV_32F).reshape(-1)
        kernel64 = cv2.getGaussianKernel(kernel_size, sigma, cv2.CV_64F).reshape(-1)
        expected_image = cv2.GaussianBlur(
            source, (0, 1), length * 0.5, borderType=cv2.BORDER_DEFAULT
        )
        controls["gaussian_vs_sepfilter_float_kernel"] += mismatch_count(
            expected_image,
            cv2.sepFilter2D(source, -1, kernel32, np.array([1], np.float32),
                            borderType=cv2.BORDER_DEFAULT),
        )
        controls["gaussian_vs_sepfilter_double_kernel"] += mismatch_count(
            expected_image,
            cv2.sepFilter2D(source, -1, kernel64, np.array([1], np.float64),
                            borderType=cv2.BORDER_DEFAULT),
        )
        controls["float_coefficient_double_accumulation"] += mismatch_count(
            expected_image, double_accumulate(source, kernel32)
        )
        controls["double_coefficient_double_accumulation"] += mismatch_count(
            expected_image, double_accumulate(source, kernel64)
        )
        controls["float_kernel_vs_double_kernel_cast_to_float"] += mismatch_count(
            kernel32, kernel64.astype(np.float32)
        )
        expected = expected_image.view(np.uint32).reshape(-1)
        for x, expected_word in enumerate(expected.tolist()):
            total += 1
            actual_word = actual[(length, x)]
            if actual_word != expected_word:
                mismatches.append({
                    "length": length,
                    "x": x,
                    "expected": f"0x{expected_word:08x}",
                    "actual": f"0x{actual_word:08x}",
                    "ulp": abs(ordered(actual_word) - ordered(expected_word)),
                })

    result = {
        "opencv": cv2.__version__,
        "total_words": total,
        "matching_words": total - len(mismatches),
        "mismatched_words": len(mismatches),
        "max_ulp": max((item["ulp"] for item in mismatches), default=0),
        "mismatches": mismatches,
        "controlled_sidecar_mismatch_words": controls,
    }
    expected_aex = evidence["output_capture"]["output_array_after"]["mat"]["words_u32"]
    actual_aex = [f"0x{int(word, 16):08x}" for _index, word in
                  (line.split() for line in aex_lines)]
    aex_mismatches = [
        {"index": index, "expected": expected, "actual": actual,
         "ulp": abs(ordered(int(expected, 16)) - ordered(int(actual, 16)))}
        for index, (expected, actual) in enumerate(zip(expected_aex, actual_aex))
        if expected != actual
    ]
    result["unicorn_actual_aex_diagnostic"] = {
        "aex_sha256": evidence["execution"]["aex_sha256"],
        "word_count": len(expected_aex),
        "matching_words": len(expected_aex) - len(aex_mismatches),
        "mismatched_words": len(aex_mismatches),
        "max_ulp": max((item["ulp"] for item in aex_mismatches), default=0),
        "mismatches": aex_mismatches,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
