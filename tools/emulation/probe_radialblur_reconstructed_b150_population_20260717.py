#!/usr/bin/env python3
"""Direct actual-AEX B150 proof with reconstructed row-sliced caller state.

The natural caller is intentionally not run.  This harness allocates a
contiguous logical plane of width 1104 through row 1048, seeds six explicit
float32 input cells, and invokes FUN_18000B150 exactly once for rows 1047..1048.
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

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
PINNED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
WORKER = 0x18000B150
WIDTH = 1104
ROW_START = 1047
ROW_END = 1049
ROWS = ROW_END
TARGETS = ((1047, 1095), (1047, 1096), (1048, 1095), (1048, 1096))
CONTROLS = ((1047, 1094), (1048, 1094))
SEED = {
    (1047, 1094): (0.125, 0.25, 0.375, 0.875),
    (1047, 1095): (0.25, 0.5, 0.75, 1.0),
    (1047, 1096): (0.5, 0.25, 0.125, 0.5),
    (1048, 1094): (0.375, 0.625, 0.25, 0.625),
    (1048, 1095): (0.75, 0.125, 0.25, 0.75),
    (1048, 1096): (1.0, 0.5, 0.25, 0.25),
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def words(raw: bytes) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack(f"<{len(raw) // 4}I", raw)]


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def alloc(loader: AexLoader, size: int) -> int:
    address = loader.bump_alloc(size, align=64)
    loader.write_bytes(address, b"\0" * size)
    return address


def rgba_cell(loader: AexLoader, plane: int, row: int, column: int) -> dict[str, Any]:
    raw = loader.read_bytes(plane + (row * WIDTH + column) * 16, 16)
    return {"f32": list(struct.unpack("<4f", raw)), "f32_words": words(raw)}


def scalar_cell(loader: AexLoader, plane: int, row: int, column: int) -> dict[str, Any]:
    raw = loader.read_bytes(plane + (row * WIDTH + column) * 4, 4)
    return {"f32": [struct.unpack("<f", raw)[0]], "f32_words": words(raw)}


def capture(loader: AexLoader, rgba: int, scalar: int) -> dict[str, Any]:
    points = TARGETS + CONTROLS
    return {f"{row},{column}": {"rgba": rgba_cell(loader, rgba, row, column),
                                 "scalar": scalar_cell(loader, scalar, row, column)}
            for row, column in points}


def plane_sha(loader: AexLoader, address: int, bytes_count: int) -> str:
    return hashlib.sha256(loader.read_bytes(address, bytes_count)).hexdigest()


def run() -> dict[str, Any]:
    from unicorn.x86_const import (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8,
                                    UC_X86_REG_R9, UC_X86_REG_RSP, UC_X86_REG_RIP)

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    work = alloc(loader, 0x4300)
    param = alloc(loader, 0x100)
    geometry = alloc(loader, 0x40)
    cells = WIDTH * ROWS
    source = alloc(loader, cells * 16)
    scale = alloc(loader, cells * 4)
    source_alpha = alloc(loader, cells * 4)
    output_rgba = alloc(loader, cells * 16)
    output_scalar = alloc(loader, cells * 4)
    final = alloc(loader, cells * 16)
    loader.write_bytes(geometry + 0x24, struct.pack("<ii", WIDTH, ROWS))
    loader.write_bytes(param + 0x08, struct.pack("<Q", geometry))
    loader.write_bytes(param + 0x98, struct.pack("<Q", source))
    loader.write_bytes(work + 0x38, struct.pack("<Q", final))
    loader.write_bytes(work + 0x4210, struct.pack("<Q", output_rgba))
    loader.write_bytes(work + 0x4218, struct.pack("<Q", output_scalar))

    scale_raw = struct.pack("<f", f32(1.0)) * cells
    alpha_raw = struct.pack("<f", f32(1.0)) * cells
    loader.write_bytes(scale, scale_raw)
    loader.write_bytes(source_alpha, alpha_raw)
    for (row, column), values in SEED.items():
        loader.write_bytes(source + (row * WIDTH + column) * 16,
                           struct.pack("<4f", *(f32(v) for v in values)))

    state: dict[str, Any] = {"entries": [], "returns": 0}

    def on_entry(ld: AexLoader, _address: int, _size: int) -> None:
        if state["entries"]:
            return
        rsp = int(ld.uc.reg_read(UC_X86_REG_RSP))
        args = [int(ld.uc.reg_read(reg)) for reg in
                (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
        args.extend(u64(ld, rsp + offset) for offset in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50))
        context, input_rgba, scale_ptr, alpha_ptr = args[:4]
        width, row_limit, row_start, row_end, out_rgba, out_scalar = args[4:]
        before = capture(ld, out_rgba, out_scalar)
        record = {
            "abi": {"context": context, "raw_float32_input_rgba_rdx": input_rgba,
                    "scale_r8": scale_ptr, "source_alpha_r9": alpha_ptr,
                    "width": width, "row_limit": row_limit, "row_start": row_start,
                    "row_end": row_end, "output_rgba": out_rgba,
                    "output_scalar": out_scalar, "return_address": u64(ld, rsp)},
            "context_fields": {
                "span_work_plus_0x4200": struct.unpack("<i", ld.read_bytes(context + 0x4200, 4))[0],
                "span_work_plus_0x4204": struct.unpack("<i", ld.read_bytes(context + 0x4204, 4))[0],
                "gaussian_table_pointer_plus_0x3ee0": u64(ld, context + 0x3ee0),
                "gaussian_table_pointer_plus_0x4070": u64(ld, context + 0x4070),
            },
            "input_cells": {key: {"rgba": rgba_cell(ld, input_rgba, *point),
                                   "source_alpha": scalar_cell(ld, alpha_ptr, *point)}
                            for key, point in ((f"{r},{c}", (r, c)) for r, c in TARGETS + CONTROLS)},
            "scale_cells": {key: scalar_cell(ld, scale_ptr, *point) for key, point in
                            ((f"{r},{c}", (r, c)) for r, c in TARGETS + CONTROLS)},
            "before_output_cells": before,
        }
        state["entries"].append(record)

        def on_return(return_ld: AexLoader, _a: int, _s: int) -> None:
            state["returns"] += 1
            record["after_output_cells"] = capture(return_ld, out_rgba, out_scalar)
            record["output_plane_sha256"] = {
                "rgba": plane_sha(return_ld, out_rgba, cells * 16),
                "scalar": plane_sha(return_ld, out_scalar, cells * 4),
            }
            return_ld.uc.emu_stop()

        loader.add_code_hook(record["abi"]["return_address"], on_return)

    loader.add_code_hook(WORKER, on_entry)
    args = [work, source, scale, source_alpha, WIDTH, ROWS, ROW_START, ROW_END,
            output_rgba, output_scalar]
    result = loader.call_function(WORKER, int_args=args, max_instructions=2_000_000)
    if state["entries"] and "after_output_cells" not in state["entries"][0]:
        state["returns"] = int(loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE)
        state["entries"][0]["after_output_cells"] = capture(loader, output_rgba, output_scalar)
        state["entries"][0]["output_plane_sha256"] = {
            "rgba": plane_sha(loader, output_rgba, cells * 16),
            "scalar": plane_sha(loader, output_scalar, cells * 4),
        }
    return {
        "instructions": result["instructions"], "return_rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
        "allocations": {"logical_width": WIDTH, "allocated_rows_through": ROWS,
                         "row_start": ROW_START, "row_end": ROW_END,
                         "rgba_bytes_per_plane": cells * 16, "scalar_bytes_per_plane": cells * 4},
        "pointers": {"work": work, "param": param, "geometry": geometry,
                     "raw_input_rgba_rdx": source, "scale_r8": scale,
                     "source_alpha_r9": source_alpha, "post_b150_rgba_work_plus_0x4210": output_rgba,
                     "post_b150_scalar_work_plus_0x4218": output_scalar, "final": final},
        "seed_oracle": {f"{r},{c}": [f32(v) for v in values] for (r, c), values in SEED.items()},
        "entries": state["entries"], "returns": state["returns"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmradialblur_reconstructed_b150_population_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmradialblur_reconstructed_b150_population_20260717.md")
    args = parser.parse_args()
    actual_hash = hashlib.sha256(AEX.read_bytes()).hexdigest()
    report: dict[str, Any] = {
        "kind": "olmradialblur_reconstructed_b150_population_20260717", "schema": 1,
        "status": "blocked", "classification": "blocked-fail-closed",
        "claim_boundary": "Mac Unicorn actual-AEX B150 with reconstructed caller state; no natural prefill, Windows, or AE-exact claim",
        "target": {"function": hex(WORKER), "loop": ["0x18000b238", "0x18000b3d3"],
                   "writeback": ["0x18000b533", "0x18000b59e"], "width": WIDTH,
                   "row_start": ROW_START, "row_end": ROW_END,
                   "cells": [list(x) for x in TARGETS], "controls": [list(x) for x in CONTROLS]},
        "provenance": {"aex_sha256": actual_hash, "pinned_aex_sha256": PINNED_AEX_SHA256,
                       "input_state": "independent documented float32 seed oracle; no PNG/prefill claim"},
    }
    if actual_hash != PINNED_AEX_SHA256:
        report["blocker"] = "pinned AEX hash mismatch"
    else:
        try:
            report["run"] = run()
            run_data = report["run"]
            entry = run_data["entries"][0] if len(run_data["entries"]) == 1 else {}
            abi = entry.get("abi", {})
            output_changed = entry.get("before_output_cells") != entry.get("after_output_cells")
            words_present = all("f32_words" in item["rgba"] and "f32_words" in item["scalar"]
                                for item in entry.get("after_output_cells", {}).values())
            report["gates"] = {
                "pinned_hash": True, "one_entry_one_return": len(run_data["entries"]) == 1 and run_data["returns"] == 1,
                "exact_abi": abi.get("width") == WIDTH and abi.get("row_start") == ROW_START and abi.get("row_end") == ROW_END,
                "six_seed_inputs_present": list(entry.get("input_cells", {})) == [f"{r},{c}" for r, c in TARGETS + CONTROLS],
                "raw_output_words_present": words_present, "output_population_changed": output_changed,
                "returned": run_data["return_rip"] == hex(RETURN_TRAMPOLINE),
            }
            report["status"] = "pass" if all(report["gates"].values()) else "blocked"
            report["classification"] = "bounded-reconstructed-mac-actual-aex-b150-proven" if report["status"] == "pass" else "blocked-gate-failure"
        except Exception as exc:
            report["blocker"] = f"reconstructed B150 execution failed: {exc}"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMRadialBlur reconstructed B150 population proof (2026-07-17)", "",
             f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`",
             "- Scope: direct actual `FUN_18000B150` once with reconstructed state; no natural prefill, Windows, or AE-exact claim.",
             f"- Logical backing: width `{WIDTH}`, rows allocated through `{ROWS - 1}`, invoked `[1047,1049)`.",
             "- Exact seeded cells, ABI pointers, spans/tables, and raw float32 output words are in JSON.", ""]
    if "blocker" in report:
        lines.append(f"- Blocker: `{report['blocker']}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
