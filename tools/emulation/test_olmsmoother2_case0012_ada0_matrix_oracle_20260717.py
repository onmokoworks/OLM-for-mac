#!/usr/bin/env python3
"""Compare actual AEX ada0/ac00/ae10 output with an independent matrix oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RIP, UC_X86_REG_RSP

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402
from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import SerialVcomp  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

ADA0 = 0x18000ADA0
AC00 = 0x18000AC00
AE10 = 0x18000AE10
WIDTH = HEIGHT = 16
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def color_dist(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    if a[3] == 0.0 and b[3] == 0.0:
        return 0.0
    dr = f32(abs(f32(a[0] - b[0])))
    dg = f32(abs(f32(a[1] - b[1])))
    db = f32(abs(f32(a[2] - b[2])))
    la = f32(f32(f32(a[1] * 0.7152) + f32(a[0] * 0.2126)) + f32(a[2] * 0.0722))
    lb = f32(f32(f32(b[1] * 0.7152) + f32(b[0] * 0.2126)) + f32(b[2] * 0.0722))
    dy = f32(abs(f32(la - lb)))
    return f32(f32(max(dr, dg, db, dy)) + f32(abs(f32(a[3] - b[3]))))


def fixture() -> list[list[tuple[float, float, float, float]]]:
    # Nonzero alpha keeps the color-distance path live. Values are small and
    # exactly representable enough to make threshold boundary ownership clear.
    return [[
        (f32(0.03125 * x + 0.0078125 * y), f32(0.015625 * x), f32(0.0234375 * y), 1.0)
        for x in range(WIDTH)
    ] for y in range(HEIGHT)]


def portable_plane(source: list[list[tuple[float, float, float, float]]], raw: int, gate: int, multiplier: float) -> bytes:
    threshold = f32(f32(raw / 100.0) + 0.001)
    multiplier = f32(multiplier)
    out = bytearray(WIDTH * HEIGHT * 4)

    def dist(x1: int, y1: int, x2: int, y2: int) -> float:
        return color_dist(source[y1][x1], source[y2][x2])

    for y in range(HEIGHT):
        for x in range(WIDTH):
            center = source[y][x]
            b0 = dist(x, y, x - 1, y) if x >= 1 else 0.0
            b1 = dist(x, y, x, y - 1) if y > 0 else 0.0
            b2 = dist(x, y, x - 1, y - 1) if x >= 1 and y > 0 else 0.0
            # This intentionally preserves the AEX's width-1 bound, which
            # leaves the final two columns at zero for byte[3].
            # AEX computes byte[3] inside the y>0 block; top-row byte[3]
            # therefore remains zero regardless of the x-bound.
            b3 = dist(x, y, x + 1, y) if y > 0 and x + 1 < WIDTH - 1 else 0.0
            flags = [b0 >= threshold if x >= 1 else False, b1 >= threshold if y > 0 else False, b2 >= threshold if x >= 1 and y > 0 else False, b3 >= threshold if y > 0 and x + 1 < WIDTH - 1 else False]

            if gate and (flags[0] or flags[1]):
                right = dist(x, y, x + 1, y) if x + 1 < WIDTH else 0.0
                down = dist(x, y, x, y + 1) if y + 1 < HEIGHT else 0.0
                peak = max(b0, right, b1, down)
                if flags[0] and x > 1:
                    peak = max(peak, dist(x - 1, y, x - 2, y))
                    if f32(b0 * multiplier) < peak:
                        flags[0] = False
                if flags[1] and y > 1:
                    peak = max(peak, dist(x, y - 1, x, y - 2))
                    if f32(b1 * multiplier) < peak:
                        flags[1] = False
            off = (y * WIDTH + x) * 4
            out[off:off + 4] = bytes(255 if item else 0 for item in flags)
    return bytes(out)


def descriptors(loader: AexLoader, smoother: SmootherStruct, raw: int, gate: int, multiplier: float) -> tuple[int, int, int, int]:
    source = loader.bump_alloc(24, align=16)
    classes = loader.bump_alloc(24, align=16)
    rectangle = loader.bump_alloc(16, align=16)
    config = loader.bump_alloc(0x80, align=16)
    loader.write_bytes(source, struct.pack("<QiiQ", smoother.src_base, WIDTH, HEIGHT, smoother.src_stride))
    loader.write_bytes(classes, struct.pack("<QiiQ", smoother.class_base, WIDTH, HEIGHT, smoother.class_stride))
    loader.write_bytes(rectangle, struct.pack("<4i", 0, 0, WIDTH, HEIGHT))
    loader.write_bytes(config, b"\x00" * 0x80)
    loader.write_bytes(config + 0x1C, struct.pack("<i", raw))
    loader.write_bytes(config + 0x70, bytes([gate]))
    loader.write_bytes(config + 0x74, struct.pack("<f", multiplier))
    return source, classes, rectangle, config


def actual_plane(source: list[list[tuple[float, float, float, float]]], raw: int, gate: int, multiplier: float) -> tuple[bytes, dict[str, int]]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, WIDTH, HEIGHT)
    for y, row in enumerate(source):
        for x, rgba in enumerate(row):
            smoother.set_src_pixel(x, y, rgba)
    loader.write_bytes(smoother.class_base, b"\xA5" * (WIDTH * HEIGHT * 4))
    source_desc, class_desc, rectangle, config = descriptors(loader, smoother, raw, gate, multiplier)
    vcomp = SerialVcomp(loader)
    result = loader.call_function(ADA0, int_args=[source_desc, class_desc, rectangle, config], max_instructions=5_000_000)
    plane = loader.read_bytes(smoother.class_base, WIDTH * HEIGHT * 4)
    require(0xA5 not in plane, "actual AEX left a canary byte in the requested rectangle")
    require(set(plane).issubset({0, 255}), "actual AEX emitted a non-boolean class byte")
    require(vcomp.worker_entries == 1 and vcomp.classifier_entries == WIDTH * HEIGHT, "natural worker/classifier coverage changed")
    return plane, {"instructions": result["instructions"], "worker_entries": vcomp.worker_entries, "classifier_entries": vcomp.classifier_entries}


def grounding() -> None:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    require("; === FUN_18000ada0" in asm and "; === FUN_18000ae10" in asm, "ada0/ae10 assembly anchors missing")
    require("MOVD XMM8,dword ptr [R15 + 0x1c]" in asm and "CMP byte ptr [R15 + 0x70],0x0" in asm and "MULSS XMM9,dword ptr [R15 + 0x74]" in asm, "config reads are not grounded")
    require("local_res18[0] = param_3[1]" in decomp and "local_10[0] = param_3[2]" in decomp and "local_14 = *param_3" in decomp and "local_18 = param_3[3]" in decomp, "rect mapping is not grounded")
    require("param_1[3] != 0.0" in decomp and "DAT_180022dbc" in decomp, "color distance owner is not grounded")


def render(report: dict[str, Any]) -> str:
    lines = ["# OLMSmoother2 case0012 ada0 matrix oracle", "", "## Verdict", "", f"`{report['verdict']}`", "", "Actual AEX `FUN_18000ada0 -> FUN_18000ac00 -> FUN_18000ae10` was compared against an independent portable implementation over threshold, hysteresis, and multiplier boundaries.", ""]
    for row in report["matrix"]:
        lines.append(f"- `{row['raw']}/{row['gate']}/{row['multiplier']}`: `{row['status']}`, differing bytes `{row['differing_bytes']}`.")
    lines += ["", "The oracle fails closed if the binary hash, owner anchors, coverage, boolean output, or first byte mismatch changes. No Windows/AE, production, or ledger claim is made.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    grounding()
    source = fixture()
    matrix = []
    for raw in (0, 1, 10, 100, 200):
        for gate in (0, 1):
            for multiplier in (0.0, 1.0, 2.0):
                expected = portable_plane(source, raw, gate, multiplier)
                actual, runtime = actual_plane(source, raw, gate, multiplier)
                differing = [i for i, (a, b) in enumerate(zip(actual, expected)) if a != b]
                require(not differing, f"first missing owner or mismatch at raw={raw} gate={gate} multiplier={multiplier} byte={differing[0] if differing else 'unknown'}")
                matrix.append({"raw": raw, "gate": gate, "multiplier": multiplier, "status": "exact", "differing_bytes": 0, **runtime})
    report = {"verdict": "PASS_EXACT_AEX_AE10_PORTABLE_MATRIX_15_BOUNDARY_FIXTURES", "scope": "local actual-AEX class-plane generation versus independent portable oracle", "matrix": matrix, "coverage": {"fixtures": len(matrix), "threshold_raw": [0, 1, 10, 100, 200], "gate": [0, 1], "multiplier": [0.0, 1.0, 2.0]}, "claims_not_made": ["No Windows/AE execution claim", "No production Mac source or ledger edit"]}
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
