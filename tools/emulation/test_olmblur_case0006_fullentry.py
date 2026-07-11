"""Case-bound OLMBlur Legacy 16bpc full-entry probe.

This drives the existing Unicorn host model with the canonical case_0006
before-effects world and parameter values.  It is an emulation probe: only
the checked-in Windows PNG is conformance truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import (  # noqa: E402
    AEX_PATH,
    FUN_ENTRY,
    build_context,
    build_pf_suites,
    u64,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json"
BASE = REPO_ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch"
CASE_ID = "olmblur__case_0006"
WITNESSES = ((314, 14), (29, 71))
FULL_FRAME_WALL_CAP_S = 30


def png_rgba16(path: Path) -> tuple[int, int, bytes]:
    """Decode the checked-in non-interlaced RGBA16 PNG to RGBA words."""
    blob = path.read_bytes()
    assert blob[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = depth = color = interlace = None
    compressed = bytearray()
    while pos < len(blob):
        size = struct.unpack(">I", blob[pos:pos + 4])[0]
        kind = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + size]
        pos += size + 12
        if kind == b"IHDR":
            width, height, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", data)
            assert (depth, color, comp, filt, interlace) == (16, 6, 0, 0, 0)
        elif kind == b"IDAT":
            compressed.extend(data)
        elif kind == b"IEND":
            break
    assert width is not None and height is not None
    raw = zlib.decompress(compressed)
    stride = width * 8
    rows: list[bytes] = []
    previous = bytearray(stride)
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        encoded = bytearray(raw[cursor + 1:cursor + 1 + stride])
        cursor += stride + 1
        recon = bytearray(stride)
        for i, value in enumerate(encoded):
            left = recon[i - 8] if i >= 8 else 0
            up = previous[i]
            up_left = previous[i - 8] if i >= 8 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                estimate = left + up - up_left
                pa = abs(estimate - left)
                pb = abs(estimate - up)
                pc = abs(estimate - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
            else:
                raise ValueError(f"unsupported PNG filter {filter_type}")
            recon[i] = (value + predictor) & 0xFF
        rows.append(bytes(recon))
        previous = recon
    rgba = bytearray(width * height * 8)
    for y, row in enumerate(rows):
        for x in range(width):
            src = y * stride + x * 8
            dst = (y * width + x) * 8
            rgba[dst:dst + 8] = row[src:src + 8]
    return width, height, bytes(rgba)


def guest_argb_words(rgba: bytes) -> bytes:
    """AE world memory is A,R,G,B 16-bit words; PNG semantics are R,G,B,A."""
    out = bytearray(len(rgba))
    for off in range(0, len(rgba), 8):
        r, g, b, a = struct.unpack_from(">4H", rgba, off)
        struct.pack_into("<4H", out, off, a, r, g, b)
    return bytes(out)


def semantic_hash(rgba: bytes) -> str:
    words = bytearray()
    for off in range(0, len(rgba), 8):
        words.extend(struct.pack("<4H", *struct.unpack_from(">4H", rgba, off)))
    return hashlib.sha256(words).hexdigest()


def build_case_params(loader: AexLoader) -> int:
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    # reference_manifest.json: Blur Amount=5, Smoothness=100, Repeat=10,
    # Bias Direction=1, Legacy=0.  These are the fields consumed by the
    # full-entry disassembly at +0x20/+0x24/+0x28/+0x2c and +0x18.
    loader.write_bytes(params + 0x18, struct.pack("<I", 16))
    loader.write_bytes(params + 0x20, struct.pack("<f", 5.0))
    loader.write_bytes(params + 0x24, struct.pack("<f", 100.0))
    loader.write_bytes(params + 0x28, struct.pack("<I", 10))
    loader.write_bytes(params + 0x2C, struct.pack("<I", 1))
    return params


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    case = next(item for item in manifest["cases"] if item["id"] == CASE_ID)
    assert case["bits_per_channel"] == 16
    assert (case["comp"]["width"], case["comp"]["height"]) == (1920, 1080)
    input_path = BASE / case["before_effects_frame"]
    expected_path = BASE / case["frame"]
    input_w, input_h, input_rgba = png_rgba16(input_path)
    expected_w, expected_h, expected_rgba = png_rgba16(expected_path)
    assert (input_w, input_h) == (expected_w, expected_h) == (1920, 1080)
    input_guest = guest_argb_words(input_rgba)

    # Confirm the channel/word contract against the source's opaque corner.
    first_words = struct.unpack_from("<4H", input_guest)
    assert first_words[0] == 65535
    assert first_words[1:] == struct.unpack_from(">3H", input_rgba)

    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic, events = build_pf_suites(loader)
    ctx = build_context(loader, spbasic)
    rowbytes = input_w * 8
    source_data = loader.bump_alloc(len(input_guest), align=64)
    output_data = loader.bump_alloc(len(input_guest), align=64)
    loader.write_bytes(source_data, input_guest)
    loader.write_bytes(output_data, input_guest)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\x00" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", rowbytes))
        loader.write_bytes(address + 0x24, struct.pack("<I", input_w))
        loader.write_bytes(address + 0x28, struct.pack("<I", input_h))
        loader.write_bytes(address + 0x2C, struct.pack("<H", 16))
        return address

    source = world(source_data)
    output = world(output_data)
    params = build_case_params(loader)
    status = "return"
    error = None
    started = time.monotonic()
    try:
        result = loader.call_function(FUN_ENTRY, int_args=[ctx, source, output, params], max_instructions=120_000_000)
    except Exception as exc:  # retain the exact emulation blocker in the report
        result = {}
        status = "exception"
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.monotonic() - started

    output_guest = loader.read_bytes(output_data, len(input_guest))
    output_rgba = bytearray(len(output_guest))
    for off in range(0, len(output_guest), 8):
        a, r, g, b = struct.unpack_from("<4H", output_guest, off)
        struct.pack_into(">4H", output_rgba, off, r, g, b, a)
    output_rgba = bytes(output_rgba)
    observed = {}
    expected = {}
    for x, y in WITNESSES:
        off = (y * input_w + x) * 8
        observed[f"({x},{y})"] = struct.unpack_from(">4H", output_rgba, off)
        expected[f"({x},{y})"] = struct.unpack_from(">4H", expected_rgba, off)
    exact = output_rgba == expected_rgba
    print("FACT case", CASE_ID)
    print("FACT input", str(input_path))
    print("FACT expected", str(expected_path))
    print("FACT dimensions", [input_w, input_h])
    print("FACT channel_order", "PNG RGBA -> guest little-endian A,R,G,B")
    print("FACT first_guest_words_ARGB", list(first_words))
    print("FACT params", {"bit_depth": 16, "blur_amount": 5.0, "smoothness": 100.0, "repeat": 10, "bias_direction": 1, "legacy": 0})
    print("FACT status", status)
    print("FACT error", error)
    print("FACT result_rax", hex(result.get("rax", 0)) if result else None)
    print("FACT instructions", loader.instructions_executed)
    print("FACT elapsed_seconds", round(elapsed, 3))
    print("FACT callback_throughput_per_second", round(len(events) / elapsed, 3) if elapsed else None)
    print("FACT callbacks", events)
    print("FACT witness_observed_RGBA16", observed)
    print("FACT witness_windows_RGBA16", expected)
    print("FACT output_semantic_sha256", semantic_hash(output_rgba))
    print("FACT windows_semantic_sha256", semantic_hash(expected_rgba))
    print("FACT windows_png_sha256", hashlib.sha256(expected_path.read_bytes()).hexdigest())
    print("INFERENCE exact_full_frame", exact)
    print("INFERENCE local_aex_is_windows_truth", False)
    return 0


def run_with_hard_timeout() -> int:
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--worker"],
        start_new_session=True,
    )
    try:
        return process.wait(timeout=FULL_FRAME_WALL_CAP_S)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        print("FACT status hard-timeout")
        print(f"FACT elapsed_seconds {FULL_FRAME_WALL_CAP_S}")
        print("FACT completed_frames 0")
        print("INFERENCE full_frame_probe_practical False")
        return 124


if __name__ == "__main__":
    raise SystemExit(main() if "--worker" in sys.argv else run_with_hard_timeout())
