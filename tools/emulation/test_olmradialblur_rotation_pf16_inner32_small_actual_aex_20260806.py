#!/usr/bin/env python3
"""Bounded actual-AEX Rotation PF16 9x7 Inner Strength=32 fixture."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_m4_case0010 as m4  # noqa: E402
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as base  # noqa: E402
from aex_loader import AexLoader  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP,
)

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf16_inner32_small_actual_aex_20260806.json"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_rotation_pf16_inner32_small_20260806"
OWNER = 0x180006D10
ROTATION_RETURN = 0x18000733A
B150 = 0x18000B150
A9D0 = 0x18000A9D0
PREPASS = 0x180002780
SCATTER = 0x1800024C0
W, H, ROWBYTES = 9, 7, 80
CELLS = 1800 * 9
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_KEY_HASHES = {
    "post_b150_pre_a9d0__prepass_alpha": "4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c",
    "post_normalize__accum_rgba": "d12cf7c4be728b8440ade07490e32c13370e7afa5e363b274179462a68cf6364",
    "post_normalize__max_alpha": "1753e6370c8c0bd8a1877ad2aa046b2b747a3e49a54b771e75990c00e5324fa1",
    "post_normalize__polar_rgba": "c01d5d840243e9a4b87ed93330f177a2298cabf90711ec03d55523bea0677834",
    "final_rgba": "8a5df2b125c892a972ba60bae4c1da5498dc36eef2f5dc898dc29ec135c4c91c",
    "output": "4861bfd510e5cd8deff80bc1d6bf542e04dc9dc15bd532815ade7bf83a01c8a9",
}
ZERO_INNER_OUTPUT_SHA256 = "2f6d2242202f22b82cc91d73923974d5432187af5b6b4a9b9bbee7989105f055"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def plane_pointers(loader: AexLoader, work: int) -> dict[str, int]:
    return {
        "polar_rgba": m4.u64(loader, work + 0xE * 4),
        "span_gate": m4.u64(loader, work + 0x10 * 4),
        "prepass_alpha": m4.u64(loader, work + 0x12 * 4),
        "factor": m4.u64(loader, work + 0x14 * 4),
        "accum_rgba": m4.u64(loader, work + 0xF250 * 4),
        "max_alpha": m4.u64(loader, work + 0xF252 * 4),
    }


def read_planes(loader: AexLoader, work: int, valid: int = 0) -> dict[str, bytes]:
    ptrs = plane_pointers(loader, work)
    result = {
        name: loader.read_bytes(ptr, CELLS * (16 if name in {"polar_rgba", "accum_rgba"} else 4))
        for name, ptr in ptrs.items()
    }
    if valid:
        result["valid"] = loader.read_bytes(valid, CELLS)
    return result


def run_actual() -> tuple[dict[str, bytes], dict[str, object]]:
    params = m4.load_case0010_params()
    params.update({
        "Center": (4.0, 3.0), "Quality": 5.0,
        "Outer Strength": 0, "Outer Offset Mode": 1, "Outer Offset": 0,
        "Inner Strength": 32, "Inner Offset Mode": 1, "Inner Offset": 0,
        "Outer Edge Fade": 0, "Inner Edge Fade": 0,
        "Size Variation": 0, "Noise Variation": 0,
        "Brightness Gain": 1.0,
    })
    loader = AexLoader(str(m4.AEX_PATH), fast=True)
    loader.register_libm_impls(max_threads=1)
    suites = m4.build_host_suites(loader)
    render_ctx = m4.build_render_context(loader, suites)
    input_world, _ = base.build_world(loader, base.source_frame())
    output_world, output_data = base.build_world(loader, base.source_frame(True))
    param_ctx = m4.build_param_block(loader)
    m4.install_reader_detours(loader, params)
    capture: dict[str, object] = {"order": []}

    def core_entry(ld, _address, _size):
        capture["work"] = ld.uc.reg_read(UC_X86_REG_RCX)

    def b150_entry(ld, _address, _size):
        capture["order"].append("prepass")
        work = ld.uc.reg_read(UC_X86_REG_RCX)
        capture["inner_base_length"] = struct.unpack("<i", ld.read_bytes(work + 0x3A9EC, 4))[0]
        capture["pre_b150"] = read_planes(ld, work)

    def a9d0_entry(ld, _address, _size):
        capture["order"].append("scatter")
        work = ld.uc.reg_read(UC_X86_REG_RCX)
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        valid = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        capture["post_b150_pre_a9d0"] = read_planes(ld, work, valid)

    def owner_return(ld, _address, _size):
        work = int(capture["work"])
        capture["post_normalize"] = read_planes(ld, work)
        owner_work = ld.uc.reg_read(UC_X86_REG_RBX)
        capture["final_rgba"] = ld.read_bytes(m4.u64(ld, owner_work + 0xA0), W * H * 16)

    loader.add_code_hook(m4.FUN_180004640, core_entry)
    # The single-threaded host detour enters the actual worker leaves directly;
    # B150/A9D0 are the parallel wrappers exercised by the separate bounded proof.
    loader.add_code_hook(PREPASS, b150_entry)
    loader.add_code_hook(SCATTER, a9d0_entry)
    loader.add_code_hook(ROTATION_RETURN, owner_return)
    setup = loader.call_function(m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    owner = loader.call_function(OWNER, int_args=[render_ctx, 0, input_world, output_world, param_ctx], max_instructions=500_000_000)
    if capture["order"] != ["prepass", "scatter"]:
        raise RuntimeError(f"fail-closed worker order: {capture['order']}")
    if not all(key in capture for key in ("pre_b150", "post_b150_pre_a9d0", "post_normalize", "final_rgba")):
        raise RuntimeError("fail-closed missing owner stage")
    artifacts: dict[str, bytes] = {"source_pf16": base.source_frame()}
    for stage in ("pre_b150", "post_b150_pre_a9d0", "post_normalize"):
        for name, raw in capture[stage].items():
            artifacts[f"{stage}__{name}"] = raw
    artifacts["final_rgba"] = capture["final_rgba"]
    artifacts["output"] = loader.read_bytes(output_data, ROWBYTES * H)
    meta = {"setup_instructions": setup["instructions"], "owner_instructions": owner["instructions"], "worker_order": capture["order"], "inner_base_length": capture["inner_base_length"]}
    return artifacts, meta


def main() -> int:
    aex_hash = sha(m4.AEX_PATH.read_bytes())
    if aex_hash != AEX_SHA256:
        raise RuntimeError(f"fail-closed AEX identity mismatch: {aex_hash}")
    artifacts, execution = run_actual()
    FIXTURE.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, raw in artifacts.items():
        encoded = zlib.compress(raw, 9)
        path = FIXTURE / f"{name}.bin.zlib"
        path.write_bytes(encoded)
        manifest[name] = {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "raw_sha256": sha(raw), "zlib_sha256": sha(encoded)}
    padding_exact = all(
        artifacts["output"][y * ROWBYTES + W * 8:(y + 1) * ROWBYTES] == bytes([0xA0 + y]) * (ROWBYTES - W * 8)
        for y in range(H)
    )
    gates = {
        "aex_identity": True,
        "worker_order": execution["worker_order"] == ["prepass", "scatter"],
        "all_stages_captured": len(artifacts) == 22,
        "inner_base_length_nonzero": execution["inner_base_length"] > 0,
        "nonzero_inner_changed_accum": artifacts["post_normalize__accum_rgba"] != artifacts["pre_b150__accum_rgba"],
        "nonzero_inner_output_differs_from_zero_fixture": sha(artifacts["output"]) != ZERO_INNER_OUTPUT_SHA256,
        "key_hashes_pinned": all(sha(artifacts[name]) == expected for name, expected in EXPECTED_KEY_HASHES.items()),
        "output_padding_preserved": padding_exact,
        "instruction_budget": execution["owner_instructions"] <= 500_000_000,
    }
    report = {
        "kind": "olmradialblur_rotation_pf16_inner32_small_actual_aex_20260806",
        "status": "exact_actual_aex_fixture" if all(gates.values()) else "fail_closed",
        "scope": "Pinned actual-AEX owner-only Rotation PF16 9x7 Inner Strength=32 internal planes and padded output; no production or AE-host claim",
        "aex": {"sha256": aex_hash, "owner": hex(OWNER), "parallel_wrappers": [hex(B150), hex(A9D0)], "workers": [hex(PREPASS), hex(SCATTER)], "writer": "0x180017440"},
        "params": {"inner_strength": 32, "outer_strength": 0, "quality": 5, "size_variation": 0, "noise_variation": 0, "edge_fades": [0, 0], "offset_modes": [1, 1], "offsets": [0, 0]},
        "geometry": {"width": W, "height": H, "rowbytes": ROWBYTES, "angular_count": 1800, "radius_count": 9, "cells": CELLS},
        "execution": execution,
        "gates": gates,
        "artifacts": manifest,
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "exact_actual_aex_fixture" else 2


if __name__ == "__main__":
    raise SystemExit(main())
