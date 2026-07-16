#!/usr/bin/env python3
"""Bounded case_0009 Zoom caller-collapse witness.

This is the small continuation of the 2026-07-16 reconstructed-state probe.
It uses one pinned 32x1 source row, executes the actual B150/A9D0 workers,
enters the actual FUN_1800056F0 collapse block at 0x180005c9f, stops at its
post-loop address 0x180005d96, and calls the actual D80 sampler.
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

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_radialblur_reconstructed_caller_state_20260716 as base  # noqa: E402

AEX = base.AEX
INPUT = base.INPUT
PINNED_AEX_SHA256 = base.PINNED_AEX_SHA256
PINNED_INPUT_SHA256 = base.PINNED_INPUT_SHA256
WORKER = base.WORKER
SCATTER = base.SCATTER
INVERSE_SAMPLER = base.INVERSE_SAMPLER
WIDTH = 32
HEIGHT = 1
SOURCE_ROW = 540
POINTS = (7, 8, 24)
CONTROL_POINTS = (8, 24)
RADIUS_INDEX = 7.25
ANGLE_INDEX = 0.0
COLLAPSE_ENTRY = 0x180005C9F
COLLAPSE_EXIT = 0x180005D96


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def typed_case0009_row() -> bytes:
    image = Image.open(INPUT).convert("RGBA")
    row = image.crop((0, SOURCE_ROW, WIDTH, SOURCE_ROW + 1))
    values = [base.f32(channel / 255.0) for channel in row.tobytes()]
    return struct.pack(f"<{len(values)}f", *values)


def floats(loader: Any, address: int, count: int) -> list[float]:
    return list(struct.unpack(f"<{count}f", loader.read_bytes(address, count * 4)))


def words(raw: bytes) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack(f"<{len(raw) // 4}I", raw)]


def cell(loader: Any, address: int, stride: int, x: int, count: int) -> dict[str, Any]:
    raw = loader.read_bytes(address + x * stride, count * 4)
    return {"f32": floats(loader, address + x * stride, count), "f32_words": words(raw)}


def oracle_cell(rgba: list[float], denom: float) -> list[float]:
    if denom == 0.0 or rgba[3] == 0.0:
        return [0.0, 0.0, 0.0, denom]
    return [base.f32(rgba[0] / rgba[3]), base.f32(rgba[1] / rgba[3]),
            base.f32(rgba[2] / rgba[3]), denom]


def run() -> dict[str, Any]:
    from unicorn.x86_const import (UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R12,
                                   UC_X86_REG_R14, UC_X86_REG_R15, UC_X86_REG_RBP,
                                   UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSI, UC_X86_REG_RIP,
                                   UC_X86_REG_RSP, UC_X86_REG_XMM6)

    loader = base.AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    state = base.build_state(loader, typed_case0009_row())
    pointer = state["pointers"]
    entries = {"worker": [], "scatter": [], "collapse_entry": [], "collapse_exit": [],
               "inverse_sampler": []}

    def hook(name: str, stack_count: int):
        def capture(ld: Any, _address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            entries[name].append({
                "register_args": [ld.uc.reg_read(reg) for reg in
                                  (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
                "stack_args": [base.u64(ld, rsp + 0x28 + i * 8) for i in range(stack_count)],
            })
        return capture

    loader.add_code_hook(WORKER, hook("worker", 6))
    loader.add_code_hook(SCATTER, hook("scatter", 7))
    loader.add_code_hook(INVERSE_SAMPLER, hook("inverse_sampler", 3))

    def capture_collapse_entry(ld: Any, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        entries["collapse_entry"].append({
            "rip": hex(COLLAPSE_ENTRY),
            "registers": {name: ld.uc.reg_read(reg) for name, reg in (
                ("rsi", UC_X86_REG_RSI), ("r12", UC_X86_REG_R12),
                ("r14", UC_X86_REG_R14), ("r15", UC_X86_REG_R15),
                ("rbp", UC_X86_REG_RBP), ("rsp", UC_X86_REG_RSP))},
            "return_address": hex(base.u64(ld, rsp)),
            "stack_plus_0x20": hex(base.u64(ld, rsp + 0x20)),
        })

    def capture_collapse_exit(ld: Any, _address: int, _size: int) -> None:
        entries["collapse_exit"].append({"rip": hex(COLLAPSE_EXIT), "stopped": True,
                                          "rsi": ld.uc.reg_read(UC_X86_REG_RSI),
                                          "r12": ld.uc.reg_read(UC_X86_REG_R12),
                                          "r15": ld.uc.reg_read(UC_X86_REG_R15)})
        ld.uc.emu_stop()

    loader.add_code_hook(COLLAPSE_ENTRY, capture_collapse_entry)
    loader.add_code_hook(COLLAPSE_EXIT, capture_collapse_exit)

    worker_args = [pointer["work"], pointer["source_rgba"], pointer["scalar_a"], pointer["scalar_b"],
                   WIDTH, 1, 0, 1, pointer["accum_rgba"], pointer["denom"]]
    scatter_args = [pointer["work"], pointer["source_rgba"], pointer["scalar_a"], pointer["scatter_b"],
                    pointer["scatter_c"], WIDTH, 1, 0, 1, pointer["accum_rgba"], pointer["denom"]]
    worker = loader.call_function(WORKER, int_args=worker_args, max_instructions=500_000)
    scatter = loader.call_function(SCATTER, int_args=scatter_args, max_instructions=500_000)

    # The actual block reads work+0x4210 / work+0x4218 and writes work+0x38.
    # These are the reconstructed caller's +0xf250 / +0xf252 / +0xe slots.
    pre_accum = [floats(loader, pointer["accum_rgba"] + x * 16, 4) for x in range(WIDTH)]
    pre_denom = [floats(loader, pointer["denom"] + x * 4, 1)[0] for x in range(WIDTH)]
    geometry_owner = base.alloc_zero(loader, 0x10, align=16)
    loader.write_bytes(geometry_owner + 0x08, struct.pack("<Q", pointer["geometry"]))
    loader.uc.reg_write(UC_X86_REG_RSI, pointer["work"])
    loader.uc.reg_write(UC_X86_REG_R12, 1)
    loader.uc.reg_write(UC_X86_REG_R14, geometry_owner)
    loader.uc.reg_write(UC_X86_REG_R15, WIDTH)
    loader.uc.reg_write(UC_X86_REG_RBP, loader.bump_alloc(0x100, align=16))
    loader.uc.reg_write(UC_X86_REG_XMM6, 0)
    collapse_result = loader.call_function(COLLAPSE_ENTRY, int_args=[0], max_instructions=500_000)

    records: list[dict[str, Any]] = []
    for x in POINTS:
        scalar = cell(loader, pointer["denom"], 4, x, 1)
        rgba = cell(loader, pointer["accum_rgba"], 16, x, 4)
        actual = cell(loader, pointer["final_rgba"], 16, x, 4)
        expected = oracle_cell(pre_accum[x], pre_denom[x])
        records.append({"x": x, "controls": "primary" if x == 7 else "control",
                        "+0xf252_scalar": scalar, "+0xf250_rgba": rgba,
                        "+0xe_collapsed_rgba": actual,
                        "python_oracle": {"f32": expected,
                                          "f32_words": words(struct.pack("<4f", *expected))},
                        "actual_matches_oracle": actual["f32_words"] == words(struct.pack("<4f", *expected))})

    out = loader.bump_alloc(16, align=16)
    loader.write_bytes(out, b"\0" * 16)
    d80 = loader.call_function(INVERSE_SAMPLER, int_args=[pointer["final_rgba"], out, WIDTH, HEIGHT,
                                                           WIDTH * 4, f32_bits(RADIUS_INDEX),
                                                           f32_bits(ANGLE_INDEX)], max_instructions=50_000)
    d80_raw = loader.read_bytes(out, 16)
    records[0]["FUN_180009D80"] = {"entry": hex(INVERSE_SAMPLER), "x": 7,
                                    "radius_index": RADIUS_INDEX, "angle_index": ANGLE_INDEX,
                                    "rgba_f32": list(struct.unpack("<4f", d80_raw)),
                                    "rgba_f32_words": words(d80_raw),
                                    "returned": loader.uc.reg_read(UC_X86_REG_RIP) == base.RETURN_TRAMPOLINE}
    return {"worker_instructions": worker["instructions"], "scatter_instructions": scatter["instructions"],
            "collapse_instructions": collapse_result["instructions"], "sampler_instructions": d80["instructions"],
            "entries": entries, "records": records,
            "initial_state_sha256": state["initial_sha256"],
            "typed_row_sha256": hashlib.sha256(typed_case0009_row()).hexdigest(),
            "plane_bindings": {"+0xf252_scalar": hex(pointer["denom"]),
                               "+0xf250_rgba": hex(pointer["accum_rgba"]),
                               "+0xe_collapsed_rgba": hex(pointer["final_rgba"])},
            "direct_entry_state": {"rsi_work": hex(pointer["work"]), "r12_outer_count": 1,
                                    "r14_geometry_owner": hex(geometry_owner), "r15_inner_count": WIDTH},
            "pointers": pointer}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "refs/conformance/olmradialblur_reconstructed_zoom_collapse_20260717.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "refs/conformance/olmradialblur_reconstructed_zoom_collapse_20260717.md")
    args = parser.parse_args()
    actual = {"aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
              "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest()}
    report: dict[str, Any] = {"kind": "olmradialblur_reconstructed_zoom_collapse_20260717", "schema": 1,
                              "status": "blocked", "classification": "bounded-only",
                              "claim_boundary": "Mac Unicorn actual-AEX reconstructed caller state; no AE exact, Windows, or production claim",
                              "target": {"function": "FUN_1800056F0", "collapse_entry": hex(COLLAPSE_ENTRY),
                                         "collapse_exit": hex(COLLAPSE_EXIT),
                                         "sampler": hex(INVERSE_SAMPLER)},
                              "fixture": {"case_id": "case_0009", "width": WIDTH, "height": HEIGHT,
                                          "source_row": SOURCE_ROW, "x": 7, "controls": list(CONTROL_POINTS)},
                              "provenance": {"aex_sha256": actual["aex_sha256"], "input_sha256": actual["input_sha256"],
                                             "pinned": {"aex_sha256": PINNED_AEX_SHA256, "input_sha256": PINNED_INPUT_SHA256}},
                              "run": None}
    if actual != {"aex_sha256": PINNED_AEX_SHA256, "input_sha256": PINNED_INPUT_SHA256}:
        report["blocker"] = "pinned AEX or input hash mismatch"
    else:
        report["run"] = run()
        run_data = report["run"]
        rec = run_data["records"]
        exact = rec[0]["FUN_180009D80"]["rgba_f32_words"] == rec[0]["+0xe_collapsed_rgba"]["f32_words"]
        distinct = len({tuple(item["+0xf250_rgba"]["f32_words"]) for item in rec}) > 1
        report["gates"] = {"hashes": True, "entry_counts": {k: len(v) for k, v in run_data["entries"].items()},
                            "actual_collapse_entry_exit": len(run_data["entries"]["collapse_entry"]) == 1 and len(run_data["entries"]["collapse_exit"]) == 1,
                            "controls_present": [item["x"] for item in rec] == [7, 8, 24],
                            "oracle_matches_actual": all(item["actual_matches_oracle"] for item in rec),
                            "discriminating_f250": distinct, "d80_matches_collapsed_x7": exact,
                            "all_finite": all(all(math.isfinite(v) for v in item["+0xf250_rgba"]["f32"])
                                               for item in rec)}
        report["status"] = "pass" if all(report["gates"].values()) else "blocked"
        report["classification"] = "bounded-actual-aex-collapse-proven" if report["status"] == "pass" else "bounded-gate-failure"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMRadialBlur reconstructed Zoom collapse witness (2026-07-17)", "",
             f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`",
             "- Scope: pinned Mac Unicorn execution with a reconstructed 32x1 case_0009 row; no AE-exact or Windows-equivalence claim.",
             f"- Target: `FUN_1800056F0+0x5c9f`, exact post-loop exit `0x180005d96`; sampler `FUN_180009D80`.",
             f"- Fixture: source row `{SOURCE_ROW}`, primary x=`7`, controls x=`8,24`.", ""]
    if report.get("run"):
        for item in report["run"]["records"]:
            lines.append(f"- x={item['x']}: +0xf252={item['+0xf252_scalar']['f32']}; +0xf250={item['+0xf250_rgba']['f32']}; +0xe={item['+0xe_collapsed_rgba']['f32']}.")
        lines += ["", "The collapse bytes are written by the actual AEX block; the independent oracle and x=7 D80 comparison are in JSON.", ""]
    else:
        lines += ["", f"Blocker: {report['blocker']}", ""]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    print(f"json={args.output_json}\nmd={args.output_md}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
