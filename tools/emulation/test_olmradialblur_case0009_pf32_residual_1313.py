#!/usr/bin/env python3
"""Trace the case0009 PF32 residual at output (1313,0), read-only."""

from __future__ import annotations

import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
import run_olmradialblur_continuation_20260718 as continuation  # noqa: E402


CHECKPOINT = Path("/private/tmp/olmradialblur_a9d0_boundary_nway_20260718/nway_merged_at_normalization_20260718.aexcp")
PLANE = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/normalized_polar_plane.f32rgba")
FRAME = Path("/tmp/olmradialblur_continuation_dump_20260718_corrected/complete_pf32_frame.f32rgba")
AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
X, Y = 1313, 0
WIDTH, HEIGHT = 1104, 1800
OUTPUT_WIDTH = 1920
FUN_A850 = 0x18000A850
FUN_D80 = 0x180009D80


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"


def add(a: float, b: float) -> float: return f32(a + b)
def sub(a: float, b: float) -> float: return f32(a - b)
def mul(a: float, b: float) -> float: return f32(a * b)
def div(a: float, b: float) -> float: return f32(a / b)


def cell(raw: bytes, angle: int, radius: int) -> tuple[float, float, float, float]:
    return struct.unpack_from("<4f", raw, (angle * WIDTH + radius) * 16)


def candidate(work_values: dict[str, float | int]) -> dict[str, object]:
    dy = sub(float(Y), float(work_values["center_y"]))
    dx = sub(float(X), float(work_values["center_x"]))
    cos_dy = mul(float(work_values["cos_angle"]), dy)
    sin_dx = mul(float(work_values["sin_angle"]), dx)
    ey_numerator = sub(cos_dy, sin_dx)
    ey = div(ey_numerator, float(work_values["ratio"]))
    sin_dy = mul(float(work_values["sin_angle"]), dy)
    cos_dx = mul(float(work_values["cos_angle"]), dx)
    ex = add(sin_dy, cos_dx)
    ex_squared = mul(ex, ex)
    ey_squared = mul(ey, ey)
    radius_squared = add(ey_squared, ex_squared)
    radius_raw = f32(math.sqrt(radius_squared))
    angle_raw = f32(math.atan2(float(ey), float(ex)))
    if angle_raw < 0.0:
        angle_raw = f32(float(angle_raw) + math.pi * 2.0)
    angle_index = div(angle_raw, float(work_values["angle_step"]))
    if angle_index >= float(work_values["angle_count"]):
        angle_index = sub(angle_index, float(work_values["angle_count"]))
    radius_index = sub(radius_raw, float(work_values["min_radius"]))
    radius0 = int(radius_index)
    angle0 = int(angle_index)
    radius1 = radius0 + 1
    angle1 = 0 if angle0 == int(work_values["angle_count"]) - 1 else angle0 + 1
    radius_fraction = sub(radius_index, float(radius0))
    angle_fraction = sub(angle_index, float(angle0))
    return {
        "fields": {"dx": dx, "dy": dy, "cos_dy": cos_dy, "sin_dx": sin_dx,
                   "ey_numerator": ey_numerator, "ey": ey, "sin_dy": sin_dy,
                   "cos_dx": cos_dx, "ex": ex, "ex_squared": ex_squared,
                   "ey_squared": ey_squared, "radius_squared": radius_squared,
                   "radius_raw": radius_raw, "angle_raw": angle_raw,
                   "radius_index": radius_index, "angle_index": angle_index,
                   "radius_fraction": radius_fraction, "angle_fraction": angle_fraction},
        "indices": {"radius0": radius0, "radius1": radius1, "angle0": angle0, "angle1": angle1},
    }


def sample(raw: bytes, trace: dict[str, object]) -> dict[str, object]:
    indices = trace["indices"]
    fields = trace["fields"]
    rf = float(fields["radius_fraction"])
    af = float(fields["angle_fraction"])
    w00 = mul(sub(1.0, rf), sub(1.0, af))
    w10 = mul(sub(1.0, af), rf)
    w01 = mul(sub(1.0, rf), af)
    w11 = mul(af, rf)
    labels = [("a0_r0", indices["angle0"], indices["radius0"], w00),
              ("a0_r1", indices["angle0"], indices["radius1"], w10),
              ("a1_r0", indices["angle1"], indices["radius0"], w01),
              ("a1_r1", indices["angle1"], indices["radius1"], w11)]
    cells = {label: list(cell(raw, angle, radius)) for label, angle, radius, _ in labels}
    out = [0.0, 0.0, 0.0, 0.0]
    for label, _, _, weight in labels:
        values = cells[label]
        alpha_weight = mul(weight, values[3])
        out[3] = add(out[3], alpha_weight)
        for channel in range(3):
            out[channel] = add(out[channel], mul(alpha_weight, values[channel]))
    if out[3] != 0.0:
        reciprocal = div(1.0, out[3])
        for channel in range(3):
            out[channel] = mul(out[channel], reciprocal)
    return {"weights": [w00, w10, w01, w11], "cells": cells, "output": out,
            "output_bits": [bits(value) for value in out]}


