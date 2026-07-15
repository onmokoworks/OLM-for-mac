#!/usr/bin/env python3
"""Prove the OLMBlur PF16 range/packing rule behind the opaque-border mismatch."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RDI, UC_X86_REG_XMM6

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_case0006_border_order_writer_differential_20260716 import (  # noqa: E402
    model,
    run_actual,
    source_bytes,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
ASM = ROOT / "disasm/OLMBlur.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMBlur.aex.c.txt"
WRITER_ENTRY = 0x1800030E2
WRITER_STOP = 0x180003123
REPORT_JSON = ROOT / "refs/conformance/olmblur_pf16_unclamped_pack_boundary_20260716_followup.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_pf16_unclamped_pack_boundary_20260716_followup.md"

WRITER_TRIPLETS = (
    (32767.49, 32767.5, 32768.49),
    (32786.66015625, 32806.6875, 65534.5),
    (65535.49, 65535.5, 65536.49),
    (-0.49, -0.5, -0.51),
)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def packed_word(value: float) -> int:
    # Matches ADDSS 0.5f, floorf, CVTTSS2SI, then MOV word ...,AX.
    rounded = math.floor(f32(f32(value) + f32(0.5)))
    return rounded & 0xFFFF


def run_writer(values: tuple[float, float, float]) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)

    def impl_floorf(uc, args):
        loader.write_xmm_f32(0, math.floor(loader.read_xmm_f32(0)))
        return 0

    loader.register_import_impl("floorf", impl_floorf)
    source = loader.bump_alloc(12, align=16)
    output = loader.bump_alloc(8, align=16)
    raw_values = tuple(f32(value) for value in values)
    loader.write_bytes(source, struct.pack("<3f", *raw_values))
    loader.write_bytes(output, struct.pack("<4H", 0x8000, 0xDEAD, 0xDEAD, 0xDEAD))
    loader.uc.reg_write(UC_X86_REG_RDI, source + 8)
    loader.uc.reg_write(UC_X86_REG_RBX, output)
    loader.uc.reg_write(
        UC_X86_REG_XMM6,
        int.from_bytes(struct.pack("<f", 0.5) + b"\0" * 12, "little"),
    )

    def stop(uc, address, size, user_data):
        if address == WRITER_STOP:
            uc.emu_stop()

    loader.uc.hook_add(UC_HOOK_CODE, stop, begin=WRITER_STOP, end=WRITER_STOP)
    result = loader.call_function(WRITER_ENTRY, max_instructions=1000)
    words = struct.unpack("<4H", loader.read_bytes(output, 8))
    expected = tuple(packed_word(value) for value in raw_values)
    assert words[1:] == expected, (raw_values, words[1:], expected)
    return {
        "input_f32": list(raw_values),
        "actual_argb16": list(words),
        "floor_add_half_low16_rgb": list(expected),
        "instructions": result["instructions"],
        "floorf_execution": "host-backed callback at the actual AEX import",
    }


def pack_worker(source: bytes, floats: list[float], clamp_nominal: bool) -> bytes:
    output = bytearray(source)
    for index, value in enumerate(floats):
        if clamp_nominal:
            rounded = math.floor(f32(f32(value) + f32(0.5)))
            word = max(0, min(32768, rounded))
        else:
            word = packed_word(value)
        pixel, channel = divmod(index, 3)
        struct.pack_into("<H", output, pixel * 8 + 2 + channel * 2, word)
    return bytes(output)


def mismatches(actual: bytes, candidate: bytes) -> list[dict[str, object]]:
    result = []
    for pixel in range(len(actual) // 8):
        actual_words = struct.unpack_from("<4H", actual, pixel * 8)
        candidate_words = struct.unpack_from("<4H", candidate, pixel * 8)
        if actual_words != candidate_words:
            result.append(
                {
                    "pixel_index": pixel,
                    "xy": [pixel % 7, pixel // 7],
                    "actual_argb16": list(actual_words),
                    "candidate_argb16": list(candidate_words),
                }
            )
    return result


def static_evidence() -> dict[str, object]:
    asm = ASM.read_text()
    decomp = DECOMP.read_text()
    needles = (
        "1800030e2  MOVSS XMM0,dword ptr [RDI + -0x8]",
        "1800030e7  ADDSS XMM0,XMM6",
        "1800030eb  CALL 0x18000ccb4",
        "1800030f0  CVTTSS2SI EAX,XMM0",
        "1800030f4  MOV word ptr [RBX + 0x2],AX",
        "18000310a  MOV word ptr [RBX + 0x4],AX",
        "18000311f  MOV word ptr [RBX + 0x6],AX",
    )
    assert all(needle in asm for needle in needles)
    assert "// === floorf @ 18000ccb4 ===" in decomp
    interval = asm[asm.index(needles[0]):asm.index("180003123  INC ESI")]
    assert "CMP" not in interval and "J" not in interval
    return {
        "writer_interval": [hex(WRITER_ENTRY), hex(WRITER_STOP)],
        "sequence": ["MOVSS", "ADDSS 0.5f", "floorf", "CVTTSS2SI EAX", "MOV word,AX"],
        "clamp_or_range_branch_in_interval": False,
        "packing": "low 16 bits of the converted signed 32-bit integer",
    }


def main() -> int:
    case = {
        "kind": "border",
        "width": 7,
        "height": 5,
        "blur_amount": 4.0,
        "repeat": 1,
        "bias_direction": 1,
    }
    source = source_bytes(case["width"], case["height"], case["kind"])
    actual, instructions = run_actual(case, source)
    _, floats = model(source, case)
    unclamped = pack_worker(source, floats, clamp_nominal=False)
    clamped = pack_worker(source, floats, clamp_nominal=True)
    unclamped_diffs = mismatches(actual, unclamped)
    clamped_diffs = mismatches(actual, clamped)
    assert not unclamped_diffs
    assert [item["pixel_index"] for item in clamped_diffs] == [33, 34]

    report = {
        "schema": "olmblur.pf16-unclamped-pack-boundary/1",
        "scope": "Mac-only local actual-AEX and portable boundary proof; no AE or Windows claim",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "static_writer_evidence": static_evidence(),
        "actual_writer_microfixtures": [run_writer(values) for values in WRITER_TRIPLETS],
        "opaque_border_worker": {
            "geometry": [7, 5],
            "parameters": {key: case[key] for key in ("blur_amount", "repeat", "bias_direction")},
            "instructions": instructions,
            "actual_sha256": hashlib.sha256(actual).hexdigest(),
            "unclamped_low16_sha256": hashlib.sha256(unclamped).hexdigest(),
            "unclamped_low16_mismatches": unclamped_diffs,
            "nominal_32768_clamp_mismatches": clamped_diffs,
            "pre_store_witnesses": [
                {
                    "pixel_index": pixel,
                    "xy": [pixel % 7, pixel // 7],
                    "pre_store_rgb_f32": floats[pixel * 3:pixel * 3 + 3],
                    "actual_argb16": list(struct.unpack_from("<4H", actual, pixel * 8)),
                }
                for pixel in (33, 34)
            ],
        },
        "conclusion": {
            "earliest_divergence": "portable final writer nominal-range clamp",
            "border_sampling_explains_observed_two_word_mismatch": False,
            "exact_rule": "floorf(float32(value + 0.5f)); CVTTSS2SI to int32; store low uint16 word without saturation",
            "remaining_case0006_residual_cause": "not decided by this local synthetic proof",
            "ae_exact_claim": False,
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    REPORT_MD.write_text(
        "\n".join(
            [
                "# OLMBlur PF16 unclamped packing boundary follow-up",
                "",
                "This is a new Mac-only local actual-AEX/portable proof. It makes no AE exact claim and does not alter earlier differentials or the ledger.",
                "",
                "## Result",
                "",
                "- The opaque 7x5 worker output is byte-exact after removing only the portable nominal `32768` clamp and storing the low 16 bits.",
                "- The clamped candidate differs only at pixel 33 `(5,4)` and pixel 34 `(6,4)`, where the actual G-like words are `32787` and `32807`.",
                "- The matching pre-store G-like floats are `32786.66015625` and `32806.6875`; `floorf(value + 0.5f)` produces those exact words.",
                "- Therefore the prior two-word `border_radius4_opaque` mismatch begins at the portable final-writer range clamp, not at border sampling or coefficient accumulation.",
                "",
                "## Binary rule",
                "",
                "The PF16 writer at `0x1800030e2..0x18000311f` performs `ADDSS 0.5f`, calls `floorf`, executes `CVTTSS2SI EAX,XMM0`, and stores `AX`. There is no comparison, branch, or saturation in the three-channel writer interval. Controlled actual-AEX probes, using a host-backed `floorf` import callback, also confirm values above `65535` and below zero are packed by their low 16 bits after conversion.",
                "",
                "## Scope",
                "",
                "This excludes border sampling as the explanation for the two observed synthetic-fixture words only. It does not establish the cause of the live `case_0006` export residual and does not establish AE exactness.",
                "",
                "## Command",
                "",
                "`python3 tools/emulation/test_olmblur_pf16_unclamped_pack_boundary_20260716_followup.py`",
            ]
        )
        + "\n"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
