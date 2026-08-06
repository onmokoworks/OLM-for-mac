"""Actual-AEX complete-buffer fixtures for FUN_180007300."""

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
FIXTURES = Path(__file__).parent / "fixtures" / "olmblur_worker8_legacy"
WORKER = 0x180007300
MAX_INSTRUCTIONS = 8_000_000

CASES = [
    {"id": "8bpc_legacy_basic", "width": 12, "height": 12, "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2, "bias_direction": 1},
    {"id": "8bpc_legacy_large_radius_reverse", "width": 18, "height": 18, "blur_amount": 11.0, "smoothness": 100.0, "repeat": 3, "bias_direction": 2},
    {"id": "8bpc_legacy_mixed_alpha_reverse", "width": 18, "height": 12, "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2, "bias_direction": 2, "mixed_alpha": True},
    {
        "id": "8bpc_legacy_case0003_radius248_boundary_gradient",
        "width": 6,
        "height": 6,
        "blur_amount": 248.6,
        "smoothness": 100.0,
        "repeat": 10,
        "bias_direction": 1,
        "boundary_gradient": True,
        "formal_case": "case0003",
        "formal_width": 960,
        "formal_height": 540,
    },
    {
        "id": "8bpc_legacy_case0003_repeat10_large_radius_full12",
        "width": 12,
        "height": 12,
        "blur_amount": 248.6,
        "smoothness": 100.0,
        "repeat": 10,
        "bias_direction": 1,
        "boundary_gradient": True,
        "formal_case": "case0003",
        "max_instructions": 30_000_000,
    },
    {
        "id": "8bpc_legacy_case0007_repeat1",
        "width": 16,
        "height": 16,
        "blur_amount": 5.0,
        "smoothness": 100.0,
        "repeat": 1,
        "bias_direction": 1,
        "formal_case": "case0007",
    },
    {
        "id": "8bpc_legacy_bias_reverse_radius1_boundary",
        "width": 10,
        "height": 8,
        "blur_amount": 1.0,
        "smoothness": 100.0,
        "repeat": 2,
        "bias_direction": 2,
        "boundary_gradient": True,
        "branch": "legacy-bias-reverse-radius1-boundary",
    },
    {
        "id": "8bpc_legacy_smoothness43_75_byte_boundaries",
        "width": 19,
        "height": 13,
        "blur_amount": 9.0,
        "smoothness": 43.75,
        "repeat": 3,
        "bias_direction": 2,
        "pattern": "byte_boundaries",
        "coverage_gap": "first retained PF8 fixture with non-default Blur "
                        "Smoothness and native 0/1/127/128/254/255 byte boundaries",
        "claim_boundary": "actual AEX worker FUN_180007300 to Mac production "
                          "worker exact; no AE-host parameter materialization claim",
    },
]


def alloc(loader: AexLoader, data: bytes) -> int:
    address = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(address, data)
    return address


def source_bytes(width: int, height: int, mixed_alpha: bool = False,
                 boundary_gradient: bool = False, pattern: str = "") -> bytes:
    data = bytearray()
    for y in range(height):
        for x in range(width):
            if pattern == "byte_boundaries":
                values = (0, 1, 127, 128, 254, 255)
                alpha = values[(x + 5 * y) % len(values)]
                rgb = (values[(2 * x + y + 1) % len(values)],
                       values[(x + 3 * y + 2) % len(values)],
                       values[(5 * x + 2 * y + 3) % len(values)])
            elif mixed_alpha:
                boundary = x in (0, width - 1) or y in (0, height - 1)
                hole = (x * 7 + y * 11) % 13 == 0
                alpha = 0 if boundary or hole else (32 + ((x * 29 + y * 17) % 4) * 64)
                rgb = (50, 100, 150)
            elif boundary_gradient:
                boundary = x in (0, width - 1) or y in (0, height - 1)
                edge = (x * 19 + y * 23 + 7) & 255
                interior = (31 + x * 9 + y * 13) & 255
                alpha = 255
                rgb = (edge if boundary else interior, 0, 0)
            else:
                alpha = 255
                rgb = ((17 * x + 3 * y + 11) & 255,
                       (7 * x + 19 * y + 23) & 255,
                       (29 * x + 13 * y + 37) & 255)
            data.extend((alpha, *rgb))
    return bytes(data)


def run_case(case: dict) -> tuple[bytes, dict]:
    width, height = case["width"], case["height"]
    source = source_bytes(width, height, case.get("mixed_alpha", False),
                         case.get("boundary_gradient", False),
                         case.get("pattern", ""))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def impl_pow(uc, args):
        loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1)))
        return 0

    def impl_powf(uc, args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
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
        loader.write_bytes(address + 0x20, struct.pack("<I", width * 4))
        loader.write_bytes(address + 0x24, struct.pack("<I", width))
        loader.write_bytes(address + 0x28, struct.pack("<I", height))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 8))
        return address

    source_world, output_world = world(source_data), world(output_data)
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", 8))
    loader.write_bytes(params + 0x20, struct.pack("<f", case["blur_amount"]))
    loader.write_bytes(params + 0x24, struct.pack("<f", case["smoothness"]))
    loader.write_bytes(params + 0x28, struct.pack("<I", case["repeat"]))
    loader.write_bytes(params + 0x2C, struct.pack("<I", case["bias_direction"]))
    loader.write_bytes(params + 0x30, b"\x01")
    max_instructions = case.get("max_instructions", MAX_INSTRUCTIONS)
    result = loader.call_function(WORKER, int_args=[context, source_world, output_world, params], max_instructions=max_instructions)
    if result["instructions"] >= max_instructions:
        raise RuntimeError(f"AEX worker hit instruction cap for {case['id']}")
    return loader.read_bytes(output_data, len(source)), {"instructions": result["instructions"], "callbacks": events}


def export() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "olm.aex.cpu-fixture/3",
        "plugin": "OLMBlur",
        "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "worker": hex(WORKER),
        "bit_depth": 8,
        "legacy": 1,
        "pixel_layout": "little-endian A,R,G,B",
        "cases": [],
    }
    for case in CASES:
        output, run = run_case(case)
        directory = FIXTURES / case["id"]
        directory.mkdir(exist_ok=True)
        source = source_bytes(case["width"], case["height"], case.get("mixed_alpha", False),
                              case.get("boundary_gradient", False),
                              case.get("pattern", ""))
        (directory / "source_argb.bin").write_bytes(source)
        (directory / "expected_argb.bin").write_bytes(output)
        entry = dict(case)
        alphas = source[0::4]
        entry.update({"zero_alpha_count": sum(value == 0 for value in alphas),
                      "partial_alpha_values": sorted({value for value in alphas if 0 < value < 255})})
        entry.update({"source_sha256": hashlib.sha256(source).hexdigest(), "expected_sha256": hashlib.sha256(output).hexdigest(), "instructions": run["instructions"], "callback_count": len(run["callbacks"])})
        manifest["cases"].append(entry)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    if not args.export:
        parser.error("use --export to execute FUN_180007300 and materialize fixtures")
    export()
