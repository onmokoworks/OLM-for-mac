#!/usr/bin/env python3
"""Close OLMSmoother v1's native PF16 Color Key first-pass boundary."""

import ctypes
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
MASK16_ENTRY = 0x180002670
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_pf16_colorkey_production_harness_20260810.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_pf16_colorkey_actual_production_20260810.json"

WIDTH, HEIGHT, ROWBYTES = 3, 2, 32
KEY8 = (202, 187, 230)


def widen(value):
    return (value * 0x8000 + 0x80) // 0xFF


def render(fn, source, use_key, tolerance):
    src = (ctypes.c_uint16 * len(source))(*source)
    # A distinct pad seed proves neither pass writes outside active pixels.
    dst = (ctypes.c_uint16 * len(source))(*([0xA55A] * len(source)))
    error = fn(src, dst, WIDTH, HEIGHT, ROWBYTES, use_key, *KEY8, tolerance)
    assert error == 0
    return list(dst)


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    key16 = tuple(map(widen, KEY8))
    stride_words = ROWBYTES // 2
    key_argb16 = (0x8000, *key16)
    pixels = [
        key_argb16,                     # exact: the native callback clears it
        (0x8000, key16[0] + 1, *key16[1:]), # near key: remains untouched
        (0x7FFF, *key16),               # alpha mismatch: remains untouched
        (0x8000, key16[0], key16[1] - 1, key16[2]),
        (0x8000, 0x0123, 0x4567, 0x789A),
        (0, 0, 0, 0),
    ]
    source = []
    for row in range(HEIGHT):
        for pixel in pixels[row * WIDTH:(row + 1) * WIDTH]:
            source.extend(pixel)
        source.extend((0xD000 + row * 4 + i for i in range(4)))
    assert len(source) == stride_words * HEIGHT

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    state = loader.host_alloc(0x40, align=16)
    inp = loader.host_alloc(8, align=8)
    out = loader.host_alloc(8, align=8)
    loader.write_bytes(state, b"\0" * 0x40)
    # LAB_180002670 reads A/R/G/B words at state offsets +2/+4/+6/+8.
    loader.write_bytes(state + 2, struct.pack("<4H", *key_argb16))

    masked = source[:]
    vectors = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            base = y * stride_words + x * 4
            before = tuple(source[base:base + 4])
            preseed = (0x1111, 0x2222, 0x3333, 0x4444)
            loader.write_bytes(inp, struct.pack("<4H", *before))
            loader.write_bytes(out, struct.pack("<4H", *preseed))
            loader.call_function(MASK16_ENTRY, [state, 0, 0, inp, out],
                                 max_instructions=1000)
            actual = struct.unpack("<4H", loader.read_bytes(out, 8))
            # The temporary Windows world is pre-copied, so a non-match keeps
            # the input even though the isolated callback leaves its out seed.
            masked[base:base + 4] = actual if before == key_argb16 else before
            vectors.append({"xy": [x, y], "input": before, "callback": actual})

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-pf16-key-") as td:
        dylib = Path(td) / "lib.dylib"
        subprocess.run([
            "clang++", "-std=c++17", "-O2", "-shared", "-fPIC",
            "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS),
            "-o", str(dylib),
        ], cwd=ROOT, check=True, capture_output=True, text=True)
        lib = ctypes.CDLL(str(dylib))
        fn = lib.olmsmoother_v1_render16_colorkey
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint16),
                       ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
                       ctypes.c_int32, ctypes.c_uint8, ctypes.c_uint8,
                       ctypes.c_uint8, ctypes.c_int32]
        fn.restype = ctypes.c_int

        cases = []
        for tolerance in (0, 6, 127, 255):
            key_off = render(fn, source, 0, tolerance)
            key_on = render(fn, source, 1, tolerance)
            # Oracle composition: pinned AEX PF16 mask callback, followed by
            # the already independently covered native PF16 main pass.
            expected_on = render(fn, masked, 0, tolerance)
            exact = key_on == expected_on
            padding_exact = all(
                key_on[y * stride_words + WIDTH * 4:(y + 1) * stride_words]
                == [0xA55A] * 4 for y in range(HEIGHT)
            )
            assert exact and padding_exact
            cases.append({
                "tolerance": tolerance,
                "key_off_sha256": hashlib.sha256(struct.pack("<%dH" % len(key_off), *key_off)).hexdigest(),
                "key_on_sha256": hashlib.sha256(struct.pack("<%dH" % len(key_on), *key_on)).hexdigest(),
                "aex_mask_then_native_main_raw_uint16_exact": exact,
                "padding_preserved": padding_exact,
            })

    report = {
        "schema_version": 1,
        "status": "exact",
        "actual_aex_sha256": AEX_SHA256,
        "scope": "OLMSmoother v1 native PF16 Color Key pass; padded 3x2 raw uint16",
        "geometry": {"width": WIDTH, "height": HEIGHT, "rowbytes": ROWBYTES},
        "key_rgb8": KEY8,
        "key_argb16": key_argb16,
        "callback_vectors": vectors,
        "cases": cases,
        "claims_not_made": ["PF32 Color Key", "AE host iteration order", "other geometry"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
