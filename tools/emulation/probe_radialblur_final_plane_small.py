#!/usr/bin/env python3
"""Stop the real OLMRadialBlur AEX immediately after Zoom normalization.

This is deliberately a small, emulator-first probe.  It runs the direct Zoom
core on a bounded 32x32 geometry, stops at the first instruction after the normalization
loop (0x180005d99), and records the four planes that are live in the AEX work
object.  It does not replace prefill or worker calls with synthetic data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_zoom_case0009 import (  # noqa: E402
    FUN_180005A00,
    FUN_180005BA2,
    FUN_1800056F0,
    FUN_180008690,
    FUN_18000A7E0,
    FUN_18000A800,
    FUN_18000A810,
    FUN_18000A9D0,
    FUN_18000B150,
    build_host_suites,
    build_param_block,
    build_render_context,
    build_world,
    call_zoom_inverse,
    load_case_params,
    prepare_direct_zoom_context,
    python_prefill_zoom_polar_planes,
    read_f32,
    read_rgba_cell,
    read_scalar_cell,
    sample_final_plane,
    u64,
    u32,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"
DEFAULT_MANIFEST = REPO_ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur" / "reference_manifest.json"
DEFAULT_INPUT = REPO_ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur" / "case_0009_before_effects.png"
NORMALIZATION_AFTER = 0x180005D99


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aex-path", type=Path, default=DEFAULT_AEX)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--input-png", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--case-id", default="case_0009")
    p.add_argument("--source-x", type=int, default=0, help="Top-left source crop X for the bounded direct geometry.")
    p.add_argument("--source-y", type=int, default=0, help="Top-left source crop Y for the bounded direct geometry.")
    p.add_argument("--width", type=int, default=32, help="Bounded direct geometry width.")
    p.add_argument("--height", type=int, default=32, help="Bounded direct geometry height.")
    p.add_argument("--max-instructions", type=int, default=2_000_000)
    p.add_argument("--output-json", type=Path, default=Path("/tmp/olmradialblur_final_plane_small.json"))
    p.add_argument("--detour-prepass", action="store_true", help="Replace FUN_18000b150 with a no-op diagnostic detour.")
    p.add_argument("--detour-scatter", action="store_true", help="Replace FUN_18000a9d0 with a no-op diagnostic detour.")
    p.add_argument("--python-prefill", action="store_true", help="Use the existing decomp-grounded Python prefill for diagnostic comparison.")
    return p.parse_args()


def rgba(loader: AexLoader, plane: int, radial: int, angle: int, radius: int) -> list[float]:
    return [float(v) for v in read_rgba_cell(loader, plane, radial, angle, radius)]


def scalar(loader: AexLoader, plane: int, radial: int, angle: int, radius: int) -> float:
    return float(read_scalar_cell(loader, plane, radial, angle, radius))


def blocked(path: Path, reason: str, facts: dict[str, Any]) -> int:
    report = {
        "kind": "olmradialblur_final_plane_small_probe",
        "schema": 1,
        "status": "blocked",
        "classification": "blocked-normalized-work-geometry-unreadable",
        "normalization_hook": "0x180005d99_after_0x180005d96_normalization_boundary",
        "geometry_requested": facts.get("geometry_requested", {"width": 32, "height": 32}),
        "reason": reason,
        "facts": facts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote_json={path}")
    print(f"status=blocked reason={reason}")
    return 2


def main() -> int:
    options = args()
    if not options.aex_path.exists():
        return blocked(options.output_json, "AEX file is missing", {"aex": str(options.aex_path)})
    if not options.manifest.exists() or not options.input_png.exists():
        return blocked(options.output_json, "manifest or input image is missing", {
            "manifest": str(options.manifest), "input_png": str(options.input_png),
        })

    from PIL import Image
    from unicorn.x86_const import (
        UC_X86_REG_R12, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX,
        UC_X86_REG_RDI, UC_X86_REG_RDX, UC_X86_REG_RIP, UC_X86_REG_R15,
        UC_X86_REG_RSI, UC_X86_REG_RSP,
    )

    params = load_case_params(options.manifest, options.case_id)
    image = Image.open(options.input_png).convert("RGBA")
    if options.width <= 0 or options.height <= 0:
        return blocked(options.output_json, "bounded geometry dimensions must be positive", {
            "geometry_requested": {"width": options.width, "height": options.height},
        })
    source = image.crop((options.source_x, options.source_y,
                         options.source_x + options.width, options.source_y + options.height))
    if source.size != (options.width, options.height):
        return blocked(options.output_json, "requested source crop is outside the input", {
            "source_xy": [options.source_x, options.source_y], "input_size": list(image.size),
            "geometry_requested": {"width": options.width, "height": options.height},
        })
    input_bytes = Image.merge("RGBA", tuple(source.getchannel(c) for c in ("A", "R", "G", "B"))).tobytes()
    host_input_bytes = Image.merge("RGBA", tuple(image.getchannel(c) for c in ("A", "R", "G", "B"))).tobytes()
    output_bytes = bytes(image.width * image.height * 4)

    loader = AexLoader(str(options.aex_path), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    suites = build_host_suites(loader)
    render_ctx = build_render_context(loader, suites)
    input_world = build_world(loader, image.width, image.height, host_input_bytes)
    output_world = build_world(loader, image.width, image.height, output_bytes)
    param_ctx = build_param_block(loader)
    # The reader detours are part of the existing case runner's host setup.
    from test_m4_case0010 import install_reader_detours  # noqa: E402
    install_reader_detours(loader, params)
    # Populate the real AEX parameter context before entering the direct core.
    # Omitting this setup leaves the center/strength fields host-uninitialized;
    # the resulting polar cells can look valid while both workers write nothing.
    loader.call_function(FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    state: dict[str, Any] = {
        "hook_hits": 0, "work": 0, "param": 0, "rdi_at_hook": 0, "rsi_at_hook": 0,
        "angle_count": 0, "radial_count": 0, "prefill": None,
        "prepass_calls": 0, "scatter_calls": 0, "prepass_detours": 0, "scatter_detours": 0,
        "worker_snapshot": None, "b150_records": [],
    }

    def after_normalization(ld: AexLoader, address: int, size: int) -> None:
        state["hook_hits"] += 1
        # The direct call owns these pointers.  Registers at this boundary are
        # loop temporaries, so do not infer the work object from them.
        state["rdi_at_hook"] = int(ld.uc.reg_read(UC_X86_REG_RDI))
        state["rsi_at_hook"] = int(ld.uc.reg_read(UC_X86_REG_RSI))
        state["min_at_hook"] = struct.unpack("<i", ld.read_bytes(work + 0x18, 4))[0]
        state["max_at_hook"] = struct.unpack("<i", ld.read_bytes(work + 0x1C, 4))[0]
        ld.uc.emu_stop()

    loader.add_code_hook(NORMALIZATION_AFTER, after_normalization)
    direct_context = prepare_direct_zoom_context(
        loader, param_ctx, render_ctx, input_world, output_world, source,
        (options.width, options.height)
    )
    work = loader.bump_alloc(0x4300, align=64)
    loader.write_bytes(work, b"\x00" * 0x4300)
    loader.call_function(FUN_18000A7E0, int_args=[work], max_instructions=10_000)
    strength = read_f32(loader, param_ctx + 0x80)
    loader.call_function(FUN_18000A810, int_args=[work], float_args={1: (strength, "f")}, max_instructions=10_000)
    loader.write_bytes(work + 0x10, struct.pack("<f", 90.0))
    state["work"] = work
    state["param"] = param_ctx

    def ensure_one_worker(ld: AexLoader, address: int, size: int) -> None:
        if u32(ld, work + 0x4220) <= 0:
            ld.write_bytes(work + 0x4220, struct.pack("<I", 1))

    loader.add_code_hook(0x18000573B, ensure_one_worker)

    def prefill_and_skip(ld: AexLoader, address: int, size: int) -> None:
        angle_count = int(ld.uc.reg_read(UC_X86_REG_R12)) & 0xFFFFFFFF
        radial_raw = int(ld.uc.reg_read(UC_X86_REG_R15)) & 0xFFFFFFFF
        # The high bit is carried as a direct-core sentinel/flag in this small
        # geometry. The allocated cell count is the low 31-bit value.
        radial_count = radial_raw & 0x7FFFFFFF
        if angle_count <= 1 or radial_count <= 1 or angle_count * radial_count > 100_000:
            raise RuntimeError(f"invalid prefill geometry angle={angle_count} radial={radial_count}")
        cells = angle_count * radial_count
        min_radius_raw = u32(ld, work + 0x18)
        min_radius_fixup = None
        if options.width <= 4 and (radial_raw & 0x80000000) and not (min_radius_raw & 0x80000000):
            signed_min_raw = min_radius_raw | 0x80000000
            ld.write_bytes(work + 0x18, struct.pack("<I", signed_min_raw))
            min_radius_fixup = {
                "before_u32": min_radius_raw,
                "sign_source": "radial_count_raw_high_bit",
                "after_i32": struct.unpack("<i", struct.pack("<I", signed_min_raw))[0],
            }
        byte_plane = ld.bump_alloc(cells, align=64)
        ld.write_bytes(byte_plane, b"\x01" * cells)
        geometry = u64(ld, param_ctx + 0x08)
        width = u32(ld, geometry + 0x24)
        height = u32(ld, geometry + 0x28)
        state["angle_count"] = angle_count
        state["radial_count"] = radial_count
        state["radial_count_raw"] = radial_raw
        state["min_radius_fixup"] = min_radius_fixup
        if not options.python_prefill:
            return
        state["prefill"] = python_prefill_zoom_polar_planes(
            ld, work, param_ctx, byte_plane, angle_count, radial_count, width, height
        )
        ld.uc.reg_write(UC_X86_REG_RDI, byte_plane)
        ld.uc.reg_write(UC_X86_REG_RIP, FUN_180005BA2)

    def detour_prepass(ld: AexLoader, int_args: list[int]) -> int:
        state["prepass_detours"] += 1
        return 0

    def detour_scatter(ld: AexLoader, int_args: list[int]) -> int:
        state["scatter_detours"] += 1
        return 0

    loader.add_code_hook(FUN_180005A00, prefill_and_skip)
    def capture_b150_inputs(ld: AexLoader, address: int, size: int) -> None:
        state["prepass_calls"] += 1
        if len(state["b150_records"]) >= 4:
            return

        # FUN_18000b150 uses the Windows x64 ABI: RCX..R9 are arguments 1..4,
        # followed by six integer/pointer arguments at RSP+0x28..0x50.
        rsp = int(ld.uc.reg_read(UC_X86_REG_RSP))
        args = [
            int(ld.uc.reg_read(UC_X86_REG_RCX)),
            int(ld.uc.reg_read(UC_X86_REG_RDX)),
            int(ld.uc.reg_read(UC_X86_REG_R8)),
            int(ld.uc.reg_read(UC_X86_REG_R9)),
        ]
        args.extend(u64(ld, rsp + offset) for offset in (0x28, 0x30, 0x38, 0x40, 0x48, 0x50))
        context, source, scalar_a, scalar_b = args[:4]
        width, row_limit, row_start, row_end, output_rgba, output_scalar = args[4:]

        record: dict[str, Any] = {
            "call_index": len(state["b150_records"]),
            "abi": {
                "context": context, "source_rgba": source,
                "scalar_a": scalar_a, "scalar_b": scalar_b,
                "width": width, "row_limit": row_limit,
                "row_start": row_start, "row_end": row_end,
                "output_rgba": output_rgba, "output_scalar": output_scalar,
            },
            "context_fields": {},
            "rows": [],
        }
        try:
            record["context_fields"] = {
                "left_span_i32": struct.unpack("<i", ld.read_bytes(context + 0x4200, 4))[0],
                "right_span_i32": struct.unpack("<i", ld.read_bytes(context + 0x4204, 4))[0],
                "left_table": u64(ld, context + 0x3ee0),
                "right_table": u64(ld, context + 0x4070),
            }
            base_index = width * row_start
            # Capture the first four work pixels of this call. This keeps the
            # report small while retaining exact source/scalar words for replay.
            for i in range(min(width, 4)):
                src_ptr = source + (base_index + i) * 16
                a_ptr = scalar_a + (base_index + i) * 4
                b_ptr = scalar_b + (base_index + i) * 4
                record["rows"].append({
                    "index": base_index + i,
                    "source_rgba_f32": [read_f32(ld, src_ptr + 4 * channel) for channel in range(4)],
                    "scalar_a_f32": read_f32(ld, a_ptr),
                    "scalar_b_f32": read_f32(ld, b_ptr),
                })
        except Exception as exc:
            record["read_error"] = str(exc)
        state["b150_records"].append(record)

    loader.add_code_hook(FUN_18000B150, capture_b150_inputs)

    def snapshot_worker_outputs(ld: AexLoader, address: int, size: int) -> None:
        state["scatter_calls"] += 1
        if state["worker_snapshot"] is not None:
            return
        radial = int(state.get("radial_count", 0))
        angles = int(state.get("angle_count", 0))
        if radial <= 0 or angles <= 0:
            return
        pointers = {
            "valid": u64(ld, work + 10 * 8),
            "accum": u64(ld, work + 0x842 * 8),
            "denom": u64(ld, work + 0x843 * 8),
        }
        rows = []
        for angle in range(angles):
            for radius in range(radial):
                av = rgba(ld, pointers["accum"], radial, angle, radius)
                dv = scalar(ld, pointers["denom"], radial, angle, radius)
                vv = scalar(ld, pointers["valid"], radial, angle, radius)
                if dv != 0.0 or vv != 0.0 or any(v != 0.0 for v in av):
                    rows.append({"angle_idx": angle, "radius_idx": radius,
                                 "accum_rgba_f32": av, "denom_f32": dv, "valid_f32": vv})
                    if len(rows) == 4:
                        break
            if len(rows) == 4:
                break
        state["worker_snapshot"] = {
            "stage": "at-scatter-entry-after-prepass",
            "informative_cell_count": len(rows),
            "records": rows,
        }

    loader.add_code_hook(FUN_18000A9D0, snapshot_worker_outputs)
    if options.detour_prepass:
        loader.detour_function(FUN_18000B150, "RadialBlur.Zoom.b150.noop", detour_prepass)
    if options.detour_scatter:
        loader.detour_function(FUN_18000A9D0, "RadialBlur.Zoom.a9d0.noop", detour_scatter)

    start = time.time()
    fault = ""
    try:
        result = loader.call_function(FUN_1800056F0, int_args=[work, param_ctx], max_instructions=options.max_instructions)
    except Exception as exc:  # A fault before the exact boundary is a blocked probe.
        fault = str(exc)
        result = {"instructions": loader.instructions_executed}
    elapsed = time.time() - start
    if state["hook_hits"] != 1:
        return blocked(options.output_json, "normalization boundary was not reached", {
            "hook_hits": state["hook_hits"], "fault": fault,
            "instructions": result.get("instructions", 0), "rip": f"0x{loader.uc.reg_read(UC_X86_REG_RIP):x}",
        })

    work = state["work"]
    try:
        final = u64(loader, work + 7 * 8)
        valid = u64(loader, work + 10 * 8)
        accum = u64(loader, work + 0x842 * 8)
        denom = u64(loader, work + 0x843 * 8)
        min_radius = struct.unpack("<i", loader.read_bytes(work + 0x18, 4))[0]
        max_radius_plus = struct.unpack("<i", loader.read_bytes(work + 0x1C, 4))[0]
        radial = int(state.get("radial_count", 0))
        quality = read_f32(loader, work + 0x10)
        angle_step = read_f32(loader, work + 0x14)
        angle_count = int(state.get("angle_count", 0))
        if not all((final, valid, accum, denom)) or radial <= 0 or angle_count <= 1:
            raise RuntimeError("one or more normalized work pointers or dimensions are invalid")
        all_records = []
        for angle in range(angle_count):
            for radius in range(radial):
                row = {
                    "angle_idx": angle,
                    "radius_idx": radius,
                    "final_rgba_f32": rgba(loader, final, radial, angle, radius),
                    "accum_rgba_f32": rgba(loader, accum, radial, angle, radius),
                    "denom_f32": scalar(loader, denom, radial, angle, radius),
                    "valid_f32": scalar(loader, valid, radial, angle, radius),
                }
                all_records.append(row)
        informative = [
            row for row in all_records
            if row["denom_f32"] != 0.0 or row["valid_f32"] != 0.0 or
               any(value != 0.0 for value in row["accum_rgba_f32"])
        ]
        selected = (informative or all_records)[:4]
        records = [dict(row, cell=index) for index, row in enumerate(selected)]
        cells = [[row["angle_idx"], row["radius_idx"]] for row in selected]
        plane_stats = {
            "cell_count": len(all_records),
            "informative_cell_count": len(informative),
            "nonzero_denom_count": sum(row["denom_f32"] != 0.0 for row in all_records),
            "nonzero_valid_count": sum(row["valid_f32"] != 0.0 for row in all_records),
            "nonzero_accum_count": sum(any(value != 0.0 for value in row["accum_rgba_f32"]) for row in all_records),
        }
        plane_hashes = {
            "final_rgba_f32": hashlib.sha256(loader.read_bytes(final, radial * angle_count * 16)).hexdigest(),
            "accum_rgba_f32": hashlib.sha256(loader.read_bytes(accum, radial * angle_count * 16)).hexdigest(),
            "denom_f32": hashlib.sha256(loader.read_bytes(denom, radial * angle_count * 4)).hexdigest(),
            "valid_f32": hashlib.sha256(loader.read_bytes(valid, radial * angle_count * 4)).hexdigest(),
        }
        output_samples = []
        for output_x, output_y in ((7, 0), (8, 0), (24, 0)):
            radius_raw, angle_raw = call_zoom_inverse(loader, work, float(output_x), float(output_y))
            angle_index = (angle_raw / angle_step) % float(angle_count)
            radius_index = radius_raw - float(min_radius)
            ri0 = int(radius_index)
            if ri0 < 0 or ri0 + 1 >= radial:
                output_samples.append({
                    "xy": [output_x, output_y],
                    "radius_raw": radius_raw,
                    "angle_raw": angle_raw,
                    "radius_index": radius_index,
                    "angle_index": angle_index,
                    "status": "out-of-bounds-radius",
                })
                continue
            sample = sample_final_plane(
                loader, final, radial, angle_count, radius_index, angle_index)
            output_samples.append({
                "xy": [output_x, output_y],
                "radius_raw": radius_raw,
                "angle_raw": angle_raw,
                "radius_index": radius_index,
                "angle_index": angle_index,
                "status": "sampled",
                "sample": sample,
            })
    except Exception as exc:
        return blocked(options.output_json, f"normalized work pointers could not be read: {exc}", {
            "hook_hits": state["hook_hits"], "work": work, "fault": fault,
            "rsi_at_hook": state["rsi_at_hook"],
            "min_at_hook": state.get("min_at_hook"), "max_at_hook": state.get("max_at_hook"),
            "raw_pointers": {"final": locals().get("final"), "valid": locals().get("valid"),
                             "accum": locals().get("accum"), "denom": locals().get("denom")},
            "dimensions": {"radial": locals().get("radial"), "angle_count": locals().get("angle_count"),
                           "prefill_radial_count": state.get("radial_count"),
                           "prefill_angle_count": state.get("angle_count")},
            "work_fields": {"min_radius": locals().get("min_radius"), "max_radius_plus": locals().get("max_radius_plus"),
                            "quality": locals().get("quality"), "angle_step": locals().get("angle_step")},
        })

    workers_real = not options.detour_prepass and not options.detour_scatter
    nonzero = plane_stats["informative_cell_count"] > 0
    if workers_real and nonzero:
        classification = "aex-normalization-boundary-small-witness"
    elif not nonzero:
        classification = "blocked-aex-workers-produced-no-typed-cell"
    else:
        classification = "aex-normalization-boundary-plane-layout-witness"
    report = {
        "kind": "olmradialblur_final_plane_small_probe", "schema": 1, "status": "ok",
        "classification": classification,
        "case_id": options.case_id, "geometry": {"width": options.width, "height": options.height, "radial_count": radial, "angle_count": angle_count,
                                                    "source": "live_r15_r12_at_prefill_boundary"},
        "source_crop_xywh": [options.source_x, options.source_y, options.width, options.height],
        "normalization_hook": "0x180005d99_after_0x180005d96_normalization_boundary",
        "elapsed_seconds": elapsed, "instructions": result.get("instructions", 0), "fault": fault,
        "pointers": {"work": work, "final_param_1_7": final, "accum_param_1_0x842": accum,
                     "denom_param_1_0x843": denom, "valid_param_1_10": valid},
        "plane_types": {"final": "rgba_f32", "accum": "rgba_f32", "denom": "f32", "valid": "f32"},
        "sample_geometry": {
            "selection": "first-informative-polar-cells",
            "cells": cells,
            "warning": "Not mapped to case_0009 output coordinates; this proves small-plane ownership/layout only.",
        },
        "records": records,
        "b150_input_capture": state["b150_records"],
        "bounded_output_samples": output_samples,
        "plane_stats": plane_stats,
        "plane_sha256": plane_hashes,
        "hook_registers": {"rdi": state["rdi_at_hook"]},
        "direct_context": direct_context,
        "prefill": state["prefill"],
        "prefill_mode": "python-repeat-border" if options.python_prefill else "actual-aex",
        "harness_fixups": {"min_radius": state.get("min_radius_fixup")},
        "worker_execution": {
            "prepass": "detoured" if options.detour_prepass else "actual-aex",
            "scatter": "detoured" if options.detour_scatter else "actual-aex",
            "prepass_calls": state["prepass_calls"],
            "scatter_calls": state["scatter_calls"],
            "prepass_detour_calls": state["prepass_detours"],
            "scatter_detour_calls": state["scatter_detours"],
            "post_prepass_snapshot": state["worker_snapshot"],
        },
    }
    if not nonzero:
        report["status"] = "blocked"
        report["reason"] = "real AEX prepass/scatter completed but no typed cell was written"
        report["failure"] = {
            "code": "AEX_WORKER_NO_TYPED_WRITE",
            "prepass_calls": state["prepass_calls"],
            "scatter_calls": state["scatter_calls"],
            "detoured": bool(options.detour_prepass or options.detour_scatter),
            "effective_geometry": {"radial_count": radial, "angle_count": angle_count},
            "worker_snapshot": state["worker_snapshot"],
            "hint": "Increase bounded width/height until the real worker effective span exceeds its strict >1 write gate; do not seed accum/denom/valid.",
        }
    options.output_json.parent.mkdir(parents=True, exist_ok=True)
    options.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote_json={options.output_json}")
    print(f"status={report['status']} classification={classification}")
    print(f"hook=0x{NORMALIZATION_AFTER:x} records={len(records)}")
    return 2 if report["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
