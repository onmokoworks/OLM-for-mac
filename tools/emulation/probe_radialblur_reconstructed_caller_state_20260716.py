#!/usr/bin/env python3
"""Bounded OLMRadialBlur worker/scatter witness with reconstructed caller state.

This Mac-only probe enters the checked-in AEX worker, scatter, and inverse
sampler directly.  It is deliberately limited to one 32-cell float32 row and
does not execute the known full-size caller path.
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
from test_zoom_case0009 import sample_final_plane  # noqa: E402

AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
INPUT = ROOT / "refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png"
PINNED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
PINNED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"

WORKER = 0x18000B150
SCATTER = 0x18000A9D0
INVERSE_SAMPLER = 0x180009D80
WIDTH = 32
HEIGHT = 1
ROW_LIMIT = 1
ROW_START = 0
ROW_END = 1
INSTRUCTION_BUDGET = 2_000_000
RADIUS_INDEX = 7.25
ANGLE_INDEX = 0.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f32(value)))[0]


def words(raw: bytes) -> list[str]:
    return [f"0x{value:08x}" for value in struct.unpack(f"<{len(raw) // 4}I", raw)]


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def alloc_zero(loader: AexLoader, size: int, align: int = 64) -> int:
    pointer = loader.bump_alloc(size, align=align)
    loader.write_bytes(pointer, b"\0" * size)
    return pointer


def typed_crop() -> bytes:
    from PIL import Image

    image = Image.open(INPUT).convert("RGBA")
    crop = image.crop((0, 0, WIDTH, HEIGHT))
    if crop.size != (WIDTH, HEIGHT):
        raise RuntimeError(f"crop geometry mismatch: {crop.size}")
    values = [f32(channel / 255.0) for channel in crop.tobytes()]
    return struct.pack(f"<{len(values)}f", *values)


def build_state(loader: AexLoader, crop_bytes: bytes) -> dict[str, Any]:
    work = alloc_zero(loader, 0x4300)
    param = alloc_zero(loader, 0x100)
    geometry = alloc_zero(loader, 0x40)
    source = alloc_zero(loader, WIDTH * 16)
    scalar_a = alloc_zero(loader, WIDTH * 4)
    scalar_b = alloc_zero(loader, WIDTH * 4)
    scatter_b = alloc_zero(loader, WIDTH * 4)
    scatter_c = alloc_zero(loader, WIDTH * 4)
    accum = alloc_zero(loader, WIDTH * 16)
    denom = alloc_zero(loader, WIDTH * 4)
    final = alloc_zero(loader, WIDTH * 16)

    loader.write_bytes(source, crop_bytes)
    loader.write_bytes(scalar_b, struct.pack(f"<{WIDTH}f", *([1.0] * WIDTH)))
    loader.write_bytes(geometry + 0x24, struct.pack("<ii", WIDTH, HEIGHT))
    loader.write_bytes(param + 0x08, struct.pack("<Q", geometry))
    loader.write_bytes(param + 0x98, struct.pack("<Q", source))

    # Zoom work-object bindings documented by the caller-collapse contract.
    loader.write_bytes(work + 0x38, struct.pack("<Q", final))
    loader.write_bytes(work + 0x50, struct.pack("<Q", scalar_a))
    loader.write_bytes(work + 0x4210, struct.pack("<Q", accum))
    loader.write_bytes(work + 0x4218, struct.pack("<Q", denom))

    pointers = {
        "work": work, "param": param, "geometry": geometry, "source_rgba": source,
        "scalar_a": scalar_a, "scalar_b": scalar_b, "scatter_b": scatter_b,
        "scatter_c": scatter_c, "accum_rgba": accum, "denom": denom, "final_rgba": final,
    }
    regions = {
        "work": (work, 0x4300), "param": (param, 0x100), "geometry": (geometry, 0x40),
        "source_rgba": (source, WIDTH * 16), "scalar_a": (scalar_a, WIDTH * 4),
        "scalar_b": (scalar_b, WIDTH * 4), "scatter_b": (scatter_b, WIDTH * 4),
        "scatter_c": (scatter_c, WIDTH * 4), "accum_rgba": (accum, WIDTH * 16),
        "denom": (denom, WIDTH * 4), "final_rgba": (final, WIDTH * 16),
    }
    initial = b"".join(loader.read_bytes(pointer, size) for pointer, size in regions.values())
    return {"pointers": pointers, "regions": regions, "initial_sha256": hashlib.sha256(initial).hexdigest()}


def capture_plane(loader: AexLoader, rgba_pointer: int, scalar_pointer: int) -> dict[str, Any]:
    rgba_raw = loader.read_bytes(rgba_pointer, WIDTH * 16)
    scalar_raw = loader.read_bytes(scalar_pointer, WIDTH * 4)
    values = struct.unpack(f"<{WIDTH * 4}f", rgba_raw) + struct.unpack(f"<{WIDTH}f", scalar_raw)
    return {
        "rgba_sha256": hashlib.sha256(rgba_raw).hexdigest(),
        "scalar_sha256": hashlib.sha256(scalar_raw).hexdigest(),
        "all_finite": all(math.isfinite(value) for value in values),
    }


def collapse(loader: AexLoader, accum: int, denom: int, final: int) -> None:
    output: list[float] = []
    for cell in range(WIDTH):
        rgba = struct.unpack("<4f", loader.read_bytes(accum + cell * 16, 16))
        alpha = struct.unpack("<f", loader.read_bytes(denom + cell * 4, 4))[0]
        if alpha == 0.0 or rgba[3] == 0.0:
            output.extend((0.0, 0.0, 0.0, alpha))
        else:
            output.extend((f32(rgba[0] / rgba[3]), f32(rgba[1] / rgba[3]),
                           f32(rgba[2] / rgba[3]), alpha))
    loader.write_bytes(final, struct.pack(f"<{WIDTH * 4}f", *output))


def run_side(side: str, crop_bytes: bytes) -> dict[str, Any]:
    from unicorn.x86_const import (
        UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RIP,
        UC_X86_REG_RSP,
    )

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    state = build_state(loader, crop_bytes)
    pointer = state["pointers"]
    calls: dict[str, list[dict[str, Any]]] = {"worker": [], "scatter": [], "inverse_sampler": []}
    noop_calls = 0

    def entry_hook(name: str, stack_count: int):
        def hook(ld: AexLoader, _address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            calls[name].append({
                "register_args": [ld.uc.reg_read(reg) for reg in
                                  (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
                "stack_args": [u64(ld, rsp + 0x28 + index * 8) for index in range(stack_count)],
                "return_address": f"0x{u64(ld, rsp):x}",
            })
        return hook

    loader.add_code_hook(WORKER, entry_hook("worker", 6))
    loader.add_code_hook(SCATTER, entry_hook("scatter", 7))
    loader.add_code_hook(INVERSE_SAMPLER, entry_hook("inverse_sampler", 3))

    if side == "noop":
        def no_op(_loader: AexLoader, _args: list[int]) -> int:
            nonlocal noop_calls
            noop_calls += 1
            return 0
        loader.detour_function(WORKER, "RadialBlur.reconstructed.b150.noop", no_op)

    worker_args = [pointer["work"], pointer["source_rgba"], pointer["scalar_a"], pointer["scalar_b"],
                   WIDTH, ROW_LIMIT, ROW_START, ROW_END, pointer["accum_rgba"], pointer["denom"]]
    scatter_args = [pointer["work"], pointer["source_rgba"], pointer["scalar_a"], pointer["scatter_b"],
                    pointer["scatter_c"], WIDTH, ROW_LIMIT, ROW_START, ROW_END,
                    pointer["accum_rgba"], pointer["denom"]]
    before = capture_plane(loader, pointer["accum_rgba"], pointer["denom"])
    worker_result = loader.call_function(WORKER, int_args=worker_args, max_instructions=500_000)
    worker_returned = loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    after_worker = capture_plane(loader, pointer["accum_rgba"], pointer["denom"])
    scatter_result = loader.call_function(SCATTER, int_args=scatter_args, max_instructions=500_000)
    scatter_returned = loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    after_scatter = capture_plane(loader, pointer["accum_rgba"], pointer["denom"])

    collapse(loader, pointer["accum_rgba"], pointer["denom"], pointer["final_rgba"])
    portable = sample_final_plane(loader, pointer["final_rgba"], WIDTH, HEIGHT, RADIUS_INDEX, ANGLE_INDEX)
    actual_out = alloc_zero(loader, 16, align=16)
    sampler_result = loader.call_function(
        INVERSE_SAMPLER,
        int_args=[pointer["final_rgba"], actual_out, WIDTH, HEIGHT, WIDTH * 4,
                  f32_bits(RADIUS_INDEX), f32_bits(ANGLE_INDEX)],
        max_instructions=50_000,
    )
    sampler_returned = loader.uc.reg_read(UC_X86_REG_RIP) == RETURN_TRAMPOLINE
    actual_raw = loader.read_bytes(actual_out, 16)
    portable_raw = struct.pack("<4f", *portable["sample_float"])
    final_raw = loader.read_bytes(pointer["final_rgba"], WIDTH * 16)
    total_instructions = sum(result["instructions"] for result in
                             (worker_result, scatter_result, sampler_result))
    bindings = {
        "work_plus_0x38_final": u64(loader, pointer["work"] + 0x38),
        "work_plus_0x50_scalar_a": u64(loader, pointer["work"] + 0x50),
        "work_plus_0x4210_accum": u64(loader, pointer["work"] + 0x4210),
        "work_plus_0x4218_denom": u64(loader, pointer["work"] + 0x4218),
        "param_plus_0x08_geometry": u64(loader, pointer["param"] + 0x08),
        "param_plus_0x98_source": u64(loader, pointer["param"] + 0x98),
    }
    context_fields = {
        "left_table": u64(loader, pointer["work"] + 0x3EE0),
        "right_table": u64(loader, pointer["work"] + 0x4070),
        "left_span_i32": struct.unpack("<i", loader.read_bytes(pointer["work"] + 0x4200, 4))[0],
        "right_span_i32": struct.unpack("<i", loader.read_bytes(pointer["work"] + 0x4204, 4))[0],
    }
    return {
        "side": side,
        "initial_state_sha256": state["initial_sha256"],
        "pointers": pointer,
        "bindings": bindings,
        "context_fields": context_fields,
        "entry_captures": calls,
        "returns": {"worker": int(worker_returned), "scatter": int(scatter_returned),
                    "inverse_sampler": int(sampler_returned)},
        "noop_detour_calls": noop_calls,
        "instructions": {
            "worker": worker_result["instructions"], "scatter": scatter_result["instructions"],
            "inverse_sampler": sampler_result["instructions"], "total": total_instructions,
            "budget": INSTRUCTION_BUDGET,
        },
        "planes": {"before": before, "after_worker": after_worker, "after_scatter": after_scatter,
                   "final_sha256": hashlib.sha256(final_raw).hexdigest(),
                   "final_all_finite": all(math.isfinite(v) for v in struct.unpack(f"<{WIDTH * 4}f", final_raw))},
        "sample": {
            "radius_index": RADIUS_INDEX, "angle_index": ANGLE_INDEX,
            "actual_f32": list(struct.unpack("<4f", actual_raw)),
            "actual_f32_words": words(actual_raw),
            "portable": portable,
            "portable_f32_words": words(portable_raw),
            "exact_float32_words": actual_raw == portable_raw,
        },
    }


def evaluate(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    provenance = report.get("provenance", {})
    if provenance.get("aex_sha256") != PINNED_AEX_SHA256:
        issues.append("binary_hash_mismatch")
    if provenance.get("input_sha256") != PINNED_INPUT_SHA256:
        issues.append("input_hash_mismatch")
    geometry = report.get("geometry", {})
    if geometry != {"width": WIDTH, "height": HEIGHT, "row_start": ROW_START, "row_end": ROW_END}:
        issues.append("geometry_or_row_slice_mismatch")
    runs = report.get("runs", [])
    if len(runs) != 2 or {run.get("side") for run in runs} != {"live", "noop"}:
        return issues + ["live_noop_pair_missing"]
    live = next(run for run in runs if run["side"] == "live")
    noop = next(run for run in runs if run["side"] == "noop")
    if live.get("initial_state_sha256") != noop.get("initial_state_sha256"):
        issues.append("initial_state_not_byte_identical")
    for run in runs:
        pointers = run.get("pointers", {})
        bindings = run.get("bindings", {})
        expected = {
            "work_plus_0x38_final": pointers.get("final_rgba"),
            "work_plus_0x50_scalar_a": pointers.get("scalar_a"),
            "work_plus_0x4210_accum": pointers.get("accum_rgba"),
            "work_plus_0x4218_denom": pointers.get("denom"),
            "param_plus_0x08_geometry": pointers.get("geometry"),
            "param_plus_0x98_source": pointers.get("source_rgba"),
        }
        if not all(isinstance(value, int) and value > 0 and value % 16 == 0 for value in pointers.values()):
            issues.append(f"{run['side']}:invalid_pointer")
        if bindings != expected:
            issues.append(f"{run['side']}:pointer_binding_mismatch")
        captures = run.get("entry_captures", {})
        if any(len(captures.get(name, [])) != 1 for name in ("worker", "scatter", "inverse_sampler")):
            issues.append(f"{run['side']}:entry_count_mismatch")
        else:
            worker_capture = captures["worker"][0]
            scatter_capture = captures["scatter"][0]
            sampler_capture = captures["inverse_sampler"][0]
            expected_worker = {
                "register_args": [pointers["work"], pointers["source_rgba"], pointers["scalar_a"], pointers["scalar_b"]],
                "stack_args": [WIDTH, ROW_LIMIT, ROW_START, ROW_END, pointers["accum_rgba"], pointers["denom"]],
            }
            expected_scatter = {
                "register_args": [pointers["work"], pointers["source_rgba"], pointers["scalar_a"], pointers["scatter_b"]],
                "stack_args": [pointers["scatter_c"], WIDTH, ROW_LIMIT, ROW_START, ROW_END,
                               pointers["accum_rgba"], pointers["denom"]],
            }
            if any(worker_capture.get(key) != value for key, value in expected_worker.items()):
                issues.append(f"{run['side']}:worker_abi_state_mismatch")
            if any(scatter_capture.get(key) != value for key, value in expected_scatter.items()):
                issues.append(f"{run['side']}:scatter_abi_state_mismatch")
            sampler_regs = sampler_capture.get("register_args", [])
            expected_sampler_stack = [WIDTH * 4, f32_bits(RADIUS_INDEX), f32_bits(ANGLE_INDEX)]
            if (len(sampler_regs) != 4 or sampler_regs[0] != pointers["final_rgba"] or
                    not isinstance(sampler_regs[1], int) or sampler_regs[1] <= 0 or
                    sampler_regs[2:] != [WIDTH, HEIGHT] or
                    sampler_capture.get("stack_args") != expected_sampler_stack):
                issues.append(f"{run['side']}:inverse_sampler_abi_state_mismatch")
        if run.get("context_fields") != {
                "left_table": 0, "right_table": 0, "left_span_i32": 0, "right_span_i32": 0}:
            issues.append(f"{run['side']}:context_state_mismatch")
        if run.get("returns") != {"worker": 1, "scatter": 1, "inverse_sampler": 1}:
            issues.append(f"{run['side']}:return_count_mismatch")
        expected_noop = 1 if run["side"] == "noop" else 0
        if run.get("noop_detour_calls") != expected_noop:
            issues.append(f"{run['side']}:noop_count_mismatch")
        if run.get("instructions", {}).get("total", INSTRUCTION_BUDGET + 1) > INSTRUCTION_BUDGET:
            issues.append(f"{run['side']}:instruction_budget_exceeded")
        planes = run.get("planes", {})
        if not all(planes.get(stage, {}).get("all_finite") for stage in ("before", "after_worker", "after_scatter")):
            issues.append(f"{run['side']}:nonfinite_worker_plane")
        if not planes.get("final_all_finite"):
            issues.append(f"{run['side']}:nonfinite_final_plane")
        if not run.get("sample", {}).get("exact_float32_words"):
            issues.append(f"{run['side']}:portable_sampler_word_mismatch")
    if live["planes"]["after_worker"]["rgba_sha256"] == noop["planes"]["after_worker"]["rgba_sha256"]:
        issues.append("worker_live_noop_not_discriminating")
    if live["planes"]["after_scatter"]["rgba_sha256"] == noop["planes"]["after_scatter"]["rgba_sha256"]:
        issues.append("scatter_output_live_noop_not_discriminating")
    if live["sample"]["actual_f32_words"] == noop["sample"]["actual_f32_words"]:
        issues.append("inverse_sample_live_noop_not_discriminating")
    return sorted(set(issues))


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur reconstructed caller-state witness", "",
        f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`",
        "- Scope: bounded Mac Unicorn execution of the checked-in AEX; no AE-exact claim.",
        f"- Geometry: `{WIDTH}x{HEIGHT}`, row slice `[{ROW_START}, {ROW_END})`.", "",
        "## Actual-binary facts", "",
    ]
    for run in report["runs"]:
        sample = run["sample"]
        lines.append(
            f"- `{run['side']}`: worker/scatter/sampler entries `1/1/1`, instructions "
            f"`{run['instructions']['total']}`, actual words `{sample['actual_f32_words']}`, "
            f"portable exact `{sample['exact_float32_words']}`."
        )
    lines.extend([
        "", "## Gates", "", f"- Issues: `{report['issues']}`",
        "- Live and no-op data state hashes are byte-identical before entry.",
        "- The no-op side replaces only B150; A9D0 and D80 remain actual checked-in code.", "",
        "## Boundary", "",
        "The final-plane collapse is the documented bounded caller operation over the actual worker/scatter planes. "
        "This witness does not execute the full-size path, compare Windows, or establish AE exactness.", "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "refs/conformance/olmradialblur_reconstructed_caller_state_witness_20260716.json")
    parser.add_argument("--output-md", type=Path,
                        default=ROOT / "refs/conformance/olmradialblur_reconstructed_caller_state_witness_20260716.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    actual_aex = sha256(AEX) if AEX.exists() else None
    actual_input = sha256(INPUT) if INPUT.exists() else None
    report: dict[str, Any] = {
        "kind": "olmradialblur_reconstructed_caller_state_witness_20260716",
        "schema": 1,
        "claim_boundary": "bounded actual-AEX worker/scatter/sampler evidence only; never AE exact",
        "provenance": {"aex_path": str(AEX.relative_to(ROOT)), "aex_sha256": actual_aex,
                       "input_path": str(INPUT.relative_to(ROOT)), "input_sha256": actual_input},
        "entries": {"worker": hex(WORKER), "scatter": hex(SCATTER), "inverse_sampler": hex(INVERSE_SAMPLER)},
        "geometry": {"width": WIDTH, "height": HEIGHT, "row_start": ROW_START, "row_end": ROW_END},
        "runs": [],
    }
    if actual_aex == PINNED_AEX_SHA256 and actual_input == PINNED_INPUT_SHA256:
        crop_bytes = typed_crop()
        report["typed_crop_sha256"] = hashlib.sha256(crop_bytes).hexdigest()
        report["runs"] = [run_side("live", crop_bytes), run_side("noop", crop_bytes)]
    report["issues"] = evaluate(report)
    report["status"] = "pass" if not report["issues"] else "fail"
    report["classification"] = (
        "bounded-reconstructed-caller-state-proven" if not report["issues"]
        else "bounded-reconstructed-caller-state-failed"
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    print(f"json={args.output_json}\nmd={args.output_md}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
