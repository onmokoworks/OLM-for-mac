"""Actual-AEX complete-buffer fixtures for FUN_1800086d0."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
FIXTURES = Path(__file__).parent / "fixtures" / "olmblur_worker32_legacy"
WORKER = 0x1800086D0

CASES = [
    {"id": "32bpc_legacy_basic", "width": 12, "height": 12,
     "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2,
     "bias_direction": 1},
    {"id": "32bpc_legacy_large_radius_reverse", "width": 18, "height": 18,
     "blur_amount": 11.0, "smoothness": 100.0, "repeat": 3,
     "bias_direction": 2},
    {"id": "32bpc_legacy_mixed_alpha_reverse", "width": 18, "height": 12,
     "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2,
     "bias_direction": 2, "mixed_alpha": True},
    {"id": "32bpc_legacy_declared_248_6_red_boundary", "width": 7, "height": 5,
     "blur_amount": 248.6, "smoothness": 100.0, "repeat": 10,
     "bias_direction": 1, "pattern": "red_boundary"},
    {"id": "32bpc_legacy_declared_5_mixed_alpha", "width": 9, "height": 7,
     "blur_amount": 5.0, "smoothness": 100.0, "repeat": 10,
     "bias_direction": 1, "mixed_alpha": True},
]


def alloc(loader: AexLoader, data: bytes) -> int:
    address = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(address, data)
    return address


def source_bytes(width: int, height: int, mixed_alpha: bool = False,
                 pattern: str = "") -> bytes:
    values: list[float] = []
    for y in range(height):
        for x in range(width):
            if pattern == "red_boundary":
                boundary = x in (0, width - 1) or y in (0, height - 1)
                alpha = 0.0 if boundary else 1.0
                rgb = (0.2 + 0.11 * x + 0.037 * y, 0.0, 0.0)
            elif mixed_alpha:
                boundary = x in (0, width - 1) or y in (0, height - 1)
                hole = (x * 7 + y * 11) % 13 == 0
                alpha = 0.0 if boundary or hole else (
                    (-0.5 if (x + 2 * y) % 7 == 0 else
                     0.25 + 0.125 * ((x * 3 + y) % 4)))
                rgb = (0.25 + 0.031 * x, -0.5 + 0.017 * y,
                       1.5 + 0.011 * (x + y))
            else:
                alpha = (0.0 if (x * 5 + y * 3) % 17 == 0 else
                         (-0.5 if (x + y) % 5 == 0 else 1.0))
                rgb = (-1.25 + 0.17 * x + 0.031 * y,
                       0.5 + 0.11 * x - 0.23 * y,
                       1.5 + 0.07 * x + 0.19 * y)
            values.extend((alpha, *rgb))
    return struct.pack("<" + "f" * len(values), *values)


def run_case(case: dict) -> tuple[bytes, dict]:
    width, height = case["width"], case["height"]
    source = source_bytes(width, height, case.get("mixed_alpha", False),
                          case.get("pattern", ""))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def impl_pow(uc, args):
        loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0),
                                        loader.read_xmm_f64(1)))
        return 0

    def impl_powf(uc, args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0),
                                        loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("pow", impl_pow)
    loader.register_import_impl("powf", impl_powf)
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = alloc(loader, source)
    output_data = alloc(loader, source)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", width * 16))
        loader.write_bytes(address + 0x24, struct.pack("<I", width))
        loader.write_bytes(address + 0x28, struct.pack("<I", height))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 32))
        return address

    source_world = world(source_data)
    output_world = world(output_data)
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", 32))
    loader.write_bytes(params + 0x20, struct.pack("<f", case["blur_amount"]))
    loader.write_bytes(params + 0x24, struct.pack("<f", case["smoothness"]))
    loader.write_bytes(params + 0x28, struct.pack("<I", case["repeat"]))
    loader.write_bytes(params + 0x2C, struct.pack("<I", case["bias_direction"]))
    loader.write_bytes(params + 0x30, b"\x01")
    result = loader.call_function(WORKER, int_args=[context, source_world,
                                                     output_world, params],
                                  max_instructions=10_000_000)
    return loader.read_bytes(output_data, len(source)), {
        "instructions": result["instructions"], "callback_count": len(events)}


def export() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "olm.aex.cpu-fixture/3",
        "plugin": "OLMBlur",
        "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "worker": hex(WORKER), "bit_depth": 32, "legacy": 1,
        "pixel_layout": "little-endian float32 A,R,G,B",
        "oracle": "actual AEX FUN_1800086d0; no EXR or host output",
        "cases": [],
    }
    for case in CASES:
        output, run = run_case(case)
        directory = FIXTURES / case["id"]
        directory.mkdir(exist_ok=True)
        source = source_bytes(case["width"], case["height"],
                              case.get("mixed_alpha", False),
                              case.get("pattern", ""))
        (directory / "source_argb_f32.bin").write_bytes(source)
        (directory / "expected_argb_f32.bin").write_bytes(output)
        entry = dict(case)
        alphas = [struct.unpack_from("<f", source, offset)[0]
                  for offset in range(0, len(source), 16)]
        entry.update({
            "zero_alpha_count": sum(value == 0.0 for value in alphas),
            "negative_alpha_count": sum(value < 0.0 for value in alphas),
            "nonzero_alpha_count": sum(value != 0.0 for value in alphas),
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "expected_sha256": hashlib.sha256(output).hexdigest(), **run})
        manifest["cases"].append(entry)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    if not args.export:
        parser.error("use --export to execute FUN_1800086d0 and materialize fixtures")
    export()
