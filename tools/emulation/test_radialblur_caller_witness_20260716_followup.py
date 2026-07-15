"""Bounded actual-AEX caller witness for OLMRadialBlur FUN_180004640.

The fixture is intentionally tiny: a 2x2 float RGBA world, one angular
sample, two caller rows, Repeat Border 0/1, and Size Variation disabled.
Exact-address hooks capture the constructed sampler coordinates and the
typed planes before/at the prepass, scatter, collapse, and inverse sampler.
This is a local actual-AEX witness, not an AE-exact claim.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
ENTRY = 0x180004640
SAMPLER_NON_REPEAT = 0x180001270
SAMPLER_REPEAT = 0x180001520
PREPASS = 0x180002780
SCATTER = 0x1800024C0
INVERSE = 0x180001000
PARAM1_FLOATS = 0x20000
WIDTH = HEIGHT = 2
CELL_COUNT = 2


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def f32(loader: AexLoader, address: int) -> float:
    return struct.unpack("<f", loader.read_bytes(address, 4))[0]


def floats(loader: AexLoader, address: int, count: int) -> list[float]:
    return list(struct.unpack(f"<{count}f", loader.read_bytes(address, count * 4)))


def plane_snapshot(loader: AexLoader, param1: int) -> dict[str, Any]:
    slots = {
        "plus_0x38_initial_or_collapsed_rgba": (0x0E, 4),
        "plus_0x40_scalar_prepass": (0x10, 1),
        "plus_0x48_scalar_scatter": (0x12, 1),
        "source_alpha_or_variation_plane": (0x14, 1),
        "plus_0x38_rgba_accum": (0xF250, 4),
        "initial_byte_sampler_map_later_float_scalar_collapse_plane": (0xF252, 1),
    }
    result: dict[str, Any] = {}
    for name, (index, width) in slots.items():
        pointer = u64(loader, param1 + index * 4)
        if not pointer:
            result[name] = {"pointer": None, "cells": []}
            continue
        stride = width * 4
        result[name] = {
            "pointer": hex(pointer),
            "cells": [floats(loader, pointer + cell * stride, width) for cell in range(CELL_COUNT)],
        }
    return result


def install_host_suites(loader: AexLoader) -> int:
    def new_handle(ld: AexLoader, args: list[int]) -> int:
        size = max(1, args[0] & 0xFFFFFFFFFFFFFFFF)
        data = ld.host_alloc(size, align=16)
        ld.write_bytes(data, b"\0" * size)
        handle = ld.host_alloc(8, align=8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        return handle

    def lock_handle(ld: AexLoader, args: list[int]) -> int:
        return u64(ld, args[0]) if args[0] else 0

    def noop(ld: AexLoader, args: list[int]) -> int:
        return 0

    callbacks = [
        loader.install_callback("followup.handle_new", new_handle),
        loader.install_callback("followup.handle_lock", lock_handle),
        loader.install_callback("followup.handle_unlock", noop),
        loader.install_callback("followup.handle_dispose", noop),
    ]
    suite = loader.host_alloc(32, align=8)
    loader.write_bytes(suite, struct.pack("<4Q", *callbacks))

    def acquire(ld: AexLoader, args: list[int]) -> int:
        ld.write_bytes(args[2], struct.pack("<Q", suite))
        return 0

    acquire_cb = loader.install_callback("followup.sp_acquire", acquire)
    release_cb = loader.install_callback("followup.sp_release", noop)
    spbasic = loader.host_alloc(16, align=8)
    loader.write_bytes(spbasic, struct.pack("<2Q", acquire_cb, release_cb))
    return spbasic


def world(loader: AexLoader, values: list[float]) -> int:
    data = loader.host_alloc(len(values) * 4, align=16)
    loader.write_f32_array(data, values)
    return data


def context(loader: AexLoader, spbasic: int, repeat_border: int) -> tuple[int, int, int]:
    param1 = loader.bump_alloc(PARAM1_FLOATS * 4, align=64)
    loader.write_bytes(param1, b"\0" * (PARAM1_FLOATS * 4))
    # 360 degrees gives one angular column; 0.5 quality keeps two rows alive
    # even for the 2x2 geometry after the caller's two-row trim.
    loader.write_bytes(param1, struct.pack("<f", 360.0))

    p0 = loader.host_alloc(0x200, align=16)
    loader.write_bytes(p0, b"\0" * 0x200)
    loader.write_bytes(p0 + 0x180, struct.pack("<Q", spbasic))
    geometry = loader.host_alloc(0x40, align=16)
    loader.write_bytes(geometry, b"\0" * 0x40)
    loader.write_bytes(geometry + 0x24, struct.pack("<i", WIDTH))
    loader.write_bytes(geometry + 0x28, struct.pack("<i", HEIGHT))

    # Distinct RGBA values make border and coordinate changes visible.
    source_values = [
        0.10, 0.20, 0.30, 0.80,
        0.40, 0.50, 0.60, 0.40,
        0.70, 0.80, 0.90, 0.20,
        1.00, 0.90, 0.80, 0.60,
    ]
    rgba_a = world(loader, source_values)
    rgba_b = world(loader, source_values)
    rgba_c = world(loader, source_values)
    output = world(loader, [0.0] * (WIDTH * HEIGHT * 4))

    param2 = loader.host_alloc(0x100, align=16)
    loader.write_bytes(param2, b"\0" * 0x100)
    put = lambda off, data: loader.write_bytes(param2 + off, data)
    put(0x00, struct.pack("<Q", p0))
    put(0x08, struct.pack("<Q", geometry))
    put(0x28, struct.pack("<d", 1.0))
    put(0x30, struct.pack("<d", 1.0))
    put(0x44, b"\0")
    put(0x54, struct.pack("<f", 1.0))
    put(0x58, struct.pack("<i", 1))
    put(0x5C, struct.pack("<f", 1.0))
    put(0x60, struct.pack("<i", 1))
    put(0x64, struct.pack("<i", 1))
    put(0x68, struct.pack("<i", 1))
    put(0x6C, struct.pack("<i", 1))
    put(0x70, struct.pack("<i", 1))
    put(0x74, bytes([repeat_border]))
    put(0x78, struct.pack("<f", 0.5))
    put(0x7C, struct.pack("<i", 0))
    put(0x88, struct.pack("<Q", rgba_a))
    put(0x90, struct.pack("<Q", rgba_b))
    put(0x98, struct.pack("<Q", rgba_c))
    put(0xA0, struct.pack("<Q", output))
    return param1, param2, output


def run(repeat_border: int) -> dict[str, Any]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    spbasic = install_host_suites(loader)
    param1, param2, output = context(loader, spbasic, repeat_border)
    records: dict[str, Any] = {
        "repeat_border": repeat_border,
        "size_variation": "disabled",
        "initial_planes": plane_snapshot(loader, param1),
        "sampler_calls": [],
        "prepass": [],
        "scatter": [],
        "inverse_sampler_calls": [],
    }

    def sampler_hook(ld: AexLoader, address: int, size: int) -> None:
        if not records["sampler_calls"]:
            # All caller-owned handles have been allocated by the first
            # sampler entry, while the +0x38 plane is still zero-filled.
            records["initial_planes"] = plane_snapshot(ld, param1)
        records["sampler_calls"].append({
            "entry": hex(address),
            "selected": "repeat-border" if address == SAMPLER_REPEAT else "non-repeat",
            "source": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
            "destination": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
            "width": ld.uc.reg_read(UC_X86_REG_R8),
            "height": ld.uc.reg_read(UC_X86_REG_R9),
            "x": ld.read_xmm_f32(2),
            "y": ld.read_xmm_f32(3),
        })

    def stage_hook(name: str):
        def hook(ld: AexLoader, address: int, size: int) -> None:
            records[name].append({"entry": hex(address), "planes": plane_snapshot(ld, param1)})
        return hook

    def inverse_hook(ld: AexLoader, address: int, size: int) -> None:
        records["inverse_sampler_calls"].append({
            "entry": hex(address),
            "source": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
            "destination": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
            "width": ld.uc.reg_read(UC_X86_REG_R8),
            "row_stride": ld.uc.reg_read(UC_X86_REG_R9),
            "x": ld.read_xmm_f32(2),
            "y": ld.read_xmm_f32(3),
        })

    loader.add_code_hook(SAMPLER_NON_REPEAT, sampler_hook)
    loader.add_code_hook(SAMPLER_REPEAT, sampler_hook)
    loader.add_code_hook(PREPASS, stage_hook("prepass"))
    loader.add_code_hook(SCATTER, stage_hook("scatter"))
    loader.add_code_hook(INVERSE, inverse_hook)

    try:
        result = loader.call_function(ENTRY, int_args=[param1, param2], max_instructions=5_000_000)
        records["stop"] = "return"
        records["instructions"] = result["instructions"]
    except RuntimeError as exc:
        message = str(exc)
        records["stop"] = "abi_or_emulation_fault"
        records["error"] = message
        records["rip"] = message.split("RIP=", 1)[1].split(":", 1)[0] if "RIP=" in message else None
        records["instructions"] = loader.instructions_executed

    records["final_planes"] = plane_snapshot(loader, param1)
    records["inverse_output_world"] = floats(loader, output, WIDTH * HEIGHT * 4)
    records["imports"] = sorted({entry.name for entry in loader.import_log})
    records["callbacks"] = sorted({entry[0] for entry in loader.callback_log})
    return records


def main() -> int:
    if not AEX.exists():
        raise SystemExit(f"missing AEX: {AEX}")
    runs = [run(0), run(1)]
    payload = {
        "kind": "olmradialblur_caller_witness_20260716_followup",
        "schema": 1,
        "status": "pass" if all(item["stop"] == "return" for item in runs) else "partial_typed_stage",
        "claim_boundary": "bounded actual-AEX caller witness only; no AE-exact claim",
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(), "entry": hex(ENTRY)},
        "fixture": {"width": WIDTH, "height": HEIGHT, "rgba_float": True, "size_variation": "disabled", "runs": [0, 1]},
        "runs": runs,
        "limits": [
            "The host suite, worlds, and callback ABI are synthetic local emulation fixtures.",
            "A partial run preserves the deepest typed hook/plane state and records the exact RIP error.",
            "No AE-exact, Windows-host, or production behavior claim is made.",
        ],
    }
    json_path = Path(__file__).with_name("OLMRADIALBLUR_CALLER_WITNESS_20260716_followup.json")
    md_path = Path(__file__).with_name("OLMRADIALBLUR_CALLER_WITNESS_20260716_followup.md")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMRadialBlur caller witness follow-up - 2026-07-16", "",
        f"- Status: **{payload['status']}**", "- Scope: bounded actual-AEX caller witness; no AE-exact claim.",
        f"- AEX: `{payload['binary']['path']}`", f"- SHA-256: `{payload['binary']['sha256']}`", "",
        "## Captured stages", "",
        "- Constructed sampler coordinates and selected helper for Repeat Border 0/1; this proves dispatch only, not general border semantics.",
        "- Initial `+0x38` RGBA plane, initial byte sampler map / later float scalar-collapse plane `+0xf252`, prepass/scatter scalar planes, and post-collapse `+0x38` output.",
        "- Inverse sampler calls and final synthetic output world when reached.",
        "- Size Variation is explicitly disabled in both runs.",
        "- `return` means completion at the synthetic loader return trampoline, not a native AE caller return.", "",
    ]
    for item in runs:
        lines.extend([f"## Repeat Border {item['repeat_border']}", "", f"- Stop: `{item['stop']}`", f"- Instructions: `{item['instructions']}`"])
        if item.get("rip"):
            lines.append(f"- Exact stop RIP: `{item['rip']}`")
            lines.append(f"- ABI/error: `{item['error']}`")
        lines.extend([f"- Sampler calls captured: `{len(item['sampler_calls'])}`", f"- Prepass entries: `{len(item['prepass'])}`; scatter entries: `{len(item['scatter'])}`", f"- Inverse sampler calls: `{len(item['inverse_sampler_calls'])}`", "", "```json", json.dumps({"sampler_calls": item["sampler_calls"], "prepass": item["prepass"], "scatter": item["scatter"], "final_planes": item["final_planes"], "inverse_output_world": item["inverse_output_world"]}, indent=2), "```", ""])
    lines.extend(["## Boundary", "", "- Repeat Border 0/1 proves helper dispatch only; it does not establish general border semantics.", "- `return` is synthetic-loader bounded completion, not a native AE caller-return observation.", "- This report records typed actual-AEX observations only. Synthetic suite callbacks and the loader are not AE host proof.", "- No production, ledger, or existing witness file was modified.", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
