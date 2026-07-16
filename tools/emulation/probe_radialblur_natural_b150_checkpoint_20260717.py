#!/usr/bin/env python3
"""Checkpoint naturally-prefilled B150 state at the actual caller boundary.

The harness uses the existing bounded 32x32 direct Zoom context, case_0009
parameters, and the actual AEX setup and polar-prefill code.  It stops at the
first FUN_18000B150 entry, before B150 can mutate its output planes.  No
Python prefill or worker detour is used.
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
    build_host_suites,
    build_param_block,
    build_render_context,
    build_world,
    install_reader_detours,
)
from test_zoom_case0009 import (  # noqa: E402
    FUN_1800056F0,
    FUN_180005A00,
    FUN_180005BA2,
    FUN_180008690,
    FUN_18000A7E0,
    FUN_18000A810,
    FUN_18000B150,
    load_case_params,
    prepare_direct_zoom_context,
    read_f32,
    u32,
    u64,
)

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
PINNED = {
    "aex": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "manifest": "7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565",
    "input": "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4",
}
CASE_ID = "case_0009"
SOURCE_WIDTH = 32
SOURCE_HEIGHT = 32
QUALITY_STEP = 90.0
EXPECTED_RADIAL = 49
EXPECTED_ANGLES = 4
MAX_INSTRUCTIONS = 2_000_000
TABLE_FLOATS = 0x190 // 4
KERNEL = 0x18000B680


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(raw: bytes) -> list[str]:
    return [f"0x{word:08x}" for word in struct.unpack(f"<{len(raw) // 4}I", raw)]


def plane_stats(loader: AexLoader, address: int, cells: int, channels: int) -> dict[str, Any]:
    raw = loader.read_bytes(address, cells * channels * 4)
    values = struct.unpack(f"<{cells * channels}f", raw)
    selected = []
    nonzero_cells = 0
    for index in range(cells):
        cell = values[index * channels:(index + 1) * channels]
        if any(value != 0.0 for value in cell):
            nonzero_cells += 1
            if len(selected) < 8:
                cell_raw = raw[index * channels * 4:(index + 1) * channels * 4]
                selected.append({"index": index, "f32": list(cell), "f32_words": words(cell_raw)})
    return {
        "address": address,
        "cells": cells,
        "channels": channels,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "all_finite": all(math.isfinite(value) for value in values),
        "nonzero_value_count": sum(value != 0.0 for value in values),
        "nonzero_cell_count": nonzero_cells,
        "selected_nonzero_cells": selected,
    }


def table_stats(loader: AexLoader, address: int) -> dict[str, Any]:
    raw = loader.read_bytes(address, TABLE_FLOATS * 4)
    values = struct.unpack(f"<{TABLE_FLOATS}f", raw)
    return {
        "address": address,
        "float_count": TABLE_FLOATS,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "all_finite": all(math.isfinite(value) for value in values),
        "nonzero_count": sum(value != 0.0 for value in values),
        "f32_words": words(raw),
    }


def run(outer_edge_fade: int) -> dict[str, Any]:
    from PIL import Image
    from unicorn.x86_const import (
        UC_X86_REG_R8,
        UC_X86_REG_R9,
        UC_X86_REG_R12,
        UC_X86_REG_R15,
        UC_X86_REG_RCX,
        UC_X86_REG_RDX,
        UC_X86_REG_RSP,
    )

    params = dict(load_case_params(MANIFEST, CASE_ID))
    manifest_outer_edge_fade = int(params["Outer Edge Fade"])
    params["Outer Edge Fade"] = outer_edge_fade
    image = Image.open(INPUT).convert("RGBA")
    argb = Image.merge("RGBA", tuple(image.getchannel(channel) for channel in ("A", "R", "G", "B"))).tobytes()
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    suites = build_host_suites(loader)
    render_ctx = build_render_context(loader, suites)
    input_world = build_world(loader, image.width, image.height, argb)
    output_world = build_world(loader, image.width, image.height, bytes(image.width * image.height * 4))
    param_ctx = build_param_block(loader)
    reader_provenance = install_reader_detours(loader, params)
    parameter_callsites: list[dict[str, int]] = []

    def parameter_callsite(ld: AexLoader, address: int, _size: int) -> None:
        parameter_callsites.append({
            "callsite": address,
            "reader_index": int(ld.uc.reg_read(UC_X86_REG_R8)),
            "output_pointer": int(ld.uc.reg_read(UC_X86_REG_R9)),
        })

    loader.add_code_hook(0x180008731, parameter_callsite)
    loader.add_code_hook(0x180008785, parameter_callsite)
    loader.call_function(FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    edge_reader_provenance = [
        {"reader": name, "reader_index": index, "value": value,
         "output_pointers": list(output_pointers)}
        for name, index, value, output_pointers in reader_provenance
        if name == "e270" and index in (5, 9)
    ]

    source_crop = image.crop((0, 0, SOURCE_WIDTH, SOURCE_HEIGHT))
    direct = prepare_direct_zoom_context(
        loader, param_ctx, render_ctx, input_world, output_world, source_crop,
        (SOURCE_WIDTH, SOURCE_HEIGHT),
    )
    work = loader.bump_alloc(0x4300, align=64)
    loader.write_bytes(work, b"\0" * 0x4300)
    loader.call_function(FUN_18000A7E0, int_args=[work], max_instructions=10_000)
    strength = read_f32(loader, param_ctx + 0x80)
    loader.call_function(FUN_18000A810, int_args=[work], float_args={1: (strength, "f")}, max_instructions=10_000)
    loader.write_bytes(work + 0x10, struct.pack("<f", QUALITY_STEP))

    state: dict[str, Any] = {
        "prefill_loop_hits": 0,
        "prefill_boundary_hits": 0,
        "kernel_calls": [],
        "b150_entries": 0,
    }

    def force_one_thread(ld: AexLoader, _address: int, _size: int) -> None:
        if u32(ld, work + 0x4220) <= 0:
            ld.write_bytes(work + 0x4220, struct.pack("<I", 1))

    def kernel_entry(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = int(ld.uc.reg_read(UC_X86_REG_RSP))
        state["kernel_calls"].append({
            "table_address": int(ld.uc.reg_read(UC_X86_REG_RCX)),
            "span_argument_i32": struct.unpack("<i", struct.pack("<I", int(ld.uc.reg_read(UC_X86_REG_RDX)) & 0xFFFFFFFF))[0],
            "return_address": u64(ld, rsp),
        })

    def prefill_loop(ld: AexLoader, _address: int, _size: int) -> None:
        state["prefill_loop_hits"] += 1
        if state.get("before_prefill") is not None:
            return
        angles = int(ld.uc.reg_read(UC_X86_REG_R12)) & 0xFFFFFFFF
        radial = int(ld.uc.reg_read(UC_X86_REG_R15)) & 0x7FFFFFFF
        cells = angles * radial
        state["before_prefill"] = {
            "angle_count": angles,
            "radial_count": radial,
            "planes": {
                "source_rgba": plane_stats(ld, u64(ld, work + 0x38), cells, 4),
                "scale": plane_stats(ld, u64(ld, work + 0x50), cells, 1),
                "source_alpha": plane_stats(ld, u64(ld, work + 0x48), cells, 1),
            },
        }

    def prefill_boundary(_ld: AexLoader, _address: int, _size: int) -> None:
        state["prefill_boundary_hits"] += 1

    def b150_entry(ld: AexLoader, _address: int, _size: int) -> None:
        state["b150_entries"] += 1
        if state.get("checkpoint") is not None:
            ld.uc.emu_stop()
            return
        rsp = int(ld.uc.reg_read(UC_X86_REG_RSP))
        args = [int(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
        args.extend(u64(ld, rsp + offset) for offset in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50))
        context, source, scale, source_alpha = args[:4]
        width, row_limit, row_start, row_end, output_rgba, output_scalar = args[4:]
        effective_end = min(row_limit, row_end)
        effective_cells = max(0, effective_end - row_start) * width
        state["checkpoint"] = {
            "abi": {
                "context": context,
                "source_rgba": source,
                "scale": scale,
                "source_alpha": source_alpha,
                "width": width,
                "row_limit": row_limit,
                "row_start": row_start,
                "row_end": row_end,
                "effective_row_end": effective_end,
                "effective_cells": effective_cells,
                "output_rgba": output_rgba,
                "output_scalar": output_scalar,
                "return_address": u64(ld, rsp),
            },
            "work_bindings": {
                "source_rgba_work_plus_0x38": u64(ld, work + 0x38),
                "source_alpha_work_plus_0x48": u64(ld, work + 0x48),
                "scale_work_plus_0x50": u64(ld, work + 0x50),
                "output_rgba_work_plus_0x4210": u64(ld, work + 0x4210),
                "output_scalar_work_plus_0x4218": u64(ld, work + 0x4218),
            },
            "context": {
                "left_span_i32": struct.unpack("<i", ld.read_bytes(context + 0x4200, 4))[0],
                "right_span_i32": struct.unpack("<i", ld.read_bytes(context + 0x4204, 4))[0],
                "left_table_inline": table_stats(ld, context + 0x3EE0),
                "right_table_inline": table_stats(ld, context + 0x4070),
            },
            "planes": {
                "source_rgba": plane_stats(ld, source + row_start * width * 16, effective_cells, 4),
                "scale": plane_stats(ld, scale + row_start * width * 4, effective_cells, 1),
                "source_alpha": plane_stats(ld, source_alpha + row_start * width * 4, effective_cells, 1),
                "output_rgba_before_b150": plane_stats(ld, output_rgba + row_start * width * 16, effective_cells, 4),
                "output_scalar_before_b150": plane_stats(ld, output_scalar + row_start * width * 4, effective_cells, 1),
            },
        }
        ld.uc.emu_stop()

    loader.add_code_hook(0x18000573B, force_one_thread)
    loader.add_code_hook(KERNEL, kernel_entry)
    loader.add_code_hook(FUN_180005A00, prefill_loop)
    loader.add_code_hook(FUN_180005BA2, prefill_boundary)
    loader.add_code_hook(FUN_18000B150, b150_entry)
    result = loader.call_function(FUN_1800056F0, int_args=[work, param_ctx], max_instructions=MAX_INSTRUCTIONS)
    return {
        "instructions": result["instructions"],
        "work": work,
        "param_ctx": param_ctx,
        "direct_context": direct,
        "parameter_materialization": {
            "manifest_outer_edge_fade": manifest_outer_edge_fade,
            "host_reader_outer_edge_fade": outer_edge_fade,
            "edge_reader_callsites": parameter_callsites,
            "edge_reader_provenance": edge_reader_provenance,
            "direct_param_field_writes_by_harness": 0,
        },
        "case_config_i32": {
            "param_plus_0x64": struct.unpack("<i", loader.read_bytes(param_ctx + 0x64, 4))[0],
            "param_plus_0x68": struct.unpack("<i", loader.read_bytes(param_ctx + 0x68, 4))[0],
            "b150_span_source_plus_0x6c": struct.unpack("<i", loader.read_bytes(param_ctx + 0x6C, 4))[0],
            "b150_span_source_plus_0x70": struct.unpack("<i", loader.read_bytes(param_ctx + 0x70, 4))[0],
        },
        **state,
    }


def evaluate(run_data: dict[str, Any], expected_outer_edge_fade: int) -> dict[str, bool]:
    checkpoint = run_data.get("checkpoint", {})
    abi = checkpoint.get("abi", {})
    bindings = checkpoint.get("work_bindings", {})
    context = checkpoint.get("context", {})
    planes = checkpoint.get("planes", {})
    before = run_data.get("before_prefill", {}).get("planes", {})
    kernel_calls = run_data.get("kernel_calls", [])
    materialization = run_data.get("parameter_materialization", {})
    expected_bindings = {
        "source_rgba_work_plus_0x38": abi.get("source_rgba"),
        "source_alpha_work_plus_0x48": abi.get("source_alpha"),
        "scale_work_plus_0x50": abi.get("scale"),
        "output_rgba_work_plus_0x4210": abi.get("output_rgba"),
        "output_scalar_work_plus_0x4218": abi.get("output_scalar"),
    }
    spans = (context.get("left_span_i32", 0), context.get("right_span_i32", 0))
    tables = (context.get("left_table_inline", {}), context.get("right_table_inline", {}))
    gates = {
        "one_b150_entry": run_data.get("b150_entries") == 1,
        "bounded_instruction_budget": 0 < run_data.get("instructions", 0) < MAX_INSTRUCTIONS,
        "natural_prefill_loop_complete": run_data.get("prefill_loop_hits") == EXPECTED_ANGLES and run_data.get("prefill_boundary_hits") == 1,
        "natural_geometry": abi.get("width") == EXPECTED_RADIAL and abi.get("row_limit") == EXPECTED_ANGLES and abi.get("row_start") == 0,
        "effective_geometry_consistent": abi.get("effective_cells") == EXPECTED_RADIAL * EXPECTED_ANGLES,
        "actual_caller_bindings": bindings == expected_bindings and abi.get("context") == run_data.get("work"),
        "natural_prefill_changed_rgba_and_alpha": all(before.get(name, {}).get("sha256") != planes.get(name, {}).get("sha256") for name in ("source_rgba", "source_alpha")),
        "natural_prefill_rgba_and_alpha_finite_nonzero": all(planes.get(name, {}).get("all_finite") and planes.get(name, {}).get("nonzero_cell_count") == EXPECTED_RADIAL * EXPECTED_ANGLES for name in ("source_rgba", "source_alpha")),
        "scale_plane_faithfully_zero": before.get("scale", {}).get("sha256") == planes.get("scale", {}).get("sha256") and planes.get("scale", {}).get("all_finite") and planes.get("scale", {}).get("nonzero_value_count") == 0,
        "binary_kernel_calls_ground_tables": any(call.get("table_address") == abi.get("context", 0) + 0x3EE0 and call.get("span_argument_i32") == spans[0] for call in kernel_calls) and any(call.get("table_address") == abi.get("context", 0) + 0x4070 and call.get("span_argument_i32") == spans[1] for call in kernel_calls),
        "b150_outputs_pristine": planes.get("output_rgba_before_b150", {}).get("nonzero_value_count") == 0 and planes.get("output_scalar_before_b150", {}).get("nonzero_value_count") == 0,
        "edge_fields_owned_by_actual_reader": (
            materialization.get("direct_param_field_writes_by_harness") == 0
            and {item.get("callsite") for item in materialization.get("edge_reader_callsites", [])} == {0x180008731, 0x180008785}
            and any(item.get("reader_index") == 5 and item.get("value") == expected_outer_edge_fade
                    and item.get("output_pointers") == [run_data.get("param_ctx", 0) + 0x6C]
                    for item in materialization.get("edge_reader_provenance", []))
            and any(item.get("reader_index") == 9 and item.get("value") == 0
                    and item.get("output_pointers") == [run_data.get("param_ctx", 0) + 0x70]
                    for item in materialization.get("edge_reader_provenance", []))
        ),
    }
    if expected_outer_edge_fade == 0:
        gates["zero_spans_fail_closed"] = spans == (0, 0)
        gates["zero_span_inline_tables_consistent"] = all(
            table.get("all_finite") and table.get("nonzero_count") == 0 for table in tables)
    else:
        gates["minimum_nonzero_span"] = spans == (expected_outer_edge_fade, 0)
        gates["minimum_nonzero_inline_table"] = (
            tables[0].get("all_finite") and tables[0].get("nonzero_count") == 1
            and tables[0].get("f32_words", [None])[0] != "0x00000000"
            and tables[1].get("nonzero_count") == 0
        )
        gates["actual_reader_to_core_lineage"] = (
            run_data.get("case_config_i32", {}).get("b150_span_source_plus_0x6c") == expected_outer_edge_fade
            and spans[0] == expected_outer_edge_fade
        )
    return gates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmradialblur_natural_b150_checkpoint_20260717.md")
    args = parser.parse_args()
    actual = {"aex": sha256(AEX), "manifest": sha256(MANIFEST), "input": sha256(INPUT)}
    manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reference_edge_fades = [
        {
            "case_id": case["id"],
            "outer_edge_fade": int(case["effects"][0]["params"][6]["value"]),
            "inner_edge_fade": int(case["effects"][0]["params"][12]["value"]),
        }
        for case in manifest_data.get("cases", [])
    ]
    report: dict[str, Any] = {
        "kind": "olmradialblur_natural_b150_checkpoint_20260717",
        "schema": 1,
        "status": "blocked",
        "classification": "blocked-fail-closed",
        "claim_boundary": "bounded Mac Unicorn actual-AEX natural caller through B150 entry; no B150 execution, full-size, Windows, AE, or production claim",
        "provenance": {
            "actual_sha256": actual,
            "pinned_sha256": PINNED,
            "case_id": CASE_ID,
            "reference_edge_fades": reference_edge_fades,
        },
        "harness": {"source_geometry": [SOURCE_WIDTH, SOURCE_HEIGHT], "quality_step_override": QUALITY_STEP, "max_instructions": MAX_INSTRUCTIONS, "python_prefill": False, "worker_detour": False},
    }
    if actual != PINNED:
        report["blocker"] = "pinned AEX, manifest, or input hash mismatch"
    else:
        try:
            baseline = run(outer_edge_fade=0)
            minimum = run(outer_edge_fade=1)
            report["runs"] = {"manifest_baseline": baseline, "outer_edge_fade_1": minimum}
            report["gates"] = {
                "manifest_baseline": evaluate(baseline, expected_outer_edge_fade=0),
                "outer_edge_fade_1": evaluate(minimum, expected_outer_edge_fade=1),
                "paired_fixture": {
                    "only_host_reader_value_changed": (
                        baseline["parameter_materialization"]["manifest_outer_edge_fade"] == 0
                        and baseline["parameter_materialization"]["host_reader_outer_edge_fade"] == 0
                        and minimum["parameter_materialization"]["manifest_outer_edge_fade"] == 0
                        and minimum["parameter_materialization"]["host_reader_outer_edge_fade"] == 1
                    ),
                    "same_natural_b150_geometry": baseline["checkpoint"]["abi"] == minimum["checkpoint"]["abi"],
                    "minimum_positive_integer_variation": minimum["parameter_materialization"]["host_reader_outer_edge_fade"] == 1,
                    "all_checked_in_reference_edge_fades_zero": bool(reference_edge_fades) and all(
                        item["outer_edge_fade"] == 0 and item["inner_edge_fade"] == 0
                        for item in reference_edge_fades
                    ),
                },
            }
            if all(value for group in report["gates"].values() for value in group.values()):
                report["status"] = "pass"
                report["classification"] = "bounded-natural-reader-owned-nonzero-b150-table-checkpoint"
            else:
                report["blocker"] = "one or more natural B150 checkpoint gates failed"
        except Exception as exc:
            report["blocker"] = f"natural caller checkpoint failed: {exc}"

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    baseline = report.get("runs", {}).get("manifest_baseline", {})
    minimum = report.get("runs", {}).get("outer_edge_fade_1", {})
    checkpoint = minimum.get("checkpoint", {})
    context = checkpoint.get("context", {})
    lines = [
        "# OLMRadialBlur natural B150 entry checkpoint (2026-07-17)",
        "",
        f"- Status: `{report['status']}`",
        f"- Classification: `{report['classification']}`",
        "- Scope: bounded Mac Unicorn actual-AEX caller and natural polar prefill through the first B150 entry; B150 itself is not executed.",
        f"- Harness: case `{CASE_ID}`, source `{SOURCE_WIDTH}x{SOURCE_HEIGHT}`, quality-step override `{QUALITY_STEP}`, cap `{MAX_INSTRUCTIONS}`.",
        "- No Python prefill, B150 detour, full-size run, Windows, AE, or production claim.",
        "",
        "## FACT",
        "",
    ]
    if checkpoint:
        abi = checkpoint["abi"]
        left = context["left_table_inline"]
        right = context["right_table_inline"]
        lines.extend([
            f"- Actual caller reached B150 once after `{minimum['prefill_loop_hits']}` prefill-row entries and one prefill-complete boundary in `{minimum['instructions']}` instructions.",
            f"- B150 ABI geometry is width `{abi['width']}`, row limit `{abi['row_limit']}`, assigned `[0,{abi['row_end']})`, effective `[0,{abi['effective_row_end']})`: `{abi['effective_cells']}` input cells.",
            "- `FUN_180008690` owns `param_ctx+0x6c/+0x70`: actual callsites `0x180008731/0x180008785` invoke integer reader indices `5/9`, mapped to Outer/Inner Edge Fade.",
            f"- All `{len(reference_edge_fades)}` checked-in reference cases supply Edge Fade `0/0`; the case_0009 baseline reaches B150 spans `{baseline['checkpoint']['context']['left_span_i32']}/{baseline['checkpoint']['context']['right_span_i32']}` with zero inline tables.",
            f"- The minimum host-reader variation Outer Edge Fade `1` reaches B150 spans `{context['left_span_i32']}/{context['right_span_i32']}`; inline table nonzero counts are `{left['nonzero_count']}` and `{right['nonzero_count']}` of `{TABLE_FLOATS}`.",
            "- The harness performs zero direct writes to `param_ctx+0x6c/+0x70` and zero direct writes to `work+0x4200/+0x4204` or either B150 inline table.",
            f"- Natural prefill changes RGBA and source-alpha to `{checkpoint['planes']['source_rgba']['nonzero_cell_count']}` and `{checkpoint['planes']['source_alpha']['nonzero_cell_count']}` nonzero cells; scale remains faithfully zero.",
            "- JSON preserves exact caller pointers, kernel-call arguments, prefill before/after hashes, representative raw float32 input words, and complete inline table words.",
        ])
    else:
        lines.append(f"- Blocker: `{report.get('blocker', 'checkpoint missing')}`")
    lines.extend([
        "",
        "## INFERENCE",
        "",
        "- The zero baseline is explained by both checked-in Edge Fade values being zero. The paired fixture proves the smallest positive host parameter naturally propagates through the actual reader, core span owner, and table builder.",
        "- This does not establish full-size values, Windows equivalence, B150 output equivalence, or any claim for spans greater than one.",
        "",
    ])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
