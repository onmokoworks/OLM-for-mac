#!/usr/bin/env python3
"""Capture the Mode-2 ramp-color branch at the direct actual-AEX boundary."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RDX


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_ramp_actual_aex_boundary_20260805.json"
TARGET = 0x18114FFD0
RAMP_HELPER = 0x181232080
EXPECTED_SHA = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"

sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


DEFAULT_STOPS = [
    [0.25, 1.0, 0.0, 0.25, 0.125],
    [0.75, 0.0, 0.5, 1.0, 0.875],
]

FOUR_STOP_STOPS = [
    [0.0, 0.1, 0.9, 0.05, 0.8],
    [0.2, 0.85, 0.15, 0.7, 0.25],
    [0.65, 0.35, 0.8, 0.2, 0.6],
    [1.0, 0.7, 0.05, 0.95, 0.1],
]

FIVE_STOP_STOPS = [
    [0.0, 0.2, 0.08, 0.12, 0.18],
    [0.12, 0.75, 0.22, 0.45, 0.09],
    [0.4, 0.4, 0.55, 0.16, 0.32],
    [0.73, 0.9, 0.18, 0.38, 0.52],
    [1.0, 0.3, 0.62, 0.24, 0.14],
]

FIVE_STOP_STOPS_B = [
    [0.0, 0.65, 0.31, 0.06, 0.27],
    [0.18, 0.25, 0.07, 0.28, 0.44],
    [0.52, 0.8, 0.41, 0.11, 0.19],
    [0.81, 0.45, 0.16, 0.57, 0.08],
    [1.0, 0.95, 0.36, 0.21, 0.49],
]


def ramp_payload(stops: list[list[float]]) -> bytes:
    return struct.pack("<I", len(stops)) + b"".join(struct.pack("<5f", *stop) for stop in stops)


def run_case(ray: float, use_ramp: bool, stops: list[list[float]] = DEFAULT_STOPS) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    ray_ptrs = []
    for value in (ray, 0.0, 0.0, 0.0, 0.0):
        pointer = loader.host_alloc(4)
        loader.write_bytes(pointer, struct.pack("<f", value))
        ray_ptrs.append(pointer)
    rays = loader.host_alloc(40)
    loader.write_bytes(rays, struct.pack("<5Q", *ray_ptrs))

    # Fixed colors are BGRA in memory as interpreted by FUN_18114ffd0. The
    # active slot therefore contributes RGB=(0.25, 0.75, 0.0) when ramp is off.
    colors = loader.host_alloc(80)
    loader.write_bytes(colors, struct.pack("<20f", *([0.0, 0.25, 0.75, 1.0] * 5)))
    flags = loader.host_alloc(5)
    loader.write_bytes(flags, bytes([int(use_ramp), 0, 0, 0, 0]))

    # Ramp ABI: int32 count followed by position + PF_PixelFloat records.
    # PF_PixelFloat memory order is alpha, red, green, blue.
    # The full state stride is 0x144 bytes even though this fixture uses 44.
    ramp = loader.host_alloc(0x144 * 5)
    payload = ramp_payload(stops)
    loader.write_bytes(ramp, payload + bytes(0x144 * 5 - len(payload)))
    output = loader.host_alloc(16)
    loader.write_bytes(output, bytes(16))

    helper_hits: list[dict[str, object]] = []
    loader.add_code_hook(
        RAMP_HELPER,
        lambda emu, _address, _size: helper_hits.append({
            "ramp": hex(emu.uc.reg_read(UC_X86_REG_RDX)),
            "ray_f32_bits": bits(ray),
        }),
    )
    call = loader.call_function(
        TARGET, [0, rays, colors, flags, ramp, 0, output, 1, 1],
        max_instructions=100_000,
    )
    values = loader.read_f32_array(output, 4)
    return {
        "ray_f32_bits": bits(ray),
        "use_ramp": use_ramp,
        "output_rgba_f32_bits": [bits(value) for value in values],
        "ramp_helper_hit_count": len(helper_hits),
        "instructions": call["instructions"],
    }


def run_mixed_toggle_case() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    ray_values = (0.82, 0.31, 0.0, 0.0, 0.0)
    ray_ptrs = []
    for value in ray_values:
        pointer = loader.host_alloc(4)
        loader.write_bytes(pointer, struct.pack("<f", value))
        ray_ptrs.append(pointer)
    rays = loader.host_alloc(40)
    loader.write_bytes(rays, struct.pack("<5Q", *ray_ptrs))
    color_records = [
        [0.0, 0.0, 0.0, 0.0],
        [0.04, 0.11, 0.07, 0.13],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ]
    colors = loader.host_alloc(80)
    loader.write_bytes(colors, b"".join(struct.pack("<4f", *record) for record in color_records))
    flags = loader.host_alloc(5)
    loader.write_bytes(flags, b"\x01\x00\x00\x00\x00")
    payload = ramp_payload(FIVE_STOP_STOPS)
    ramps = loader.host_alloc(0x144 * 5)
    loader.write_bytes(ramps, (payload + bytes(0x144 - len(payload))) * 5)
    output = loader.host_alloc(16)
    loader.write_bytes(output, bytes(16))
    helper_hits = []
    loader.add_code_hook(RAMP_HELPER, lambda _emu, _address, _size: helper_hits.append(1))
    call = loader.call_function(
        TARGET, [0, rays, colors, flags, ramps, 0, output, 1, 1], max_instructions=100_000)
    values = loader.read_f32_array(output, 4)
    return {
        "ray_f32_bits": [bits(value) for value in ray_values],
        "use_ramp": [True, False, False, False, False],
        "output_rgba_f32_bits": [bits(value) for value in values],
        "ramp_helper_hit_count": len(helper_hits),
        "instructions": call["instructions"],
    }


def run_two_enabled_ramps_case() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    ray_values = (0.82, 0.33, 0.0, 0.0, 0.0)
    ray_ptrs = []
    for value in ray_values:
        pointer = loader.host_alloc(4)
        loader.write_bytes(pointer, struct.pack("<f", value))
        ray_ptrs.append(pointer)
    rays = loader.host_alloc(40)
    loader.write_bytes(rays, struct.pack("<5Q", *ray_ptrs))
    colors = loader.host_alloc(80)
    loader.write_bytes(colors, bytes(80))
    flags = loader.host_alloc(5)
    loader.write_bytes(flags, b"\x01\x01\x00\x00\x00")
    payload_a = ramp_payload(FIVE_STOP_STOPS)
    payload_b = ramp_payload(FIVE_STOP_STOPS_B)
    empty = bytes(0x144)
    ramps = loader.host_alloc(0x144 * 5)
    loader.write_bytes(ramps,
        payload_a + bytes(0x144 - len(payload_a)) +
        payload_b + bytes(0x144 - len(payload_b)) + empty * 3)
    output = loader.host_alloc(16)
    loader.write_bytes(output, bytes(16))
    helper_hits = []
    loader.add_code_hook(RAMP_HELPER, lambda _emu, _address, _size: helper_hits.append(1))
    call = loader.call_function(
        TARGET, [0, rays, colors, flags, ramps, 0, output, 1, 1], max_instructions=100_000)
    values = loader.read_f32_array(output, 4)
    return {
        "ray_f32_bits": [bits(value) for value in ray_values],
        "use_ramp": [True, True, False, False, False],
        "output_rgba_f32_bits": [bits(value) for value in values],
        "ramp_helper_hit_count": len(helper_hits),
        "instructions": call["instructions"],
    }


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == EXPECTED_SHA
    cases = {
        "below_first_stop": run_case(0.125, True),
        "between_stops": run_case(0.5, True),
        "above_last_stop": run_case(0.875, True),
        "same_ray_ramp_off": run_case(0.5, False),
        "four_stop_nonuniform": run_case(0.37, True, FOUR_STOP_STOPS),
        "five_stop_mixed_toggle": run_mixed_toggle_case(),
        "two_enabled_distinct_five_stop": run_two_enabled_ramps_case(),
    }
    expected = {
        "below_first_stop": [bits(0.0), bits(0.25), bits(0.125), bits(0.125)],
        "between_stops": [bits(0.25), bits(0.625), bits(0.5), bits(0.5)],
        "above_last_stop": [bits(0.5), bits(1.0), bits(0.875), bits(0.875)],
        "same_ray_ramp_off": [bits(0.25), bits(0.75), bits(1.0), bits(0.5)],
    }
    expected["four_stop_nonuniform"] = [
        "0x3eca8642", "0x3f02d82d", "0x3ec3b2a2", "0x3ebd70a4",
    ]
    expected["five_stop_mixed_toggle"] = [
        "0x3edf92c6", "0x3ece81b5", "0x3f05f92c", "0x3f800000",
    ]
    expected["two_enabled_distinct_five_stop"] = [
        "0x3f0bf259", "0x3f09d036", "0x3f391919", "0x3f800000",
    ]
    checks = {
        name: case["output_rgba_f32_bits"] == expected[name]
        for name, case in cases.items()
    }
    checks["helper_only_when_enabled"] = all(
        cases[name]["ramp_helper_hit_count"] == (
            0 if name == "same_ray_ramp_off" else
            2 if name == "two_enabled_distinct_five_stop" else 1)
        for name in cases
    )
    assert all(checks.values()), {"checks": checks, "cases": cases}
    report = {
        "schema": "olmkirakira-mode2-ramp-actual-aex-boundary/2",
        "status": "captured_exact",
        "aex_sha256": EXPECTED_SHA,
        "target": hex(TARGET),
        "ramp_helper": hex(RAMP_HELPER),
        "ramp_abi": {
            "stride_bytes": 0x144,
            "count": 2,
            "record": "float32 position, then PF_PixelFloat alpha, red, green, blue",
            "stops": [
                [0.25, 1.0, 0.0, 0.25, 0.125],
                [0.75, 0.0, 0.5, 1.0, 0.875],
            ],
            "consumed_prefix_hex": struct.pack(
                "<I10f", 2,
                0.25, 1.0, 0.0, 0.25, 0.125,
                0.75, 0.0, 0.5, 1.0, 0.875,
            ).hex(),
        },
        "four_stop_fixture": {
            "ray": 0.37,
            "stops": FOUR_STOP_STOPS,
            "payload_hex": (ramp_payload(FOUR_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FOUR_STOP_STOPS)))).hex(),
            "canonical_flat_hex": (b"\x01" + ramp_payload(FOUR_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FOUR_STOP_STOPS)))).hex(),
            "canonical_flat_sha256": hashlib.sha256(
                b"\x01" + ramp_payload(FOUR_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FOUR_STOP_STOPS)))
            ).hexdigest(),
        },
        "five_stop_mixed_toggle_fixture": {
            "rays": [0.82, 0.31, 0.0, 0.0, 0.0],
            "use_ramp": [True, False, False, False, False],
            "fixed_color_records": [
                [0.0, 0.0, 0.0, 0.0], [0.04, 0.11, 0.07, 0.13],
                [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0],
            ],
            "stops": FIVE_STOP_STOPS,
            "payload_hex": (ramp_payload(FIVE_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FIVE_STOP_STOPS)))).hex(),
            "canonical_flat_hex": (b"\x01" + ramp_payload(FIVE_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FIVE_STOP_STOPS)))).hex(),
            "canonical_flat_sha256": hashlib.sha256(
                b"\x01" + ramp_payload(FIVE_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FIVE_STOP_STOPS)))
            ).hexdigest(),
        },
        "two_enabled_distinct_five_stop_fixture": {
            "rays": [0.82, 0.33, 0.0, 0.0, 0.0],
            "use_ramp": [True, True, False, False, False],
            "group_order": ["vertical", "horizontal", "diagonal", "highlight", "diagonal2"],
            "stops_a": FIVE_STOP_STOPS,
            "stops_b": FIVE_STOP_STOPS_B,
            "canonical_flat_a_hex": (b"\x01" + ramp_payload(FIVE_STOP_STOPS) + bytes(0x144 - len(ramp_payload(FIVE_STOP_STOPS)))).hex(),
            "canonical_flat_b_hex": (b"\x01" + ramp_payload(FIVE_STOP_STOPS_B) + bytes(0x144 - len(ramp_payload(FIVE_STOP_STOPS_B)))).hex(),
        },
        "cases": cases,
        "expected_output_rgba_f32_bits": expected,
        "checks": checks,
        "facts": [
            "The ramp flag replaces the fixed RGB with the endpoint or linearly interpolated ramp RGB.",
            "Ramp alpha is not accumulated by FUN_18114ffd0; output alpha remains the raw ray amount.",
            "With the ramp flag clear, the same ray uses the fixed color and does not call the ramp helper.",
        ],
        "production_connection": {
            "status": "connected",
            "path": "five Mac arbitrary rows -> checkout/handle copy -> Merge2RampView -> add_colored_merge2",
            "wire": "actual meaningful prefix fixed; Mac serializer canonicalizes the ignored tail to zero",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMKIRAKIRA_MODE2_RAMP_ACTUAL_AEX_BOUNDARY_20260805 cases=7 two_enabled=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
