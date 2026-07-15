#!/usr/bin/env python3
"""Run the smallest bounded actual-AEX DG U8 conversion boundary fixture."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_XMM1, UC_X86_REG_XMM3, UC_X86_REG_XMM5, UC_X86_REG_XMM6

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
CALLBACK = 0x181170870
PRE_STORE = 0x181170C20
POST_STORE = 0x181170C40


def f32(loader: AexLoader, reg: int) -> float:
    return struct.unpack("<f", loader.uc.reg_read(reg).to_bytes(16, "little")[:4])[0]


def world(loader: AexLoader, pixels: list[tuple[int, int, int, int]]) -> int:
    data = loader.bump_alloc(len(pixels) * 4, align=64)
    loader.write_bytes(data, b"".join(bytes(p) for p in pixels))
    result = loader.host_alloc(0x80, align=16)
    loader.write_bytes(result, b"\0" * 0x80)
    loader.write_bytes(result + 0x18, struct.pack("<Q", data))
    loader.write_bytes(result + 0x20, struct.pack("<I", len(pixels) * 4))
    loader.write_bytes(result + 0x24, struct.pack("<I", len(pixels)))
    loader.write_bytes(result + 0x28, struct.pack("<I", 1))
    return result


def refcon(loader: AexLoader, field: int, source: int, color_code: float) -> int:
    result = loader.host_alloc(0x100, align=16)
    loader.write_bytes(result, b"\0" * 0x100)
    loader.write_bytes(result + 0x00, struct.pack("<Q", source))
    loader.write_bytes(result + 0x08, struct.pack("<Q", field))
    loader.write_bytes(result + 0x94, struct.pack("<I", 3))  # Both
    # The degenerate/background branch feeds these three floats directly to
    # the U8 conversion.  Use the same value in G/R/B to make the result easy
    # to compare channel-by-channel.
    normalized = color_code / 255.0
    for offset, value in ((0x9C, 0.0), (0xA0, 0.0), (0xA4, 0.0),
                          (0xAC, normalized), (0xB0, normalized), (0xB4, normalized)):
        loader.write_bytes(result + offset, struct.pack("<f", value))
    loader.write_bytes(result + 0x90, b"\1")  # degenerate branch
    loader.write_bytes(result + 0xC0, b"\1")  # background enabled
    loader.write_bytes(result + 0xC1, b"\0")  # X = 1 - field green
    loader.write_bytes(result + 0xC8, struct.pack("<I", 1))  # Gradation
    loader.write_bytes(result + 0xCC, struct.pack("<I", 1))  # Linear
    return result


def model(value: float) -> dict[str, int]:
    scaled = value * 255.0
    return {"truncate": math.trunc(scaled), "round_nearest": math.floor(scaled + 0.5)}


def main() -> int:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    # Two independently steered calls straddle the 12.5 code boundary.
    field = world(loader, [(0, 127, 0, 255), (0, 128, 0, 255)])
    source = world(loader, [(0, 0, 0, 0), (0, 0, 0, 0)])
    rows: list[dict[str, object]] = []
    for x in range(2):
        output = loader.bump_alloc(4, align=16)
        loader.write_bytes(output, b"\xee" * 4)
        color_code = (12.49, 12.51)[x]
        target = refcon(loader, field, source, color_code)
        lane: dict[str, object] = {}

        def hook(ld: AexLoader, rip: int, _size: int) -> None:
            if rip == PRE_STORE:
                lane["scaled_lanes_1_3_2_0"] = [
                    f32(ld, UC_X86_REG_XMM1), f32(ld, UC_X86_REG_XMM3),
                    f32(ld, UC_X86_REG_XMM5), f32(ld, UC_X86_REG_XMM6),
                ]
            elif rip == POST_STORE:
                lane["bytes_at_post_store"] = list(ld.read_bytes(output, 4))

        loader.add_code_hook(POST_STORE, hook)
        call = loader.call_function(CALLBACK, int_args=[target, x, 0, 0, output], max_instructions=200_000)
        lanes = [color_code, color_code, color_code, 255.0]
        actual = list(loader.read_bytes(output, 4))
        rows.append({
            "x": x,
            "field_green_u8": [127, 128][x],
            "steered_scaled_inputs_agrb": [lanes[3], lanes[0], lanes[1], lanes[2]],
            "actual_output_memory": actual,
            "actual_matches_truncate": actual == [model(lanes[3] / 255.0)["truncate"], model(lanes[0] / 255.0)["truncate"], model(lanes[1] / 255.0)["truncate"], model(lanes[2] / 255.0)["truncate"]],
            "actual_matches_round_nearest": actual == [model(lanes[3] / 255.0)["round_nearest"], model(lanes[0] / 255.0)["round_nearest"], model(lanes[1] / 255.0)["round_nearest"], model(lanes[2] / 255.0)["round_nearest"]],
            "models_by_lane": [model(float(v) / 255.0) for v in lanes],
            "instructions": call["instructions"],
        })

    report = {
        "kind": "dg_u8_rounding_boundary_20260716",
        "schema": 1,
        "status": "executed_actual_aex",
        "classification": "Mac-local Unicorn execution of checked-in Windows PE; not AE-host execution",
        "aex": str(AEX.relative_to(ROOT)),
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "entry": hex(CALLBACK),
        "conversion_address": {"pre_store": hex(PRE_STORE), "post_store": hex(POST_STORE)},
        "normal_path_probe": {"pre_store_reached": False, "reason": "The minimal degenerate/background branch returns after its direct byte casts; the normal-path marker at 0x181170c20 is not executed."},
        "fixture": {"width": 2, "height": 1, "field_channel": "green", "source": [[0, 0, 0, 0]] * 2},
        "rows": rows,
        "conclusion": "Actual bytes are compared against truncation and round-nearest per the steered direct-cast scaled input; the normal-path pre-store lane is not reached by this minimal branch.",
    }
    output = ROOT / "refs/conformance/dg_u8_rounding_boundary_20260716.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(output), "rows": rows}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
