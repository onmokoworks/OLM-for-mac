#!/usr/bin/env python3
"""Full portable-core gates for current 8bpc front-only reference cases."""

from __future__ import annotations

import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from dblur_fullrender_host_fixture_20260711 import (
    byte_diff_summary,
    load_argb,
    premultiply_argb8,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "refs/win_references/olm_reference_return_windows_20260611/OLMDirectionalBlur"
REPORT = ROOT / "refs/conformance/dblur_frontonly_current_exact_20260711.json"
CASES = (
    {
        "id": "db_angle0_strength_sweep_small",
        "angle": 0.0,
        "brightness_gain": 1.0,
        "front_strength": 48,
        "front_alpha_fade": 0,
        "actual_aex_raw_sha256": "ebfda2207558a335d35a3928fe623b6d6d5cc44a7e0befe89dc06cdf1c4d9544",
    },
    {
        "id": "db_angle0_alpha_fade_hard_edges",
        "angle": 0.0,
        "brightness_gain": 1.0,
        "front_strength": 240,
        "front_alpha_fade": 96,
        "actual_aex_raw_sha256": "250023dbd2dbba4fbeb160b7cc17d428a744d97ce52926481d45edea8e453ac9",
    },
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(directory: Path) -> Path:
    objects = []
    for source, optimization in (
        (ROOT / "core/dblur_rotate.cpp", "-O0"),
        (ROOT / "core/dblur_rowdriver.cpp", "-O2"),
        (ROOT / "core/dblur_field.cpp", "-O2"),
        (ROOT / "core/dblur_frontonly.cpp", "-O2"),
    ):
        obj = directory / f"{source.stem}.o"
        subprocess.run(
            [
                "c++", "-std=c++17", optimization, "-fno-fast-math",
                "-ffp-contract=off", "-fPIC", "-c", str(source), "-o", str(obj),
            ],
            cwd=ROOT,
            check=True,
        )
        objects.append(obj)
    library = directory / "libdblur_frontonly.dylib"
    subprocess.run(
        ["c++", "-dynamiclib", *(str(obj) for obj in objects), "-o", str(library)],
        cwd=ROOT,
        check=True,
    )
    return library


def run_case(function, item: dict) -> dict:
    source_path = REFERENCE_DIR / (
        f"directionalblur_context_scale_20260606__software__fr24__{item['id']}_before_effects.png"
    )
    expected_path = REFERENCE_DIR / (
        f"directionalblur_context_scale_20260606__software__fr24__{item['id']}.png"
    )
    source_image = Image.open(source_path).convert("RGBA")
    source = source_image.tobytes()
    output = (ctypes.c_uint8 * len(source))()
    input_array = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    return_code = function(
        input_array, output, source_image.width, source_image.height,
        ctypes.c_float(item["angle"]), ctypes.c_float(item["brightness_gain"]),
        item["front_strength"], item["front_alpha_fade"],
    )
    actual = bytes(output)
    _width, _height, _expected_rgba, expected_argb = load_argb(expected_path)
    actual_argb = bytearray(len(actual))
    for offset in range(0, len(actual), 4):
        red, green, blue, alpha = actual[offset:offset + 4]
        actual_argb[offset:offset + 4] = bytes((alpha, red, green, blue))
    actual_argb = bytes(actual_argb)
    models = {
        rounding: byte_diff_summary(
            premultiply_argb8(actual_argb, rounding), expected_argb)
        for rounding in ("floor", "nearest")
    }
    raw_hash = sha(actual_argb)
    return {
        "id": item["id"],
        "source": str(source_path.relative_to(ROOT)),
        "expected": str(expected_path.relative_to(ROOT)),
        "parameters": {
            "angle": item["angle"],
            "brightness_gain": item["brightness_gain"],
            "front_strength": item["front_strength"],
            "front_alpha_fade": item["front_alpha_fade"],
        },
        "dimensions": [source_image.width, source_image.height],
        "return_code": return_code,
        "portable_raw_argb_sha256": raw_hash,
        "actual_aex_raw_argb_sha256": item["actual_aex_raw_sha256"],
        "raw_exact": raw_hash == item["actual_aex_raw_sha256"],
        "ae_output_premultiply_models": models,
        "modeled_ae_render_exact": any(result["exact"] for result in models.values()),
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_frontonly_") as temp:
        library = ctypes.CDLL(str(build(Path(temp))))
        function = library.olm_dblur_frontonly_rgba8
        function.argtypes = [
            ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float,
            ctypes.c_int, ctypes.c_int,
        ]
        function.restype = ctypes.c_int
        cases = [run_case(function, item) for item in CASES]
    report = {
        "schema": 1,
        "kind": "dblur_frontonly_current_portable_core_gate",
        "status": "pass" if all(item["return_code"] == 0 and item["raw_exact"] for item in cases) else "known-red",
        "comparison": "raw full-entry AEX SHA-256 plus modeled AE-rendered PNG; no tolerance",
        "cases": cases,
        "raw_exact_cases": sum(item["raw_exact"] for item in cases),
        "total_cases": len(cases),
        "not_ae_exact": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
