"""Actual-AEX complete-worker fixtures for FUN_180005f20."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader
from test_olmblur_fullentry import build_context, build_pf_suites

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
FIXTURES = Path(__file__).parent / "fixtures" / "olmblur_worker16_legacy"
ENTRY = 0x180005F20
CASES = [
    {"id": "16bpc_legacy_basic", "width": 12, "height": 12, "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2, "bias_direction": 1},
    {"id": "16bpc_legacy_large_radius_reverse", "width": 18, "height": 18, "blur_amount": 11.0, "smoothness": 100.0, "repeat": 3, "bias_direction": 2},
    {"id": "16bpc_legacy_mixed_alpha_reverse", "width": 18, "height": 12, "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2, "bias_direction": 2, "mixed_alpha": True},
]


def source_bytes(width: int, height: int, mixed_alpha: bool = False) -> bytes:
    data = bytearray()
    for y in range(height):
        for x in range(width):
            if mixed_alpha:
                boundary = x in (0, width - 1) or y in (0, height - 1)
                hole = (x * 7 + y * 11) % 13 == 0
                alpha = 0 if boundary or hole else 8192 + ((x * 29 + y * 17) % 4) * 16384
                rgb = (12800, 25600, 30000)
            else:
                alpha = 32768
                rgb = ((257 * x + 31 * y + 101) % 32769,
                       (113 * x + 211 * y + 307) % 32769,
                       (401 * x + 97 * y + 503) % 32769)
            data.extend(struct.pack("<4H", alpha, *rgb))
    return bytes(data)


def alloc(loader: AexLoader, data: bytes) -> int:
    address = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(address, data)
    return address


def run_case(case: dict) -> tuple[bytes, dict]:
    width, height = case["width"], case["height"]
    source = source_bytes(width, height, case.get("mixed_alpha", False))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl("pow", lambda uc, args: (loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1))) or 0))
    loader.register_import_impl("powf", lambda uc, args: (loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1))) or 0))
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data, output_data = alloc(loader, source), alloc(loader, source)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", width * 8))
        loader.write_bytes(address + 0x24, struct.pack("<I", width))
        loader.write_bytes(address + 0x28, struct.pack("<I", height))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    source_world, output_world = world(source_data), world(output_data)
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", 16))
    loader.write_bytes(params + 0x20, struct.pack("<f", case["blur_amount"]))
    loader.write_bytes(params + 0x24, struct.pack("<f", case["smoothness"]))
    loader.write_bytes(params + 0x28, struct.pack("<I", case["repeat"]))
    loader.write_bytes(params + 0x2C, struct.pack("<I", case["bias_direction"]))
    loader.write_bytes(params + 0x30, b"\x01")
    result = loader.call_function(ENTRY, int_args=[context, source_world, output_world, params], max_instructions=12_000_000)
    return loader.read_bytes(output_data, len(source)), {"instructions": result["instructions"], "callbacks": events}


def export() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "olm.aex.cpu-fixture/1", "plugin": "OLMBlur", "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(), "entry": hex(ENTRY), "bit_depth": 16, "legacy": 1, "pixel_layout": "little-endian A,R,G,B", "cases": []}
    for case in CASES:
        source = source_bytes(case["width"], case["height"], case.get("mixed_alpha", False))
        output, run = run_case(case)
        directory = FIXTURES / case["id"]
        directory.mkdir(exist_ok=True)
        (directory / "source_argb16.bin").write_bytes(source)
        (directory / "expected_argb16.bin").write_bytes(output)
        entry = dict(case)
        entry.update({"source_sha256": hashlib.sha256(source).hexdigest(), "expected_sha256": hashlib.sha256(output).hexdigest(), "instructions": run["instructions"], "callback_count": len(run["callbacks"])})
        manifest["cases"].append(entry)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    if not parser.parse_args().export: parser.error("use --export to execute FUN_180005f20 and materialize fixtures")
    export()
