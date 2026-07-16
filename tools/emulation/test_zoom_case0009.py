#!/usr/bin/env python3
"""AEX-side OLMRadialBlur Zoom case_0009 witness runner.

Runs the Windows AEX under Unicorn through the same render path used by
``test_m4_case0010.py``, but hooks the Zoom entry (FUN_1800056f0) and records
the caller-collapse planes:

  - param_1[0x842]: RGBA accumulation
  - param_1[0x843]: scalar denominator / alpha plane
  - param_1[7]: normalized final polar plane

The goal is not to tune PNGs. It is to locate whether the case_0009 (6,0)
alpha 254/255 split is already present in the denominator/final polar state or
appears later.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402
from test_m4_case0010 import (  # noqa: E402
    build_host_suites,
    build_param_block,
    build_render_context,
    build_world,
    install_reader_detours,
    read_param_ctx,
    read_world_pixel_argb,
    u32,
    u64,
    FUN_180007520,
    FUN_180008690,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"
DEFAULT_REF_DIR = REPO_ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
DEFAULT_MANIFEST = DEFAULT_REF_DIR / "reference_manifest.json"
DEFAULT_INPUT = DEFAULT_REF_DIR / "case_0009_before_effects.png"
DEFAULT_TRACE = REPO_ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmradialblur_residual_witness_20260624.json"
DEFAULT_JSON = REPO_ROOT / "refs" / "reports" / "olmradialblur_zoom_case0009_aex_witness.json"
DEFAULT_MD = REPO_ROOT / "refs" / "reports" / "olmradialblur_zoom_case0009_aex_witness.md"

FUN_1800056F0 = 0x1800056F0
FUN_18000A7E0 = 0x18000A7E0
FUN_18000A800 = 0x18000A800
FUN_18000A810 = 0x18000A810
FUN_18000A850 = 0x18000A850
FUN_18000B150 = 0x18000B150
FUN_18000A9D0 = 0x18000A9D0
FUN_1800072D3 = 0x1800072D3
FUN_1800072FD = 0x1800072FD
FUN_180007811 = 0x180007811
FUN_18000573B = 0x18000573B
FUN_180005849 = 0x180005849
FUN_1800058B0 = 0x1800058B0
FUN_180005A00 = 0x180005A00
FUN_180005BA2 = 0x180005BA2
FUN_180005BBB = 0x180005BBB
FUN_180005C1A = 0x180005C1A
FUN_180005C2B = 0x180005C2B
FUN_180005C7C = 0x180005C7C
FUN_180005C9F = 0x180005C9F
FUN_180005D99 = 0x180005D99
DIRECT_CORE_BRANCH_HOOKS = {
    FUN_18000573B: "thread-count-read",
    FUN_180005849: "input-world-read",
    FUN_1800058B0: "post-input-world",
    FUN_180005A00: "polar-prefill-start",
    FUN_180005BA2: "pre-prepass-region-a",
    FUN_180005BBB: "pre-prepass-region-b",
    FUN_180005C1A: "pre-scatter-branch-a",
    FUN_180005C2B: "pre-scatter-branch-b",
    FUN_180005C7C: "post-scatter-branch",
    FUN_180005C9F: "final-plane-branch",
    FUN_180005D99: "late-core-branch",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--input-png", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--x", type=int, default=6)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument(
        "--point",
        type=parse_point,
        action="append",
        default=[],
        metavar="X,Y",
        help="Repeatable post-core sample point. The expensive direct-core run is shared.",
    )
    parser.add_argument("--trace-comparison-json", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--max-instructions", type=int, default=50_000_000)
    parser.add_argument(
        "--trace-staging-loop",
        action="store_true",
        help="Sample the hot pre-Zoom staging loop around 0x180007811. Disabled by default because it is hit per pixel.",
    )
    parser.add_argument(
        "--direct-zoom-core",
        action="store_true",
        help="Bypass FUN_180007520 and directly run Zoom init/core/teardown after FUN_180008690 builds the param context.",
    )
    parser.add_argument(
        "--direct-debug-size",
        default="",
        metavar="WIDTHxHEIGHT",
        help="Direct-core debug only: replace param_2[1] geometry and float planes with a small crop such as 32x32.",
    )
    parser.add_argument(
        "--direct-debug-quality-step",
        type=float,
        default=90.0,
        help="Direct-core debug only: when --direct-debug-size is set, overwrite work+0x10 to reduce angular rows.",
    )
    parser.add_argument(
        "--direct-fast-forward-prefill",
        action="store_true",
        help="Direct-core harness only: skip the Zoom polar input prefill after allocation and jump to b150/a9d0 setup.",
    )
    parser.add_argument(
        "--direct-python-prefill",
        action="store_true",
        help=(
            "Direct-core harness only: skip the hot AEX polar prefill loop, but fill "
            "the polar planes with a Python implementation of the decompiled repeat-border sampler."
        ),
    )
    parser.add_argument(
        "--direct-stop-after-prefill",
        action="store_true",
        help=(
            "Direct-core harness only: stop at 0x180005ba2 after the original or "
            "Python polar prefill and report the pre-worker final/scalar planes."
        ),
    )
    parser.add_argument(
        "--direct-detour-prepass",
        action="store_true",
        help="Direct-core harness only: replace FUN_18000b150 with a no-op callback to test downstream reachability.",
    )
    parser.add_argument(
        "--direct-detour-scatter",
        action="store_true",
        help="Direct-core harness only: replace FUN_18000a9d0 with a no-op callback to test final-plane reachability.",
    )
    parser.add_argument(
        "--save-checkpoint-at-rip",
        nargs=2,
        metavar=("PATH", "RIP"),
        help="Save primary-render state before RIP executes, then stop (for example /tmp/case0009.aexcp 0x180005ba2).",
    )
    parser.add_argument(
        "--resume-checkpoint",
        type=Path,
        help="Resume the primary render from an AexLoader checkpoint created by this runner.",
    )
    return parser.parse_args()


def parse_point(value: str) -> tuple[int, int]:
    try:
        x_text, y_text = value.split(",", 1)
        return int(x_text.strip()), int(y_text.strip())
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(f"point must be X,Y, got {value!r}") from exc


def parse_debug_size(value: str) -> tuple[int, int] | None:
    if not value:
        return None
    try:
        left, right = value.lower().split("x", 1)
        width = int(left)
        height = int(right)
    except Exception as exc:
        raise SystemExit(f"--direct-debug-size must be WIDTHxHEIGHT, got {value!r}") from exc
    if width <= 0 or height <= 0:
        raise SystemExit("--direct-debug-size dimensions must be positive")
    return width, height


def load_case_params(manifest: Path, case_id: str) -> dict[str, Any]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for case in data.get("cases", []):
        if case.get("id") != case_id:
            continue
        params = case["effects"][0]["params"]
        return {
            "Blur Type": params[0]["value"],
            "Center": tuple(params[1]["value"]),
            "Outer Strength": params[3]["value"],
            "Outer Offset Mode": params[4]["value"],
            "Outer Offset": params[5]["value"],
            "Outer Edge Fade": params[6]["value"],
            "Inner Strength": params[9]["value"],
            "Inner Offset Mode": params[10]["value"],
            "Inner Offset": params[11]["value"],
            "Inner Edge Fade": params[12]["value"],
            "Repeat Border": params[14]["value"],
            "Ratio": params[16]["value"],
            "Angle": params[17]["value"],
            "Quality": params[19]["value"],
            "Brightness Gain": params[20]["value"],
            "Size Variation": params[21]["value"],
            "Noise Variation": params[23]["value"],
            "Noise Type": params[24]["value"],
            "Seed": params[26]["value"],
            "Noise Offset": params[27]["value"],
            "Thickness": params[28]["value"],
            "GPU Rendering": params[30]["value"],
        }
    raise RuntimeError(f"case not found: {case_id}")


def windows_case(trace_json: Path, case_id: str) -> dict[str, Any]:
    data = json.loads(trace_json.read_text(encoding="utf-8"))
    for case in data.get("windows", {}).get("cases", []):
        if case.get("case_id") == case_id:
            return case
    return {}


def read_f32(loader: AexLoader, addr: int) -> float:
    return struct.unpack("<f", loader.read_bytes(addr, 4))[0]


def read_rgba_cell(loader: AexLoader, plane: int, radial_count: int, angle_idx: int, radius_idx: int) -> tuple[float, float, float, float]:
    off = ((angle_idx * radial_count) + radius_idx) * 16
    return struct.unpack("<4f", loader.read_bytes(plane + off, 16))


def read_scalar_cell(loader: AexLoader, plane: int, radial_count: int, angle_idx: int, radius_idx: int) -> float:
    off = ((angle_idx * radial_count) + radius_idx) * 4
    return read_f32(loader, plane + off)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def read_scalar_f32_cell(loader: AexLoader, plane: int, width: int, height: int, x: int, y: int) -> float:
    x = max(0, min(width - 1, int(x)))
    y = max(0, min(height - 1, int(y)))
    return read_f32(loader, plane + (y * width + x) * 4)


def read_rgba_f32_cell(loader: AexLoader, plane: int, width: int, height: int, x: int, y: int) -> tuple[float, float, float, float]:
    x = max(0, min(width - 1, int(x)))
    y = max(0, min(height - 1, int(y)))
    return struct.unpack("<4f", loader.read_bytes(plane + (y * width + x) * 16, 16))


def sample_scalar_repeat(loader: AexLoader, plane: int, width: int, height: int, x: float, y: float) -> float:
    ix = int(x)
    iy = int(y)
    fx = f32(x - float(ix))
    fy = f32(y - float(iy))
    x0 = max(0, min(width - 1, ix))
    x1 = max(0, min(width - 1, ix + 1))
    y0 = max(0, min(height - 1, iy))
    y1 = max(0, min(height - 1, iy + 1))
    w00 = f32(f32(1.0 - fx) * f32(1.0 - fy))
    w10 = f32(f32(1.0 - fy) * fx)
    w01 = f32(f32(1.0 - fx) * fy)
    w11 = f32(fy * fx)
    return f32(
        f32(w00 * read_scalar_f32_cell(loader, plane, width, height, x0, y0))
        + f32(w10 * read_scalar_f32_cell(loader, plane, width, height, x1, y0))
        + f32(w01 * read_scalar_f32_cell(loader, plane, width, height, x0, y1))
        + f32(w11 * read_scalar_f32_cell(loader, plane, width, height, x1, y1))
    )


def sample_rgba_repeat(loader: AexLoader, plane: int, width: int, height: int, x: float, y: float) -> tuple[float, float, float, float]:
    ix = int(x)
    iy = int(y)
    fx = f32(x - float(ix))
    fy = f32(y - float(iy))
    x0 = max(0, min(width - 1, ix))
    x1 = max(0, min(width - 1, ix + 1))
    y0 = max(0, min(height - 1, iy))
    y1 = max(0, min(height - 1, iy + 1))
    w00 = f32(f32(1.0 - fx) * f32(1.0 - fy))
    w10 = f32(f32(1.0 - fy) * fx)
    w01 = f32(f32(1.0 - fx) * fy)
    w11 = f32(fy * fx)
    cells = (
        read_rgba_f32_cell(loader, plane, width, height, x0, y0),
        read_rgba_f32_cell(loader, plane, width, height, x1, y0),
        read_rgba_f32_cell(loader, plane, width, height, x0, y1),
        read_rgba_f32_cell(loader, plane, width, height, x1, y1),
    )
    weights = (w00, w10, w01, w11)
    return tuple(
        f32(sum(f32(weights[i] * cells[i][channel]) for i in range(4)))
        for channel in range(4)
    )


def python_prefill_zoom_polar_planes(
    loader: AexLoader,
    work: int,
    param: int,
    byte_plane: int,
    angle_count: int,
    radial_count: int,
    width: int,
    height: int,
) -> dict[str, Any]:
    """Fill FUN_1800056f0 polar input planes from the decompiled repeat-border path.

    This mirrors the pre-b150 part only: final polar RGBA (param_1[7]), scalar
    plane (param_1[8]), optional scalar plane (param_1[9]), and validity bytes.
    The downstream b150/a9d0 accumulation planes are initialized, not solved.
    """
    rgba_src = u64(loader, param + 0x98)
    scalar_90 = u64(loader, param + 0x90)
    scalar_88 = u64(loader, param + 0x88)
    final_plane = u64(loader, work + 7 * 8)
    scalar_8 = u64(loader, work + 8 * 8)
    scalar_9 = u64(loader, work + 9 * 8)
    accum = u64(loader, work + 0x842 * 8)
    denom = u64(loader, work + 0x843 * 8)
    plane_10 = u64(loader, work + 10 * 8)

    min_radius = struct.unpack("<i", loader.read_bytes(work + 0x18, 4))[0]
    ratio = read_f32(loader, work + 0x20)
    rot_cos = read_f32(loader, work + 0x28)
    rot_sin = read_f32(loader, work + 0x2C)
    angle_step = read_f32(loader, work + 0x14)
    center_x = read_f32(loader, work + 0x4208)
    center_y = read_f32(loader, work + 0x420C)
    sample_plane_9 = loader.read_bytes(param + 0x44, 1) != b"\x00"

    valid_count = 0
    first_cells: list[dict[str, Any]] = []
    final_payload = bytearray(angle_count * radial_count * 16)
    scalar8_payload = bytearray(angle_count * radial_count * 4)
    scalar9_payload = bytearray(angle_count * radial_count * 4)
    byte_payload = bytearray(angle_count * radial_count)

    for angle_idx in range(angle_count):
        angle = f32(float(angle_idx) * angle_step)
        # FUN_18001d060 returns a packed sin/cos pair.  The decomp usage is
        # equivalent to cos(angle) for the X radius term and sin(angle) for Y.
        cos_v = f32(math.cos(angle))
        sin_v = f32(math.sin(angle))
        for radius_idx in range(radial_count):
            radius = float(min_radius + radius_idx)
            radius_x = f32(radius * cos_v)
            radius_y = f32(f32(radius * sin_v) * ratio)
            src_x = f32(f32(rot_cos * radius_x) - f32(rot_sin * radius_y) + center_x)
            src_y = f32(f32(rot_sin * radius_x) + f32(rot_cos * radius_y) + center_y)
            flat = angle_idx * radial_count + radius_idx
            rgba = sample_rgba_repeat(loader, rgba_src, width, height, src_x, src_y)
            scalar8 = sample_scalar_repeat(loader, scalar_90, width, height, src_x, src_y)
            scalar9 = sample_scalar_repeat(loader, scalar_88, width, height, src_x, src_y) if sample_plane_9 else 1.0
            # Repeat-border path is valid for every destination cell after clamp.
            byte_payload[flat] = 1
            valid_count += 1
            struct.pack_into("<4f", final_payload, flat * 16, *rgba)
            struct.pack_into("<f", scalar8_payload, flat * 4, f32(scalar8))
            struct.pack_into("<f", scalar9_payload, flat * 4, f32(scalar9))
            if len(first_cells) < 8:
                first_cells.append(
                    {
                        "angle_idx": angle_idx,
                        "radius_idx": radius_idx,
                        "src_xy": [src_x, src_y],
                        "rgba": list(rgba),
                        "scalar8": f32(scalar8),
                        "scalar9": f32(scalar9),
                    }
                )

    loader.write_bytes(byte_plane, bytes(byte_payload))
    loader.write_bytes(final_plane, bytes(final_payload))
    loader.write_bytes(scalar_8, bytes(scalar8_payload))
    loader.write_bytes(scalar_9, bytes(scalar9_payload))
    loader.write_bytes(accum, b"\x00" * (angle_count * radial_count * 16))
    loader.write_bytes(denom, b"\x00" * (angle_count * radial_count * 4))
    loader.write_bytes(plane_10, b"\x00" * (angle_count * radial_count * 4))
    return {
        "angle_count": angle_count,
        "radial_count": radial_count,
        "cells": angle_count * radial_count,
        "valid_count": valid_count,
        "source_rgba_0x98": rgba_src,
        "source_scalar_0x90": scalar_90,
        "source_scalar_0x88": scalar_88,
        "sample_plane_9_from_source": bool(sample_plane_9),
        "first_cells": first_cells,
    }


def build_rgba_f32_plane(loader: AexLoader, image: Image.Image) -> int:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    raw = rgba.tobytes()
    out = bytearray(width * height * 16)
    for idx in range(width * height):
        r, g, b, a = raw[idx * 4 : idx * 4 + 4]
        struct.pack_into(
            "<4f",
            out,
            idx * 16,
            r / 255.0,
            g / 255.0,
            b / 255.0,
            a / 255.0,
        )
    ptr = loader.bump_alloc(len(out), align=64)
    loader.write_bytes(ptr, bytes(out))
    return ptr


def build_scalar_f32_plane(loader: AexLoader, width: int, height: int, value: float = 1.0) -> int:
    payload = struct.pack("<f", value) * (width * height)
    ptr = loader.bump_alloc(len(payload), align=64)
    loader.write_bytes(ptr, payload)
    return ptr


def prepare_direct_zoom_context(
    loader: AexLoader,
    param_ctx: int,
    render_ctx: int,
    input_world: int,
    output_world: int,
    image: Image.Image,
    debug_size: tuple[int, int] | None = None,
) -> dict[str, int]:
    """Populate the fields FUN_180007520 normally owns before calling Zoom core."""
    working_image = image
    geometry_ptr = input_world
    if debug_size is not None:
        width, height = debug_size
        working_image = image.crop((0, 0, min(width, image.width), min(height, image.height)))
        if working_image.size != (width, height):
            padded = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            padded.paste(working_image, (0, 0))
            working_image = padded
        geometry_ptr = loader.host_alloc(0x80)
        loader.write_bytes(geometry_ptr, b"\x00" * 0x80)
        loader.write_bytes(geometry_ptr + 0x24, struct.pack("<I", width))
        loader.write_bytes(geometry_ptr + 0x28, struct.pack("<I", height))
    else:
        width, height = image.size
    rgba_plane = build_rgba_f32_plane(loader, working_image)
    scalar_ones = build_scalar_f32_plane(loader, width, height, 1.0)
    scalar_zeros = build_scalar_f32_plane(loader, width, height, 0.0)
    output_plane = build_rgba_f32_plane(loader, Image.new("RGBA", (width, height), (0, 0, 0, 0)))
    loader.write_bytes(param_ctx + 0x00, struct.pack("<Q", render_ctx))
    loader.write_bytes(param_ctx + 0x08, struct.pack("<Q", geometry_ptr))
    loader.write_bytes(param_ctx + 0x10, struct.pack("<Q", output_world))
    loader.write_bytes(param_ctx + 0x48, struct.pack("<f", 1.0))
    loader.write_bytes(param_ctx + 0x88, struct.pack("<Q", scalar_ones))
    loader.write_bytes(param_ctx + 0x90, struct.pack("<Q", scalar_ones))
    loader.write_bytes(param_ctx + 0x98, struct.pack("<Q", rgba_plane))
    loader.write_bytes(param_ctx + 0xA0, struct.pack("<Q", output_plane))
    return {
        "rgba_plane_0x98": rgba_plane,
        "scalar_ones_0x88_0x90": scalar_ones,
        "scalar_zeros": scalar_zeros,
        "output_plane_0xa0": output_plane,
        "geometry_ptr_0x08": geometry_ptr,
        "geometry_width": width,
        "geometry_height": height,
    }


def call_zoom_inverse(loader: AexLoader, work_param1: int, x: float, y: float) -> tuple[float, float]:
    radius_out = loader.bump_alloc(4, align=16)
    angle_out = loader.bump_alloc(4, align=16)
    loader.write_bytes(radius_out, b"\x00" * 4)
    loader.write_bytes(angle_out, b"\x00" * 4)
    loader.call_function(
        FUN_18000A850,
        int_args=[work_param1, 0, 0, radius_out, angle_out],
        float_args={1: (x, "f"), 2: (y, "f")},
        max_instructions=20_000,
    )
    return read_f32(loader, radius_out), read_f32(loader, angle_out)


def sample_final_plane(
    loader: AexLoader,
    plane: int,
    radial_count: int,
    angle_count: int,
    radius_index: float,
    angle_index: float,
) -> dict[str, Any]:
    # Mirrors FUN_180009d80: rows are angle, columns are radius. Angle wraps at
    # the last row; radius uses the current integer cell and +1 neighbor.
    radius_index = f32(radius_index)
    angle_index = f32(angle_index)
    ai0 = int(angle_index)
    ai1 = ai0 + 1
    if ai0 == angle_count - 1:
        ai1 = 0
    ri0 = int(radius_index)
    ri1 = ri0 + 1
    # FUN_180009d80 uses scalar float32 SUBSS/MULSS/ADDSS throughout. Keep
    # every intermediate rounded to float32 and preserve its cell-add order.
    af = f32(angle_index - ai0)
    rf = f32(radius_index - ri0)
    one_minus_af = f32(1.0 - af)
    one_minus_rf = f32(1.0 - rf)
    w00 = f32(one_minus_rf * one_minus_af)
    w10 = f32(one_minus_af * rf)
    w01 = f32(one_minus_rf * af)
    w11 = f32(af * rf)
    cells = {
        "a0_r0": read_rgba_cell(loader, plane, radial_count, ai0, ri0),
        "a0_r1": read_rgba_cell(loader, plane, radial_count, ai0, ri1),
        "a1_r0": read_rgba_cell(loader, plane, radial_count, ai1, ri0),
        "a1_r1": read_rgba_cell(loader, plane, radial_count, ai1, ri1),
    }
    out = [f32(0.0), f32(0.0), f32(0.0), f32(0.0)]
    for key, weight in (("a0_r0", w00), ("a0_r1", w10), ("a1_r0", w01), ("a1_r1", w11)):
        cell = cells[key]
        alpha_weight = f32(weight * cell[3])
        out[3] = f32(out[3] + alpha_weight)
        out[0] = f32(out[0] + f32(alpha_weight * cell[0]))
        out[1] = f32(out[1] + f32(alpha_weight * cell[1]))
        out[2] = f32(out[2] + f32(alpha_weight * cell[2]))
    if out[3] != 0.0:
        reciprocal = f32(1.0 / out[3])
        out[0] = f32(out[0] * reciprocal)
        out[1] = f32(out[1] * reciprocal)
        out[2] = f32(out[2] * reciprocal)
    return {
        "angle_indices": [ai0, ai1],
        "radius_indices": [ri0, ri1],
        "weights": [w00, w10, w01, w11],
        "cells": {key: [float(v) for v in val] for key, val in cells.items()},
        "sample_float": [float(v) for v in out],
        "trunc_u8": [max(0, min(255, int(v * 255.0))) for v in out],
        "round_u8": [max(0, min(255, int(round(v * 255.0)))) for v in out],
    }


def sample_zoom_point(
    loader: AexLoader,
    final: int,
    accum: int,
    denom: int,
    radial_count: int,
    angle_count: int,
    min_radius: int,
    angle_step: float,
    work: int,
    output_world: int,
    x: int,
    y: int,
    debug_size: bool = False,
) -> dict[str, Any]:
    """Read one point from the already-computed Zoom planes and output world."""
    radius_raw, angle_raw = call_zoom_inverse(loader, work, float(x), float(y))
    angle_index = angle_raw / angle_step if angle_step else 0.0
    if debug_size and angle_count:
        angle_index %= float(angle_count)
    elif float(angle_count) <= angle_index:
        angle_index -= float(angle_count)
    radius_index = radius_raw - float(min_radius)
    final_sample = sample_final_plane(loader, final, radial_count, angle_count, radius_index, angle_index)
    cell_labels = {
        "a0_r0": (final_sample["angle_indices"][0], final_sample["radius_indices"][0]),
        "a0_r1": (final_sample["angle_indices"][0], final_sample["radius_indices"][1]),
        "a1_r0": (final_sample["angle_indices"][1], final_sample["radius_indices"][0]),
        "a1_r1": (final_sample["angle_indices"][1], final_sample["radius_indices"][1]),
    }
    witness_cells = {"accum_0x842": {}, "denom_0x843": {}, "final_7": {}}
    for label, (ai, ri) in cell_labels.items():
        witness_cells["accum_0x842"][label] = [float(v) for v in read_rgba_cell(loader, accum, radial_count, ai, ri)]
        witness_cells["denom_0x843"][label] = float(read_scalar_cell(loader, denom, radial_count, ai, ri))
        witness_cells["final_7"][label] = [float(v) for v in read_rgba_cell(loader, final, radial_count, ai, ri)]
    out_argb = read_world_pixel_argb(loader, output_world, x, y)
    out_rgba = [int(out_argb[1]), int(out_argb[2]), int(out_argb[3]), int(out_argb[0])]
    return {
        "xy": [x, y],
        "inverse_coords": {"radius_raw": radius_raw, "angle_raw": angle_raw},
        "indices": {
            "radius": radius_index,
            "angle": angle_index,
            "angle_cells": final_sample["angle_indices"],
            "radius_cells": final_sample["radius_indices"],
        },
        "weights": final_sample["weights"],
        "four_cells": final_sample["cells"],
        "final_float": final_sample["sample_float"],
        "final_u8": final_sample["trunc_u8"],
        "final_sample": final_sample,
        "witness_cells": witness_cells,
        "output_world_rgba": out_rgba,
    }


def classify(local: dict[str, Any], win: dict[str, Any]) -> str:
    win_f = win.get("aex_pre_writeback_rgba_float_or_hex")
    local_sample = local["final_sample"]["sample_float"]
    denom_values = local["witness_cells"]["denom_0x843"]
    final_values = [cell[3] for cell in local["witness_cells"]["final_7"].values()]
    if isinstance(win_f, list) and len(win_f) == 4:
        if abs(local_sample[3] - float(win_f[3])) < 1e-7:
            return "mac-aex-final-sample-alpha-matches-windows-trace"
    if any(abs(float(v) - 0.9999999403953552) < 1e-7 for v in denom_values.values()):
        return "alpha-split-present-in-denominator-plane"
    if any(abs(float(v) - 0.9999999403953552) < 1e-7 for v in final_values):
        return "alpha-split-present-in-final-polar-plane-cells"
    if local_sample[3] >= 1.0:
        return "local-aex-sample-alpha-is-1.0-split-not-reproduced-before-final-output"
    return "alpha-split-present-after-bilinear-final-plane-sample"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom case_0009 AEX Witness",
        "",
        f"- Case: `{report['case_id']}`",
        f"- XY: `{report['xy']}`",
        f"- AEX: `{report['aex']}`",
        f"- AEX SHA-256: `{report.get('provenance', {}).get('aex_sha256')}`",
        f"- Input SHA-256: `{report.get('provenance', {}).get('input_sha256')}`",
        f"- Manifest SHA-256: `{report.get('provenance', {}).get('manifest_sha256')}`",
        f"- Entry reached: `{report['entry_reached']}`",
        f"- Classification: `{report['classification']}`",
        "",
        "## Execution",
        "",
        f"- `elapsed_seconds`: `{report.get('elapsed_seconds')}`",
        f"- `render_instructions`: `{report.get('render_instructions')}`",
        f"- `render_fault`: `{report.get('render_fault')}`",
        f"- `max_instructions`: `{report.get('max_instructions')}`",
        f"- `zoom_setup_a7e0_calls`: `{report.get('zoom_setup_a7e0_calls')}`",
        f"- `zoom_setup_a810_calls`: `{report.get('zoom_setup_a810_calls')}`",
        f"- `zoom_branch_hits_0x1800072d3`: `{report.get('zoom_branch_hits')}`",
        f"- `zoom_callsite_hits_0x1800072fd`: `{report.get('zoom_callsite_hits')}`",
        f"- `prepass_calls`: `{report.get('prepass_calls')}`",
        f"- `scatter_calls`: `{report.get('scatter_calls')}`",
        f"- `staging_loop_hits_0x180007811`: `{report.get('staging_loop_hits')}`",
        f"- `render_stop_rip`: `{report.get('render_stop_rip')}`",
        "",
    ]
    if not report["entry_reached"]:
        lines.extend([
            "## Staging Loop Samples",
            "",
            "```json",
            json.dumps(report.get("staging_loop_samples", []), indent=2, sort_keys=True),
            "```",
            "",
            "## Reading",
            "",
            report["reading"],
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "## Geometry",
        "",
    ])
    for key, value in report["geometry"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Pointers",
        "",
    ])
    for key, value in report["pointers"].items():
        lines.append(f"- `{key}`: `0x{value:x}`")
    lines.extend([
        "",
        "## Final Sample",
        "",
        f"- Mac AEX final-plane sample float: `{report['final_sample']['sample_float']}`",
        f"- Mac AEX trunc u8: `{report['final_sample']['trunc_u8']}`",
        f"- Mac output-world RGBA: `{report['output_world_rgba']}`",
        f"- Windows trace float: `{report['windows_trace'].get('pre_writeback_rgba_float')}`",
        f"- Windows final u8: `{report['windows_trace'].get('final_rgba_u8')}`",
        "",
        "## Witness Cells",
        "",
        "### Denominator `param_1[0x843]`",
    ])
    point_samples = report.get("point_samples", [])
    if point_samples:
        insertion = lines.index("## Witness Cells")
        lines[insertion:insertion] = [
            "## Same-run point samples",
            "",
            "| XY | radius / angle index | final float RGBA | trunc u8 | output-world RGBA |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| `{point['xy']}` | `{point['indices']['radius']}` / `{point['indices']['angle']}` | "
                f"`{point['final_float']}` | `{point['final_u8']}` | `{point['output_world_rgba']}` |"
                for point in point_samples
            ],
            "",
        ]
    for key, value in report["witness_cells"]["denom_0x843"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("### Final polar `param_1[7]`")
    for key, value in report["witness_cells"]["final_7"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("### Accum RGBA `param_1[0x842]`")
    for key, value in report["witness_cells"]["accum_0x842"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Reading")
    lines.append("")
    lines.append(report["reading"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.save_checkpoint_at_rip and args.resume_checkpoint:
        raise SystemExit("--save-checkpoint-at-rip and --resume-checkpoint are mutually exclusive")
    checkpoint_path = None
    checkpoint_rip = None
    if args.save_checkpoint_at_rip:
        checkpoint_path = Path(args.save_checkpoint_at_rip[0])
        try:
            checkpoint_rip = int(args.save_checkpoint_at_rip[1], 0)
        except ValueError as exc:
            raise SystemExit("checkpoint RIP must be a decimal or 0x-prefixed integer") from exc
    debug_size = parse_debug_size(args.direct_debug_size)
    if debug_size is not None and not args.direct_zoom_core:
        raise SystemExit("--direct-debug-size requires --direct-zoom-core")
    params = load_case_params(args.manifest, args.case_id)
    image = Image.open(args.input_png).convert("RGBA")
    width, height = image.size
    r, g, b, a = image.split()
    input_bytes = Image.merge("RGBA", (a, r, g, b)).tobytes()
    output_bytes = bytes(width * height * 4)

    loader = AexLoader(str(args.aex_path), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = build_host_suites(loader)
    render_ctx = build_render_context(loader, spbasic)
    input_world = build_world(loader, width, height, input_bytes)
    output_world = build_world(loader, width, height, output_bytes)
    param_ctx = build_param_block(loader)
    provenance = install_reader_detours(loader, params)

    captured: dict[str, Any] = {
        "zoom_param1": 0,
        "zoom_param2": 0,
        "zoom_setup_a7e0_calls": 0,
        "zoom_setup_a810_calls": 0,
        "zoom_branch_hits": 0,
        "zoom_callsite_hits": 0,
        "last_branch_blur_type": None,
        "last_branch_ctx": 0,
        "prepass_calls": 0,
        "scatter_calls": 0,
        "prepass_detour_calls": 0,
        "scatter_detour_calls": 0,
        "staging_loop_hits": 0,
        "staging_loop_samples": [],
        "direct_thread_fixups": 0,
        "direct_core_samples": [],
        "direct_prefill_fast_forwarded": False,
        "direct_prefill_fast_forward_plane": 0,
        "direct_prefill_mode": None,
        "direct_python_prefill": None,
        "direct_stop_after_prefill": False,
    }
    execution_state: dict[str, Any] = {
        "checkpoint_enabled": False,
        "checkpoint_saved": False,
        "direct_context": None,
        "param_ctx_dump": None,
    }

    checkpoint_config = {
        "case_id": args.case_id,
        "input_sha256": sha256_file(args.input_png),
        "manifest_sha256": sha256_file(args.manifest),
        "trace_staging_loop": bool(args.trace_staging_loop),
        "direct_zoom_core": bool(args.direct_zoom_core),
        "direct_debug_size": args.direct_debug_size,
        "direct_debug_quality_step": float(args.direct_debug_quality_step),
        "direct_fast_forward_prefill": bool(args.direct_fast_forward_prefill),
        "direct_python_prefill": bool(args.direct_python_prefill),
        "direct_stop_after_prefill": bool(args.direct_stop_after_prefill),
        "direct_detour_prepass": bool(args.direct_detour_prepass),
        "direct_detour_scatter": bool(args.direct_detour_scatter),
    }

    # Avoid relying on numeric register ids in the hook body.
    from unicorn.x86_const import (
        UC_X86_REG_R12,
        UC_X86_REG_R14,
        UC_X86_REG_R15,
        UC_X86_REG_RAX,
        UC_X86_REG_RBX,
        UC_X86_REG_RCX,
        UC_X86_REG_RDI,
        UC_X86_REG_RDX,
        UC_X86_REG_RIP,
        UC_X86_REG_RSI,
    )

    def safe_u32(addr: int) -> int | None:
        try:
            return u32(loader, addr)
        except Exception:
            return None

    def safe_u64(addr: int) -> int | None:
        try:
            return u64(loader, addr)
        except Exception:
            return None

    def safe_f32(addr: int) -> float | None:
        try:
            return float(read_f32(loader, addr))
        except Exception:
            return None

    def fill_f32(addr: int | None, count: int, value: float) -> None:
        if not addr or count <= 0:
            return
        chunk = struct.pack("<f", float(value)) * count
        loader.write_bytes(addr, chunk)

    def fill_rgba(addr: int | None, cells: int, rgba: tuple[float, float, float, float]) -> None:
        if not addr or cells <= 0:
            return
        chunk = struct.pack("<4f", *rgba) * cells
        loader.write_bytes(addr, chunk)

    def capture_zoom_named(ld: AexLoader, address: int, size: int) -> None:
        captured["zoom_param1"] = ld.uc.reg_read(UC_X86_REG_RCX)
        captured["zoom_param2"] = ld.uc.reg_read(UC_X86_REG_RDX)

    def capture_zoom_setup_a7e0(ld: AexLoader, address: int, size: int) -> None:
        captured["zoom_setup_a7e0_calls"] += 1

    def capture_zoom_setup_a810(ld: AexLoader, address: int, size: int) -> None:
        captured["zoom_setup_a810_calls"] += 1

    def capture_zoom_branch(ld: AexLoader, address: int, size: int) -> None:
        captured["zoom_branch_hits"] += 1
        branch_ctx = ld.uc.reg_read(UC_X86_REG_RBX)
        captured["last_branch_ctx"] = branch_ctx
        captured["last_branch_blur_type"] = u32(ld, branch_ctx + 0x20)

    def capture_zoom_callsite(ld: AexLoader, address: int, size: int) -> None:
        captured["zoom_callsite_hits"] += 1

    def capture_prepass(ld: AexLoader, address: int, size: int) -> None:
        captured["prepass_calls"] += 1

    def capture_scatter(ld: AexLoader, address: int, size: int) -> None:
        captured["scatter_calls"] += 1

    def capture_staging_loop(ld: AexLoader, address: int, size: int) -> None:
        captured["staging_loop_hits"] += 1
        samples = captured["staging_loop_samples"]
        if len(samples) >= 12:
            return
        r15 = ld.uc.reg_read(UC_X86_REG_R15)
        sample = {
            "hit": captured["staging_loop_hits"],
            "r12_row": ld.uc.reg_read(UC_X86_REG_R12),
            "r14_col": ld.uc.reg_read(UC_X86_REG_R14),
            "r15": r15,
            "bound_x_r15_0x24": u32(ld, r15 + 0x24) if r15 else None,
            "bound_y_r15_0x28": u32(ld, r15 + 0x28) if r15 else None,
            "rdi": ld.uc.reg_read(UC_X86_REG_RDI),
            "rsi": ld.uc.reg_read(UC_X86_REG_RSI),
        }
        try:
            sample["rgba_being_written"] = [
                read_f32(ld, sample["rdi"] + 0),
                read_f32(ld, sample["rdi"] + 4),
                read_f32(ld, sample["rdi"] + 8),
                read_f32(ld, sample["rdi"] + 12),
            ]
        except Exception as exc:
            sample["rgba_being_written_error"] = str(exc)
        samples.append(sample)

    def force_direct_thread_count(ld: AexLoader, address: int, size: int) -> None:
        if not args.direct_zoom_core:
            return
        work = int(captured.get("zoom_param1") or 0)
        if not work:
            return
        current = u32(ld, work + 0x4220)
        if current <= 0:
            ld.write_bytes(work + 0x4220, struct.pack("<I", 1))
            captured["direct_thread_fixups"] += 1

    def capture_direct_core_branch(ld: AexLoader, address: int, size: int) -> None:
        if not args.direct_zoom_core:
            return
        samples = captured["direct_core_samples"]
        if len(samples) >= 80:
            return
        work = int(captured.get("zoom_param1") or 0)
        param = int(captured.get("zoom_param2") or 0)
        sample: dict[str, Any] = {
            "hook": DIRECT_CORE_BRANCH_HOOKS.get(address, f"0x{address:x}"),
            "rip": f"0x{address:x}",
            "rax": ld.uc.reg_read(UC_X86_REG_RAX),
            "rbx": ld.uc.reg_read(UC_X86_REG_RBX),
            "rcx": ld.uc.reg_read(UC_X86_REG_RCX),
            "rdx": ld.uc.reg_read(UC_X86_REG_RDX),
            "rsi": ld.uc.reg_read(UC_X86_REG_RSI),
            "rdi": ld.uc.reg_read(UC_X86_REG_RDI),
            "r12": ld.uc.reg_read(UC_X86_REG_R12),
            "r14": ld.uc.reg_read(UC_X86_REG_R14),
            "r15": ld.uc.reg_read(UC_X86_REG_R15),
        }
        if work:
            sample["work"] = work
            sample["work_thread_count_0x4220"] = safe_u32(work + 0x4220)
            sample["work_quality_step_0x10"] = safe_f32(work + 0x10)
            sample["work_angle_step_0x14"] = safe_f32(work + 0x14)
            sample["work_min_radius_0x18"] = safe_u32(work + 0x18)
            sample["work_max_radius_0x1c"] = safe_u32(work + 0x1C)
            sample["work_plane_0x38"] = safe_u64(work + 0x38)
            sample["work_plane_0x40"] = safe_u64(work + 0x40)
            sample["work_plane_0x4210"] = safe_u64(work + 0x4210)
            sample["work_plane_0x4218"] = safe_u64(work + 0x4218)
            sample["work_accum_0x842"] = safe_u64(work + 0x842 * 8)
            sample["work_denom_0x843"] = safe_u64(work + 0x843 * 8)
            sample["work_final_7"] = safe_u64(work + 7 * 8)
        if param:
            sample["param"] = param
            sample["param_source_0x88"] = safe_u64(param + 0x88)
            sample["param_source_0x90"] = safe_u64(param + 0x90)
            sample["param_rgba_0x98"] = safe_u64(param + 0x98)
            sample["param_output_0xa0"] = safe_u64(param + 0xA0)
        samples.append(sample)

    def fast_forward_polar_prefill(ld: AexLoader, address: int, size: int) -> None:
        if not args.direct_zoom_core or not (args.direct_fast_forward_prefill or args.direct_python_prefill):
            return
        work = int(captured.get("zoom_param1") or 0)
        if not work:
            return
        angle_count = ld.uc.reg_read(UC_X86_REG_R12) & 0xFFFFFFFF
        radial_count = ld.uc.reg_read(UC_X86_REG_R15) & 0xFFFFFFFF
        cells = int(angle_count) * int(radial_count)
        byte_plane = loader.bump_alloc(max(cells, 1), align=64)
        loader.write_bytes(byte_plane, b"\x01" * max(cells, 1))
        captured["direct_prefill_fast_forwarded"] = True
        captured["direct_prefill_fast_forward_plane"] = byte_plane
        captured["direct_prefill_fast_forward_cells"] = cells
        if args.direct_python_prefill:
            param = int(captured.get("zoom_param2") or 0)
            geometry = safe_u64(param + 0x08) if param else None
            source_width = safe_u32(geometry + 0x24) if geometry else None
            source_height = safe_u32(geometry + 0x28) if geometry else None
            if not param or not source_width or not source_height:
                raise RuntimeError("direct-python-prefill could not recover param geometry")
            captured["direct_prefill_mode"] = "python-repeat-border"
            captured["direct_python_prefill"] = python_prefill_zoom_polar_planes(
                ld,
                work,
                param,
                byte_plane,
                int(angle_count),
                int(radial_count),
                int(source_width),
                int(source_height),
            )
        else:
            captured["direct_prefill_mode"] = "synthetic"
            fill_rgba(safe_u64(work + 0x38), cells, (0.0, 0.0, 0.0, 1.0))
            fill_f32(safe_u64(work + 0x40), cells, 1.0)
            fill_f32(safe_u64(work + 0x48), cells, 1.0)
            fill_f32(safe_u64(work + 0x50), cells, 1.0)
            fill_rgba(safe_u64(work + 0x842 * 8), cells, (0.0, 0.0, 0.0, 1.0))
            fill_f32(safe_u64(work + 0x843 * 8), cells, 1.0)

        ld.uc.reg_write(UC_X86_REG_RDI, byte_plane)
        ld.uc.reg_write(UC_X86_REG_RIP, FUN_180005BA2)

    def stop_after_prefill(ld: AexLoader, address: int, size: int) -> None:
        if not args.direct_zoom_core or not args.direct_stop_after_prefill:
            return
        captured["direct_stop_after_prefill"] = True
        ld.uc.emu_stop()

    loader.add_code_hook(FUN_18000A7E0, capture_zoom_setup_a7e0)
    loader.add_code_hook(FUN_18000A810, capture_zoom_setup_a810)
    loader.add_code_hook(FUN_1800072D3, capture_zoom_branch)
    loader.add_code_hook(FUN_1800072FD, capture_zoom_callsite)
    loader.add_code_hook(FUN_1800056F0, capture_zoom_named)
    loader.add_code_hook(FUN_18000B150, capture_prepass)
    loader.add_code_hook(FUN_18000A9D0, capture_scatter)
    loader.add_code_hook(FUN_18000573B, force_direct_thread_count)
    for hook_addr in DIRECT_CORE_BRANCH_HOOKS:
        loader.add_code_hook(hook_addr, capture_direct_core_branch)
    loader.add_code_hook(FUN_180005A00, fast_forward_polar_prefill)
    loader.add_code_hook(FUN_180005BA2, stop_after_prefill)
    if args.trace_staging_loop:
        loader.add_code_hook(FUN_180007811, capture_staging_loop)
    if args.direct_detour_prepass:
        def detour_prepass(ld: AexLoader, int_args: list[int]) -> int:
            captured["prepass_detour_calls"] += 1
            return 0
        loader.detour_function(FUN_18000B150, "RadialBlur.Zoom.b150.noop", detour_prepass)
    if args.direct_detour_scatter:
        def detour_scatter(ld: AexLoader, int_args: list[int]) -> int:
            captured["scatter_detour_calls"] += 1
            return 0
        loader.detour_function(FUN_18000A9D0, "RadialBlur.Zoom.a9d0.noop", detour_scatter)

    def save_primary_render_checkpoint(ld: AexLoader, address: int, size: int) -> None:
        if not execution_state["checkpoint_enabled"] or execution_state["checkpoint_saved"]:
            return
        metadata = {
            "harness": "test_zoom_case0009",
            "harness_checkpoint_version": 1,
            "config": checkpoint_config,
            "captured": captured,
            "pointers": {
                "render_ctx": render_ctx,
                "input_world": input_world,
                "output_world": output_world,
                "param_ctx": param_ctx,
            },
            "direct_context": execution_state["direct_context"],
            "param_ctx_dump": execution_state["param_ctx_dump"],
        }
        ld.save_checkpoint(checkpoint_path, metadata=metadata)
        execution_state["checkpoint_saved"] = True
        ld.uc.emu_stop()

    if checkpoint_rip is not None:
        loader.add_code_hook(checkpoint_rip, save_primary_render_checkpoint)

    start = time.time()
    if args.resume_checkpoint:
        checkpoint_header = loader.load_checkpoint(args.resume_checkpoint)
        checkpoint_metadata = checkpoint_header.get("metadata", {})
        if checkpoint_metadata.get("harness") != "test_zoom_case0009":
            raise SystemExit("checkpoint was not created by test_zoom_case0009")
        if checkpoint_metadata.get("harness_checkpoint_version") != 1:
            raise SystemExit("unsupported case0009 harness checkpoint version")
        if checkpoint_metadata.get("config") != checkpoint_config:
            raise SystemExit("checkpoint case0009 options do not match this invocation")
        expected_pointers = {
            "render_ctx": render_ctx,
            "input_world": input_world,
            "output_world": output_world,
            "param_ctx": param_ctx,
        }
        if checkpoint_metadata.get("pointers") != expected_pointers:
            raise SystemExit("checkpoint host pointer layout does not match this fresh process")
        captured.clear()
        captured.update(checkpoint_metadata["captured"])
        direct_context = checkpoint_metadata.get("direct_context")
        param_ctx_dump = checkpoint_metadata.get("param_ctx_dump")
        render_fault = ""
        try:
            render_result = loader.resume_execution(max_instructions=args.max_instructions)
        except RuntimeError as exc:
            render_fault = str(exc)
            render_result = {"instructions": 0, "fault": render_fault}
    else:
        loader.call_function(FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
        param_ctx_dump = read_param_ctx(loader, param_ctx)
        execution_state["param_ctx_dump"] = param_ctx_dump
        if args.direct_zoom_core:
            direct_context = prepare_direct_zoom_context(
                loader, param_ctx, render_ctx, input_world, output_world, image, debug_size,
            )
            execution_state["direct_context"] = direct_context
            work_addr = loader.bump_alloc(0x4300, align=64)
            loader.write_bytes(work_addr, b"\x00" * 0x4300)
            loader.call_function(FUN_18000A7E0, int_args=[work_addr], max_instructions=10_000)
            strength = read_f32(loader, param_ctx + 0x80)
            loader.call_function(
                FUN_18000A810, int_args=[work_addr], float_args={1: (strength, "f")},
                max_instructions=10_000,
            )
            if debug_size is not None:
                loader.write_bytes(work_addr + 0x10, struct.pack("<f", float(args.direct_debug_quality_step)))
            captured["zoom_param1"] = work_addr
            captured["zoom_param2"] = param_ctx
            direct_start_instr = loader.instructions_executed
            render_fault = ""
            execution_state["checkpoint_enabled"] = True
            try:
                render_result = loader.call_function(
                    FUN_1800056F0, int_args=[work_addr, param_ctx],
                    max_instructions=args.max_instructions,
                )
            except RuntimeError as exc:
                render_fault = str(exc)
                render_result = {
                    "instructions": loader.instructions_executed - direct_start_instr,
                    "fault": render_fault,
                }
            finally:
                execution_state["checkpoint_enabled"] = False
        else:
            direct_context = None
            render_fault = ""
            execution_state["checkpoint_enabled"] = True
            try:
                render_result = loader.call_function(
                    FUN_180007520, int_args=[render_ctx, 0, input_world, output_world, param_ctx],
                    max_instructions=args.max_instructions,
                )
            finally:
                execution_state["checkpoint_enabled"] = False

    render_stop_rip = loader.uc.reg_read(UC_X86_REG_RIP)
    if execution_state["checkpoint_saved"]:
        print(f"checkpoint_saved={checkpoint_path}")
        print(f"checkpoint_rip=0x{checkpoint_rip:x}")
        return 0
    if checkpoint_path is not None:
        raise SystemExit(
            f"checkpoint RIP 0x{checkpoint_rip:x} was not reached; no checkpoint was written"
        )

    if args.direct_zoom_core:
        work_addr = int(captured.get("zoom_param1") or 0)
        try:
            loader.call_function(FUN_18000A800, int_args=[work_addr], max_instructions=10_000)
        except Exception:
            pass
    elapsed = time.time() - start

    work = int(captured["zoom_param1"])
    if not work:
        report = {
            "kind": "olmradialblur_zoom_case0009_aex_witness",
            "schema": 1,
            "case_id": args.case_id,
            "xy": [args.x, args.y],
            "aex": str(args.aex_path.relative_to(REPO_ROOT) if args.aex_path.is_relative_to(REPO_ROOT) else args.aex_path),
            "provenance": {
                "aex_sha256": sha256_file(args.aex_path),
                "input_sha256": sha256_file(args.input_png),
                "manifest_sha256": sha256_file(args.manifest),
            },
            "entry_reached": False,
            "elapsed_seconds": elapsed,
            "render_instructions": int(render_result["instructions"]),
            "render_fault": render_fault,
            "max_instructions": int(args.max_instructions),
            "zoom_setup_a7e0_calls": captured["zoom_setup_a7e0_calls"],
            "zoom_setup_a810_calls": captured["zoom_setup_a810_calls"],
            "zoom_branch_hits": captured["zoom_branch_hits"],
            "zoom_callsite_hits": captured["zoom_callsite_hits"],
            "last_branch_blur_type": captured["last_branch_blur_type"],
            "last_branch_ctx": captured["last_branch_ctx"],
            "prepass_calls": captured["prepass_calls"],
            "scatter_calls": captured["scatter_calls"],
            "prepass_detour_calls": captured["prepass_detour_calls"],
            "scatter_detour_calls": captured["scatter_detour_calls"],
            "staging_loop_hits": captured["staging_loop_hits"],
            "staging_loop_samples": captured["staging_loop_samples"],
            "direct_thread_fixups": captured["direct_thread_fixups"],
            "direct_core_samples": captured["direct_core_samples"],
            "direct_prefill_fast_forwarded": captured["direct_prefill_fast_forwarded"],
            "direct_prefill_fast_forward_plane": captured["direct_prefill_fast_forward_plane"],
            "direct_prefill_fast_forward_cells": captured.get("direct_prefill_fast_forward_cells", 0),
            "direct_prefill_mode": captured.get("direct_prefill_mode"),
            "direct_python_prefill": captured.get("direct_python_prefill"),
            "direct_stop_after_prefill": captured.get("direct_stop_after_prefill"),
            "render_stop_rip": f"0x{render_stop_rip:x}",
            "reader_call_count": len(provenance),
            "param_ctx": param_ctx_dump,
            "direct_zoom_context": direct_context if args.direct_zoom_core else None,
            "point_samples": [],
            "setup_pointers": {
                "render_ctx": render_ctx,
                "param_ctx": param_ctx,
                "input_world": input_world,
                "output_world": output_world,
            },
            "classification": "zoom-entry-not-reached-within-instruction-cap",
            "reading": (
                "The parameter setup completed with Blur Type 1 in param_ctx, but "
                "FUN_1800056f0 was not observed before the configured instruction cap. "
                "In this run the exact hooks at 0x1800072d3 (Blur Type branch), "
                "0x1800072fd (Zoom callsite), 0x18000a7e0, and 0x18000a810 also stayed "
                "cold, so the current blocker is upstream of the known Zoom dispatch "
                "sequence inside FUN_180007520, not inside the Zoom worker itself. "
                "This is a partial Mac-side emulation fact, not a semantic proof."
            ),
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        args.output_md.write_text(build_markdown(report), encoding="utf-8")
        print(f"wrote_json={args.output_json}")
        print(f"wrote_md={args.output_md}")
        print(f"classification={report['classification']}")
        print(f"render_instructions={report['render_instructions']} max_instructions={report['max_instructions']}")
        return 2
    accum = u64(loader, work + 0x842 * 8)
    denom = u64(loader, work + 0x843 * 8)
    final = u64(loader, work + 7 * 8)
    min_radius = struct.unpack("<i", loader.read_bytes(work + 0x18, 4))[0]
    max_radius_plus = struct.unpack("<i", loader.read_bytes(work + 0x1C, 4))[0]
    radial_count = (max_radius_plus - min_radius) + 1
    quality_step = read_f32(loader, work + 0x10)
    angle_step = read_f32(loader, work + 0x14)
    python_prefill_info = captured.get("direct_python_prefill") or {}
    angle_count = int(python_prefill_info.get("angle_count") or (360.0 / quality_step if quality_step else 0))

    legacy_point = sample_zoom_point(
        loader, final, accum, denom, radial_count, angle_count, min_radius,
        angle_step, work, output_world, args.x, args.y,
        debug_size is not None,
    )
    point_samples = [
        sample_zoom_point(
            loader, final, accum, denom, radial_count, angle_count, min_radius,
            angle_step, work, output_world, point_x, point_y,
            debug_size is not None,
        )
        for point_x, point_y in args.point
    ]
    radius_raw = legacy_point["inverse_coords"]["radius_raw"]
    angle_raw = legacy_point["inverse_coords"]["angle_raw"]
    radius_index = legacy_point["indices"]["radius"]
    angle_index = legacy_point["indices"]["angle"]
    final_sample = legacy_point["final_sample"]
    witness_cells = legacy_point["witness_cells"]
    out_rgba = legacy_point["output_world_rgba"]
    win = windows_case(args.trace_comparison_json, args.case_id)
    report: dict[str, Any] = {
        "kind": "olmradialblur_zoom_case0009_aex_witness",
        "schema": 1,
        "case_id": args.case_id,
        "xy": [args.x, args.y],
        "aex": str(args.aex_path.relative_to(REPO_ROOT) if args.aex_path.is_relative_to(REPO_ROOT) else args.aex_path),
        "provenance": {
            "aex_sha256": sha256_file(args.aex_path),
            "input_sha256": sha256_file(args.input_png),
            "manifest_sha256": sha256_file(args.manifest),
        },
        "entry_reached": True,
        "elapsed_seconds": elapsed,
        "render_instructions": int(render_result["instructions"]),
        "render_fault": render_fault,
        "max_instructions": int(args.max_instructions),
        "zoom_setup_a7e0_calls": captured["zoom_setup_a7e0_calls"],
        "zoom_setup_a810_calls": captured["zoom_setup_a810_calls"],
        "zoom_branch_hits": captured["zoom_branch_hits"],
        "zoom_callsite_hits": captured["zoom_callsite_hits"],
        "prepass_calls": captured["prepass_calls"],
        "scatter_calls": captured["scatter_calls"],
        "prepass_detour_calls": captured["prepass_detour_calls"],
        "scatter_detour_calls": captured["scatter_detour_calls"],
        "direct_thread_fixups": captured["direct_thread_fixups"],
        "direct_core_samples": captured["direct_core_samples"],
        "direct_prefill_fast_forwarded": captured["direct_prefill_fast_forwarded"],
        "direct_prefill_fast_forward_plane": captured["direct_prefill_fast_forward_plane"],
        "direct_prefill_fast_forward_cells": captured.get("direct_prefill_fast_forward_cells", 0),
        "direct_prefill_mode": captured.get("direct_prefill_mode"),
        "direct_python_prefill": captured.get("direct_python_prefill"),
        "direct_stop_after_prefill": captured.get("direct_stop_after_prefill"),
        "render_stop_rip": f"0x{render_stop_rip:x}",
        "reader_call_count": len(provenance),
        "param_ctx": param_ctx_dump,
        "direct_zoom_context": direct_context if args.direct_zoom_core else None,
        "direct_debug_size": list(debug_size) if debug_size is not None else None,
        "pointers": {
            "zoom_param1": work,
            "zoom_param2": int(captured["zoom_param2"]),
            "accum_0x842": accum,
            "denom_0x843": denom,
            "final_7": final,
        },
        "geometry": {
            "width": width,
            "height": height,
            "min_radius": min_radius,
            "max_radius_plus": max_radius_plus,
            "radial_count": radial_count,
            "quality_step": quality_step,
            "angle_step": angle_step,
            "angle_count": angle_count,
            "radius_raw": radius_raw,
            "angle_raw": angle_raw,
            "radius_index": radius_index,
            "angle_index": angle_index,
        },
        "witness_cells": witness_cells,
        "final_sample": final_sample,
        "output_world_rgba": out_rgba,
        "point_samples": point_samples,
        "windows_trace": {
            "pre_writeback_rgba_float": win.get("aex_pre_writeback_rgba_float_or_hex"),
            "final_rgba_u8": win.get("aex_final_rgba_u8"),
            "classification": win.get("classification"),
            "sampler_or_polar_xy": win.get("aex_sampler_or_polar_xy"),
        },
    }
    if debug_size is not None:
        report["classification"] = "direct-debug-core-hooks-reached-nonsemantic"
        report["reading"] = (
            "This is a reduced-geometry Mac-side AEX CPU emulation witness. It is "
            "only valid for proving harness reachability: the direct Zoom core can "
            "reach the prepass/scatter/final-plane branches when geometry and "
            "quality step are reduced. The sampled color/alpha values are not a "
            "case_0009 semantic proof and must not be compared to Windows output."
        )
    if args.direct_stop_after_prefill:
        report["classification"] = (
            "direct-python-prefill-stop-candidate"
            if args.direct_python_prefill
            else "direct-original-prefill-stop-witness"
        )
        report["reading"] = (
            "This run stops at 0x180005ba2 immediately after the Zoom polar input "
            "prefill and before FUN_18000b150/FUN_18000a9d0. It is useful for "
            "comparing the original AEX prefill cells against the Python prefill "
            "candidate without mixing in the heavy worker stages."
        )
    elif (
        debug_size is None
        and render_stop_rip == RETURN_TRAMPOLINE
        and not render_fault
        and not args.direct_python_prefill
        and not args.direct_fast_forward_prefill
        and not args.direct_detour_prepass
        and not args.direct_detour_scatter
    ):
        report["classification"] = classify(report, win)
        report["reading"] = (
            "This is a Mac-side AEX CPU emulation witness. It proves Zoom entry and "
            "the caller-collapse plane values for the local AEX. Compare the final "
            "sample alpha and denominator cells to the Windows trace to decide whether "
            "the 254/255 split is already present before final output. It does not by "
            "itself prove Mac AE exact."
        )
    elif debug_size is None:
        report["classification"] = "natural-fullsize-execution-incomplete-values-not-claimed"
        report["reading"] = (
            "The authentic, non-detoured full-size render did not reach its return "
            "trampoline in this run. Any currently mapped plane bytes are partial "
            "execution state and are not claimed as natural full-size case0009 values."
        )
    if args.direct_python_prefill and not args.direct_stop_after_prefill:
        report["classification"] = (
            "direct-python-prefill-detoured-candidate"
            if (args.direct_detour_prepass or args.direct_detour_scatter)
            else "direct-python-prefill-candidate-hooks-reached"
        )
        report["reading"] = (
            "This is a full-size direct-core harness witness with the hot Zoom "
            "polar input prefill replaced by a Python implementation derived "
            "from FUN_1800056f0 and the repeat-border bilinear samplers. It is "
            "stronger than the synthetic fast-forward because source planes and "
            "geometry participate. The prefill formula is exact against the "
            "original AEX at reduced geometry (max_abs_diff=0.0; see "
            "olmradialblur_zoom_python_prefill_validation_20260708.md), but the "
            "full-frame result remains a local candidate until its host/output "
            "binding is compared with a same-run Windows witness."
        )
    elif args.direct_fast_forward_prefill:
        report["classification"] = "direct-fast-forward-prefill-hooks-reached-nonsemantic"
        report["reading"] = (
            "This is a full-size direct-core harness reachability witness with "
            "the Zoom polar input prefill replaced by synthetic planes. It proves "
            "that the harness can reach the b150/a9d0/final-plane branches at "
            "full case geometry, but the plane values are synthetic and therefore "
            "not a case_0009 semantic proof."
        )
    if (args.direct_detour_prepass or args.direct_detour_scatter) and not args.direct_python_prefill:
        report["classification"] = "direct-detoured-core-reachability-nonsemantic"
        report["reading"] = (
            "This is a full-size direct-core harness reachability witness with "
            "one or more heavy Zoom workers replaced by no-op callbacks. It is "
            "valid only for proving downstream dispatch/reachability, not for "
            "case_0009 pixel semantics."
        )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.output_md.write_text(build_markdown(report), encoding="utf-8")
    print(f"wrote_json={args.output_json}")
    print(f"wrote_md={args.output_md}")
    print(f"classification={report['classification']}")
    print(f"local_sample={report['final_sample']['sample_float']} trunc={report['final_sample']['trunc_u8']}")
    print(f"output_world_rgba={out_rgba}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
