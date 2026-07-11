"""Actual-AEX fixtures for the 8bpc Non-Legacy FUN_180003710 worker."""

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
FIXTURES = Path(__file__).parent / "fixtures" / "olmblur_worker_orchestration"
WORKER = 0x180003710

CASES = [
    {"id": "8bpc_nonlegacy_basic", "width": 12, "height": 12, "blur_amount": 3.0, "smoothness": 100.0, "repeat": 2, "bias_direction": 1},
    {"id": "8bpc_nonlegacy_large_radius", "width": 18, "height": 18, "blur_amount": 11.0, "smoothness": 100.0, "repeat": 3, "bias_direction": 2},
]


def alloc(loader: AexLoader, data: bytes, align: int = 16) -> int:
    address = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(address, data)
    return address


def source_bytes(width: int, height: int) -> bytes:
    data = bytearray()
    for y in range(height):
        for x in range(width):
            alpha = 0 if ((x * 5 + y * 3) % 17 == 0) else 255
            data.extend((alpha, (17 * x + 3 * y + 11) & 255,
                         (7 * x + 19 * y + 23) & 255,
                         (29 * x + 13 * y + 37) & 255))
    return bytes(data)


def run_case(case: dict) -> tuple[bytes, dict]:
    width = case["width"]
    height = case["height"]
    source = source_bytes(width, height)
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def impl_pow(uc, args):
        loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1)))
        return 0

    def impl_powf(uc, args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    # FUN_180003710 uses these imports for repeat decay. The shared loader's
    # generic smoke mode intentionally leaves them unimplemented.
    loader.register_import_impl("pow", impl_pow)
    loader.register_import_impl("powf", impl_powf)
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data = alloc(loader, source, 64)
    output_data = alloc(loader, source, 64)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", width * 4))
        loader.write_bytes(address + 0x24, struct.pack("<I", width))
        loader.write_bytes(address + 0x28, struct.pack("<I", height))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 8))
        return address

    source_world = world(source_data)
    output_world = world(output_data)
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", 8))
    loader.write_bytes(params + 0x20, struct.pack("<f", case["blur_amount"]))
    loader.write_bytes(params + 0x24, struct.pack("<f", case["smoothness"]))
    loader.write_bytes(params + 0x28, struct.pack("<I", case["repeat"]))
    loader.write_bytes(params + 0x2C, struct.pack("<I", case["bias_direction"]))
    result = loader.call_function(WORKER, int_args=[context, source_world, output_world, params], max_instructions=8_000_000)
    return loader.read_bytes(output_data, len(source)), {"instructions": result["instructions"], "callbacks": events}


def export() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "olm.aex.cpu-fixture/3",
        "plugin": "OLMBlur",
        "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "worker": hex(WORKER),
        "bit_depth": 8,
        "legacy": 0,
        "pixel_layout": "little-endian A,R,G,B",
        "cases": [],
    }
    for case in CASES:
        output, run = run_case(case)
        directory = FIXTURES / case["id"]
        directory.mkdir(exist_ok=True)
        source = source_bytes(case["width"], case["height"])
        (directory / "source_argb.bin").write_bytes(source)
        (directory / "expected_argb.bin").write_bytes(output)
        entry = dict(case)
        entry.update({"source_sha256": hashlib.sha256(source).hexdigest(), "expected_sha256": hashlib.sha256(output).hexdigest(), "instructions": run["instructions"], "callback_count": len(run["callbacks"])})
        manifest["cases"].append(entry)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    if not args.export:
        parser.error("use --export to execute FUN_180003710 and materialize fixtures")
    export()
