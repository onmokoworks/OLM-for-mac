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
from aex_loader import AexLoader, RETURN_TRAMPOLINE  # noqa: E402
from unicorn import UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX,
    UC_X86_REG_RSI, UC_X86_REG_RDI, UC_X86_REG_RBP, UC_X86_REG_RSP,
    UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11,
    UC_X86_REG_R12, UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R15,
    UC_X86_REG_RIP, UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2,
    UC_X86_REG_XMM3, UC_X86_REG_XMM4, UC_X86_REG_XMM5, UC_X86_REG_XMM6,
    UC_X86_REG_XMM7, UC_X86_REG_XMM8, UC_X86_REG_XMM9, UC_X86_REG_XMM10,
    UC_X86_REG_XMM11, UC_X86_REG_XMM12, UC_X86_REG_XMM13, UC_X86_REG_XMM14,
    UC_X86_REG_XMM15,
)

REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf16_inner32_small_actual_aex_20260806.json"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_rotation_pf16_inner32_small_20260806"
OWNER = 0x180006D10
ROTATION_RETURN = 0x18000733A
B150 = 0x18000B150
A9D0 = 0x18000A9D0
PREPASS = 0x180002780
SCATTER = 0x1800024C0
INNER_HELPER = 0x180001C90
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
EXPECTED_HELPER_HASHES = {
    "first_helper__work_head": "2886e8916105d89f6a95df1545732d50e01621123d2df77f69584efb09e56304",
    "first_helper__work_span_config": "8a0fa73e4f8dcdd56832892e4e63df795620139a0d31a730e64ed5ea182b792f",
    "first_helper__inner_table": "1b858f7c458ce368fa6db4b4990ab2ab3f5c3ce93629ddf365284ce027f67fff",
    "first_helper__accum_before": "b9ad15ac07f2951fb0008d91153225ca28de61182b82b508d6c13178c2a6da8e",
    "first_helper__accum_after": "dd2e3302589047c85a53be7c184b8c0451f963ca20e1c527e17303de2af2d2a1",
    "first_helper__max_before": "4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c",
    "first_helper__max_after": "4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c",
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
    capture: dict[str, object] = {"order": [], "helper_calls": 0, "helper_active": False,
                                  "trace_enabled": True, "first_inner_trace": [],
                                  "all_store_count": 0, "all_store_hash": hashlib.sha256()}
    gp_regs = (UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX,
               UC_X86_REG_RSI, UC_X86_REG_RDI, UC_X86_REG_RBP, UC_X86_REG_RSP,
               UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11,
               UC_X86_REG_R12, UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R15)
    xmm_regs = (UC_X86_REG_XMM0, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3,
                UC_X86_REG_XMM4, UC_X86_REG_XMM5, UC_X86_REG_XMM6, UC_X86_REG_XMM7,
                UC_X86_REG_XMM8, UC_X86_REG_XMM9, UC_X86_REG_XMM10, UC_X86_REG_XMM11,
                UC_X86_REG_XMM12, UC_X86_REG_XMM13, UC_X86_REG_XMM14, UC_X86_REG_XMM15)

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

    def helper_entry(ld, _address, _size):
        capture["helper_calls"] += 1
        capture["helper_active"] = True
        return_address = struct.unpack("<Q", ld.read_bytes(ld.uc.reg_read(UC_X86_REG_RSP), 8))[0]
        if return_address not in capture.setdefault("helper_returns", set()):
            capture["helper_returns"].add(return_address)
            ld.add_code_hook(return_address, helper_any_return)
        if "helper" in capture or ld.uc.reg_read(UC_X86_REG_RDX) != 1:
            return
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        work = ld.uc.reg_read(UC_X86_REG_RCX)
        ptrs = plane_pointers(ld, work)
        capture["helper"] = {
            "return_address": struct.unpack("<Q", ld.read_bytes(rsp, 8))[0],
            "gp": [ld.uc.reg_read(reg) for reg in gp_regs],
            "xmm": [ld.uc.reg_read(reg) for reg in xmm_regs],
            "stack": ld.read_bytes(rsp, 0x100),
            "work_head": ld.read_bytes(work, 0x68),
            "work_span_config": ld.read_bytes(work + 0x3A9D0, 0x40),
            "inner_table": ld.read_bytes(work + 0x1D528, 30000 * 4),
            "accum_before": ld.read_bytes(ptrs["accum_rgba"], CELLS * 16),
            "max_before": ld.read_bytes(ptrs["max_alpha"], CELLS * 4),
            "work": work,
            "accum_ptr": ptrs["accum_rgba"], "max_ptr": ptrs["max_alpha"],
        }
        ld.add_code_hook(capture["helper"]["return_address"], helper_return)

    def helper_return(ld, _address, _size):
        helper = capture.get("helper")
        if not helper or "accum_after" in helper:
            return
        helper["accum_after"] = ld.read_bytes(helper["accum_ptr"], CELLS * 16)
        helper["max_after"] = ld.read_bytes(helper["max_ptr"], CELLS * 4)

    def helper_any_return(_ld, address, _size):
        capture["helper_active"] = False
        if "helper" in capture and address == capture["helper"]["return_address"]:
            capture["record_first_inner"] = False

    def memory_write(_uc, _access, address, size, value, _user):
        if not capture["trace_enabled"] or "helper" not in capture:
            return
        helper = capture["helper"]
        regions = (("accum", helper["accum_ptr"], CELLS * 16),
                   ("max", helper["max_ptr"], CELLS * 4))
        for region, base_ptr, length in regions:
            if base_ptr <= address and address + size <= base_ptr + length:
                offset = address - base_ptr
                raw_value = int(value).to_bytes(size, "little", signed=False)
                record = struct.pack("<BII", 0 if region == "accum" else 1, offset, size) + raw_value
                model = capture.setdefault(f"model_{region}", bytearray(helper[f"{region}_before"]))
                model[offset:offset + size] = raw_value
                capture["all_region_write_count"] = capture.get("all_region_write_count", 0) + 1
                if capture["helper_active"]:
                    capture["all_store_hash"].update(record)
                    capture["all_store_count"] += 1
                if capture["helper_active"] and capture.get("record_first_inner", True):
                    capture["first_inner_trace"].append({"region": region, "offset": offset,
                                                          "size": size, "value_hex": raw_value.hex()})
                return

    loader.add_code_hook(m4.FUN_180004640, core_entry)
    # The single-threaded host detour enters the actual worker leaves directly;
    # B150/A9D0 are the parallel wrappers exercised by the separate bounded proof.
    loader.add_code_hook(PREPASS, b150_entry)
    loader.add_code_hook(SCATTER, a9d0_entry)
    loader.add_code_hook(ROTATION_RETURN, owner_return)
    loader.add_code_hook(INNER_HELPER, helper_entry)
    loader.uc.hook_add(UC_HOOK_MEM_WRITE, memory_write)
    setup = loader.call_function(m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    owner = loader.call_function(OWNER, int_args=[render_ctx, 0, input_world, output_world, param_ctx], max_instructions=500_000_000)
    if capture["order"] != ["prepass", "scatter"]:
        raise RuntimeError(f"fail-closed worker order: {capture['order']}")
    if not all(key in capture for key in ("pre_b150", "post_b150_pre_a9d0", "post_normalize", "final_rgba")):
        raise RuntimeError("fail-closed missing owner stage")
    helper = capture.get("helper")
    if not helper or "accum_after" not in helper:
        raise RuntimeError("fail-closed first helper call was not captured through return")
    capture["record_first_inner"] = False
    artifacts: dict[str, bytes] = {"source_pf16": base.source_frame()}
    for stage in ("pre_b150", "post_b150_pre_a9d0", "post_normalize"):
        for name, raw in capture[stage].items():
            artifacts[f"{stage}__{name}"] = raw
    artifacts["final_rgba"] = capture["final_rgba"]
    artifacts["output"] = loader.read_bytes(output_data, ROWBYTES * H)
    for name in ("stack", "work_head", "work_span_config", "inner_table", "accum_before", "accum_after", "max_before", "max_after"):
        artifacts[f"first_helper__{name}"] = helper[name]

    # Directly replay the captured call in the same mapped AEX instance.
    loader.write_bytes(helper["accum_ptr"], helper["accum_before"])
    loader.write_bytes(helper["max_ptr"], helper["max_before"])
    loader.write_bytes(helper["work"], helper["work_head"])
    loader.write_bytes(helper["work"] + 0x3A9D0, helper["work_span_config"])
    loader.write_bytes(helper["work"] + 0x1D528, helper["inner_table"])
    rsp = helper["gp"][7]
    loader.write_bytes(rsp, struct.pack("<Q", RETURN_TRAMPOLINE) + helper["stack"][8:])
    for reg, value in zip(gp_regs, helper["gp"]): loader.uc.reg_write(reg, value)
    loader.uc.reg_write(UC_X86_REG_RSP, rsp)
    for reg, value in zip(xmm_regs, helper["xmm"]): loader.uc.reg_write(reg, value)
    before_instructions = loader.instructions_executed
    loader.uc.emu_start(INNER_HELPER, RETURN_TRAMPOLINE, count=5_000_000)
    replay_accum = loader.read_bytes(helper["accum_ptr"], CELLS * 16)
    replay_max = loader.read_bytes(helper["max_ptr"], CELLS * 4)
    artifacts["first_helper__replay_accum_after"] = replay_accum
    artifacts["first_helper__replay_max_after"] = replay_max
    replay = {"instructions": loader.instructions_executed - before_instructions,
              "accum_exact": replay_accum == helper["accum_after"],
              "max_exact": replay_max == helper["max_after"]}
    capture["trace_enabled"] = False
    changed_cells = []
    for cell in range(CELLS):
        lo, hi = cell * 16, (cell + 1) * 16
        if helper["accum_before"][lo:hi] != helper["accum_after"][lo:hi]:
            changed_cells.append([cell // 1800, cell % 1800])
    first_trace = capture["first_inner_trace"]
    meta = {"setup_instructions": setup["instructions"], "owner_instructions": owner["instructions"], "worker_order": capture["order"], "inner_base_length": capture["inner_base_length"], "helper_calls": capture["helper_calls"], "first_helper_return": hex(helper["return_address"]), "first_helper_registers": {"gp": [hex(x) for x in helper["gp"]], "xmm": [hex(x) for x in helper["xmm"]]}, "first_inner_helper_write_set": {"changed_cells": changed_cells, "count": len(changed_cells), "max_plane_changed": helper["max_before"] != helper["max_after"], "memory_store_count": len(first_trace), "memory_stores": first_trace, "candidate_store_discriminator": {"actual_first_store": first_trace[0], "portable_backward_first_store": {"region": "accum", "offset": 1799 * 16, "size": 4, "channel": "red"}, "portable_forward_first_store": {"region": "accum", "offset": 1 * 16, "size": 4, "channel": "red"}, "classification": "actual walks cells 1799 down to 1770 and stores alpha, blue, green, red; both current portable candidates store red first and forward chooses cell 1"}}, "all_helper_store_trace": {"helper_store_count": capture["all_store_count"], "all_region_write_count": capture.get("all_region_write_count", 0), "sha256": capture["all_store_hash"].hexdigest(), "reconstructed_accum_exact": bytes(capture["model_accum"]) == capture["post_normalize"]["accum_rgba"], "reconstructed_max_exact": bytes(capture["model_max"]) == capture["post_normalize"]["max_alpha"], "classification": "compact trace captured, but replaying callback values alone does not reconstruct final accum; full-call semantics not promoted"}, "direct_replay": replay}
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
        "all_stages_captured": len(artifacts) == 32,
        "inner_base_length_nonzero": execution["inner_base_length"] > 0,
        "nonzero_inner_changed_accum": artifacts["post_normalize__accum_rgba"] != artifacts["pre_b150__accum_rgba"],
        "nonzero_inner_output_differs_from_zero_fixture": sha(artifacts["output"]) != ZERO_INNER_OUTPUT_SHA256,
        "key_hashes_pinned": all(sha(artifacts[name]) == expected for name, expected in EXPECTED_KEY_HASHES.items()),
        "first_helper_hashes_pinned": all(sha(artifacts[name]) == expected for name, expected in EXPECTED_HELPER_HASHES.items()),
        "output_padding_preserved": padding_exact,
        "instruction_budget": execution["owner_instructions"] <= 500_000_000,
        "first_helper_direct_replay": all(execution["direct_replay"][key] for key in ("accum_exact", "max_exact")),
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
