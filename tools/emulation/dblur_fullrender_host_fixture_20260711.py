#!/usr/bin/env python3
"""Bounded 8bpc host fixture for the DirectionalBlur render path."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

POPULATE = 0x180006980
OUTPUT = 0x180006B30
POPULATE16 = 0x1800068E0
OUTPUT16 = 0x180006A90
POPULATE32 = 0x180006A20
OUTPUT32 = 0x180006BD0
ITERATE8_WRAPPER = 0x180006700
ROTATE = 0x180001EC0
ROWDRIVER = 0x1800038D0
ROTATE_CALL = 0x180005628
ROTATE_RETURN = 0x1800057A2
ENTRY = 0x180007BD0
DISPATCHER = 0x1800083F0
TARGETS = ((494, 169), (579, 169))


def u32(loader: AexLoader, address: int) -> int:
    return struct.unpack("<I", loader.read_bytes(address, 4))[0]


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def f32(loader: AexLoader, address: int) -> float:
    return struct.unpack("<f", loader.read_bytes(address, 4))[0]


def require_ptr(loader: AexLoader, address: int, label: str, size: int = 8) -> int:
    if address == 0:
        raise RuntimeError(f"PF_Iterate8 {label} pointer is null")
    try:
        loader.read_bytes(address, size)
    except Exception as exc:
        raise RuntimeError(f"PF_Iterate8 {label} pointer is unreadable: 0x{address:x}") from exc
    return address


def load_argb(path: Path) -> tuple[int, int, bytes, bytes]:
    image = Image.open(path).convert("RGBA")
    rgba = image.tobytes()
    argb = bytearray(len(rgba))
    for offset in range(0, len(rgba), 4):
        red, green, blue, alpha = rgba[offset:offset + 4]
        argb[offset:offset + 4] = bytes((alpha, red, green, blue))
    return image.width, image.height, rgba, bytes(argb)


def premultiply_argb8(argb: bytes, rounding: str) -> bytes:
    """Model the AE/output-module premultiply observed in rendered PNG refs."""
    if len(argb) % 4:
        raise ValueError("ARGB8 byte count is not pixel aligned")
    if rounding not in {"floor", "nearest"}:
        raise ValueError(f"unsupported premultiply rounding: {rounding}")
    premultiplied = bytearray(len(argb))
    for offset in range(0, len(argb), 4):
        alpha, red, green, blue = argb[offset:offset + 4]
        bias = 0 if rounding == "floor" else 127
        premultiplied[offset:offset + 4] = bytes((
            alpha,
            (red * alpha + bias) // 255,
            (green * alpha + bias) // 255,
            (blue * alpha + bias) // 255,
        ))
    return bytes(premultiplied)


def byte_diff_summary(actual: bytes, expected: bytes) -> dict:
    if len(actual) != len(expected):
        return {
            "exact": False,
            "max_diff": None,
            "differing_bytes": None,
            "actual_byte_count": len(actual),
            "expected_byte_count": len(expected),
        }
    differing_bytes = 0
    max_diff = 0
    for actual_value, expected_value in zip(actual, expected):
        difference = abs(actual_value - expected_value)
        differing_bytes += difference != 0
        max_diff = max(max_diff, difference)
    return {
        "exact": actual == expected,
        "max_diff": max_diff,
        "differing_bytes": differing_bytes,
        "actual_sha256": hashlib.sha256(actual).hexdigest(),
        "expected_sha256": hashlib.sha256(expected).hexdigest(),
    }


def pixel_float(loader: AexLoader, params: int, x: int, y: int) -> list[float]:
    stride = u32(loader, params + 0x80A0)
    row0 = u32(loader, params + 0x8098)
    col0 = u32(loader, params + 0x809C)
    base = u64(loader, params + 0x8090)
    address = base + (((row0 + y) * stride + col0 + x) * 16)
    return [f32(loader, address + 4 * i) for i in range(4)]


def model_populate(loader: AexLoader, params: int, y: int, x: int, pixel: bytes) -> None:
    # Exact 0x180006980 order: PF A/R/G/B bytes, divided by 255, work R/G/B/A.
    stride = u32(loader, params + 0x80A0)
    row0 = u32(loader, params + 0x8098)
    col0 = u32(loader, params + 0x809C)
    base = u64(loader, params + 0x8078)
    index = ((row0 + y) * stride + col0 + x) * 16
    values = (pixel[1] / 255.0, pixel[2] / 255.0, pixel[3] / 255.0, pixel[0] / 255.0)
    loader.write_bytes(base + index, struct.pack("<4f", *values))


def model_output(loader: AexLoader, params: int, y: int, x: int, out: bytearray, out_ptr: int, width: int) -> None:
    # Actual plugins_2025 0x180006B30 stores bytes at offsets A/R/G/B.
    rgba = pixel_float(loader, params, x, y)
    gain = f32(loader, params + 0x28)
    rgb = [min(1.0, value * gain) * 255.0 for value in rgba[:3]]
    values = [int(rgba[3] * 255.0), int(rgb[0]), int(rgb[1]), int(rgb[2])]
    address = (y * width + x) * 4
    packed = bytes(value & 0xFF for value in values)
    out[address:address + 4] = packed
    loader.write_bytes(out_ptr, packed)


def round_f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def model_populate16(loader: AexLoader, params: int, y: int, x: int, pixel: bytes) -> None:
    # Actual 0x1800068E0 loads PF_Pixel16 A/R/G/B words and performs a binary32
    # multiply by the binary32 constant 1/32768 before storing work R/G/B/A.
    stride = u32(loader, params + 0x80A0)
    row0 = u32(loader, params + 0x8098)
    col0 = u32(loader, params + 0x809C)
    base = u64(loader, params + 0x8078)
    index = ((row0 + y) * stride + col0 + x) * 16
    alpha, red, green, blue = struct.unpack("<4H", pixel)
    scale = round_f32(1.0 / 32768.0)
    values = tuple(round_f32(value * scale) for value in (red, green, blue, alpha))
    loader.write_bytes(base + index, struct.pack("<4f", *values))


def model_output16(loader: AexLoader, params: int, y: int, x: int,
                   out: bytearray, out_ptr: int, width: int) -> None:
    # Actual 0x180006A90 uses binary32 math, truncates toward zero, and stores
    # the low u16 word. RGB alone receives gain and the upper 1.0 clamp.
    rgba = pixel_float(loader, params, x, y)
    gain = f32(loader, params + 0x28)
    rgb = [round_f32(min(round_f32(value * gain), 1.0) * 32768.0)
           for value in rgba[:3]]
    alpha = round_f32(rgba[3] * 32768.0)
    values = [int(alpha), int(rgb[0]), int(rgb[1]), int(rgb[2])]
    packed = struct.pack("<4H", *(value & 0xFFFF for value in values))
    address = (y * width + x) * 8
    out[address:address + 8] = packed
    loader.write_bytes(out_ptr, packed)


def model_populate32(loader: AexLoader, params: int, y: int, x: int, pixel: bytes) -> None:
    alpha, red, green, blue = struct.unpack("<4f", pixel)
    stride, row0, col0 = u32(loader, params + 0x80A0), u32(loader, params + 0x8098), u32(loader, params + 0x809C)
    base = u64(loader, params + 0x8078)
    loader.write_bytes(base + ((row0 + y) * stride + col0 + x) * 16,
                       struct.pack("<4f", red, green, blue, alpha))


def model_output32(loader: AexLoader, params: int, y: int, x: int,
                   out: bytearray, out_ptr: int, width: int) -> None:
    rgba = pixel_float(loader, params, x, y)
    gain = f32(loader, params + 0x28)
    packed = struct.pack("<4f", rgba[3], *(min(round_f32(v * gain), 1.0) for v in rgba[:3]))
    address = (y * width + x) * 16
    out[address:address + 16] = packed
    loader.write_bytes(out_ptr, packed)


def callback_model_check(loader: AexLoader, source: bytes, width: int) -> dict:
    params = loader.host_alloc(0x8200)
    work = loader.bump_alloc(width * 540 * 16, align=64)
    pixel_ptr = loader.bump_alloc(4, align=4)
    out = loader.bump_alloc(width * 540 * 4, align=8)
    loader.write_bytes(params, b"\x00" * 0x8200)
    loader.write_bytes(params + 0x8078, struct.pack("<Q", work))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", width))
    loader.write_bytes(params + 0x28, struct.pack("<f", 1.0))
    loader.write_bytes(params + 0x8090, struct.pack("<Q", work))
    samples = tuple(item for item in ((0, 0), (494, 169), (579, 169)) if item[0] < width and item[1] < 540)
    checks = []
    for x, y in samples:
        pixel = bytes((source[(y * width + x) * 4 + i] for i in range(4)))
        loader.write_bytes(pixel_ptr, pixel)
        loader.write_bytes(work, b"\x00" * 16)
        # AEX callback ABI is (params, x in RDX, y in R8, pixel in R9).
        loader.call_function(POPULATE, int_args=[params, x, y, pixel_ptr], max_instructions=10000)
        aex_rgba = list(struct.unpack("<4f", loader.read_bytes(work + (y * width + x) * 16, 16)))
        loader.write_bytes(work + (y * width + x) * 16, b"\x00" * 16)
        model_populate(loader, params, y, x, pixel)
        model_rgba = list(struct.unpack("<4f", loader.read_bytes(work + (y * width + x) * 16, 16)))
        loader.write_bytes(work + (y * width + x) * 16, struct.pack("<4f", 0.25, 0.5, 0.75, 1.0))
        loader.write_bytes(out, b"\x00" * (width * 540 * 4))
        address = (y * width + x) * 4
        loader.call_function(OUTPUT, int_args=[params, x, y, 0, out + address], max_instructions=10000)
        aex_bytes = loader.read_bytes(out + address, 4).hex()
        expected_out = bytearray(width * 540 * 4)
        model_output(loader, params, y, x, expected_out, out + address, width)
        model_bytes = bytes(expected_out[address:address + 4]).hex()
        checks.append({"xy": [x, y], "aex_populate_rgba": aex_rgba, "model_populate_rgba": model_rgba, "aex_output_bytes": aex_bytes, "model_output_bytes": model_bytes, "match": aex_rgba == model_rgba and aex_bytes == model_bytes})
    return {"status": "pass" if all(item["match"] for item in checks) else "mismatch", "samples": checks, "disasm": {"populate": "0x180006980", "output": "0x180006b30", "channel_max": 255.0}}


def callback_model_check16(loader: AexLoader) -> dict:
    width, height = 3, 2
    params = loader.host_alloc(0x8200)
    work = loader.bump_alloc(width * height * 16, align=64)
    pixel_ptr = loader.bump_alloc(8, align=8)
    out = loader.bump_alloc(width * height * 8, align=8)
    loader.write_bytes(params, b"\x00" * 0x8200)
    loader.write_bytes(params + 0x8078, struct.pack("<Q", work))
    loader.write_bytes(params + 0x8090, struct.pack("<Q", work))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", width))
    loader.write_bytes(params + 0x28, struct.pack("<f", 1.0))
    witnesses = (
        (0, 0, (0, 1, 16384, 32768)),
        (1, 0, (32768, 32640, 128, 255)),
        (2, 1, (12345, 23456, 30000, 32767)),
    )
    checks = []
    for x, y, words in witnesses:
        pixel = struct.pack("<4H", *words)
        address = (y * width + x) * 16
        loader.write_bytes(pixel_ptr, pixel)
        loader.write_bytes(work + address, b"\x00" * 16)
        loader.call_function(POPULATE16, int_args=[params, x, y, pixel_ptr], max_instructions=10000)
        actual_floats = loader.read_bytes(work + address, 16)
        loader.write_bytes(work + address, b"\x00" * 16)
        model_populate16(loader, params, y, x, pixel)
        model_floats = loader.read_bytes(work + address, 16)

        probe = struct.pack("<4f", 0.25, 0.5, 0.75, 1.0)
        loader.write_bytes(work + address, probe)
        out_address = out + (y * width + x) * 8
        loader.write_bytes(out_address, b"\x00" * 8)
        loader.call_function(OUTPUT16, int_args=[params, x, y, 0, out_address], max_instructions=10000)
        actual_output = loader.read_bytes(out_address, 8)
        expected_output = bytearray(width * height * 8)
        model_output16(loader, params, y, x, expected_output, out_address, width)
        model_output_bytes = bytes(expected_output[(y * width + x) * 8:(y * width + x + 1) * 8])
        checks.append({
            "xy": [x, y], "input_words_argb": list(words),
            "actual_populate_hex": actual_floats.hex(),
            "model_populate_hex": model_floats.hex(),
            "actual_output_hex": actual_output.hex(),
            "model_output_hex": model_output_bytes.hex(),
            "match": actual_floats == model_floats and actual_output == model_output_bytes,
        })
    return {
        "status": "pass" if all(item["match"] for item in checks) else "mismatch",
        "samples": checks,
        "disasm": {"populate": "0x1800068e0", "output": "0x180006a90", "channel_max": 32768.0},
    }


def callback_model_check32(loader: AexLoader) -> dict:
    width, height = 2, 2
    params = loader.host_alloc(0x8200); work = loader.bump_alloc(width * height * 16, align=64)
    pixel_ptr = loader.bump_alloc(16, align=16); out_ptr = loader.bump_alloc(16, align=16)
    loader.write_bytes(params, b"\0" * 0x8200)
    loader.write_bytes(params + 0x8078, struct.pack("<Q", work)); loader.write_bytes(params + 0x8090, struct.pack("<Q", work))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", width)); loader.write_bytes(params + 0x28, struct.pack("<f", 1.0))
    checks = []
    for x, y, values in ((0, 0, (0.0, 0.25, 0.5, 0.75)), (1, 1, (1.0, 1.25, -0.5, 0.125))):
        pixel = struct.pack("<4f", *values); address = (y * width + x) * 16
        loader.write_bytes(pixel_ptr, pixel); loader.call_function(POPULATE32, int_args=[params, x, y, pixel_ptr], max_instructions=10000)
        actual_pop = loader.read_bytes(work + address, 16)
        loader.write_bytes(work + address, b"\0" * 16); model_populate32(loader, params, y, x, pixel)
        model_pop = loader.read_bytes(work + address, 16)
        loader.write_bytes(work + address, struct.pack("<4f", 0.25, 0.5, 0.75, 1.0))
        loader.call_function(OUTPUT32, int_args=[params, x, y, 0, out_ptr], max_instructions=10000)
        actual_out = loader.read_bytes(out_ptr, 16); modeled = bytearray(width * height * 16)
        model_output32(loader, params, y, x, modeled, out_ptr, width)
        model_out = bytes(modeled[address:address + 16])
        checks.append({"xy": [x, y], "actual_populate": actual_pop.hex(), "model_populate": model_pop.hex(),
                       "actual_output": actual_out.hex(), "model_output": model_out.hex(),
                       "match": actual_pop == model_pop and actual_out == model_out})
    return {"status": "pass" if all(c["match"] for c in checks) else "mismatch", "samples": checks,
            "disasm": {"populate": "0x180006a20", "output": "0x180006bd0"}}


def build_world(loader: AexLoader, width: int, height: int, data: bytes,
                rowbytes: int, area: tuple[int, int, int, int]) -> int:
    ptr = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(ptr, data)
    world = loader.host_alloc(0x80)
    loader.write_bytes(world, b"\x00" * 0x80)
    loader.write_bytes(world + 0x18, struct.pack("<Q", ptr))
    loader.write_bytes(world + 0x20, struct.pack("<I", rowbytes))
    loader.write_bytes(world + 0x24, struct.pack("<I", width))
    loader.write_bytes(world + 0x28, struct.pack("<I", height))
    loader.write_bytes(world + 0x2C, struct.pack("<4i", *area))
    return world


def padded_world_bytes(pixels: bytes, width: int, height: int, rowbytes: int) -> bytes:
    packed_rowbytes = len(pixels) // height
    if len(pixels) != packed_rowbytes * height or rowbytes < packed_rowbytes:
        raise ValueError("invalid PF_EffectWorld byte layout")
    rows = bytearray(rowbytes * height)
    for y in range(height):
        source = y * packed_rowbytes
        destination = y * rowbytes
        rows[destination:destination + packed_rowbytes] = pixels[source:source + packed_rowbytes]
    return bytes(rows)


def build_rotate_candidate() -> tuple[tempfile.TemporaryDirectory, ctypes.CDLL, object]:
    """Build the bounded, actual-AEX-conformant rotate primitive outside the repo."""
    temp_dir = tempfile.TemporaryDirectory(prefix="olm_dblur_rotate_")
    library_path = Path(temp_dir.name) / "libdblur_rotate.dylib"
    subprocess.run(
        [
            "c++",
            "-std=c++17",
            "-O0",
            "-fno-fast-math",
            "-ffp-contract=off",
            "-fPIC",
            "-shared",
            str(ROOT / "core/dblur_rotate.cpp"),
            "-o",
            str(library_path),
        ],
        cwd=ROOT,
        check=True,
    )
    library = ctypes.CDLL(str(library_path))
    function = library.olm_dblur_rotate_rgba_f32
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
    ]
    function.restype = None
    return temp_dir, library, function


def build_rowdriver_candidate() -> tuple[tempfile.TemporaryDirectory, ctypes.CDLL, object, object, object]:
    """Build the bounded, actual-AEX-conformant default-mode rowdriver."""
    temp_dir = tempfile.TemporaryDirectory(prefix="olm_dblur_rowdriver_")
    library_path = Path(temp_dir.name) / "libdblur_rowdriver.dylib"
    subprocess.run(
        [
            "c++",
            "-std=c++17",
            "-O2",
            "-fno-fast-math",
            "-ffp-contract=off",
            "-fPIC",
            "-shared",
            str(ROOT / "core/dblur_rowdriver.cpp"),
            "-o",
            str(library_path),
        ],
        cwd=ROOT,
        check=True,
    )
    library = ctypes.CDLL(str(library_path))
    function = library.olm_dblur_rowdriver_f32
    base_argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]
    function.argtypes = base_argtypes
    function.restype = None
    noise_function = library.olm_dblur_rowdriver_noise_f32
    noise_function.argtypes = base_argtypes[:5] + base_argtypes[6:] + [
        ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_float, ctypes.c_int,
    ]
    noise_function.restype = None
    field_function = library.olm_dblur_rowdriver_field_f32
    field_function.argtypes = base_argtypes[:5] + base_argtypes[6:] + [
        ctypes.POINTER(ctypes.c_float),
    ]
    field_function.restype = None
    return temp_dir, library, function, noise_function, field_function


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=ROOT / "plugins_2025/OLMDirectionalBlur.aex")
    parser.add_argument("--source", type=Path, default=ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png")
    parser.add_argument("--expected", type=Path, help="optional Windows reference PNG for direct host-output comparison")
    parser.add_argument("--output", type=Path, default=ROOT / "refs/conformance/dblur_fullrender_host_fixture_20260711.json")
    parser.add_argument("--host-output-raw", type=Path, help="write complete host ARGB8 bytes when render finishes")
    parser.add_argument("--host-output-png", type=Path, help="write complete host output as RGBA PNG when render finishes")
    parser.add_argument("--field-source-raw", type=Path,
                        help="write mode-2 unrotated float32 field bytes")
    parser.add_argument("--field-rotated-raw", type=Path,
                        help="write mode-2 rotated float32 field bytes")
    parser.add_argument("--slow-trace", action="store_true", help="enable image-text instruction tracing for ABI capture")
    parser.add_argument("--max-instructions", type=int, default=200_000_000)
    parser.add_argument("--downsample-num", type=int, default=1)
    parser.add_argument("--downsample-den", type=int, default=2)
    parser.add_argument("--angle", type=float, default=0.0)
    parser.add_argument("--brightness-gain", type=float, default=1.0)
    parser.add_argument("--size-variation", type=int, default=92)
    parser.add_argument("--front-strength", type=int, default=1690)
    parser.add_argument("--front-alpha-fade", type=int, default=0)
    parser.add_argument("--front-sharp-tail", type=int, default=45)
    parser.add_argument("--back-strength", type=int, default=0)
    parser.add_argument("--back-alpha-fade", type=int, default=0)
    parser.add_argument("--back-sharp-tail", type=int, default=0)
    parser.add_argument("--noise-variation", type=int, default=0)
    parser.add_argument("--noise-type", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--noise-offset", type=int, default=0)
    parser.add_argument("--thickness", type=float, default=10.0)
    parser.add_argument("--bitdepth", type=int, choices=(8, 16, 32), default=8)
    parser.add_argument(
        "--world-area", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        default=(0, 0, None, None),
        help="PF_EffectWorld extent passed to PF_Iterate8; defaults to the full world",
    )
    parser.add_argument("--row-padding", type=int, default=0,
                        help="extra bytes after each PF_EffectWorld row")
    parser.add_argument("--noise-layer-row-padding", type=int,
                        help="extra bytes after each controlled Noise Layer row; defaults to --row-padding")
    parser.add_argument("--noise-layer-origin", nargs=2, type=int, metavar=("X", "Y"),
                        help="controlled Noise Layer extent origin; defaults to the render world origin")
    parser.add_argument("--noise-layer-size", nargs=2, type=int, metavar=("WIDTH", "HEIGHT"),
                        help="controlled Noise Layer dimensions; defaults to render source dimensions; smaller sizes use a top-left crop")
    parser.add_argument(
        "--detour-rotate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="replace FUN_180001ec0 with the bounded byte-exact portable candidate",
    )
    parser.add_argument(
        "--detour-rowdriver",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="replace default-mode FUN_1800038d0 chunks with the bounded byte-exact candidate",
    )
    parser.add_argument(
        "--schedule-only-rowdriver",
        action="store_true",
        help="record AEX rowdriver scheduling, skip row work, and stop before normalization",
    )
    args = parser.parse_args()
    if args.schedule_only_rowdriver and not args.detour_rowdriver:
        parser.error("--schedule-only-rowdriver requires --detour-rowdriver")
    width, height, source_rgba, source8 = load_argb(args.source)
    if args.bitdepth == 32:
        source = b"".join(
            struct.pack("<f", value / 255.0) for value in source8
        )
        pixel_size = 16
        populate_callback = POPULATE32
        output_callback = OUTPUT32
    elif args.bitdepth == 16:
        source = b"".join(
            struct.pack("<H", value * 128) for value in source8
        )
        pixel_size = 8
        populate_callback = POPULATE16
        output_callback = OUTPUT16
    else:
        source = source8
        pixel_size = 4
        populate_callback = POPULATE
        output_callback = OUTPUT
    left, top, right, bottom = args.world_area
    right = width if right is None else right
    bottom = height if bottom is None else bottom
    area = (left, top, right, bottom)
    if (args.row_padding < 0 or
            (args.noise_layer_row_padding is not None and args.noise_layer_row_padding < 0) or
            not (0 <= left <= right <= width and 0 <= top <= bottom <= height)):
        raise ValueError(f"invalid world mapping controls: area={area}, row_padding={args.row_padding}")
    rowbytes = width * pixel_size + args.row_padding
    source_world_bytes = padded_world_bytes(source, width, height, rowbytes)
    noise_layer_width, noise_layer_height = (
        (width, height) if args.noise_layer_size is None else tuple(args.noise_layer_size)
    )
    if noise_layer_width <= 0 or noise_layer_height <= 0:
        raise ValueError("controlled Noise Layer size must be positive")
    noise_layer_pixels_mut = bytearray(noise_layer_width * noise_layer_height * pixel_size)
    copy_width = min(width, noise_layer_width)
    copy_height = min(height, noise_layer_height)
    for y in range(copy_height):
        source_offset = y * width * pixel_size
        layer_offset = y * noise_layer_width * pixel_size
        noise_layer_pixels_mut[layer_offset:layer_offset + copy_width * pixel_size] = \
            source[source_offset:source_offset + copy_width * pixel_size]
    noise_layer_pixels = bytes(noise_layer_pixels_mut)
    noise_layer_padding = args.row_padding if args.noise_layer_row_padding is None else args.noise_layer_row_padding
    noise_layer_rowbytes = noise_layer_width * pixel_size + noise_layer_padding
    noise_layer_world_bytes = padded_world_bytes(
        noise_layer_pixels, noise_layer_width, noise_layer_height, noise_layer_rowbytes
    )
    noise_origin_x, noise_origin_y = (
        (left, top) if args.noise_layer_origin is None else tuple(args.noise_layer_origin)
    )
    noise_layer_area = (
        noise_origin_x, noise_origin_y,
        noise_origin_x + noise_layer_width, noise_origin_y + noise_layer_height,
    )
    loader = AexLoader(str(args.aex), verbose=False, fast=not args.slow_trace)
    loader.register_libm_impls(max_threads=1)

    # Keep the real AEX math path alive.  register_libm_impls covers the
    # common trig/exp helpers; these additional imports are present in this
    # binary's hot render path and must not fall through to RAX=0.
    def import_f1(fn):
        def impl(_uc, _args):
            loader.write_xmm_f32(0, fn(loader.read_xmm_f32(0)))
            return 0
        return impl

    def import_d1(fn):
        def impl(_uc, _args):
            loader.write_xmm_f64(0, fn(loader.read_xmm_f64(0)))
            return 0
        return impl

    def import_powf(_uc, _args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    import math
    for name, impl in {
        "powf": import_powf,
        "sqrtf": import_f1(math.sqrt),
        "ceilf": import_f1(math.ceil),
        "ceil": import_d1(math.ceil),
        "cosf": import_f1(math.cos),
        "sinf": import_f1(math.sin),
    }.items():
        loader.register_import_impl(name, impl)

    spbasic = loader.host_alloc(0x20)
    iterate_suite = loader.host_alloc(0x20)
    loader.write_bytes(iterate_suite, struct.pack("<Q", loader.install_callback("PF_Iterate8", lambda ld, _args: 0)))

    handle_objects: dict[int, int] = {}

    def handle_new(ld: AexLoader, args_: list[int]) -> int:
        size = max(1, args_[0] & 0xFFFFFFFF)
        handle = ld.host_alloc(8)
        payload = ld.bump_alloc(size, align=8)
        ld.write_bytes(handle, struct.pack("<Q", payload))
        handle_objects[handle] = payload
        return handle

    def handle_lock(ld: AexLoader, args_: list[int]) -> int:
        handle = args_[0]
        return handle_objects.get(handle, u64(ld, handle) if handle else 0)

    def handle_unlock(_ld: AexLoader, _args_: list[int]) -> int:
        return 0

    def handle_dispose(ld: AexLoader, args_: list[int]) -> int:
        handle_objects.pop(args_[0], None)
        return 0

    handle_suite = loader.host_alloc(0x20)
    loader.write_bytes(handle_suite, struct.pack("<4Q",
        loader.install_callback("PFHandle.new", handle_new),
        loader.install_callback("PFHandle.lock", handle_lock),
        loader.install_callback("PFHandle.unlock", handle_unlock),
        loader.install_callback("PFHandle.dispose", handle_dispose),
    ))

    def acquire_suite(ld: AexLoader, args_: list[int]) -> int:
        out = args_[2]
        name = ld.read_bytes(args_[0], 64).split(b"\x00", 1)[0]
        suite = handle_suite if name == b"PF Handle Suite" else iterate_suite
        ld.write_bytes(out, struct.pack("<Q", suite))
        return 0

    loader.write_bytes(spbasic, struct.pack("<2Q", loader.install_callback("SPBasic.AcquireSuite", acquire_suite), loader.install_callback("SPBasic.ReleaseSuite", lambda _ld, _args: 0)))
    in_data = loader.host_alloc(0x200)
    loader.write_bytes(in_data, b"\x00" * 0x200)
    loader.write_bytes(in_data + 0x180, struct.pack("<Q", spbasic))
    if args.downsample_num <= 0 or args.downsample_den <= 0:
        raise ValueError("downsample numerator and denominator must be positive")
    loader.write_bytes(in_data + 0x11C, struct.pack("<I", args.downsample_num))
    loader.write_bytes(in_data + 0x120, struct.pack("<I", args.downsample_den))
    # Mode-2 validates the checked-out Layer dimensions against the render
    # source dimensions at PF_InData +0xfc/+0x100 after applying render scale.
    loader.write_bytes(in_data + 0xFC, struct.pack("<I", width))
    loader.write_bytes(in_data + 0x100, struct.pack("<I", height))

    def param_checkout(ld: AexLoader, _args: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        # The AEX call has four register arguments plus param_def as the fifth
        # stack argument, so its callee slot is RSP+0x30.
        param_def = u64(ld, rsp + 0x30)
        require_ptr(ld, param_def, "param_def", 0xB0)
        ld.write_bytes(param_def, b"\x00" * 0xB0)
        index = ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF  # PF param index
        # FUN_180006c50 reads PF_ParamDef.u at +0x38. Double values begin at
        # +0x38, int sliders use the full int32 there, and short-slider values
        # are sStack_ae at +0x3a within that union.
        if index == 1:
            ld.write_bytes(param_def + 0x3A, struct.pack("<h", int(round(args.angle))))
        elif index == 2:
            ld.write_bytes(param_def + 0x38, struct.pack("<d", args.brightness_gain))
        elif index == 3:
            ld.write_bytes(param_def + 0x3A, struct.pack("<h", args.size_variation))
        elif index == 5:
            ld.write_bytes(param_def + 0x38, struct.pack("<i", args.front_strength))
        elif index == 6:
            ld.write_bytes(param_def + 0x38, struct.pack("<i", args.front_alpha_fade))
        elif index == 7:
            ld.write_bytes(param_def + 0x3A, struct.pack("<h", args.front_sharp_tail))
        elif index == 10:
            ld.write_bytes(param_def + 0x38, struct.pack("<i", args.back_strength))
        elif index == 11:
            ld.write_bytes(param_def + 0x38, struct.pack("<i", args.back_alpha_fade))
        elif index == 12:
            ld.write_bytes(param_def + 0x3A, struct.pack("<h", args.back_sharp_tail))
        elif index == 15:
            ld.write_bytes(param_def + 0x3A, struct.pack("<h", args.noise_variation))
        elif index == 16:
            ld.write_bytes(param_def + 0x38, struct.pack("<i", args.noise_type))
        elif index == 17:
            # PF_LayerDef begins at PF_ParamDef.u (+0x38).  The 8-bpc render
            # path reads its embedded PF_EffectWorld fields at u+0x18:
            # data, rowbytes, width and height.  Use the fixture source as a
            # controlled Layer-noise checkout so mode 2 exercises the natural
            # AEX field builder instead of observing an all-zero null layer.
            ld.write_bytes(
                param_def + 0x50,
                ld.read_bytes(noise_layer_world + 0x18, 0x28),
            )
        elif index == 18:
            ld.write_bytes(param_def + 0x38, struct.pack("<i", args.seed))
        elif index == 19:
            ld.write_bytes(param_def + 0x3A, struct.pack("<h", args.noise_offset))
        elif index == 20:
            ld.write_bytes(param_def + 0x38, struct.pack("<d", args.thickness))
        return 0

    def param_checkin(_ld: AexLoader, _args: list[int]) -> int:
        return 0

    loader.write_bytes(in_data, struct.pack("<Q", loader.install_callback("PF_ParamCheckout", param_checkout)))
    loader.write_bytes(in_data + 8, struct.pack("<Q", loader.install_callback("PF_ParamCheckin", param_checkin)))
    dispatch = loader.host_alloc(0x80)
    loader.write_bytes(dispatch, b"\x00" * 0x80)
    loader.write_bytes(dispatch + 0x40, struct.pack("<Q", loader.install_callback("RenderContext.suite40", lambda _ld, _args: 0)))
    loader.write_bytes(in_data + 0xB0, struct.pack("<Q", dispatch))
    loader.write_bytes(in_data + 0xB8, struct.pack("<Q", loader.host_alloc(8)))

    input_world = build_world(loader, width, height, source_world_bytes, rowbytes, area)
    noise_layer_world = build_world(
        loader, noise_layer_width, noise_layer_height,
        noise_layer_world_bytes, noise_layer_rowbytes, noise_layer_area
    )
    render_desc = loader.host_alloc(0x80)
    loader.write_bytes(render_desc, b"\x00" * 0x80)
    loader.write_bytes(render_desc + 0x24, struct.pack("<I", width))
    loader.write_bytes(render_desc + 0x28, struct.pack("<I", height))
    output_bytes = bytearray(width * height * pixel_size)
    output_world = build_world(loader, width, height, bytes(rowbytes * height), rowbytes, area)
    output_data_ptr = u64(loader, output_world + 0x18)
    depth_descriptor = loader.host_alloc(0x40)
    loader.write_bytes(depth_descriptor, b"\x00" * 0x40)
    loader.write_bytes(depth_descriptor + 0x2C, struct.pack("<H", args.bitdepth))
    cb_struct = loader.host_alloc(0x20)
    param_6 = loader.host_alloc(0x20)
    # FUN_180007bd0 reads param_6[0]+0x2c as depth.  It is a separate host
    # descriptor; checked-out PF_EffectWorld objects own extent_hint at +0x2c.
    loader.write_bytes(param_6, struct.pack("<2Q", depth_descriptor, cb_struct))

    def checkout_input(ld: AexLoader, args_: list[int]) -> int:
        ld.write_bytes(args_[2], struct.pack("<Q", input_world))
        return 0

    def checkout_output(ld: AexLoader, args_: list[int]) -> int:
        ld.write_bytes(args_[1], struct.pack("<Q", output_world))
        return 0

    loader.write_bytes(cb_struct, struct.pack("<Q", loader.install_callback("checkout_input", checkout_input)))
    # FUN_180007bd0 reads the output checkout callback at cb_struct+0x10.
    loader.write_bytes(cb_struct + 0x10, struct.pack("<Q", loader.install_callback("checkout_output", checkout_output)))

    observed = {"iterate_calls": [], "rotate_entry": [], "rotate_detours": [], "rowdriver_calls": [], "rowdriver_detours": [], "rowdriver_state": {}, "param_context": {}, "render_return": 0, "host_output": {}, "last_rips": [], "early_branches": [], "wrapper_trace": [], "worker_loop": [], "budget": {}, "checkpoints": {}}

    rotate_temp_dir = None
    rotate_library = None
    if args.detour_rotate:
        rotate_temp_dir, rotate_library, rotate_function = build_rotate_candidate()

        def detour_rotate(ld: AexLoader, args_: list[int]) -> int:
            source_ptr, destination_ptr = args_[0], args_[1]
            rotate_width = args_[2] & 0xFFFFFFFF
            rotate_height = args_[3] & 0xFFFFFFFF
            if not (0 < rotate_width <= 32768 and 0 < rotate_height <= 32768):
                raise RuntimeError(f"invalid rotate dimensions: {rotate_width}x{rotate_height}")
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            angle_bits = u32(ld, rsp + 0x28)
            angle = struct.unpack("<f", struct.pack("<I", angle_bits))[0]
            float_count = rotate_width * rotate_height * 4
            byte_count = float_count * 4
            source_bytes = ld.read_bytes(source_ptr, byte_count)
            destination_before = ld.read_bytes(destination_ptr, byte_count)
            source_array = (ctypes.c_float * float_count).from_buffer_copy(source_bytes)
            destination_array = (ctypes.c_float * float_count).from_buffer_copy(destination_before)
            rotate_function(
                source_array,
                destination_array,
                rotate_width,
                rotate_height,
                ctypes.c_float(angle),
            )
            destination_after = ctypes.string_at(ctypes.addressof(destination_array), byte_count)
            ld.write_bytes(destination_ptr, destination_after)
            observed["rotate_detours"].append({
                "call": len(observed["rotate_detours"]) + 1,
                "source": hex(source_ptr),
                "destination": hex(destination_ptr),
                "dimensions": [rotate_width, rotate_height],
                "angle_bits": f"0x{angle_bits:08x}",
                "angle": angle,
                "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
                "destination_before_sha256": hashlib.sha256(destination_before).hexdigest(),
                "destination_after_sha256": hashlib.sha256(destination_after).hexdigest(),
            })
            return 0

        loader.detour_function(ROTATE, "DirectionalBlur.rotate.byte_exact", detour_rotate)

    rowdriver_temp_dir = None
    rowdriver_library = None
    rowdriver_cache: dict = {}
    if args.detour_rowdriver:
        if not args.schedule_only_rowdriver:
            (rowdriver_temp_dir, rowdriver_library, rowdriver_function,
             rowdriver_noise_function,
             rowdriver_field_function) = build_rowdriver_candidate()

        def make_float_array(blob: bytes):
            count = len(blob) // 4
            array = (ctypes.c_float * max(1, count))()
            if blob:
                ctypes.memmove(ctypes.addressof(array), blob, len(blob))
            return array

        def array_bytes(array, size: int) -> bytes:
            return ctypes.string_at(ctypes.addressof(array), size)

        def detour_rowdriver(ld: AexLoader, args_: list[int]) -> int:
            row_start = args_[0] & 0xFFFFFFFF
            row_end = args_[1] & 0xFFFFFFFF
            source_slot, destination_slot = args_[2], args_[3]
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            row_width = u32(ld, rsp + 0x28)
            row_height = u32(ld, rsp + 0x30)
            params = u64(ld, rsp + 0x38)
            source_ptr = u64(ld, source_slot)
            destination_ptr = u64(ld, destination_slot)
            mode = u32(ld, params + 0x20)
            if source_ptr == destination_ptr:
                raise RuntimeError("rowdriver source/destination alias is not covered")
            if not (0 <= row_start < row_end <= row_height and 0 < row_width <= 32768 and row_height <= 32768):
                raise RuntimeError(f"invalid rowdriver range {row_start}:{row_end} for {row_width}x{row_height}")

            if args.schedule_only_rowdriver:
                observed["rowdriver_detours"].append({
                    "call": len(observed["rowdriver_detours"]) + 1,
                    "rows": [row_start, row_end],
                    "width": row_width,
                    "height": row_height,
                    "source": hex(source_ptr),
                    "destination": hex(destination_ptr),
                    "params": hex(params),
                    "mode": mode,
                    "rsp": hex(rsp),
                    "return_address": hex(u64(ld, rsp)),
                    "execution_context": "single Unicorn thread; AEX worker-loop call order",
                })
                return 0

            key = (source_ptr, destination_ptr, row_width, row_height, params)
            if not rowdriver_cache:
                pixel_count = row_width * row_height
                plane_bytes = pixel_count * 16
                scalar_bytes = pixel_count * 4
                denominator_ptr = u64(ld, params + 0x8080)
                alpha_ptr = u64(ld, params + 0x8088)
                comp_ptr = u64(ld, params + 0x8118)
                counts = {
                    "scatter_front": u32(ld, params + 0x48),
                    "prepass_front": u32(ld, params + 0x4C),
                    "scatter_back": u32(ld, params + 0x50),
                    "prepass_back": u32(ld, params + 0x54),
                }
                source_blob = ld.read_bytes(source_ptr, plane_bytes)
                destination_blob = ld.read_bytes(destination_ptr, plane_bytes)
                denominator_blob = ld.read_bytes(denominator_ptr, scalar_bytes)
                alpha_blob = ld.read_bytes(alpha_ptr, scalar_bytes)
                comp_blob = ld.read_bytes(comp_ptr, plane_bytes)
                table_blobs = {
                    "scatter_front": ld.read_bytes(params + 0x58, counts["scatter_front"] * 4),
                    "scatter_back": ld.read_bytes(params + 0x4068, counts["scatter_back"] * 4),
                    "prepass_front": ld.read_bytes(params + 0x3ED8, counts["prepass_front"] * 4),
                    "prepass_back": ld.read_bytes(params + 0x7EE8, counts["prepass_back"] * 4),
                }
                tables = {name: make_float_array(blob) for name, blob in table_blobs.items()}
                noise = None
                field = None
                if mode == 2:
                    field_ptr = u64(ld, params + 0x80B0)
                    field_blob = ld.read_bytes(field_ptr, scalar_bytes)
                    field = {
                        "samples": make_float_array(field_blob),
                        "sha256": hashlib.sha256(field_blob).hexdigest(),
                    }
                if mode == 3:
                    noise_context = params + 0x80C0
                    noise_ptr = u64(ld, noise_context + 0x08)
                    noise_width = u32(ld, noise_context + 0x10)
                    noise_height = u32(ld, noise_context + 0x14)
                    noise_blob = ld.read_bytes(noise_ptr, noise_width * noise_height * 4)
                    noise = {
                        "samples": make_float_array(noise_blob),
                        "stride": noise_width,
                        "height": noise_height,
                        "cell_size": f32(ld, noise_context + 0x40),
                        "interpolate": int(bool(ld.read_bytes(params + 0x80BC, 1)[0])),
                        "sha256": hashlib.sha256(noise_blob).hexdigest(),
                    }
                rowdriver_cache.update({
                    "key": key,
                    "next_row": row_start,
                    "plane_bytes": plane_bytes,
                    "scalar_bytes": scalar_bytes,
                    "denominator_ptr": denominator_ptr,
                    "alpha_ptr": alpha_ptr,
                    "source": make_float_array(source_blob),
                    "destination": make_float_array(destination_blob),
                    "denominator": make_float_array(denominator_blob),
                    "alpha": make_float_array(alpha_blob),
                    "comp": make_float_array(comp_blob),
                    "tables": tables,
                    "counts": counts,
                    "noise": noise,
                    "field": field,
                })
                observed["rowdriver_state"] = {
                    "dimensions": [row_width, row_height],
                    "source": hex(source_ptr),
                    "destination": hex(destination_ptr),
                    "denominator": hex(denominator_ptr),
                    "alpha": hex(alpha_ptr),
                    "comp_map": hex(comp_ptr),
                    "mode": mode,
                    "mode_branch": "field" if mode == 2 else (
                        "interpolated" if mode == 3 else "default"),
                    "counts": counts,
                    "table_sha256": {
                        name: hashlib.sha256(blob).hexdigest()
                        for name, blob in table_blobs.items()
                    },
                    "table_edge_values": {
                        name: {
                            "first": struct.unpack("<f", blob[:4])[0] if blob else None,
                            "last": struct.unpack("<f", blob[-4:])[0] if blob else None,
                        }
                        for name, blob in table_blobs.items()
                    },
                    "source_before_sha256": hashlib.sha256(source_blob).hexdigest(),
                    "destination_before_sha256": hashlib.sha256(destination_blob).hexdigest(),
                    "denominator_before_sha256": hashlib.sha256(denominator_blob).hexdigest(),
                    "alpha_before_sha256": hashlib.sha256(alpha_blob).hexdigest(),
                    "comp_map_sha256": hashlib.sha256(comp_blob).hexdigest(),
                    "noise_plane": None if noise is None else {
                        "dimensions": [noise["stride"], noise["height"]],
                        "cell_size": noise["cell_size"],
                        "interpolate": bool(noise["interpolate"]),
                        "sha256": noise["sha256"],
                    },
                    "field_sha256": None if field is None else field["sha256"],
                }
            elif rowdriver_cache["key"] != key:
                raise RuntimeError("rowdriver detour ownership changed within one render")

            if row_start != rowdriver_cache["next_row"]:
                raise RuntimeError(f"non-contiguous rowdriver range: expected {rowdriver_cache['next_row']}, got {row_start}")

            rowdriver_args = (
                row_start,
                row_end,
                rowdriver_cache["source"],
                rowdriver_cache["destination"],
                row_width,
                mode,
                ctypes.c_float(f32(ld, params + 0x2C)),
                ctypes.c_float(f32(ld, params + 0x30)),
                ctypes.c_float(f32(ld, params + 0x38)),
                ctypes.c_float(f32(ld, params + 0x40)),
                ctypes.c_float(f32(ld, params + 0x44)),
                rowdriver_cache["tables"]["scatter_front"],
                rowdriver_cache["tables"]["scatter_back"],
                rowdriver_cache["tables"]["prepass_front"],
                rowdriver_cache["tables"]["prepass_back"],
                rowdriver_cache["denominator"],
                rowdriver_cache["alpha"],
                rowdriver_cache["comp"],
                rowdriver_cache["counts"]["scatter_front"],
                rowdriver_cache["counts"]["scatter_back"],
                rowdriver_cache["counts"]["prepass_front"],
                rowdriver_cache["counts"]["prepass_back"],
            )
            if mode == 3:
                noise = rowdriver_cache["noise"]
                rowdriver_noise_function(
                    *rowdriver_args[:5], *rowdriver_args[6:],
                    noise["samples"], noise["stride"],
                    ctypes.c_float(noise["cell_size"]), noise["interpolate"],
                )
            elif mode == 2:
                rowdriver_field_function(
                    *rowdriver_args[:5], *rowdriver_args[6:],
                    rowdriver_cache["field"]["samples"],
                )
            else:
                rowdriver_function(*rowdriver_args)

            row_pixels = (row_end - row_start) * row_width
            plane_offset = row_start * row_width * 16
            scalar_offset = row_start * row_width * 4
            plane_size = row_pixels * 16
            scalar_size = row_pixels * 4
            destination_all = array_bytes(rowdriver_cache["destination"], rowdriver_cache["plane_bytes"])
            denominator_all = array_bytes(rowdriver_cache["denominator"], rowdriver_cache["scalar_bytes"])
            alpha_all = array_bytes(rowdriver_cache["alpha"], rowdriver_cache["scalar_bytes"])
            destination_rows = destination_all[plane_offset:plane_offset + plane_size]
            denominator_rows = denominator_all[scalar_offset:scalar_offset + scalar_size]
            alpha_rows = alpha_all[scalar_offset:scalar_offset + scalar_size]
            ld.write_bytes(destination_ptr + plane_offset, destination_rows)
            ld.write_bytes(rowdriver_cache["denominator_ptr"] + scalar_offset, denominator_rows)
            ld.write_bytes(rowdriver_cache["alpha_ptr"] + scalar_offset, alpha_rows)
            rowdriver_cache["next_row"] = row_end
            observed["rowdriver_detours"].append({
                "call": len(observed["rowdriver_detours"]) + 1,
                "rows": [row_start, row_end],
                "destination_rows_sha256": hashlib.sha256(destination_rows).hexdigest(),
                "denominator_rows_sha256": hashlib.sha256(denominator_rows).hexdigest(),
                "alpha_rows_sha256": hashlib.sha256(alpha_rows).hexdigest(),
            })
            if row_end == row_height:
                observed["rowdriver_state"].update({
                    "complete": True,
                    "destination_after_sha256": hashlib.sha256(destination_all).hexdigest(),
                    "denominator_after_sha256": hashlib.sha256(denominator_all).hexdigest(),
                    "alpha_after_sha256": hashlib.sha256(alpha_all).hexdigest(),
                    "calls": len(observed["rowdriver_detours"]),
                })
            return 0

        loader.detour_function(ROWDRIVER, "DirectionalBlur.rowdriver.byte_exact", detour_rowdriver)

    if args.schedule_only_rowdriver:
        def stop_before_normalization(ld: AexLoader, _address: int, _size: int) -> None:
            observed["checkpoints"]["schedule_complete"] = {
                "stop": "0x180005554",
                "rowdriver_calls": len(observed["rowdriver_detours"]),
            }
            ld.uc.emu_stop()

        loader.add_code_hook(0x180005554, stop_before_normalization)

    def trace_rip(uc, address, _size, _user_data):
        observed["last_rips"].append(hex(address))
        del observed["last_rips"][:-32]
        if 0x180006700 <= address <= 0x1800067D0 and len(observed["wrapper_trace"]) < 96:
            rsp = uc.reg_read(UC_X86_REG_RSP)
            observed["wrapper_trace"].append({
                "rip": hex(address),
                "rcx": hex(uc.reg_read(UC_X86_REG_RCX)),
                "rdx": hex(uc.reg_read(UC_X86_REG_RDX)),
                "r8": hex(uc.reg_read(UC_X86_REG_R8)),
                "r9": hex(uc.reg_read(UC_X86_REG_R9)),
                "r10": hex(uc.reg_read(UC_X86_REG_R10)),
                "rsp": hex(rsp),
                "slots": {hex(offset): hex(u64(loader, rsp + offset)) for offset in (0x20, 0x28, 0x30, 0x38, 0x40, 0x2f8, 0x510, 0x518, 0x520, 0x528)},
            })

    loader.uc.hook_add(UC_HOOK_CODE, trace_rip)

    from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R12, UC_X86_REG_R14, UC_X86_REG_RSI, UC_X86_REG_RDI
    branch_sites = {
        0x180007BD0: "render_worker_entry",
        0x180004A20: "smart_render_entry",
        0x1800067C5: "iterate8_wrapper_call",
        0x180007C0F: "depth_read",
        0x180007C38: "checkout_input_return",
        0x180007C51: "checkout_output_return",
        0x180007C65: "depth_dispatch_compare",
        0x180007CB7: "8bpc_setup_error_test",
        0x180007CD5: "param_read_return",
        0x180007CDA: "param_read_error_test",
        0x180007D04: "call_8bpc_worker",
        0x180004B50: "smart_render_nonzero_guard",
    }
    def capture_branch(ld: AexLoader, address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        observed["early_branches"].append({
            "rip": hex(address), "label": branch_sites[address],
            "rax": hex(ld.uc.reg_read(UC_X86_REG_RAX)), "rbx": ld.uc.reg_read(UC_X86_REG_RBX),
            "r12w_depth": ld.uc.reg_read(UC_X86_REG_R12) & 0xFFFF,
            "rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)), "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(ld.uc.reg_read(UC_X86_REG_R8)), "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
            "rdi": hex(ld.uc.reg_read(UC_X86_REG_RDI)), "rsi": hex(ld.uc.reg_read(UC_X86_REG_RSI)),
            "r14": hex(ld.uc.reg_read(UC_X86_REG_R14)),
            "stack_20": hex(u64(ld, rsp + 0x20)), "stack_28": hex(u64(ld, rsp + 0x28)),
            "stack_30": hex(u64(ld, rsp + 0x30)), "stack_38": hex(u64(ld, rsp + 0x38)),
        })
        if address == 0x180004B50:
            params = ld.uc.reg_read(UC_X86_REG_RBX)
            observed["early_branches"][-1]["param_block_values"] = {
                "plus_0x24": f32(ld, params + 0x24), "plus_0x28": f32(ld, params + 0x28),
                "plus_0x30": f32(ld, params + 0x30), "plus_0x34": f32(ld, params + 0x34),
                "plus_0x40": u32(ld, params + 0x40), "plus_0x48": u32(ld, params + 0x48),
                "plus_0x4c": u32(ld, params + 0x4C), "plus_0x50": u32(ld, params + 0x50),
                "plus_0x54": u32(ld, params + 0x54),
            }
    for site in branch_sites:
        loader.add_code_hook(site, capture_branch)

    def capture_worker_loop(ld: AexLoader, _address: int, _size: int) -> None:
        if observed["worker_loop"]:
            return
        params = ld.uc.reg_read(UC_X86_REG_RBX)
        observed["worker_loop"].append({
            "rip": "0x180004d84", "params": hex(params),
            "plus_0x8078": hex(u64(ld, params + 0x8078)),
            "plus_0x8090": hex(u64(ld, params + 0x8090)),
            "plus_0x80a0": u32(ld, params + 0x80A0),
            "plus_0x80a4": u32(ld, params + 0x80A4),
        })

    loader.add_code_hook(0x180004D84, capture_worker_loop)

    last_wrapper_call: dict = {}

    def iterate8_wrapper_call(ld: AexLoader, address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        last_wrapper_call.clear()
        last_wrapper_call.update({
            "rip": hex(address), "r10_suite": hex(u64(ld, rsp + 0x2F8)),
            "rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)), "rdx": ld.uc.reg_read(UC_X86_REG_RDX),
            "r8": ld.uc.reg_read(UC_X86_REG_R8), "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
            "stack20": hex(u64(ld, rsp + 0x20)), "stack28": hex(u64(ld, rsp + 0x28)),
            "stack30": hex(u64(ld, rsp + 0x30)), "stack38": hex(u64(ld, rsp + 0x38)),
        })

    loader.add_code_hook(0x1800067C5, iterate8_wrapper_call)

    def trace_iterate_wrapper(uc, address, _size, _user_data):
        # Range tracing is deliberate: the exact-address helper is not a reliable
        # witness when the loader's fast hook path is enabled.
        if len(observed["wrapper_trace"]) >= 96:
            return
        rsp = uc.reg_read(UC_X86_REG_RSP)
        observed["wrapper_trace"].append({
            "rip": hex(address),
            "rcx": hex(uc.reg_read(UC_X86_REG_RCX)),
            "rdx": hex(uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(uc.reg_read(UC_X86_REG_R8)),
            "r9": hex(uc.reg_read(UC_X86_REG_R9)),
            "r10": hex(uc.reg_read(UC_X86_REG_R10)),
            "rsp": hex(rsp),
            "slots": {hex(offset): hex(u64(loader, rsp + offset)) for offset in (0x20, 0x28, 0x30, 0x38, 0x40, 0x2f8, 0x510, 0x518, 0x520, 0x528)},
        })

    loader.uc.hook_add(UC_HOOK_CODE, trace_iterate_wrapper, begin=0x180006700, end=0x1800067D0)

    def iterate8(ld: AexLoader, args_: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        raw_stack = {hex(offset): hex(u64(ld, rsp + offset)) for offset in range(0x20, 0x61, 8)}
        # PF_Iterate8Suite1::iterate(in_data, start, end, src, rect, refcon,
        # fn, dst).  FUN_180006700 copies args 5..8 to its call area; at this
        # callback entry they are therefore +0x28, +0x30, +0x38, +0x40.
        rect = u64(ld, rsp + 0x28)
        params = u64(ld, rsp + 0x30)
        callback = u64(ld, rsp + 0x38)
        dst_world = u64(ld, rsp + 0x40)
        source_world = args_[3]
        require_ptr(ld, rect, "area", 0x20)
        require_ptr(ld, params, "refcon", 0x80A8)
        require_ptr(ld, source_world, "source world", 0x30)
        require_ptr(ld, dst_world, "destination world", 0x30)
        area_words = list(struct.unpack("<4i", ld.read_bytes(rect, 16)))
        call = {"rip": "0x1800067c5", "stack_slots_at_callback": raw_stack}
        observed["iterate_calls"].append({"callback": hex(callback), "params": hex(params), "start": args_[1], "end": args_[2], "regs": [hex(value) for value in args_], "return_rip": hex(u64(ld, rsp)), "raw_stack": raw_stack, "source_world": hex(source_world), "rect": hex(rect), "area_words": area_words, "area_bounds": {"start": args_[1], "end": args_[2], "width": u32(ld, params + 0x80A0), "height": u32(ld, params + 0x80A4)}, "dst_world": hex(dst_world), "refcon": hex(params), "wrapper_call": call})
        if callback not in (POPULATE, OUTPUT, POPULATE16, OUTPUT16, POPULATE32, OUTPUT32) or params == 0:
            raise RuntimeError(f"PF_Iterate8 ABI unresolved: callback=0x{callback:x} refcon=0x{params:x}")
        # PF Iterate walks the requested host-world rectangle. The pixel callback
        # applies the padded work-buffer offset itself; iterating the padded
        # dimensions here would apply that offset twice.
        iterate_width = u32(ld, params + 0x80A0)
        iterate_height = u32(ld, params + 0x80A4)
        observed["iterate_calls"][-1].update({"param_stride": iterate_width, "param_height": iterate_height})
        left, top, right, bottom = area_words
        source_width = u32(ld, source_world + 0x24)
        source_height = u32(ld, source_world + 0x28)
        destination_width = u32(ld, dst_world + 0x24)
        destination_height = u32(ld, dst_world + 0x28)
        if not (0 <= left <= right <= source_width and 0 <= top <= bottom <= source_height):
            raise RuntimeError(
                f"PF_Iterate8 area {area_words} exceeds source world {source_width}x{source_height}"
            )
        if not (right <= destination_width and bottom <= destination_height):
            raise RuntimeError(
                f"PF_Iterate8 area {area_words} exceeds destination world "
                f"{destination_width}x{destination_height}"
            )
        source_data = u64(ld, source_world + 0x18)
        source_rowbytes = u32(ld, source_world + 0x20)
        destination_data = u64(ld, dst_world + 0x18)
        destination_rowbytes = u32(ld, dst_world + 0x20)
        callback_pixel_size = 16 if callback in (POPULATE32, OUTPUT32) else (8 if callback in (POPULATE16, OUTPUT16) else 4)
        if (source_rowbytes < source_width * callback_pixel_size or
                destination_rowbytes < destination_width * callback_pixel_size):
            raise RuntimeError(
                f"PF_Iterate8 rowbytes are too small: source={source_rowbytes}, "
                f"destination={destination_rowbytes}"
            )
        if source_height:
            require_ptr(
                ld, source_data + (source_height - 1) * source_rowbytes,
                "source world final row", source_width * callback_pixel_size,
            )
        if destination_height:
            require_ptr(
                ld, destination_data + (destination_height - 1) * destination_rowbytes,
                "destination world final row", destination_width * callback_pixel_size,
            )
        for y in range(top, bottom):
            for x in range(left, right):
                if source_world == input_world and source_rowbytes == width * callback_pixel_size:
                    pixel = source[(y * width + x) * callback_pixel_size:(y * width + x + 1) * callback_pixel_size]
                else:
                    pixel = ld.read_bytes(
                        source_data + y * source_rowbytes + x * callback_pixel_size,
                        callback_pixel_size,
                    )
                if callback == POPULATE:
                    model_populate(ld, params, y, x, pixel)
                elif callback == OUTPUT:
                    model_output(
                        ld, params, y, x, output_bytes,
                        destination_data + y * destination_rowbytes + x * 4,
                        width,
                    )
                elif callback == POPULATE16:
                    model_populate16(ld, params, y, x, pixel)
                elif callback == OUTPUT16:
                    destination = destination_data + y * destination_rowbytes + x * 8
                    if (x, y) in ((14, 13), (15, 13), (14, 14), (15, 14),
                                  (14, 15), (15, 15)):
                        rgba = pixel_float(ld, params, x, y)
                        observed.setdefault("pf16_writer_probes", []).append({
                            "xy": [x, y],
                            "source_words_argb": list(struct.unpack("<4H", pixel)),
                            "writer_rgba": rgba,
                            "writer_rgba_bits": [
                                f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08X}"
                                for value in rgba
                            ],
                        })
                    model_output16(ld, params, y, x, output_bytes, destination, width)
                elif callback == POPULATE32:
                    model_populate32(ld, params, y, x, pixel)
                elif callback == OUTPUT32:
                    destination = destination_data + y * destination_rowbytes + x * 16
                    model_output32(ld, params, y, x, output_bytes, destination, width)
        observed["iterate_calls"][-1]["callback_error"] = 0
        if callback in (POPULATE, POPULATE16, POPULATE32) and "first_iterate" not in observed["checkpoints"]:
            observed["checkpoints"]["first_iterate"] = {"callback": hex(callback), "area_words": area_words, "refcon": hex(params)}
        if callback in (OUTPUT, OUTPUT16, OUTPUT32):
            observed["checkpoints"]["final_host_output"] = {"callback": hex(callback), "area_words": area_words, "refcon": hex(params)}
        return 0

    loader.write_bytes(iterate_suite, struct.pack("<Q", loader.install_callback("PF_Iterate8", iterate8)))

    # Register hooks with constants imported lazily to keep this fixture compact.
    from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RBX
    def rotate_entry_real(ld: AexLoader, _address: int, _size: int) -> None:
        observed["rotate_entry"].append({"rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)), "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)), "r8": ld.uc.reg_read(UC_X86_REG_R8), "r9": ld.uc.reg_read(UC_X86_REG_R9)})

    def rotate_after(ld: AexLoader, _address: int, _size: int) -> None:
        params = ld.uc.reg_read(UC_X86_REG_RBX)
        base = u64(ld, params + 0x8090)
        stride = u32(ld, params + 0x80A0)
        row0 = u32(ld, params + 0x8098)
        col0 = u32(ld, params + 0x809C)
        observed.setdefault("post_rotateback", []).append({
            "params": hex(params), "destination": hex(base),
            "targets": {f"{x},{y}": list(struct.unpack("<4f", ld.read_bytes(base + (((row0 + y) * stride + col0 + x) * 16), 16))) for x, y in TARGETS},
        })
    loader.add_code_hook(ROTATE_CALL, rotate_entry_real)
    loader.add_code_hook(ROTATE_CALL + 5, rotate_after)
    loader.add_code_hook(ROTATE_RETURN, lambda _ld, _address, _size: observed.__setitem__("render_return", observed["render_return"] + 1))
    loader.add_code_hook(0x18000528A, lambda _ld, _address, _size: observed["checkpoints"].__setitem__("rotate", {"callsite": "0x18000528a"}))
    def capture_mode2_source_field(ld: AexLoader, _address: int, _size: int) -> None:
        params = ld.uc.reg_read(UC_X86_REG_RBX)
        if u32(ld, params + 0x20) != 2:
            return
        field_pointer = u64(ld, params + 0x80A8)
        field_width = u32(ld, params + 0x80A0)
        field_height = u32(ld, params + 0x80A4)
        field_bytes = ld.read_bytes(field_pointer, field_width * field_height * 4)
        field_words = struct.unpack(f"<{field_width * field_height}f", field_bytes)
        if args.field_source_raw is not None:
            args.field_source_raw.parent.mkdir(parents=True, exist_ok=True)
            args.field_source_raw.write_bytes(field_bytes)
        observed["noise_field_source_probe"] = {
            "pointer": hex(field_pointer),
            "dimensions": [field_width, field_height],
            "placement": {
                "row0": u32(ld, params + 0x8098),
                "col0": u32(ld, params + 0x809C),
            },
            "sha256": hashlib.sha256(field_bytes).hexdigest(),
            "minimum": min(field_words),
            "maximum": max(field_words),
        }
    loader.add_code_hook(0x1800052BE, capture_mode2_source_field)
    def capture_rowdriver_entry(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        source_slot = ld.uc.reg_read(UC_X86_REG_R8)
        destination_slot = ld.uc.reg_read(UC_X86_REG_R9)
        row_width = u32(ld, rsp + 0x28)
        params = u64(ld, rsp + 0x38)
        mode = u32(ld, params + 0x20)
        observed["rowdriver_calls"].append({
            "row_start": ld.uc.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF,
            "row_end": ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF,
            "source_slot": hex(source_slot),
            "destination_slot": hex(destination_slot),
            "source": hex(u64(ld, source_slot)),
            "destination": hex(u64(ld, destination_slot)),
            "width": row_width,
            "unused_stack_30": hex(u64(ld, rsp + 0x30)),
            "params": hex(params),
            "mode_plus_0x20": mode,
            "mode_branch": "field" if mode == 2 else ("interpolated" if mode == 3 else "default"),
            "opacity_plus_0x2c": f32(ld, params + 0x2C),
            "exponent_plus_0x30": f32(ld, params + 0x30),
            "divisor_plus_0x38": f32(ld, params + 0x38),
            "front_edge_plus_0x40": f32(ld, params + 0x40),
            "back_edge_plus_0x44": f32(ld, params + 0x44),
            "counts": {
                "scatter_front": u32(ld, params + 0x48),
                "prepass_front": u32(ld, params + 0x4C),
                "scatter_back": u32(ld, params + 0x50),
                "prepass_back": u32(ld, params + 0x54),
            },
        })
        if mode == 3 and "noise_plane_probe" not in observed:
            noise_context = params + 0x80C0
            noise_pointer = u64(ld, noise_context + 0x08)
            noise_width = u32(ld, noise_context + 0x10)
            noise_height = u32(ld, noise_context + 0x14)
            noise_bytes = ld.read_bytes(noise_pointer, noise_width * noise_height * 4)
            noise_words = struct.unpack(
                f"<{noise_width * noise_height}f", noise_bytes
            )
            observed["noise_plane_probe"] = {
                "context": hex(noise_context),
                "pointer": hex(noise_pointer),
                "dimensions": [noise_width, noise_height],
                "source_dimensions": [
                    u32(ld, noise_context + 0x18),
                    u32(ld, noise_context + 0x1C),
                ],
                "table_size": u32(ld, noise_context + 0x20),
                "cell_size": f32(ld, noise_context + 0x40),
                "sha256": hashlib.sha256(noise_bytes).hexdigest(),
                "first_words": [
                    f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08X}"
                    for value in noise_words[:16]
                ],
            }
        if mode == 2 and "noise_field_probe" not in observed:
            field_pointer = u64(ld, params + 0x80B0)
            field_bytes = ld.read_bytes(field_pointer, row_width * row_width * 4)
            field_words = struct.unpack(f"<{row_width * row_width}f", field_bytes)
            if args.field_rotated_raw is not None:
                args.field_rotated_raw.parent.mkdir(parents=True, exist_ok=True)
                args.field_rotated_raw.write_bytes(field_bytes)
            observed["noise_field_probe"] = {
                "pointer": hex(field_pointer),
                "dimensions": [row_width, row_width],
                "sha256": hashlib.sha256(field_bytes).hexdigest(),
                "minimum": min(field_words),
                "maximum": max(field_words),
                "first_words": [
                    f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08X}"
                    for value in field_words[:16]
                ],
            }
        if "component_map_probe" not in observed:
            component_map = u64(ld, params + 0x8118)
            sample_points = ((0, 0), (row_width // 2, row_width // 2),
                             (row_width // 2, 73), (row_width // 2, row_width - 72))
            observed["component_map_probe"] = {
                "pointer": hex(component_map),
                "samples": {
                    f"{x},{y}": list(struct.unpack(
                        "<4f", ld.read_bytes(component_map + (y * row_width + x) * 16, 16)))
                    for x, y in sample_points
                },
            }
        observed["checkpoints"].setdefault("rowdriver", {"entry": "0x1800038d0"})

    loader.add_code_hook(ROWDRIVER, capture_rowdriver_entry)

    def capture_param_context(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        context = u64(ld, rsp + 0x20)
        require_ptr(ld, context, "directional blur parameter context", 0x8114)
        observed["param_context"] = {
            "address": hex(context),
            "internal_mode": u32(ld, context + 0x20),
            "angle_radians": f32(ld, context + 0x24),
            "brightness_gain": f32(ld, context + 0x28),
            "noise_variation": f32(ld, context + 0x2C),
            "size_variation_exponent": f32(ld, context + 0x30),
            "noise_type": u32(ld, context + 0x3C),
            "front_sharp_tail": f32(ld, context + 0x40),
            "back_sharp_tail": f32(ld, context + 0x44),
            "front_strength": u32(ld, context + 0x48),
            "front_alpha_fade": u32(ld, context + 0x4C),
            "back_strength": u32(ld, context + 0x50),
            "back_alpha_fade": u32(ld, context + 0x54),
            "noise_type_is_one": bool(ld.read_bytes(context + 0x80BC, 1)[0]),
            "seed": u32(ld, context + 0x8108),
            "noise_offset": f32(ld, context + 0x810C),
            "thickness": f32(ld, context + 0x8110),
        }

    # FUN_180006c50 has just materialized the active bit-depth worker context.
    for return_address in (0x180007CDA, 0x180007D85, 0x180007E30):
        loader.add_code_hook(return_address, capture_param_context)
    loader.add_code_hook(0x180005628, lambda _ld, _address, _size: observed["checkpoints"].__setitem__("rotateback", {"callsite": "0x180005628"}))
    loader.add_code_hook(0x180005675, lambda _ld, _address, _size: observed["checkpoints"].setdefault("normalization", {"after_rotateback": True}))

    source_name = str(args.source.resolve().relative_to(ROOT)) if args.source.resolve().is_relative_to(ROOT) else str(args.source.resolve())
    rotate_source = ROOT / "core/dblur_rotate.cpp"
    rotate_manifest = ROOT / "replay/fixtures/dblur_rotate/manifest.json"
    rowdriver_source = ROOT / "core/dblur_rowdriver.cpp"
    rowdriver_manifest = ROOT / "replay/fixtures/dblur_rowdriver_full/manifest.json"
    result = {"kind": "dblur_fullrender_host_fixture", "schema": 1, "status": "blocked", "exact_case": {"path": source_name, "dimensions": [width, height], "comp_dimensions": [width * args.downsample_den // args.downsample_num, height * args.downsample_den // args.downsample_num], "downsample": [args.downsample_num, args.downsample_den], "png_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(), "decoded_rgba_sha256": hashlib.sha256(source_rgba).hexdigest(), "host_argb_sha256": hashlib.sha256(source).hexdigest(), "host_pixel_layout": f"PF_Pixel{args.bitdepth} A/R/G/B little-endian words" if args.bitdepth == 16 else "PF_Pixel8 A/R/G/B"}, "callback_model_check": None, "execution": observed, "setup_addresses": {"in_data": hex(in_data), "output_world": hex(output_world), "input_world": hex(input_world), "noise_layer_world": hex(noise_layer_world), "depth_descriptor": hex(depth_descriptor), "render_desc": hex(render_desc), "param_6": hex(param_6)}, "world_layout": {"input_dimensions": [width, height], "noise_layer_dimensions": [noise_layer_width, noise_layer_height], "input_extent_hint": list(area), "output_extent_hint": list(area), "noise_layer_extent_hint": list(noise_layer_area), "input_rowbytes": rowbytes, "noise_layer_rowbytes": noise_layer_rowbytes, "depth_descriptor_offset": "0x2c", "depth_bits": args.bitdepth, "downsample_num": args.downsample_num, "downsample_den": args.downsample_den}, "param_def_case_values": {"1": {"type": "short@+0x3a", "value": 0}, "2": {"type": "double@+0x38", "value": 1.0}, "3": {"type": "short@+0x3a", "value": 92}, "5": {"type": "int32@+0x38", "value": 1690}, "6": {"type": "int32@+0x38", "value": 0}, "7": {"type": "short@+0x3a", "value": 45}, "10": {"type": "int32@+0x38", "value": 0}, "11": {"type": "int32@+0x38", "value": 0}, "12": {"type": "short@+0x3a", "value": 0}}, "binary_callback_provenance": {"file": "plugins_2025/OLMDirectionalBlur.aex", "input_load": "PF_Pixel16 A/R/G/B words" if args.bitdepth == 16 else "PF_Pixel8 A/R/G/B bytes decoded from PNG RGBA", "output_store": "u16 A/R/G/B at 0x180006a90" if args.bitdepth == 16 else "movb A/R/G/B at 0x180006bc5/0x180006bb0/0x180006bbe/0x180006bb3", "checked_in_disasm_note": "typed callback selected by the actual depth dispatch"}, "rotate_detour": {"enabled": args.detour_rotate, "primitive": "FUN_180001ec0", "candidate": "core/dblur_rotate.cpp", "candidate_sha256": hashlib.sha256(rotate_source.read_bytes()).hexdigest(), "fixture_manifest": "replay/fixtures/dblur_rotate/manifest.json", "fixture_manifest_sha256": hashlib.sha256(rotate_manifest.read_bytes()).hexdigest(), "fixture_gate": "6/6 byte-exact against actual AEX", "compile_flags": ["-O0", "-fno-fast-math", "-ffp-contract=off"]} if args.detour_rotate else {"enabled": False}, "rowdriver_detour": {"enabled": args.detour_rowdriver, "primitive": "FUN_1800038d0", "candidate": "core/dblur_rowdriver.cpp", "candidate_sha256": hashlib.sha256(rowdriver_source.read_bytes()).hexdigest(), "fixture_manifest": "replay/fixtures/dblur_rowdriver_full/manifest.json", "fixture_manifest_sha256": hashlib.sha256(rowdriver_manifest.read_bytes()).hexdigest(), "fixture_gate": "3/3 full rowdriver plus 5/5 leaf cases byte-exact against actual AEX at O2", "covered_modes": [0, 1], "rejected_modes": [2, 3], "compile_flags": ["-O2", "-fno-fast-math", "-ffp-contract=off"]} if args.detour_rowdriver else {"enabled": False}}
    if args.detour_rowdriver:
        result["rowdriver_detour"].update(
            {
                "fixture_gate": (
                    "default/mode-1 fixture suite plus focused nonzero mode-2 field "
                    "and mode-3 Smooth/Block full-frame gates, byte-exact against actual AEX"
                ),
                "covered_modes": [0, 1, 2, 3],
                "mode_boundaries": {
                    "2": "rowdriver only; host Layer checkout and field construction remain unresolved",
                    "3": "generated Smooth and Block planes plus rowdriver",
                },
                "rejected_modes": [],
            }
        )
    result["param_def_case_values"] = {
        "1": {"type": "short@+0x3a", "value": args.angle},
        "2": {"type": "double@+0x38", "value": args.brightness_gain},
        "3": {"type": "short@+0x3a", "value": args.size_variation},
        "5": {"type": "int32@+0x38", "value": args.front_strength},
        "6": {"type": "int32@+0x38", "value": args.front_alpha_fade},
        "7": {"type": "short@+0x3a", "value": args.front_sharp_tail},
        "10": {"type": "int32@+0x38", "value": args.back_strength},
        "11": {"type": "int32@+0x38", "value": args.back_alpha_fade},
        "12": {"type": "short@+0x3a", "value": args.back_sharp_tail},
        "15": {"type": "short@+0x3a", "value": args.noise_variation},
        "16": {"type": "int32@+0x38", "value": args.noise_type},
        "18": {"type": "int32@+0x38", "value": args.seed},
        "19": {"type": "short@+0x3a", "value": args.noise_offset},
        "20": {"type": "double@+0x38", "value": args.thickness},
    }
    if args.bitdepth == 8:
        try:
            result["callback_model_check"] = callback_model_check(loader, source, width)
        except Exception as exc:
            result["callback_model_check"] = {"status": "error", "reason": type(exc).__name__, "message": str(exc)}
    elif args.bitdepth == 16:
        try:
            result["callback_model_check"] = callback_model_check16(loader)
        except Exception as exc:
            result["callback_model_check"] = {"status": "error", "reason": type(exc).__name__, "message": str(exc)}
    else:
        try:
            result["callback_model_check"] = callback_model_check32(loader)
        except Exception as exc:
            result["callback_model_check"] = {"status": "error", "reason": type(exc).__name__, "message": str(exc)}
    try:
        # The existing render-entry ABI is three integer arguments; host callbacks are real AEX entrypoints.
        # PF_Cmd_RENDER=0x18 was traced above. The direct worker comparison is
        # four-argument and supplies the grounded R9 world descriptor required
        # by FUN_180004a20's reads at R9+0x24/+0x28.
        call_result = loader.call_function(ENTRY, int_args=[in_data, output_world, param_6, render_desc], max_instructions=args.max_instructions)
        observed["budget"] = {"instruction_limit": args.max_instructions, "instructions": call_result["instructions"], "exhausted": call_result["instructions"] >= args.max_instructions}
        if observed["budget"]["exhausted"]:
            raise RuntimeError(f"AEX instruction budget exhausted before render return; last_rip={observed['last_rips'][-1] if observed['last_rips'] else 'none'}")
        if observed["iterate_calls"] and "final_host_output" in observed["checkpoints"]:
            result["status"] = "ok"
        else:
            result["blocked"] = {"reason": "pre-render-return", "message": "FUN_180007bd0 returned without a complete populate/output callback pair", "last_rips": observed["last_rips"], "required": "the exact typed iterate callback ABI and render branch state; no callback values were fabricated"}
    except Exception as exc:
        if observed["budget"].get("exhausted"):
            if "rowdriver" in observed["checkpoints"] and "rotateback" not in observed["checkpoints"]:
                reason = "rowdriver-instruction-budget"
            elif "first_iterate" in observed["checkpoints"] and not observed["rotate_detours"]:
                reason = "rotate-instruction-budget"
            else:
                reason = "instruction-budget"
        else:
            reason = "iterate8-suite-abi" if any(item[0] == "PF_Iterate8" for item in loader.callback_log) else type(exc).__name__
        result["blocked"] = {"reason": reason, "message": str(exc), "last_rip": observed["last_rips"][-1] if observed["last_rips"] else None, "completed_checkpoints": sorted(observed["checkpoints"]), "required": "continue from the real PF Iterate8 populate return through AEX rotate, rowdriver, normalization, rotateback 0x180005628, and output callback; do not synthesize missing stages"}
    complete = len(output_bytes) == width * height * pixel_size and bool(
        observed["iterate_calls"] and "final_host_output" in observed["checkpoints"]
    )
    result["output"] = {"format": f"ARGB{args.bitdepth * 4}", "dimensions": [width, height], "complete": complete, "sha256": hashlib.sha256(output_bytes).hexdigest() if complete else None, "byte_count": len(output_bytes) if complete else 0}
    if complete and args.host_output_raw is not None:
        args.host_output_raw.parent.mkdir(parents=True, exist_ok=True)
        args.host_output_raw.write_bytes(output_bytes)
        result["output"]["raw_path"] = str(args.host_output_raw)
    if complete and args.host_output_png is not None and args.bitdepth == 8:
        rgba_bytes = bytearray(len(output_bytes))
        for offset in range(0, len(output_bytes), 4):
            alpha, red, green, blue = output_bytes[offset:offset + 4]
            rgba_bytes[offset:offset + 4] = bytes((red, green, blue, alpha))
        args.host_output_png.parent.mkdir(parents=True, exist_ok=True)
        Image.frombytes("RGBA", (width, height), bytes(rgba_bytes)).save(args.host_output_png)
        result["output"]["png_path"] = str(args.host_output_png)
    if complete and args.expected is not None and args.bitdepth == 8:
        expected_width, expected_height, expected_rgba, expected_argb = load_argb(args.expected)
        if (expected_width, expected_height) != (width, height):
            raise RuntimeError(
                f"expected image dimensions {expected_width}x{expected_height} do not match {width}x{height}"
            )
        raw_comparison = byte_diff_summary(output_bytes, expected_argb)
        premultiply_models = {
            rounding: byte_diff_summary(
                premultiply_argb8(output_bytes, rounding), expected_argb
            )
            for rounding in ("floor", "nearest")
        }
        matching_models = [
            rounding for rounding, comparison in premultiply_models.items()
            if comparison["exact"]
        ]
        result["reference_comparison"] = {
            "path": str(args.expected),
            "png_sha256": hashlib.sha256(args.expected.read_bytes()).hexdigest(),
            "decoded_rgba_sha256": hashlib.sha256(expected_rgba).hexdigest(),
            "host_argb_sha256": hashlib.sha256(expected_argb).hexdigest(),
            "reference_stage": "AE rendered PNG",
            "plugin_callback_raw": raw_comparison,
            "ae_output_premultiply_models": {
                "formula": "A unchanged; RGB=(RGB*A+bias)//255",
                "bias": {"floor": 0, "nearest": 127},
                "results": premultiply_models,
                "matching_models": matching_models,
                "rounding_resolved": len(matching_models) == 1,
                "scope": "host/output-module model, not code to add inside the plug-in",
            },
            "modeled_ae_render_exact": bool(matching_models),
            "exact": False,
            "exact_reason": "AE exact remains reserved for an actual Mac AE render; this is a host-stage model",
        }
    for x, y in TARGETS:
        if x >= width or y >= height:
            final_bytes = "out-of-bounds"
        else:
            address = (y * width + x) * pixel_size
            final_bytes = output_bytes[address:address + pixel_size].hex() if complete else "not captured"
        result.setdefault("targets", {})[f"{x},{y}"] = {"final_host_bytes": final_bytes}
    result["execution"]["callback_log"] = [
        {"label": label, "args": [hex(value) for value in args_], "ret": ret}
        for label, args_, ret in loader.callback_log
    ]
    result["execution"]["import_log"] = [{"dll": item.dll, "name": item.name, "args": [hex(value) for value in item.args], "ret": item.ret} for item in loader.import_log]
    tracked_imports = {"powf", "sqrtf", "cosf", "sinf", "ceilf", "ceil", "omp_get_max_threads"}
    result["execution"]["import_counts"] = {name: sum(1 for item in loader.import_log if item.name == name) for name in sorted(tracked_imports | {item.name for item in loader.import_log})}
    result["execution"]["unimplemented_imports"] = sorted({item.name for item in loader.import_log if item.name not in loader.import_impls})
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if rotate_temp_dir is not None:
        rotate_temp_dir.cleanup()
    if rowdriver_temp_dir is not None:
        rowdriver_temp_dir.cleanup()
    output_name = str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output)
    print(json.dumps({"status": result["status"], "output": output_name, "iterate_calls": len(observed["iterate_calls"]), "rotate_calls": len(observed["rotate_entry"]), "complete_output": result["output"]["complete"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