def main() -> int:
    if PLANE.stat().st_size != WIDTH * HEIGHT * 16:
        raise SystemExit("normalized plane size mismatch")
    loader, pointers = continuation.build_loader(AEX, MANIFEST, INPUT, "case_0009")
    header = loader.load_checkpoint(CHECKPOINT)
    identity = continuation.checkpoint_metadata_gate(header, CHECKPOINT, AEX, MANIFEST, INPUT, "case_0009")
    work = identity["work"]
    values = {
        "center_x": continuation.u32(loader, work + 0x4208),
        "center_y": continuation.u32(loader, work + 0x420C),
        "ratio": struct.unpack("<f", loader.read_bytes(work + 0x20, 4))[0],
        "cos_angle": struct.unpack("<f", loader.read_bytes(work + 0x28, 4))[0],
        "sin_angle": struct.unpack("<f", loader.read_bytes(work + 0x2C, 4))[0],
        "angle_step": struct.unpack("<f", loader.read_bytes(work + 0x14, 4))[0],
        "min_radius": struct.unpack("<i", loader.read_bytes(work + 0x18, 4))[0],
        "angle_count": HEIGHT,
    }
    # The values above are raw f32 words; center fields are interpreted below.
    values["center_x"] = struct.unpack("<f", loader.read_bytes(work + 0x4208, 4))[0]
    values["center_y"] = struct.unpack("<f", loader.read_bytes(work + 0x420C, 4))[0]
    radius_out = loader.bump_alloc(4, align=16)
    angle_out = loader.bump_alloc(4, align=16)
    loader.call_function(FUN_A850, int_args=[work, 0, 0, radius_out, angle_out],
                         float_args={1: (float(X), "f"), 2: (float(Y), "f")}, max_instructions=20000)
    actual_a850 = [struct.unpack("<f", loader.read_bytes(ptr, 4))[0] for ptr in (radius_out, angle_out)]
    raw = PLANE.read_bytes()
    prod = candidate(values)
    prod_sample = sample(raw, prod)
    actual_trace = candidate(values)
    actual_trace["fields"]["angle_raw"] = actual_a850[1]
    actual_trace["fields"]["angle_index"] = div(actual_a850[1], float(values["angle_step"]))
    actual_trace["indices"]["angle0"] = int(actual_trace["fields"]["angle_index"])
    actual_trace["indices"]["angle1"] = (actual_trace["indices"]["angle0"] + 1) % int(values["angle_count"])
    actual_trace["fields"]["angle_fraction"] = sub(
        actual_trace["fields"]["angle_index"], float(actual_trace["indices"]["angle0"]))
    actual_sample = sample(raw, actual_trace)
    plane_ptr = loader.bump_alloc(len(raw), align=64)
    loader.write_bytes(plane_ptr, raw)
    d80_out = loader.bump_alloc(16, align=16)
    radius_index = float(prod["fields"]["radius_index"])
    angle_index = float(prod["fields"]["angle_index"])
    loader.call_function(FUN_D80, int_args=[plane_ptr, d80_out, WIDTH, HEIGHT, WIDTH * 4,
                                             struct.unpack("<I", struct.pack("<f", radius_index))[0],
                                             struct.unpack("<I", struct.pack("<f", angle_index))[0]],
                         max_instructions=20000)
    actual_d80 = list(struct.unpack("<4f", loader.read_bytes(d80_out, 16)))
    actual_index_d80_out = loader.bump_alloc(16, align=16)
    actual_radius_index = float(actual_trace["fields"]["radius_index"])
    actual_angle_index = float(actual_trace["fields"]["angle_index"])
    loader.call_function(FUN_D80, int_args=[plane_ptr, actual_index_d80_out, WIDTH, HEIGHT, WIDTH * 4,
                                             struct.unpack("<I", struct.pack("<f", actual_radius_index))[0],
                                             struct.unpack("<I", struct.pack("<f", actual_angle_index))[0]],
                         max_instructions=20000)
    actual_index_d80 = list(struct.unpack("<4f", loader.read_bytes(actual_index_d80_out, 16)))
    frame = FRAME.read_bytes()[(Y * OUTPUT_WIDTH + X) * 16:(Y * OUTPUT_WIDTH + X + 1) * 16]
    frame_values = list(struct.unpack("<4f", frame))
    report = {"FACT": {
        "checkpoint": str(CHECKPOINT), "normalized_plane": str(PLANE), "xy": [X, Y],
        "actual_a850": {"values": actual_a850, "bits": [bits(v) for v in actual_a850]},
        "actual_d80_at_production_indices": {"values": actual_d80, "bits": [bits(v) for v in actual_d80]},
        "actual_caller_indices": actual_trace["indices"] | {"radius_index": actual_radius_index, "angle_index": actual_angle_index},
        "actual_d80_at_actual_indices": {"values": actual_index_d80, "bits": [bits(v) for v in actual_index_d80]},
        "retained_actual_frame": {"values": frame_values, "bits": [f"0x{v:08x}" for v in struct.unpack('<4I', frame)]},
    }, "INFERENCE": {
        "production_candidate": prod, "production_sample": prod_sample,
        "actual_index_sample": actual_sample,
        "a850_delta_bits": [bits(prod["fields"][key]) for key in ("radius_raw", "angle_raw")],
        "first_local_word_divergence": {
            "stage": "final sampled R",
            "production": prod_sample["output_bits"][0],
            "actual_frame_oracle": f"0x{struct.unpack('<I', frame[:4])[0]:08x}",
            "actual_d80": bits(actual_d80[0]),
        },
    }}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
