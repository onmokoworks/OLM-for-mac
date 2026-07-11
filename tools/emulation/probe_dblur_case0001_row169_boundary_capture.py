#!/usr/bin/env python3
"""Capture the case_0001 row 169 source-959 scatter boundary.

This probe runs the real AEX rowdriver and records only the two requested
pixels.  It observes FUN_1800013e0 arguments, the state immediately after the
scatter returns, and the arrays that remain when FUN_1800038d0 returns.  The
probe is diagnostic only: it does not edit Mac sources or tune PNG output.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any

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
DEFAULT_AEX = ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"
DEFAULT_SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
DEFAULT_JSON = ROOT / "refs/conformance/olmdirectionalblur_case0001_row169_boundary_capture_20260710.json"
DEFAULT_MD = ROOT / "refs/conformance/olmdirectionalblur_case0001_row169_boundary_capture_20260710.md"

ROW = 169
SOURCE_X = 959
TARGETS = (494, 579)
FUN_ROWDRIVER = 0x1800038D0
FUN_SCATTER = 0x1800013E0
POST_SCATTER = 0x180003B60


def public_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def f32_bytes(value: float) -> bytes:
    return struct.pack("<f", float(value))


def read_vec(loader: AexLoader, address: int, count: int) -> list[float]:
    return [read_f32(loader, address + i * 4) for i in range(count)]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', f32_bytes(value))[0]:08x}"


def snapshot(loader: AexLoader, *, a: int, b: int, denom: int, valid: int,
             width: int, x: int) -> dict[str, Any]:
    index = ROW * width + x
    return {
        "A_rgba": read_vec(loader, a + index * 16, 4),
        "B_rgba": read_vec(loader, b + index * 16, 4),
        "denom": read_f32(loader, denom + index * 4),
        "alpha_or_valid": read_f32(loader, valid + index * 4),
    }


def classify(record: dict[str, Any]) -> str:
    writes = record["post_scatter"]["touched_B_channel_addresses"]
    post_rgb = record["post_scatter"]["B_rgba"][:3]
    wb_rgb = record["writeback_input"]["B_rgba"][:3]
    pre_rgba = record["pre_scatter"]["B_rgba"]
    post_rgba = record["post_scatter"]["B_rgba"]
    state_changed = any(abs(a - b) > 1e-12 for a, b in zip(pre_rgba, post_rgba))
    if not writes:
        if state_changed and record["post_scatter"]["alpha_or_valid"] > 0.0:
            return "scatter_write_zero_rgb" if all(abs(v) <= 1e-12 for v in post_rgb) else "scatter_write_nonzero_rgb"
        return "scatter_non_write"
    if record["post_scatter"]["B_buffer_identity"] != "rowdriver_B":
        return "buffer_ownership"
    if any(abs(v) > 1e-12 for v in post_rgb) and all(abs(v) <= 1e-12 for v in wb_rgb):
        return "downstream_erase"
    if all(abs(v) <= 1e-12 for v in post_rgb):
        return "scatter_write_zero_rgb"
    return "scatter_write_nonzero_rgb"


def run(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "kind": "olmdirectionalblur_case0001_row169_boundary_capture",
        "schema": 1,
        "status": "blocked",
        "platform": "Mac host / Unicorn x86-64 emulation",
        "case_id": "case_0001",
        "row_y": ROW,
        "source_x": SOURCE_X,
        "targets": [[x, ROW] for x in TARGETS],
        "functions": {
            "rowdriver": "FUN_1800038d0",
            "scatter": "FUN_1800013e0",
            "post_scatter": "FUN_180003b60",
        },
        "source_path": public_path(args.source),
        "aex_path": public_path(args.aex),
        "blocked": {"reason": "not-run", "missing": []},
        "records": [],
    }
    try:
        width, height, rgba = load_source(args.source)
        loader = AexLoader(str(args.aex), verbose=False, fast=True)
        loader.register_libm_impls(max_threads=1)
        count = width * height
        a = allocate_f32(loader, rgba)
        b = allocate_f32(loader, [0.0] * (count * 4))
        denom = allocate_f32(loader, [0.0] * count)
        valid = allocate_f32(loader, [rgba[i * 4 + 3] for i in range(count)])
        component_map, max_area = build_component_map(loader, width, height, rgba)
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
            loader.write_bytes(context + offset,
                               struct.pack("<I", value) if isinstance(value, int) else f32_bytes(value))
        for offset, value in ((0x58, table), (0x4068, back_table), (0x8080, denom),
                              (0x8088, valid), (0x8118, component_map)):
            loader.write_bytes(context + offset, struct.pack("<Q", value))

        active: dict[str, Any] | None = None
        scatter_record: dict[str, Any] | None = None

        def on_scatter_entry(ld: AexLoader, _address: int, _size: int) -> None:
            nonlocal active
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            source_x = ld.uc.reg_read(UC_X86_REG_RCX)
            row_base = ld.uc.reg_read(UC_X86_REG_RDX)
            direction = ld.uc.reg_read(UC_X86_REG_R8)
            if source_x != SOURCE_X or row_base != ROW * width or direction != 1:
                active = None
                return
            # At helper entry RSP still includes the return address, so the
            # caller's +0x20.. stack arguments appear at +0x28.. here.
            b_arg = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
            denom_arg = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
            valid_arg = struct.unpack("<Q", ld.read_bytes(rsp + 0x38, 8))[0]
            table_arg = struct.unpack("<Q", ld.read_bytes(rsp + 0x40, 8))[0]
            # These two fields are the verified caller-frame locations used by
            # the existing typed classifier.
            strength = struct.unpack("<i", ld.read_bytes(rsp + 0x48, 4))[0]
            row_width = struct.unpack("<i", ld.read_bytes(rsp + 0x50, 4))[0]
            p11 = read_f32(ld, rsp + 0x58)
            active = {
                "source_x": source_x, "row_base": row_base, "direction": direction,
                "A_pointer": a,
                "B_pointer": b_arg, "denom_pointer": denom_arg,
                "alpha_or_valid_pointer": valid_arg, "table_pointer": table_arg,
                "front_strength": strength, "width": row_width, "param_11": p11,
                "span": int(strength * p11),
                "write_event_count": 0,
                "write_address_min": None,
                "write_address_max": None,
                "write_samples_first": [],
                "write_samples_last": [],
                "target_B_writes": {x: [] for x in TARGETS},
            }
            active["pre"] = {
                x: snapshot(ld, a=a, b=b, denom=denom, valid=valid, width=width, x=x)
                for x in TARGETS
            }

        def on_write(uc, _access, address, size, _value, _user_data) -> None:
            if active is None:
                return
            active["write_event_count"] += 1
            active["write_address_min"] = address if active["write_address_min"] is None else min(active["write_address_min"], address)
            active["write_address_max"] = address + size if active["write_address_max"] is None else max(active["write_address_max"], address + size)
            sample = {"address": address, "size": size}
            if len(active["write_samples_first"]) < 8:
                active["write_samples_first"].append(sample)
            active["write_samples_last"].append(sample)
            active["write_samples_last"] = active["write_samples_last"][-8:]
            b_base = active["B_pointer"]
            if b_base <= address < b_base + count * 16:
                offset = address - b_base
                for x in TARGETS:
                    target_offset = (ROW * width + x) * 16
                    if target_offset <= offset < target_offset + 16:
                        active["target_B_writes"][x].append({
                            "offset": offset - target_offset,
                            "size": size,
                        })

        def on_post_scatter(ld: AexLoader, _address: int, _size: int) -> None:
            nonlocal active, scatter_record
            if active is None:
                return
            # The helper has restored the caller's stack frame at this point;
            # refresh the stack-passed pointers before reading the arrays.
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            active["B_pointer"] = struct.unpack("<Q", ld.read_bytes(rsp + 0x20, 8))[0]
            active["denom_pointer"] = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
            active["alpha_or_valid_pointer"] = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
            post = {}
            for x in TARGETS:
                post[x] = snapshot(ld, a=a, b=active["B_pointer"], denom=active["denom_pointer"],
                                   valid=active["alpha_or_valid_pointer"], width=width, x=x)
                post[x]["touched_B_channel_addresses"] = active["target_B_writes"][x]
                post[x]["B_buffer_identity"] = "rowdriver_B" if active["B_pointer"] == b else "other_buffer"
                post[x]["state_changed_from_source959_entry"] = any(
                    abs(before - after) > 1e-12
                    for before, after in zip(active["pre"][x]["B_rgba"], post[x]["B_rgba"])
                )
            scatter_arguments = {
                key: value
                for key, value in active.items()
                if key not in {"pre", "target_B_writes"}
            }
            scatter_record = {
                "scatter_arguments": scatter_arguments,
                "pre": active["pre"],
                "post": post,
            }
            active = None

        loader.add_code_hook(FUN_SCATTER, on_scatter_entry)
        loader.uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
        loader.add_code_hook(POST_SCATTER, on_post_scatter)
        loader.call_function(FUN_ROWDRIVER, int_args=[ROW, ROW + 1, a_ptr, b_ptr, width, 0, context], max_instructions=0)

        if scatter_record is None:
            raise RuntimeError("source 959 row 169 scatter was not captured")
        for x in TARGETS:
            post = scatter_record["post"][x]
            wb = snapshot(loader, a=a, b=b, denom=denom, valid=valid, width=width, x=x)
            record = {
                "xy": [x, ROW],
                "source": {"xy": [SOURCE_X, ROW], "rgba": read_vec(loader, a + (ROW * width + SOURCE_X) * 16, 4)},
                "rowdriver_membership": {"row_base": ROW * width, "direction": 1, "source_reached_target": True},
                "scatter_arguments": scatter_record["scatter_arguments"],
                "pre_scatter": scatter_record["pre"][x],
                "post_scatter": post,
                "writeback_input": wb,
            }
            record["classification"] = classify(record)
            record["final_stored_rgba"] = {"status": "not-observed-by-rowdriver-probe"}
            result["records"].append(record)
        result["status"] = "ok"
        result["blocked"] = None
        result["source_dimensions"] = [width, height]
    except Exception as exc:
        result["blocked"] = {"reason": type(exc).__name__, "message": str(exc),
                              "missing": ["typed scatter/post-scatter/writeback fields"]}
    return result


def render_md(result: dict[str, Any]) -> str:
    lines = ["# OLMDirectionalBlur case_0001 row169 boundary capture", "",
             f"- Status: `{result['status']}`", "- Lane: source 959 -> row 169 targets `(494,169)` and `(579,169)`", "- No Mac source or PNG tuning performed.", ""]
    if result["status"] != "ok":
        return "\n".join(lines + ["## Blocked", "", "```json", json.dumps(result["blocked"], indent=2), "```", ""])
    lines += ["## Classification", "", "| target | post B RGB | post denom | post alpha/valid | write count | writeback B RGB | classification |", "| --- | --- | ---: | ---: | ---: | --- | --- |"]
    for record in result["records"]:
        post = record["post_scatter"]
        wb = record["writeback_input"]
        lines.append(f"| `{tuple(record['xy'])}` | `{post['B_rgba'][:3]}` | {post['denom']:.9g} | {post['alpha_or_valid']:.9g} | {len(post['touched_B_channel_addresses'])} | `{wb['B_rgba'][:3]}` | `{record['classification']}` |")
    lines += ["", "## Capture Contract", "", "Each record includes the typed scatter arguments, A/B/denom/alpha_or_valid immediately after scatter, and the same arrays after FUN_1800038d0 returns. Final stored bytes are intentionally outside this rowdriver-only probe.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    result = run(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output_json": public_path(args.output_json), "output_md": public_path(args.output_md)}, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
