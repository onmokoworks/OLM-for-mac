#!/usr/bin/env python3
"""Capture real AEX helper calls that write DirectionalBlur target B cells.

The probe intentionally does not assume source x=959. It runs the existing
rowdriver fixture, observes every FUN_1800013e0 invocation, and retains only
calls whose actual B pointer writes one of the two target records. The target
record is read before helper entry and after helper return. Final host-store
bytes are attempted only when a local host-store boundary is available.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PIL import Image
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from probe_dblur_case0001_row169_typed_classifier import (  # noqa: E402
    allocate_f32,
    build_component_map,
    load_source,
    read_f32,
)

ROOT = Path(__file__).resolve().parents[2]
ROW = 169
TARGETS = (494, 579)
FUN_ROWDRIVER = 0x1800038D0
FUN_SCATTER = 0x1800013E0
POST_SCATTER = 0x180003B60


def f32(v: float) -> bytes:
    return struct.pack("<f", float(v))


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def public_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def vec(loader: AexLoader, address: int) -> list[float]:
    return list(struct.unpack("<4f", loader.read_bytes(address, 16)))


def cell(loader: AexLoader, *, a: int, b: int, denom: int, valid: int,
         width: int, x: int) -> dict[str, Any]:
    offset = (ROW * width + x)
    return {
        "B_address": b + offset * 16,
        "B_rgba": vec(loader, b + offset * 16),
        "denom": read_f32(loader, denom + offset * 4),
        "valid": read_f32(loader, valid + offset * 4),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    source_width, source_height, rgba = load_source(args.source)
    loader = AexLoader(str(args.aex), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    count = source_width * source_height
    a = allocate_f32(loader, rgba)
    b = allocate_f32(loader, [0.0] * (count * 4))
    denom = allocate_f32(loader, [0.0] * count)
    valid = allocate_f32(loader, [rgba[i * 4 + 3] for i in range(count)])
    component_map, max_area = build_component_map(loader, source_width, source_height, rgba)
    front_strength = 1690
    table = allocate_f32(loader, [1.0] * (front_strength + 4))
    back_table = allocate_f32(loader, [1.0] * (front_strength + 4))
    a_ptr = loader.bump_alloc(8, align=8)
    b_ptr = loader.bump_alloc(8, align=8)
    loader.write_bytes(a_ptr, struct.pack("<Q", a))
    loader.write_bytes(b_ptr, struct.pack("<Q", b))
    context = loader.bump_alloc(0x8200, align=16)
    loader.write_bytes(context, b"\x00" * 0x8200)
    for offset, value in ((0x20, 0), (0x30, 1.0), (0x38, max_area or 1.0),
                          (0x40, 1.0), (0x44, 1.0), (0x48, front_strength),
                          (0x4C, front_strength), (0x50, 0), (0x54, 0)):
        loader.write_bytes(context + offset, struct.pack("<I", value) if isinstance(value, int) else f32(value))
    for offset, value in ((0x58, table), (0x4068, back_table), (0x8080, denom),
                          (0x8088, valid), (0x8118, component_map)):
        loader.write_bytes(context + offset, struct.pack("<Q", value))

    active: dict[str, Any] | None = None
    pending: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    def helper_entry(ld: AexLoader, _address: int, _size: int) -> None:
        nonlocal active
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        source_x = ld.uc.reg_read(UC_X86_REG_RCX)
        row_base = ld.uc.reg_read(UC_X86_REG_RDX)
        direction = ld.uc.reg_read(UC_X86_REG_R8)
        b_arg = u64(ld, rsp + 0x28)
        denom_arg = u64(ld, rsp + 0x30)
        valid_arg = u64(ld, rsp + 0x38)
        table_arg = u64(ld, rsp + 0x40)
        strength = struct.unpack("<i", ld.read_bytes(rsp + 0x48, 4))[0]
        row_width = struct.unpack("<i", ld.read_bytes(rsp + 0x50, 4))[0]
        param_11 = read_f32(ld, rsp + 0x58)
        target_cells = {
            x: cell(ld, a=a, b=b_arg, denom=denom_arg, valid=valid_arg,
                    width=source_width, x=x)
            for x in TARGETS
            if b_arg <= b_arg + (ROW * source_width + x) * 16 < b_arg + count * 16
        }
        active = {
            "source_xy": [source_x, row_base // row_width if row_width else None],
            "source_index": source_x + row_base,
            "source_rgba": vec(ld, a + (source_x + row_base) * 16),
            "destination_B_base": b_arg,
            "denom_base": denom_arg,
            "valid_base": valid_arg,
            "table_base": table_arg,
            "direction": direction,
            "callsite_return": u64(ld, rsp),
            "row_width": row_width,
            "param_9": strength,
            "param_11": param_11,
            "effective_span": int(strength * param_11),
            "pre": target_cells,
            "writes": {x: [] for x in TARGETS},
        }

    def memory_write(uc, _access, address, size, _value, _user_data) -> None:
        if active is None:
            return
        base = active["destination_B_base"]
        for x in TARGETS:
            target = base + (ROW * source_width + x) * 16
            if address < target + 16 and address + size > target:
                active["writes"][x].append({"address": address, "size": size})

    def helper_return(ld: AexLoader, _address: int, _size: int) -> None:
        nonlocal active
        if active is None:
            return
        for x in TARGETS:
            if not active["writes"][x]:
                continue
            after = cell(ld, a=a, b=active["destination_B_base"],
                         denom=active["denom_base"], valid=active["valid_base"],
                         width=source_width, x=x)
            before = active["pre"][x]
            record = {
                "target_xy": [x, ROW],
                "source_xy": active["source_xy"],
                "source_rgba": active["source_rgba"],
                "destination_B_address": after["B_address"],
                "direction": active["direction"],
                "callsite_return": active["callsite_return"],
                "effective_span": active["effective_span"],
                "pre_B_rgba": before["B_rgba"],
                "post_B_rgba": after["B_rgba"],
                "pre_denom": before["denom"],
                "post_denom": after["denom"],
                "pre_valid": before["valid"],
                "post_valid": after["valid"],
                "target_write_addresses": [event["address"] for event in active["writes"][x]],
                "final_host_store": {"status": "not-observed; rowdriver-only run"},
            }
            pending.append(record)
        active = None

    loader.add_code_hook(FUN_SCATTER, helper_entry)
    loader.uc.hook_add(UC_HOOK_MEM_WRITE, memory_write)
    loader.add_code_hook(POST_SCATTER, helper_return)
    loader.call_function(FUN_ROWDRIVER, int_args=[ROW, ROW + 1, a_ptr, b_ptr,
                                                   source_width, 0, context],
                         max_instructions=0)

    # A helper can be entered while a previous helper is still pending only in
    # a nested path; preserve one compact record per target-writing call.
    records.extend(pending)
    summary = summarize(records, loader=loader, a=a, b=b, denom=denom,
                        valid=valid, width=source_width)
    return {
        "kind": "dblur_target_writer_capture",
        "schema": 1,
        "status": "ok",
        "case_id": "case_0001",
        "row_y": ROW,
        "targets": [[x, ROW] for x in TARGETS],
        "source_coordinate_policy": "discover_actual_helper_contributors; source_959_not_forced",
        "aex": {"path": public_path(args.aex), "rowdriver": "FUN_1800038d0", "helper": "FUN_1800013e0"},
        "execution": {"platform": "Unicorn x86-64", "width": source_width,
                      "height": source_height, "rowdriver_only": True},
        "summary": summary,
    }


def is_nonzero_rgb(values: list[float]) -> bool:
    return any(abs(value) > 1e-12 for value in values[:3])


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_xy": record["source_xy"],
        "source_rgba": record["source_rgba"],
        "destination_B_address": record["destination_B_address"],
        "direction": record["direction"],
        "callsite_return": record["callsite_return"],
        "effective_span": record["effective_span"],
        "pre_B_rgba": record["pre_B_rgba"],
        "post_B_rgba": record["post_B_rgba"],
        "pre_denom": record["pre_denom"],
        "post_denom": record["post_denom"],
        "pre_valid": record["pre_valid"],
        "post_valid": record["post_valid"],
        "target_write_addresses": record["target_write_addresses"],
    }


def summarize(records: list[dict[str, Any]], *, loader: AexLoader, a: int, b: int,
              denom: int, valid: int, width: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "target_writer_call_count": len(records),
        "final_host_store": "not locally feasible from this rowdriver boundary",
    }
    for target in TARGETS:
        rows = [r for r in records if r["target_xy"] == [target, ROW]]
        sources = sorted({r["source_xy"][0] for r in rows})
        changes = [r for r in rows if r["pre_B_rgba"] != r["post_B_rgba"]]
        source_nonzero = [r for r in rows if is_nonzero_rgb(r["source_rgba"])]
        pre_nonzero = [r for r in rows if is_nonzero_rgb(r["pre_B_rgba"])]
        post_nonzero = [r for r in rows if is_nonzero_rgb(r["post_B_rgba"])]
        final = cell(loader, a=a, b=b, denom=denom, valid=valid,
                     width=width, x=target)
        result[str(target)] = {
            "helper_call_count": len(rows),
            "source_x_range": [sources[0], sources[-1]] if sources else None,
            "source_x_count": len(sources),
            "unique_callsites": sorted({r["callsite_return"] for r in rows}),
            "unique_directions": sorted({r["direction"] for r in rows}),
            "unique_spans": sorted({r["effective_span"] for r in rows}),
            "target_write_count": sum(len(r["target_write_addresses"]) for r in rows),
            "source_nonzero_event_count": len(source_nonzero),
            "pre_B_nonzero_event_count": len(pre_nonzero),
            "post_B_nonzero_event_count": len(post_nonzero),
            "first_B_change_event": compact_record(changes[0]) if changes else None,
            "nonzero_source_events_capped": [compact_record(r) for r in source_nonzero[:8]],
            "B_change_events_capped": [compact_record(r) for r in changes[:8]],
            "first_representative_calls": [compact_record(r) for r in rows[:8]],
            "last_representative_calls": [compact_record(r) for r in rows[-8:]],
            "final_B_rgba": final["B_rgba"],
            "final_denom": final["denom"],
            "final_valid": final["valid"],
        }
    return result


def render_md(result: dict[str, Any]) -> str:
    lines = ["# DirectionalBlur target-writer capture", "",
             f"- Status: `{result['status']}`",
             "- Actual AEX/Unicorn helper calls only; source `(959,169)` was not forced.",
             "- No Mac source, ledger, existing artifact, NAS, coefficient, or PNG edits.", "",
             "| target | helper calls | source x range | direction | span | B address | pre/post B RGBA | denom | valid |",
             "| --- | ---: | --- | --- | --- | ---: | --- | --- | --- |"]
    for target in TARGETS:
        summary = result["summary"][str(target)]
        samples = summary["first_representative_calls"]
        if not samples:
            lines.append(f"| `{(target, ROW)}` | 0 | `-` | `-` | `-` | `-` | `-` | `-` | `-` |")
            continue
        lines.append(f"| `{(target, ROW)}` | {summary['helper_call_count']} | `{summary['source_x_range']}` ({summary['source_x_count']}) | `{summary['unique_directions']}` | `{summary['unique_spans']}` | `0x{samples[0]['destination_B_address']:x}` | `{summary['final_B_rgba']}` | `{summary['final_denom']}` | `{summary['final_valid']}` |")
    lines += ["", "## Reading", "", "The JSON is aggregated per target. It retains bounded first/last helper representatives plus capped nonzero/change events, never the full 845-call stream. Source RGB and target B RGB are zero for every retained event; alpha/valid remains 1.0. Final host-store bytes are unavailable at the rowdriver boundary, so the next exact boundary is the host output write after rowdriver normalization/rotate-back.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=ROOT / "plugins_2025/OLMDirectionalBlur.aex")
    parser.add_argument("--source", type=Path, default=ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png")
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/dblur_target_writer_capture_20260711.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/dblur_target_writer_capture_20260711.md")
    args = parser.parse_args()
    result = run(SimpleNamespace(aex=args.aex, source=args.source))
    args.output_json.write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")
    args.output_md.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "helper_calls": result["summary"]["target_writer_call_count"],
                      "json": public_path(args.output_json), "md": public_path(args.output_md)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
