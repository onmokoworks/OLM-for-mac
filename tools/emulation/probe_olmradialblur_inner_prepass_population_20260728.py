#!/usr/bin/env python3
"""Mac-only actual-AEX Inner B150 -> A9D0 population proof fixture.

This deliberately stops at the worker boundary.  It does not re-prove the
already-closed FUN_180001c90 scatter tail and makes no AE-exact claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_RIP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
B150 = 0x18000B150
A9D0 = 0x18000A9D0
WIDTH, HEIGHT = 8, 2
CELLS = WIDTH * HEIGHT
SCENARIOS = (
    {"name": "rb_inner_only_strength_large_low_span", "prepass_span": 1, "scatter_span": 1},
    {"name": "rb_inner_quality_1", "prepass_span": 3, "scatter_span": 4},
)


def alloc_zero(loader: AexLoader, size: int, align: int = 64) -> int:
    pointer = loader.bump_alloc(size, align=align)
    loader.write_bytes(pointer, b"\0" * size)
    return pointer


def f32_words(raw: bytes) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack(f"<{len(raw) // 4}I", raw)]


def nonzero_words(raw: bytes) -> int:
    return sum(value != 0 for value in struct.unpack(f"<{len(raw) // 4}I", raw))


def run_scenario(spec: dict[str, Any]) -> dict[str, Any]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    work = alloc_zero(loader, 0x4300)
    source = alloc_zero(loader, CELLS * 16)
    prepass = alloc_zero(loader, CELLS * 4)
    source_alpha = alloc_zero(loader, CELLS * 4)
    span_gate = alloc_zero(loader, CELLS * 4)
    valid = alloc_zero(loader, CELLS)
    accum = alloc_zero(loader, CELLS * 16)
    maximum = alloc_zero(loader, CELLS * 4)

    rgba: list[float] = []
    for cell in range(CELLS):
        scale = float(cell + 1) / float(CELLS)
        rgba.extend((scale, scale * 0.5, scale * 0.25, 1.0))
    loader.write_f32_array(source, rgba)
    loader.write_f32_array(source_alpha, [1.0] * CELLS)
    loader.write_f32_array(span_gate, [1.0] * CELLS)
    loader.write_bytes(valid, bytes([1] * CELLS))

    # B150 owns its prepass spans/tables.
    loader.write_bytes(work + 0x4200, struct.pack("<ii", 0, spec["prepass_span"]))
    loader.write_f32_array(work + 0x3EE0, [0.0] * 100)
    loader.write_f32_array(work + 0x4070, [1.0] * 100)
    # A9D0 owns separate scatter spans/tables.  Outer is disabled.
    loader.write_bytes(work + 0x3ED8, struct.pack("<ii", 0, spec["scatter_span"]))
    loader.write_f32_array(work + 0x58, [0.0] * 2000)
    loader.write_f32_array(work + 0x1F98, [1.0] * 2000)

    order: list[str] = []
    loader.add_code_hook(B150, lambda *_: order.append("B150"))
    loader.add_code_hook(A9D0, lambda *_: order.append("A9D0"))
    before_prepass = loader.read_bytes(prepass, CELLS * 4)
    b150 = loader.call_function(
        B150,
        int_args=[work, source, prepass, source_alpha, WIDTH, HEIGHT, 0, HEIGHT, accum, maximum],
        max_instructions=500_000,
    )
    b150_returned = loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    after_prepass = loader.read_bytes(prepass, CELLS * 4)
    before_a9d0_accum = loader.read_bytes(accum, CELLS * 16)
    before_a9d0_max = loader.read_bytes(maximum, CELLS * 4)

    # Counterfactual: keep source/span/valid and the B150-created accumulation
    # baseline byte-identical, changing only param_3 from zero to the actual
    # B150-populated prepass plane.
    loader.write_bytes(prepass, before_prepass)
    a9d0_zero = loader.call_function(
        A9D0,
        int_args=[work, source, prepass, span_gate, valid, WIDTH, HEIGHT, 0, HEIGHT, accum, maximum],
        max_instructions=1_000_000,
    )
    a9d0_zero_returned = loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    zero_prepass_accum = loader.read_bytes(accum, CELLS * 16)
    zero_prepass_max = loader.read_bytes(maximum, CELLS * 4)

    loader.write_bytes(accum, before_a9d0_accum)
    loader.write_bytes(maximum, before_a9d0_max)
    loader.write_bytes(prepass, after_prepass)
    a9d0_populated = loader.call_function(
        A9D0,
        int_args=[work, source, prepass, span_gate, valid, WIDTH, HEIGHT, 0, HEIGHT, accum, maximum],
        max_instructions=1_000_000,
    )
    a9d0_populated_returned = loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    after_a9d0_accum = loader.read_bytes(accum, CELLS * 16)
    after_a9d0_max = loader.read_bytes(maximum, CELLS * 4)

    a9d0_changed = after_a9d0_accum != before_a9d0_accum or after_a9d0_max != before_a9d0_max
    counterfactual_diverged = (
        after_a9d0_accum != zero_prepass_accum or after_a9d0_max != zero_prepass_max
    )
    expected_a9d0_change = spec["scatter_span"] > 1
    gates = {
        "actual_worker_order": order == ["B150", "A9D0", "A9D0"],
        "b150_returned": b150_returned,
        "a9d0_zero_prepass_returned": a9d0_zero_returned,
        "a9d0_populated_prepass_returned": a9d0_populated_returned,
        "prepass_started_zero": nonzero_words(before_prepass) == 0,
        "b150_populated_prepass": nonzero_words(after_prepass) > 0,
        "a9d0_population_matches_span_class": a9d0_changed == expected_a9d0_change,
        "prepass_counterfactual_matches_span_class": counterfactual_diverged == expected_a9d0_change,
        "instruction_budget": (
            b150["instructions"] <= 500_000
            and a9d0_zero["instructions"] <= 1_000_000
            and a9d0_populated["instructions"] <= 1_000_000
        ),
    }
    return {
        "name": spec["name"],
        "configured": {"outer_disabled": True, **spec},
        "instructions": {
            "b150": b150["instructions"],
            "a9d0_zero_prepass": a9d0_zero["instructions"],
            "a9d0_populated_prepass": a9d0_populated["instructions"],
        },
        "population": {
            "prepass_nonzero_words_before": nonzero_words(before_prepass),
            "prepass_nonzero_words_after_b150": nonzero_words(after_prepass),
            "accum_nonzero_words_before_a9d0": nonzero_words(before_a9d0_accum),
            "maximum_nonzero_words_before_a9d0": nonzero_words(before_a9d0_max),
            "accum_nonzero_words_after_a9d0": nonzero_words(after_a9d0_accum),
            "maximum_nonzero_words_after_a9d0": nonzero_words(after_a9d0_max),
            "a9d0_changed_population": a9d0_changed,
            "expected_a9d0_changed_population": expected_a9d0_change,
            "zero_vs_populated_prepass_diverged": counterfactual_diverged,
            "expected_zero_vs_populated_prepass_diverged": expected_a9d0_change,
            "zero_prepass_accum_nonzero_words": nonzero_words(zero_prepass_accum),
            "zero_prepass_maximum_nonzero_words": nonzero_words(zero_prepass_max),
            "prepass_words_after_b150": f32_words(after_prepass),
        },
        "gates": gates,
        "status": "pass" if all(gates.values()) else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "kind": "olmradialblur_inner_prepass_population_20260728",
        "schema": 1,
        "status": "blocked_fail_closed",
        "claim_boundary": (
            "Mac Unicorn pinned actual-AEX B150 caller-generated prepass population "
            "and paired A9D0 zero/populated-prepass counterfactuals; consumption is "
            "claimed only where those outputs diverge; excludes the closed scatter tail, Windows, "
            "AE exactness, production wiring, and full-frame semantics"
        ),
        "addresses": {"b150": hex(B150), "a9d0": hex(A9D0)},
        "geometry": {"width": WIDTH, "height": HEIGHT, "cells": CELLS},
        "scatter_tail": {"address": "0x180001c90", "status": "out_of_scope_already_closed"},
    }
    try:
        if sys.platform != "darwin":
            raise RuntimeError("fixture is Mac-only")
        if not AEX.is_file():
            raise RuntimeError("pinned OLMRadialBlur AEX is unavailable")
        actual_hash = hashlib.sha256(AEX.read_bytes()).hexdigest()
        if actual_hash != AEX_SHA256:
            raise RuntimeError(f"AEX SHA256 mismatch: {actual_hash}")
        report["aex_sha256"] = actual_hash
        report["scenarios"] = [run_scenario(spec) for spec in SCENARIOS]
        report["status"] = "pass" if all(x["status"] == "pass" for x in report["scenarios"]) else "fail"
    except (OSError, RuntimeError, ValueError, struct.error) as error:
        report["blocker"] = str(error)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        args.output_json.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
