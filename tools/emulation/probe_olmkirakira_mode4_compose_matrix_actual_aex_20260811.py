#!/usr/bin/env python3
"""Cross Mode-4 ray evidence with color/ramp/merge and typed writers."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
RAY_REPORT = ROOT / "refs/conformance/olmkirakira_mode4_canonical_angles_actual_aex_20260810.json"
HIGHLIGHT_REPORT = ROOT / "refs/conformance/olmkirakira_mode4_fullcaller_hostless_exact_20260807.json"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_compose_matrix_actual_aex_20260811.json"
EXPECTED_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
AGGREGATE = {1: 0x18114FD90, 2: 0x18114FFD0}
COMPOSE = {"PF8": (0x18114E110, 4), "PF16": (0x18114DDC0, 8), "PF32": (0x18114E460, 16)}
RAMP_HELPER = 0x181232080

sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402
from olmkirakira_outer_compose_oracle_20260728 import (  # noqa: E402
    compose_pixel, f32, stage_typed_writer,
)


STOPS_A = [
    [0.0, 0.20, 0.08, 0.12, 0.18],
    [0.12, 0.75, 0.22, 0.45, 0.09],
    [0.40, 0.40, 0.55, 0.16, 0.32],
    [0.73, 0.90, 0.18, 0.38, 0.52],
    [1.0, 0.30, 0.62, 0.24, 0.14],
]
STOPS_B = [
    [0.0, 0.65, 0.31, 0.06, 0.27],
    [0.18, 0.25, 0.07, 0.28, 0.44],
    [0.52, 0.80, 0.41, 0.11, 0.19],
    [0.81, 0.45, 0.16, 0.57, 0.08],
    [1.0, 0.95, 0.36, 0.21, 0.49],
]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def from_bits(word: str) -> float:
    return struct.unpack("<f", struct.pack("<I", int(word, 16)))[0]


def ramp_payload(stops: list[list[float]]) -> bytes:
    return struct.pack("<I", len(stops)) + b"".join(struct.pack("<5f", *stop) for stop in stops)


def sample_ramp(stops: list[list[float]], amount: float) -> tuple[float, float, float]:
    stops = [[f32(field) for field in stop] for stop in stops]
    amount = f32(amount)
    lower = None
    upper = None
    for stop in stops:
        if stop[0] <= amount:
            if lower is None or (lower[0] <= stop[0] and stop[0] != lower[0]):
                lower = stop
        elif upper is None or stop[0] < upper[0]:
            upper = stop
    if lower is None:
        return tuple(f32(x) for x in upper[2:5])  # type: ignore[return-value]
    if upper is None:
        return tuple(f32(x) for x in lower[2:5])  # type: ignore[return-value]
    t = f32(f32(amount - lower[0]) / f32(upper[0] - lower[0]))
    result = []
    for index in range(2, 5):
        delta = f32(f32(upper[index] - lower[index]) * t)
        result.append(f32(lower[index] + delta))
    return tuple(result)  # type: ignore[return-value]


def clamp(value: float) -> float:
    value = f32(value)
    if value >= 1.0:
        return f32(1.0)
    if value <= 0.0:
        return f32(0.0)
    return value


def portable_aggregate(
    rays: list[list[float]], colors: list[list[float]], flags: list[bool],
    ramps: list[list[list[float]]], merge_mode: int, scale: float,
) -> bytes:
    output = []
    for pixel in range(len(rays[0])):
        if merge_mode == 2:
            r = g = b = a = f32(0.0)
            for layer in range(5):
                amount = f32(rays[layer][pixel])
                if amount <= f32(0.001):
                    continue
                color = sample_ramp(ramps[layer], amount) if flags[layer] else tuple(colors[layer][1:4])
                # FUN_18114ffd0 adds the selected straight RGB once for each
                # live ray; only alpha accumulates the raw ray amount.
                r = f32(r + f32(color[0]))
                g = f32(g + f32(color[1]))
                b = f32(b + f32(color[2]))
                a = f32(a + amount)
            output.extend((clamp(r), clamp(g), clamp(b), clamp(a)))
        else:
            r = g = b = a = f32(0.0)
            for layer in range(5):
                amount = f32(rays[layer][pixel])
                if amount <= f32(0.001):
                    continue
                alpha = clamp(f32(f32(amount * f32(scale)) * f32(colors[layer][0])))
                r = f32(r + f32(alpha * f32(colors[layer][1])))
                g = f32(g + f32(alpha * f32(colors[layer][2])))
                b = f32(b + f32(alpha * f32(colors[layer][3])))
                a = f32(f32(a + alpha) - f32(a * alpha))
            if a > f32(1.0e-6):
                inverse = f32(f32(1.0) / a)
                r, g, b = f32(r * inverse), f32(g * inverse), f32(b * inverse)
            output.extend((r, g, b, a))
    return struct.pack(f"<{len(output)}f", *output)


def load_actual_planes() -> tuple[list[float], list[float], list[float]]:
    ray_report = json.loads(RAY_REPORT.read_text(encoding="utf-8"))
    case = next(case for case in ray_report["cases"] if
                (case["width"], case["height"], case["radius"], case["angle_degrees"]) == (9, 7, 5, 0))
    ray = [from_bits(word) for word in case["final"]["words_u32"][:4]]
    length1_case = next(case for case in ray_report["cases"] if
                        (case["width"], case["height"], case["radius"], case["angle_degrees"]) == (39, 30, 1, 17))
    length1_values = [from_bits(word) for word in length1_case["final"]["words_u32"]]
    first_live = next(index for index, value in enumerate(length1_values) if value != 0.0)
    length1_ray = length1_values[first_live:first_live + 4]
    highlight_report = json.loads(HIGHLIGHT_REPORT.read_text(encoding="utf-8"))
    highlight = [from_bits(word) for word in highlight_report["actual_aex"]["highlight_plane_u32"]]
    return ray, length1_ray, highlight


def run_case(spec: dict[str, object], directional: list[float], highlight: list[float]) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    zero = [0.0] * 4
    rays_values = [
        directional if not spec.get("d2") else zero,
        zero, zero,
        directional if spec.get("d2") else zero,
        highlight if spec["highlight"] else zero,
    ]
    ray_ptrs = []
    for values in rays_values:
        pointer = loader.host_alloc(16)
        loader.write_bytes(pointer, struct.pack("<4f", *values))
        ray_ptrs.append(pointer)
    rays = loader.host_alloc(40)
    loader.write_bytes(rays, struct.pack("<5Q", *ray_ptrs))
    colors = spec["colors"]
    color_array = loader.host_alloc(80)
    loader.write_bytes(color_array, b"".join(struct.pack("<4f", *record) for record in colors))
    flags = spec["flags"]
    flag_array = loader.host_alloc(5)
    loader.write_bytes(flag_array, bytes(int(flag) for flag in flags))
    ramps = [STOPS_A, STOPS_A, STOPS_A, STOPS_A, STOPS_B]
    ramp_array = loader.host_alloc(0x144 * 5)
    payloads = []
    for stops in ramps:
        payload = ramp_payload(stops)
        payloads.append(payload + bytes(0x144 - len(payload)))
    loader.write_bytes(ramp_array, b"".join(payloads))
    glow = loader.host_alloc(64)
    loader.write_bytes(glow, bytes(64))
    ramp_hits = []
    loader.add_code_hook(RAMP_HELPER, lambda _emu, _address, _size: ramp_hits.append(1))
    scale = float(spec["scale"])
    call = loader.call_function(
        AGGREGATE[int(spec["merge_mode"])],
        [0, rays, color_array, flag_array, ramp_array, 0, glow, 4, 1, struct.unpack("<I", struct.pack("<f", scale))[0]],
        max_instructions=500_000,
    )
    actual_glow = loader.read_bytes(glow, 64)
    portable_glow = portable_aggregate(
        rays_values, colors, flags, ramps, int(spec["merge_mode"]), scale)
    if actual_glow != portable_glow:
        raise AssertionError({"case": spec["name"], "actual": actual_glow.hex(), "portable": portable_glow.hex()})

    source_rgba = spec["source_rgba"]
    source = loader.host_alloc(64)
    loader.write_bytes(source, struct.pack("<16f", *source_rgba))
    owner = loader.host_alloc(0x200)
    loader.write_bytes(owner, bytes(0x200))
    loader.write_bytes(owner + 0x38, struct.pack("<f", float(spec["glow_opacity"])))
    loader.write_bytes(owner + 0x3C, struct.pack("<f", float(spec["source_opacity"])))
    loader.write_bytes(owner + 0x44, struct.pack("<i", int(spec["merge_mode"])))
    loader.write_bytes(owner + 0x58, struct.pack("<i", 4))
    loader.write_bytes(owner + 0x128, struct.pack("<Q", source))
    loader.write_bytes(owner + 0x190, struct.pack("<Q", glow))
    glow_values = struct.unpack("<16f", actual_glow)
    typed = {}
    for depth, (entry, pixel_size) in COMPOSE.items():
        output = loader.host_alloc(4 * pixel_size)
        loader.write_bytes(output, bytes(4 * pixel_size))
        world = loader.host_alloc(0x40)
        loader.write_bytes(world, bytes(0x40))
        loader.write_bytes(world + 0x18, struct.pack("<Q", output))
        loader.write_bytes(world + 0x20, struct.pack("<i", 4 * pixel_size))
        loader.write_bytes(world + 0x24, struct.pack("<i", 4))
        loader.write_bytes(world + 0x28, struct.pack("<i", 1))
        loader.call_function(entry, [owner, world], max_instructions=200_000)
        actual = loader.read_bytes(output, 4 * pixel_size)
        portable = b"".join(stage_typed_writer(compose_pixel(
            glow_values[i * 4:i * 4 + 4], source_rgba[i * 4:i * 4 + 4],
            glow_opacity=float(spec["glow_opacity"]), source_opacity=float(spec["source_opacity"]),
            merge_mode=int(spec["merge_mode"])), depth=depth) for i in range(4))
        if actual != portable:
            raise AssertionError({"case": spec["name"], "depth": depth, "actual": actual.hex(), "portable": portable.hex()})
        typed[depth] = {"exact_bytes": len(actual), "actual_hex": actual.hex(), "portable_hex": portable.hex()}
    return {
        "name": spec["name"], "merge_mode": spec["merge_mode"], "highlight": spec["highlight"],
        "directional_slot": 3 if spec.get("d2") else 0,
        "flags": flags, "scale_f32_bits": bits(scale), "ramp_helper_hits": len(ramp_hits),
        "aggregate_instructions": call["instructions"],
        "ray_u32": [bits(value) for value in directional],
        "highlight_u32": [bits(value) for value in rays_values[4]],
        "glow_u32": [bits(value) for value in glow_values], "typed_outputs": typed,
    }


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == EXPECTED_SHA
    directional, length1_ray, highlight = load_actual_planes()
    opaque = [0.10, 0.20, 0.30, 1.0, 0.20, 0.30, 0.40, 1.0, 0.30, 0.40, 0.50, 1.0, 0.40, 0.50, 0.60, 1.0]
    semihdr = [1.40, -0.10, 0.30, 0.35, 0.20, 1.70, 0.40, 0.60, 0.30, 0.40, 2.20, 0.15, 0.40, 0.50, 0.60, 0.90]
    default_colors = [[1.0, 1.0, 1.0, 1.0] for _ in range(5)]
    # AE's public color controls expose RGB here; keep their synthetic alpha at
    # one while varying every visible component.
    colors = [[1.0, 0.90, 0.15, 0.35], [1.0, 0.2, 0.8, 0.3], [1.0, 0.4, 0.2, 0.9], [1.0, 0.5, 0.5, 0.5], [1.0, 0.12, 0.70, 0.95]]
    specs = [
        {"name": "merge1_length1_directional", "merge_mode": 1, "length1": True, "highlight": False, "flags": [False] * 5, "colors": default_colors, "scale": 1.0, "source_rgba": opaque, "glow_opacity": 1.0, "source_opacity": 1.0},
        {"name": "merge1_colored_d2_highlight_semihdr", "merge_mode": 1, "d2": True, "highlight": True, "flags": [False] * 5, "colors": colors, "scale": 0.73, "source_rgba": semihdr, "glow_opacity": 0.68, "source_opacity": 0.73},
        {"name": "merge2_fixed_directional_highlight_semihdr", "merge_mode": 2, "highlight": True, "flags": [False] * 5, "colors": colors, "scale": 1.0, "source_rgba": semihdr, "glow_opacity": 0.68, "source_opacity": 0.73},
        {"name": "merge2_directional_ramp_fixed_highlight", "merge_mode": 2, "highlight": True, "flags": [True, False, False, False, False], "colors": colors, "scale": 1.0, "source_rgba": opaque, "glow_opacity": 0.41, "source_opacity": 0.82},
        {"name": "merge2_directional_and_highlight_ramps", "merge_mode": 2, "highlight": True, "flags": [True, False, False, False, True], "colors": colors, "scale": 1.0, "source_rgba": semihdr, "glow_opacity": 1.0, "source_opacity": 0.37},
    ]
    cases = [run_case(spec, length1_ray if spec.get("length1") else directional, highlight) for spec in specs]
    report = {
        "schema": "olmkirakira.mode4-compose-matrix-actual-aex/1", "status": "exact",
        "aex_sha256": EXPECTED_SHA,
        "source_evidence": {
            "directional": "Mode4 actual AEX FUN_181150790, 9x7 radius5 angle0 final plane",
            "length1_directional": "Mode4 actual AEX FUN_181150790, 39x30 radius1 angle17 first four live final values",
            "highlight": "Mode4 actual AEX FUN_18114f4a0 fifth ray, 4x1 radius5 three-pass isotropic box",
        },
        "matrix_rationale": "Five branch representatives cover default/non-default color, directional+highlight interaction, semitransparent/HDR source, Merge 1/2, ramp off/one/two, and PF8/PF16/PF32 without a redundant full Cartesian product.",
        "cases": cases,
        "exact": {"cases": len(cases), "aggregate_bytes": len(cases) * 64, "typed_bytes": len(cases) * (16 + 32 + 64), "max_ulp": 0},
        "boundary": "Hostless Mac Unicorn execution of the checked-in Windows AEX. The two actual Mode4 ray planes are crossed at the recovered aggregate/compose boundary; this is not a live Windows/AE claim.",
        "verification": "python3 tools/emulation/probe_olmkirakira_mode4_compose_matrix_actual_aex_20260811.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "exact", "cases": len(cases), "typed_bytes": report["exact"]["typed_bytes"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
