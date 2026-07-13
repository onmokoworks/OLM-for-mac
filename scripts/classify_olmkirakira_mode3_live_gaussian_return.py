#!/usr/bin/env python3
"""Classify the live Windows Mode 3 kernel without image-level inference."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CV455_PYTHON = ROOT / "tools/emulation/.venv-cv455/bin/python"
REQUEST_ID = "olmkirakira_mode3_live_gaussian_20260713"
UNIFORM_WORD = 0x3D430C31


def load_return(path: Path) -> dict:
    if path.suffix.lower() != ".zip":
        return json.loads(path.read_text(encoding="utf-8-sig"))
    with zipfile.ZipFile(path) as archive:
        result_names = {
            "RETURN_RUNTIME_TRACE.json",
            "AE_RUNTIME_TRACE_RESULT.json",
        }
        names = [
            name for name in archive.namelist()
            if name.replace("\\", "/").rsplit("/", 1)[-1] in result_names
        ]
        if len(names) != 1:
            raise ValueError(f"expected one runtime trace result JSON, found {len(names)}")
        return json.loads(archive.read(names[0]).decode("utf-8-sig"))


def opencv_words() -> list[int]:
    code = (
        "import cv2,json,numpy as np;"
        "assert cv2.__version__=='4.5.5';"
        "k=cv2.getGaussianKernel(21,2.5,cv2.CV_32F).reshape(-1);"
        "print(json.dumps([int(x) for x in k.view(np.uint32)]))"
    )
    output = subprocess.check_output([str(CV455_PYTHON), "-c", code], text=True)
    return json.loads(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    payload = load_return(args.return_path)
    if payload.get("request_id") != REQUEST_ID:
        raise ValueError("request_id mismatch")
    if payload.get("status") != "answered":
        raise ValueError(f"return is not answered: {payload.get('status')}")
    raw = payload.get("observation", {}).get("raw_words_u32", [])
    if len(raw) != 21:
        raise ValueError(f"expected 21 raw words, got {len(raw)}")
    words = [int(str(word), 16) for word in raw]
    gaussian = opencv_words()
    uniform = [UNIFORM_WORD] * 21
    gaussian_mismatches = sum(a != b for a, b in zip(words, gaussian))
    uniform_mismatches = sum(a != b for a, b in zip(words, uniform))
    if gaussian_mismatches == 0:
        classification = "opencv_4_5_5_gaussian_exact"
    elif uniform_mismatches == 0:
        classification = "uniform_21tap_exact"
    else:
        classification = "neither_known_model"
    result = {
        "request_id": REQUEST_ID,
        "classification": classification,
        "word_count": 21,
        "opencv_4_5_5_gaussian_mismatches": gaussian_mismatches,
        "uniform_21tap_mismatches": uniform_mismatches,
        "raw_words_u32": [f"0x{word:08x}" for word in words],
        "opencv_words_u32": [f"0x{word:08x}" for word in gaussian],
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if classification != "neither_known_model" else 2


if __name__ == "__main__":
    raise SystemExit(main())
