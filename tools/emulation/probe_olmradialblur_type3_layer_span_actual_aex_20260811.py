#!/usr/bin/env python3
"""Execute the pinned AEX Type-3 layer-to-span composers at all depths."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402
from unicorn.x86_const import UC_X86_REG_RSP, UC_X86_REG_XMM0  # noqa: E402

AEX = ROOT / "plugins_2025/OLMRadialBlur.aex"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_layer_span_actual_aex_20260811.json"
NOTE = REPORT.with_suffix(".md")
W, H = 3, 2
COMPOSERS = {8: 0x180006830, 16: 0x1800065C0, 32: 0x180006AA0}
CONVERTERS = {8: 0x1800172F0, 16: 0x180017360, 32: 0x1800173D0}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def pixel_bytes(depth: int, argb: tuple[float, float, float, float]) -> bytes:
    if depth == 8:
        return bytes(round(v * 255) for v in argb)
    if depth == 16:
        return struct.pack("<4H", *(round(v * 32768) for v in argb))
    return struct.pack("<4f", *argb)


def decoded(depth: int, argb: tuple[float, float, float, float]) -> tuple[float, ...]:
    if depth == 8:
        return tuple(f32(round(v * 255) * float.fromhex("0x1.0101020000000p-8")) for v in argb)
    if depth == 16:
        return tuple(f32(round(v * 32768) * float.fromhex("0x1.0000000000000p-15")) for v in argb)
    return tuple(f32(v) for v in argb)


def expected_luma(depth: int, argb: tuple[float, float, float, float]) -> float:
    a, r, g, b = decoded(depth, argb)
    rp, gp, bp = f32(r * a), f32(g * a), f32(b * a)
    # FUN_18000b630: three float-to-double conversions, then this exact order.
    # Preserve the exact binary64 constants embedded at 0x180021750/758/748.
    cr = float.fromhex("0x1.322d0e5604189p-2")
    cg = float.fromhex("0x1.2c8b439581062p-1")
    cb = float.fromhex("0x1.d2f1a9fbe76c9p-4")
    return f32((float(rp) * cr + float(gp) * cg) + float(bp) * cb)


def expected_span(size: float, nv: float, luma: float) -> float:
    mixed = f32(f32(nv * luma) + f32(1.0 - nv))
    return f32(mixed * size)


def qword(loader: AexLoader, address: int, value: int) -> None:
    loader.write_bytes(address, struct.pack("<Q", value))


def world(loader: AexLoader, data: int, rowbytes: int, left: int, top: int) -> int:
    ptr = loader.host_alloc(0x80, align=16)
    loader.write_bytes(ptr, bytes(0x80))
    qword(loader, ptr + 0x18, data)
    loader.write_bytes(ptr + 0x20, struct.pack("<iii", rowbytes, W, H))
    loader.write_bytes(ptr + 0x68, struct.pack("<ii", left, top))
    return ptr


def run_case(depth: int, nv: float, seed: int, offset: float, thickness: float) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    px = 4 if depth == 8 else 8 if depth == 16 else 16
    # Distinct alpha and RGB expose both converter scaling and plugin premultiplication.
    layer_values = [
        (0.5, 0.75, 0.25, 1.0), (1.0, 0.125, 0.5, 0.875), (0.25, 1.0, 0.5, 0.0),
        (0.75, 0.25, 1.0, 0.5), (1.0, 0.9, 0.1, 0.4), (0.0, 1.0, 1.0, 1.0),
    ]
    raw = b"".join(pixel_bytes(depth, p) for p in layer_values)
    data = loader.host_alloc(len(raw), align=16); loader.write_bytes(data, raw)
    source_world = world(loader, data, W * px, 10, 20)
    # Equal dimensions but shifted origin: first row and first column map OOB.
    layer_world = world(loader, data, W * px, 11, 21)
    sizes = [f32(v) for v in (0.25, 0.5, 0.75, 1.0, 0.625, 0.375)]
    size_ptr = loader.host_alloc(W * H * 4, align=16)
    span_ptr = loader.host_alloc(W * H * 4, align=16)
    loader.write_bytes(size_ptr, struct.pack("<6f", *sizes))
    loader.write_bytes(span_ptr, b"\xA5" * (W * H * 4))
    ctx = loader.host_alloc(0x120, align=64); loader.write_bytes(ctx, bytes(0x120))
    qword(loader, ctx + 0x08, source_world); qword(loader, ctx + 0x88, size_ptr)
    qword(loader, ctx + 0x90, span_ptr); qword(loader, ctx + 0xA8, layer_world)
    loader.write_bytes(ctx + 0x3C, struct.pack("<f", f32(nv)))
    loader.write_bytes(ctx + 0x50, struct.pack("<I", 3))
    loader.write_bytes(ctx + 0xFC, struct.pack("<Iff", seed, f32(offset), f32(thickness)))
    converted = []
    actual_lumas = []
    return_sites = {8: 0x180006928, 16: 0x1800066B8, 32: 0x180006B9F}
    def after_convert(current, _address, _size):
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        converted.append(struct.unpack("<4f", current.read_bytes(rsp + 0x40, 16)))
    loader.add_code_hook(return_sites[depth], after_convert)
    luma_sites = {8: 0x180006971, 16: 0x180006701, 32: 0x180006BE8}
    def after_luma(current, _address, _size):
        raw = int(current.uc.reg_read(UC_X86_REG_XMM0)).to_bytes(16, "little")
        actual_lumas.append(struct.unpack("<f", raw[:4])[0])
    loader.add_code_hook(luma_sites[depth], after_luma)
    loader.call_function(COMPOSERS[depth], int_args=[ctx], max_instructions=1_000_000)
    expected_converted = [decoded(depth, layer_values[0]), decoded(depth, layer_values[1])]
    assert b"".join(struct.pack("<4f", *p) for p in converted) == b"".join(
        struct.pack("<4f", *p) for p in expected_converted), (depth, converted, expected_converted)
    observed = struct.unpack("<6f", loader.read_bytes(span_ptr, 24))
    # (x,y) maps to layer (x-1,y-1); mapped source data is indexed locally.
    expected = []
    lumas = []
    li = 0
    for y in range(H):
        for x in range(W):
            if x == 0 or y == 0:
                luma = 0.0
            else:
                luma = actual_lumas[li]; li += 1
                static_luma = expected_luma(depth, layer_values[(y - 1) * W + x - 1])
                # Python does not model every SSE conversion rounding edge, but
                # executable bytes pin the coefficient and add order. Require a
                # tight numerical cross-check in addition to the exact span.
                assert abs(luma - static_luma) <= 6e-8, (depth, luma, static_luma)
            lumas.append(luma); expected.append(expected_span(sizes[y * W + x], f32(nv), luma))
    assert struct.pack("<6f", *observed) == struct.pack("<6f", *expected), (depth, nv, observed, expected, lumas, converted)
    return {
        "depth": depth, "noise_variation": int(nv * 100), "seed": seed,
        "noise_offset": offset, "thickness": thickness,
        "converter": hex(CONVERTERS[depth]), "composer": hex(COMPOSERS[depth]),
        "converted_argb": [list(p) for p in converted],
        "mapped_luma": lumas, "span_words": list(struct.unpack("<6I", struct.pack("<6f", *observed))),
        "span_sha256": hashlib.sha256(struct.pack("<6f", *observed)).hexdigest(),
    }


def probe() -> dict:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    rows = []
    for depth in COMPOSERS:
        for nv in (0.25, 1.0):
            base = run_case(depth, nv, 1, 0.0, 3.0)
            changed = run_case(depth, nv, 0xDEADBEEF, -17.25, 99.0)
            assert base["span_words"] == changed["span_words"]
            base["invariance_control"] = {
                "seed": changed["seed"], "noise_offset": changed["noise_offset"],
                "thickness": changed["thickness"], "span_sha256": changed["span_sha256"],
                "exact": True,
            }
            rows.append(base)
    return {
        "schema_version": 1, "status": "exact_static_and_executed_composer_contract",
        "plugin": "OLMRadialBlur", "aex_sha256": AEX_SHA256,
        "scope": "Type 3 Layer-to-span composer only; direct actual-AEX execution, 3x2 equal-size worlds, shifted origins",
        "rows": rows,
        "formula": "f32(f32(f32(NV*luma)+f32(1-NV))*size_factor)",
        "luminance": "f32((double(f32(R*A))*0.299 + double(f32(G*A))*0.587) + double(f32(B*A))*0.114)",
        "origin_rule": "layer local=(input.left-layer.left+x,input.top-layer.top+y); OOB luminance=0",
        "static_control_flow": {
            "parameter_checkout": "0x1800088b0-0x1800088c9",
            "pf8_owner_validation": "0x180007868-0x18000795f",
            "pf16_owner_validation": "0x180007058-0x18000714f",
            "pf32_owner_validation": "0x180008078-0x18000816f",
            "luminance": "0x18000b630",
            "seed_offset_thickness": "Type3 bypasses FUN_180009380, its only generator call supplied with ctx+0xfc/+0x100/+0x104",
            "zoom_rotation": "composition precedes blur_type dispatch at 0x1800072d3/0x180007ae3/0x1800082f3",
        },
        "zero_fill_boundary": "A zero-filled checked-out world yields zero luminance; a null/rejected world skips composition and can leave allocator-zero span. Neither observation proves native AE Type3 output.",
        "not_admitted": ["RenderWorld Type3", "native AE checkout conversion", "other geometry/origins", "pixel output"],
    }


def main() -> int:
    report = probe()
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    NOTE.write_text("""# OLM RadialBlur Type 3 Layer-to-span contract — 2026-08-11

Status: **exact static and executed composer contract**

The pinned Windows AEX composers execute exactly at PF8, PF16, and PF32 for Noise Variation 25/100. They convert the checked-out Layer pixel to float ARGB, premultiply RGB by alpha, calculate BT.601 luminance with double coefficients in binary instruction order, mix it with one by Noise Variation, and multiply the existing size-factor plane. Equal-size worlds with shifted origins prove that local out-of-bounds samples contribute zero luminance.

Changing Seed, Noise Offset, and Thickness leaves all span words unchanged. Static control flow independently proves why: Type 3 bypasses the generated-noise function receiving those fields. Zoom and Rotation dispatch after the common composition.

AEXCompat zero-filled Layer backing can therefore produce deterministic zero luminance, while a rejected/null Layer can preserve a zero-filled destination allocation. Those are harness initialization effects and do not admit Type 3 RenderWorld or native AE behavior.

Reproduction: `python3 tools/emulation/probe_olmradialblur_type3_layer_span_actual_aex_20260811.py`
""")
    print("PASS_OLMRADIALBLUR_TYPE3_LAYER_SPAN rows=6 depths=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
