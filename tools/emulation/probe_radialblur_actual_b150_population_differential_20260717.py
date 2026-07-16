#!/usr/bin/env python3
"""Capture the first actual-AEX RadialBlur B150 population differential.

This Mac Unicorn probe runs the real polar prefill, records the direct-core
callsite, lets FUN_18000B150 run once, captures its row-slice before/after
population, and stops at the B150 return.  It deliberately does not claim AE
or Windows behavior and does not execute collapse/D80 unless requested as a
small sanity check.
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

from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402
from test_m4_case0010 import (  # noqa: E402
    build_host_suites, build_param_block, build_render_context, build_world,
    install_reader_detours,
)
from test_zoom_case0009 import (  # noqa: E402
    FUN_1800056F0, FUN_18000A7E0, FUN_18000A800, FUN_18000A810,
    FUN_180005A00, FUN_180005C1A, FUN_18000B150,
    load_case_params, prepare_direct_zoom_context, read_f32, read_rgba_cell,
    sample_final_plane, u32, u64,
)

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
PINNED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
PINNED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"
TARGETS = ((1047, 1095), (1047, 1096), (1048, 1095), (1048, 1096))
CONTROLS = ((1047, 1094), (1048, 1097))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(raw: bytes) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack(f"<{len(raw) // 4}I", raw)]


def cell(loader: AexLoader, plane: int, angle: int, radius: int, radial_count: int) -> dict[str, Any]:
    raw = loader.read_bytes(plane + (angle * radial_count + radius) * 16, 16)
    return {"f32": list(struct.unpack("<4f", raw)), "f32_words": words(raw)}


def scalar(loader: AexLoader, plane: int, angle: int, radius: int, radial_count: int) -> dict[str, Any]:
    raw = loader.read_bytes(plane + (angle * radial_count + radius) * 4, 4)
    return {"f32": [struct.unpack("<f", raw)[0]], "f32_words": words(raw)}


def capture_cells(loader: AexLoader, rgba: int, denom: int, radial_count: int) -> dict[str, Any]:
    return {
        f"{angle},{radius}": {"rgba": cell(loader, rgba, angle, radius, radial_count),
                               "scalar": scalar(loader, denom, angle, radius, radial_count)}
        for angle, radius in TARGETS + CONTROLS
    }


def plane_hashes(loader: AexLoader, rgba: int, denom: int, angle_count: int, radial_count: int) -> dict[str, str]:
    return {
        "rgba_sha256": hashlib.sha256(loader.read_bytes(rgba, angle_count * radial_count * 16)).hexdigest(),
        "scalar_sha256": hashlib.sha256(loader.read_bytes(denom, angle_count * radial_count * 4)).hexdigest(),
    }


def slice_dump(loader: AexLoader, rgba: int, denom: int, width: int, row_start: int, row_end: int) -> dict[str, Any]:
    count = max(0, row_end - row_start) * width
    rgba_raw = loader.read_bytes(rgba + row_start * width * 16, count * 16)
    scalar_raw = loader.read_bytes(denom + row_start * width * 4, count * 4)
    return {"rgba_f32_words": words(rgba_raw), "scalar_f32_words": words(scalar_raw),
            "rgba_sha256": hashlib.sha256(rgba_raw).hexdigest(),
            "scalar_sha256": hashlib.sha256(scalar_raw).hexdigest(),
            "cell_count": count}


def run() -> dict[str, Any]:
    from PIL import Image
    from unicorn.x86_const import (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8,
                                    UC_X86_REG_R9, UC_X86_REG_RSP, UC_X86_REG_R12,
                                    UC_X86_REG_R15)

    params = load_case_params(MANIFEST, "case_0009")
    image = Image.open(INPUT).convert("RGBA")
    raw = Image.merge("RGBA", tuple(image.getchannel(c) for c in ("A", "R", "G", "B"))).tobytes()
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    suites = build_host_suites(loader)
    render_ctx = build_render_context(loader, suites)
    input_world = build_world(loader, image.width, image.height, raw)
    output_world = build_world(loader, image.width, image.height, bytes(image.width * image.height * 4))
    param_ctx = build_param_block(loader)
    install_reader_detours(loader, params)
    loader.call_function(0x180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    direct = prepare_direct_zoom_context(loader, param_ctx, render_ctx, input_world, output_world, image, (32, 32))
    work = loader.bump_alloc(0x4300, align=64)
    loader.write_bytes(work, b"\0" * 0x4300)
    loader.call_function(FUN_18000A7E0, int_args=[work], max_instructions=10_000)
    strength = read_f32(loader, param_ctx + 0x80)
    loader.call_function(FUN_18000A810, int_args=[work], float_args={1: (strength, "f")}, max_instructions=10_000)
    loader.write_bytes(work + 0x10, struct.pack("<f", 90.0))
    def force_one_thread(ld: AexLoader, _address: int, _size: int) -> None:
        if u32(ld, work + 0x4220) <= 0:
            ld.write_bytes(work + 0x4220, struct.pack("<I", 1))
    loader.add_code_hook(0x18000573B, force_one_thread)

    state: dict[str, Any] = {"prefill_hits": 0, "callsite_hits": 0, "b150_entries": [], "b150_returns": 0}
    records = state["b150_entries"]

    def prefill_hook(_ld: AexLoader, _address: int, _size: int) -> None:
        state["prefill_hits"] += 1
        state["angle_count"] = int(_ld.uc.reg_read(UC_X86_REG_R12))
        state["radial_count"] = int(_ld.uc.reg_read(UC_X86_REG_R15)) & 0x7fffffff

    def callsite_hook(ld: AexLoader, _address: int, _size: int) -> None:
        state["callsite_hits"] += 1
        if state["callsite_hits"] == 1:
            state["callsite"] = {name: int(ld.uc.reg_read(reg)) for name, reg in
                                  (("rcx", UC_X86_REG_RCX), ("rdx", UC_X86_REG_RDX),
                                   ("r8", UC_X86_REG_R8), ("r9", UC_X86_REG_R9))}

    def b150_hook(ld: AexLoader, _address: int, _size: int) -> None:
        if records:
            return
        rsp = int(ld.uc.reg_read(UC_X86_REG_RSP))
        args = [int(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
        args.extend(u64(ld, rsp + off) for off in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50))
        context, source, scale, source_alpha = args[:4]
        angle_count = int(state.get("angle_count") or 1800)
        radial_count = int(state.get("radial_count") or 1104)
        width, row_limit, row_start, row_end, out_rgba, out_scalar = args[4:]
        record = {
            "abi": {"context": context, "raw_float32_input_rgba_rdx": source,
                    "scale_r8": scale, "source_alpha_r9": source_alpha,
                    "width": width, "row_limit": row_limit, "row_start": row_start,
                    "row_end": row_end, "output_rgba": out_rgba, "output_scalar": out_scalar,
                    "return_address": u64(ld, rsp)},
            "context_fields": {
                "span_work_plus_0x4200": struct.unpack("<i", ld.read_bytes(context + 0x4200, 4))[0],
                "span_work_plus_0x4204": struct.unpack("<i", ld.read_bytes(context + 0x4204, 4))[0],
                "gaussian_table_plus_0x3ee0": u64(ld, context + 0x3ee0),
                "gaussian_table_plus_0x4070": u64(ld, context + 0x4070),
            },
            "before": {
                "prefill_cells": {},
                "post_b150_work_offsets": {"rgba": "work+0x4210", "scalar": "work+0x4218"},
                "row_slice": slice_dump(ld, out_rgba, out_scalar, width, row_start, row_end),
            },
        }
        records.append(record)

        def returned(return_ld: AexLoader, _a: int, _s: int) -> None:
            state["b150_returns"] += 1
            record["after"] = {
                "prefill_cells": {},
                "post_b150_work_offsets": {"rgba": "work+0x4210", "scalar": "work+0x4218"},
                "row_slice": slice_dump(return_ld, out_rgba, out_scalar, width, row_start, row_end),
            }
            return_ld.uc.emu_stop()

        loader.add_code_hook(record["abi"]["return_address"], returned)

    loader.add_code_hook(FUN_180005A00, prefill_hook)
    loader.add_code_hook(FUN_180005C1A, callsite_hook)
    loader.add_code_hook(FUN_18000B150, b150_hook)
    result = loader.call_function(FUN_1800056F0, int_args=[work, param_ctx], max_instructions=400_000_000)
    if not records or "after" not in records[0]:
        raise RuntimeError("fail-closed: actual B150 did not enter and return exactly once")
    pointer = {"work": work, "work_plus_0x4210": u64(loader, work + 0x4210),
               "work_plus_0x4218": u64(loader, work + 0x4218),
               "final": u64(loader, work + 0x38)}
    return {"instructions": result["instructions"], "direct_context": direct, "pointers": pointer,
            "prefill_hits": state["prefill_hits"], "callsite_hits": state["callsite_hits"],
            "callsite": state.get("callsite"), "b150_entries": records, "b150_returns": state["b150_returns"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmradialblur_actual_b150_population_differential_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmradialblur_actual_b150_population_differential_20260717.md")
    args = parser.parse_args()
    report: dict[str, Any] = {
        "kind": "olmradialblur_actual_b150_population_differential_20260717", "schema": 1,
        "status": "blocked", "classification": "blocked-fail-closed",
        "claim_boundary": "Mac Unicorn actual-AEX B150 population only; no AE exact, Windows, or production claim",
        "target": {"prefill": ["0x180005a00", "0x180005b98"], "callsite": "0x180005c1a",
                   "b150_loop": ["0x18000b238", "0x18000b3d3"],
                   "b150_writeback": ["0x18000b533", "0x18000b59e"],
                   "primary_xy": [7, 0], "cells": [list(x) for x in TARGETS],
                   "controls": [list(x) for x in CONTROLS]},
        "provenance": {"aex_sha256": sha(AEX), "input_sha256": sha(INPUT),
                       "pinned": {"aex_sha256": PINNED_AEX_SHA256, "input_sha256": PINNED_INPUT_SHA256}},
    }
    if report["provenance"]["aex_sha256"] != PINNED_AEX_SHA256 or report["provenance"]["input_sha256"] != PINNED_INPUT_SHA256:
        report["blocker"] = "pinned AEX or input hash mismatch"
    else:
        try:
            report["run"] = run()
            run_data = report["run"]
            entry = run_data["b150_entries"][0]
            before, after = entry["before"], entry["after"]
            changed = before["row_slice"] != after["row_slice"]
            report["gates"] = {
                "hashes": True, "actual_prefill_once": run_data["prefill_hits"] == 1,
                "callsite_once": run_data["callsite_hits"] == 1,
                "b150_entry_return_once": len(run_data["b150_entries"]) == 1 and run_data["b150_returns"] == 1,
                "requested_cells_present": list(before["prefill_cells"]) == [f"{a},{r}" for a, r in TARGETS + CONTROLS],
                "population_changed": changed,
                "post_b150_words_present": after["row_slice"]["cell_count"] > 0,
            }
            report["status"] = "pass" if all(report["gates"].values()) else "blocked"
            report["classification"] = "bounded-mac-actual-aex-b150-population-differential" if report["status"] == "pass" else "blocked-gate-failure"
        except Exception as exc:
            report["blocker"] = f"actual prefill/B150 run failed: {exc}"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMRadialBlur actual-AEX B150 population differential (2026-07-17)", "",
             f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`",
             "- Scope: Mac Unicorn only; actual polar prefill, first B150 callsite, one B150 entry/return; no AE, Windows, or production claim.",
             "- Target cells: `(1047,1095)`, `(1047,1096)`, `(1048,1095)`, `(1048,1096)`; controls `(1047,1094)`, `(1048,1097)`.", ""]
    if "run" in report:
        lines.append(f"- Actual prefill hits: `{report['run']['prefill_hits']}`; callsite hits: `{report['run']['callsite_hits']}`; B150 returns: `{report['run']['b150_returns']}`.")
        lines.append("- Before/after raw float32 cells and plane hashes are preserved in JSON.")
    else:
        lines.append(f"- Blocker: `{report['blocker']}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
