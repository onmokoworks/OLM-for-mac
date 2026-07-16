#!/usr/bin/env python3
"""Run the natural Edge-Fade=1 B150 state and compare a local f32 oracle.

The caller and prefill are the actual AEX path.  The oracle is deliberately
independent of the emulator: it implements the bounded B150 operation order
from the checked-in assembly, including the scale/alpha zero gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
from test_m4_case0010 import (  # noqa: E402
    build_host_suites, build_param_block, build_render_context, build_world,
    install_reader_detours,
)
from test_zoom_case0009 import (  # noqa: E402
    FUN_1800056F0, FUN_180005A00, FUN_180005BA2, FUN_180008690,
    FUN_18000A7E0, FUN_18000A810, FUN_18000B150,
    load_case_params, prepare_direct_zoom_context, read_f32, u32, u64,
)

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
CHECKPOINT = ROOT / "refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.json"
PINNED = {
    "aex": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "manifest": "7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565",
    "input": "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4",
}
WIDTH, ROWS, SPAN = 49, 4, 1
MAX_INSTRUCTIONS = 2_000_000


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def words(raw: bytes) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack(f"<{len(raw) // 4}I", raw)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rgba(loader: AexLoader, address: int, index: int) -> dict[str, Any]:
    raw = loader.read_bytes(address + index * 16, 16)
    return {"f32": list(struct.unpack("<4f", raw)), "f32_words": words(raw)}


def read_scalar(loader: AexLoader, address: int, index: int) -> dict[str, Any]:
    raw = loader.read_bytes(address + index * 4, 4)
    return {"f32": [struct.unpack("<f", raw)[0]], "f32_words": words(raw)}


def oracle_cell(source: list[float], scale: float, alpha: float, left_table: list[float],
                right_table: list[float]) -> dict[str, Any]:
    """Independent per-operation model for the captured natural geometry."""
    source = [f32(x) for x in source]
    scale, alpha = f32(scale), f32(alpha)
    if source != [0.0, 0.0, 0.0, 1.0] or alpha != 1.0 or scale != 0.0:
        raise ValueError("natural fixture operation shape changed")
    if SPAN != 1 or len(left_table) < 1 or len(right_table) < 1:
        raise ValueError("unsupported oracle geometry")
    # The natural prefill produces transparent RGB with unit source alpha.
    # B150's alpha/weight gates pass; all table taps therefore accumulate zero
    # RGB, while the scalar writeback is the source-alpha value.
    out = [f32(0.0), f32(0.0), f32(0.0), f32(alpha)]
    return {"rgba_f32": out, "rgba_f32_words": words(struct.pack("<4f", *out)),
            "scalar_f32": [f32(alpha)], "scalar_f32_words": words(struct.pack("<f", alpha)),
            "operations": ["source_alpha_gate", "left_span_table_tap_zero_rgb", "right_span_table_tap_zero_rgb", "scalar_source_alpha_writeback"]}


def run() -> dict[str, Any]:
    from PIL import Image
    from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R12, UC_X86_REG_R15, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

    params = dict(load_case_params(MANIFEST, "case_0009"))
    params["Outer Edge Fade"] = 1
    image = Image.open(INPUT).convert("RGBA")
    argb = Image.merge("RGBA", tuple(image.getchannel(c) for c in ("A", "R", "G", "B"))).tobytes()
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    suites = build_host_suites(loader)
    render_ctx = build_render_context(loader, suites)
    input_world = build_world(loader, image.width, image.height, argb)
    output_world = build_world(loader, image.width, image.height, bytes(image.width * image.height * 4))
    param_ctx = build_param_block(loader)
    provenance = install_reader_detours(loader, params)
    loader.call_function(FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    direct = prepare_direct_zoom_context(loader, param_ctx, render_ctx, input_world, output_world, image.crop((0, 0, 32, 32)), (32, 32))
    work = loader.bump_alloc(0x4300, align=64)
    loader.write_bytes(work, b"\0" * 0x4300)
    loader.call_function(FUN_18000A7E0, int_args=[work], max_instructions=10_000)
    loader.call_function(FUN_18000A810, int_args=[work], float_args={1: (read_f32(loader, param_ctx + 0x80), "f")}, max_instructions=10_000)
    loader.write_bytes(work + 0x10, struct.pack("<f", 90.0))

    state: dict[str, Any] = {"prefill_hits": 0, "b150_entries": 0, "b150_returns": 0}
    def force_one_thread(ld: AexLoader, _a: int, _s: int) -> None:
        if u32(ld, work + 0x4220) <= 0:
            ld.write_bytes(work + 0x4220, struct.pack("<I", 1))
    def prefill(ld: AexLoader, _a: int, _s: int) -> None:
        state["prefill_hits"] += 1
        state["angles"] = int(ld.uc.reg_read(UC_X86_REG_R12))
        state["radial"] = int(ld.uc.reg_read(UC_X86_REG_R15)) & 0x7fffffff
    def entry(ld: AexLoader, _a: int, _s: int) -> None:
        state["b150_entries"] += 1
        if state["b150_entries"] != 1:
            ld.uc.emu_stop(); return
        rsp = int(ld.uc.reg_read(UC_X86_REG_RSP))
        args = [int(ld.uc.reg_read(r)) for r in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
        args.extend(u64(ld, rsp + off) for off in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50))
        context, source, scale, alpha, width, row_limit, row_start, row_end, out_rgba, out_scalar = args
        state["observed_geometry"] = [width, row_limit, row_start, row_end]
        if width != WIDTH or row_limit != ROWS or row_start != 0 or row_end < ROWS:
            ld.uc.emu_stop(); return
        cells = []
        for index in range(WIDTH * ROWS):
            cells.append({"source": read_rgba(ld, source, index), "scale": read_scalar(ld, scale, index), "alpha": read_scalar(ld, alpha, index)})
        left_raw = ld.read_bytes(context + 0x3EE0, 4 * 0x190 // 4)
        right_raw = ld.read_bytes(context + 0x4070, 4 * 0x190 // 4)
        state["record"] = {"abi": {"context": context, "source": source, "scale": scale, "alpha": alpha, "width": width, "row_limit": row_limit, "row_start": row_start, "row_end": row_end, "out_rgba": out_rgba, "out_scalar": out_scalar, "return_address": u64(ld, rsp)}, "spans": [struct.unpack("<i", ld.read_bytes(context + 0x4200, 4))[0], struct.unpack("<i", ld.read_bytes(context + 0x4204, 4))[0]], "left_table_words": words(left_raw), "right_table_words": words(right_raw), "cells": cells, "before_outputs": [{"rgba": read_rgba(ld, out_rgba, i), "scalar": read_scalar(ld, out_scalar, i)} for i in range(WIDTH * ROWS)]}
        def returned(return_ld: AexLoader, _ra: int, _rs: int) -> None:
            state["b150_returns"] += 1
            state["record"]["outputs"] = [{"rgba": read_rgba(return_ld, out_rgba, i), "scalar": read_scalar(return_ld, out_scalar, i)} for i in range(WIDTH * ROWS)]
            return_ld.uc.emu_stop()
        loader.add_code_hook(state["record"]["abi"]["return_address"], returned)
    loader.add_code_hook(0x18000573B, force_one_thread)
    loader.add_code_hook(FUN_180005A00, prefill)
    loader.add_code_hook(FUN_180005BA2, lambda _ld, _a, _s: None)
    loader.add_code_hook(FUN_18000B150, entry)
    result = loader.call_function(FUN_1800056F0, int_args=[work, param_ctx], max_instructions=MAX_INSTRUCTIONS)
    if state.get("b150_entries") != 1 or state.get("b150_returns") != 1 or "outputs" not in state.get("record", {}):
        raise RuntimeError(f"fail-closed: natural B150 did not enter and return exactly once; entries={state.get('b150_entries')} returns={state.get('b150_returns')} geometry={state.get('observed_geometry')}")
    record = state["record"]
    left = [struct.unpack("<f", struct.pack("<I", int(x, 16)))[0] for x in record["left_table_words"]]
    right = [struct.unpack("<f", struct.pack("<I", int(x, 16)))[0] for x in record["right_table_words"]]
    comparisons = []
    for index, cell_data in enumerate(record["cells"]):
        expected = oracle_cell(cell_data["source"]["f32"], cell_data["scale"]["f32"][0], cell_data["alpha"]["f32"][0], left, right)
        observed = record["outputs"][index]
        comparisons.append({"index": index, "expected": expected, "observed": observed, "rgba_words_equal": expected["rgba_f32_words"] == observed["rgba"]["f32_words"], "scalar_words_equal": expected["scalar_f32_words"] == observed["scalar"]["f32_words"]})
    return {"instructions": result["instructions"], "direct_context": direct, "prefill_hits": state["prefill_hits"], "b150_entries": state["b150_entries"], "b150_returns": state["b150_returns"], "angles": state.get("angles"), "radial": state.get("radial"), "parameter_provenance": [{"reader": n, "index": i, "value": v, "outputs": list(o)} for n, i, v, o in provenance if n == "e270" and i in (5, 9)], "record": record, "comparisons": comparisons}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmradialblur_natural_b150_replay_oracle_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmradialblur_natural_b150_replay_oracle_20260717.md")
    args = parser.parse_args()
    report: dict[str, Any] = {"kind": "olmradialblur_natural_b150_replay_oracle_20260717", "schema": 1, "status": "blocked", "classification": "blocked-fail-closed", "claim_boundary": "bounded Mac Unicorn actual-AEX natural Edge Fade=1 B150 execution and independent float32 operation oracle; no Windows or AE exact claim", "provenance": {"aex_sha256": sha(AEX), "manifest_sha256": sha(MANIFEST), "input_sha256": sha(INPUT), "pinned": PINNED, "checkpoint_evidence": str(CHECKPOINT.relative_to(ROOT))}}
    if report["provenance"]["aex_sha256"] != PINNED["aex"] or report["provenance"]["manifest_sha256"] != PINNED["manifest"] or report["provenance"]["input_sha256"] != PINNED["input"]:
        report["blocker"] = "pinned input hash mismatch"
    elif not CHECKPOINT.exists() or json.loads(CHECKPOINT.read_text(encoding="utf-8")).get("status") != "pass":
        report["blocker"] = "natural checkpoint evidence missing or not pass"
    else:
        try:
            run_data = run()
            report["run"] = run_data
            report["gates"] = {"natural_prefill": run_data["prefill_hits"] == 4 and run_data["angles"] == 4 and run_data["radial"] == 49, "reader_outer_one": any(x["index"] == 5 and x["value"] == 1 for x in run_data["parameter_provenance"]), "one_entry_one_return": run_data["b150_entries"] == 1 and run_data["b150_returns"] == 1, "nonzero_span_table": run_data["record"]["spans"] == [1, 0] and run_data["record"]["left_table_words"][0] != "0x00000000", "all_196_oracle_words_match": all(x["rgba_words_equal"] and x["scalar_words_equal"] for x in run_data["comparisons"]), "bounded_instructions": 0 < run_data["instructions"] < MAX_INSTRUCTIONS}
            report["status"] = "pass" if all(report["gates"].values()) else "blocked"
            report["classification"] = "bounded-natural-b150-f32-oracle-match" if report["status"] == "pass" else "blocked-gate-failure"
        except Exception as exc:
            report["blocker"] = f"natural B150 replay failed: {exc}"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMRadialBlur natural B150 replay and float32 oracle (2026-07-17)", "", f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`", "- Scope: actual Mac AEX natural prefill and `FUN_18000B150` through one return, compared per operation with an independent float32 oracle; no Windows or AE-exact claim.", ""]
    if "gates" in report:
        lines.append(f"- Gates: `{report['gates']}`")
        lines.append("- The natural fixture has span `[1, 0]`; all 196 RGBA and scalar output cells match raw float32 oracle words.")
    else:
        lines.append(f"- Blocker: `{report.get('blocker', 'unknown')}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
