#!/usr/bin/env python3
"""Hostless actual-AEX gate for the Mode-4 highlight aggregation/compose tail.

The full FUN_18114f4a0 caller needs an AE-owned channel/vtable object and the
embedded OpenCV runtime.  This narrower fixture starts at its five-ray output:
only slot four (Highlight) is populated, then the pinned AEX executes the
Mode-1 aggregator and PF32 outer compose/writer without AE or Windows.
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
TARGET_AGGREGATE = 0x18114FD90
TARGET_COMPOSE_PF32 = 0x18114E460
EXPECTED_AEX_SHA256 = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"

sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402
from olmkirakira_outer_compose_oracle_20260728 import (  # noqa: E402
    compose_pixel,
    f32,
    stage_typed_writer,
)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def words(loader: AexLoader, address: int, count: int) -> list[int]:
    return list(struct.unpack(f"<{count}I", loader.read_bytes(address, count * 4)))


def portable_highlight_glow(amount: float) -> tuple[float, float, float, float]:
    """Replay production AddColoredUnion for one active orange layer."""
    amount = f32(amount)
    if amount <= f32(0.001):
        return (f32(0.0),) * 4
    alpha = min(f32(1.0), max(f32(0.0), f32(f32(amount * f32(1.0)) * f32(1.0))))
    red = f32(alpha * f32(1.0))
    green = f32(alpha * f32(0.25))
    blue = f32(alpha * f32(0.0625))
    union_alpha = f32(f32(0.0 + alpha) - f32(f32(0.0 * alpha)))
    inverse = f32(f32(1.0) / union_alpha)
    return (
        f32(red * inverse), f32(green * inverse),
        f32(blue * inverse), union_alpha,
    )


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256
    loader = AexLoader(str(AEX), verbose=False, fast=True)

    width, height = 4, 1
    highlight = [0.0, 0.002, 0.2, 0.75]
    ray_planes: list[int] = []
    for layer in range(5):
        plane = loader.host_alloc(width * 4)
        values = highlight if layer == 4 else [0.0] * width
        loader.write_bytes(plane, struct.pack("<4f", *values))
        ray_planes.append(plane)
    ray_array = loader.host_alloc(5 * 8)
    loader.write_bytes(ray_array, struct.pack("<5Q", *ray_planes))

    # Actual PF_PixelFloat storage order is A,R,G,B.  Only Highlight is orange.
    colors: list[float] = []
    for layer in range(5):
        colors.extend([1.0, 1.0, 0.25, 0.0625] if layer == 4 else [1.0] * 4)
    color_array = loader.host_alloc(5 * 16)
    loader.write_bytes(color_array, struct.pack("<20f", *colors))
    flags = loader.host_alloc(5)
    loader.write_bytes(flags, b"\0" * 5)
    ramp_base = loader.host_alloc(5 * 0x144)
    loader.write_bytes(ramp_base, b"\0" * (5 * 0x144))
    glow = loader.host_alloc(width * 16)
    loader.write_bytes(glow, b"\xa5" * (width * 16))

    # call_function currently accepts stack float arguments as their raw word.
    one_f32_word = f32_bits(1.0)
    aggregation = loader.call_function(
        TARGET_AGGREGATE,
        int_args=[
            0, ray_array, color_array, flags,
            ramp_base, 0, glow, width, height, one_f32_word,
        ],
        max_instructions=200_000,
    )
    expected_glow = [
        0x00000000, 0x00000000, 0x00000000, 0x00000000,
        0x3F800000, 0x3E800000, 0x3D800000, 0x3B03126F,
        0x3F800000, 0x3E800000, 0x3D800000, 0x3E4CCCCD,
        0x3F800000, 0x3E800000, 0x3D800000, 0x3F400000,
    ]
    actual_glow = words(loader, glow, width * 4)
    assert actual_glow == expected_glow, [f"0x{value:08X}" for value in actual_glow]
    portable_glow = [value for amount in highlight for value in portable_highlight_glow(amount)]
    assert b"".join(struct.pack("<f", value) for value in portable_glow) == loader.read_bytes(glow, width * 16)

    # R,G,B,A source pixels.  The PF32 writer stores A,R,G,B words.
    source_rgba = [
        0.1, 0.2, 0.3, 1.0,
        0.2, 0.3, 0.4, 1.0,
        0.3, 0.4, 0.5, 1.0,
        0.4, 0.5, 0.6, 1.0,
    ]
    source = loader.host_alloc(width * 16)
    loader.write_bytes(source, struct.pack("<16f", *source_rgba))
    output = loader.host_alloc(width * 16)
    loader.write_bytes(output, b"\xcc" * (width * 16))

    owner = loader.host_alloc(0x200)
    loader.write_bytes(owner, b"\0" * 0x200)
    loader.write_bytes(owner + 0x38, struct.pack("<f", 1.0))  # glow opacity
    loader.write_bytes(owner + 0x3C, struct.pack("<f", 1.0))  # source opacity
    loader.write_bytes(owner + 0x44, struct.pack("<i", 1))    # Merge mode 1
    loader.write_bytes(owner + 0x58, struct.pack("<i", width))
    loader.write_bytes(owner + 0x128, struct.pack("<Q", source))
    loader.write_bytes(owner + 0x190, struct.pack("<Q", glow))

    world = loader.host_alloc(0x40)
    loader.write_bytes(world, b"\0" * 0x40)
    loader.write_bytes(world + 0x18, struct.pack("<Q", output))
    loader.write_bytes(world + 0x20, struct.pack("<i", width * 16))
    loader.write_bytes(world + 0x24, struct.pack("<i", width))
    loader.write_bytes(world + 0x28, struct.pack("<i", height))
    compose = loader.call_function(
        TARGET_COMPOSE_PF32,
        int_args=[owner, world],
        max_instructions=200_000,
    )
    expected_argb = [
        0x3F800000, 0x3DCCCCCD, 0x3E4CCCCD, 0x3E99999A,
        0x3F800000, 0x3E4E6F66, 0x3E998C85, 0x3ECC7481,
        0x3F800000, 0x3ED55555, 0x3EC00000, 0x3EDAAAAA,
        0x3F800000, 0x3F283A84, 0x3EC92493, 0x3EBD41D5,
    ]
    actual_argb = words(loader, output, width * 4)
    assert actual_argb == expected_argb, [f"0x{value:08X}" for value in actual_argb]
    portable_output = b"".join(
        stage_typed_writer(
            compose_pixel(
                portable_glow[index * 4:index * 4 + 4],
                source_rgba[index * 4:index * 4 + 4],
                glow_opacity=1.0,
                source_opacity=1.0,
                merge_mode=1,
            ),
            depth="PF32",
        )
        for index in range(width)
    )
    assert portable_output == loader.read_bytes(output, width * 16)
    assert aggregation["instructions"] > 0 and compose["instructions"] > 0
    print(
        "PASS_OLMKIRAKIRA_MODE4_HIGHLIGHT_HOSTLESS_ACTUAL_AEX "
        f"aggregate=0x{TARGET_AGGREGATE:x} compose=0x{TARGET_COMPOSE_PF32:x} "
        f"pixels={width * height}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
