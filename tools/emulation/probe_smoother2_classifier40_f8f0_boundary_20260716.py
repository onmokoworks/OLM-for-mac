#!/usr/bin/env python3
"""Compare the local AEX and portable classifier-0x40 f8f0 boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_RAX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM0,
    UC_X86_REG_XMM2,
    UC_X86_REG_XMM3,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_fullchain_diff import call_c280_entry, setup_fixture  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

F8F0 = 0x18000F8F0
FEF0 = 0x18000FEF0
EAD0 = 0x18000EAD0
E050 = 0x18000E050
E050_RETURN_TO_EAD0 = 0x18000EAEA
PRIMARY_SCAN_RETURN = 0x18000EB36
SECONDARY_SCAN_CALL = 0x18000EBDB
SECONDARY_SCAN_RETURN = 0x18000EBE0
E3A0 = 0x18000E3A0
TRAPEZOID = 0x180013630
TRAPEZOID_RETURN_TO_E3A0 = 0x18000E3DE
APPEND = 0x1800104D0


def xmm_f32(loader: AexLoader, reg: int) -> float:
    raw = loader.uc.reg_read(reg)
    return struct.unpack("<f", int(raw).to_bytes(16, "little")[:4])[0]


def trace_aex_f8f0() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 16, 16)
    x, y = 5, 6
    ss.set_cur(x, y)
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    ss.set_src_pixel(x, y - 1, (0.8, 0.1, 0.1, 0.99607843))
    ss.set_src_pixel(x, y, (1.0, 1.0, 1.0, 1.0))
    setup_fixture(ss, "classifier_one")

    trace: dict = {"addresses": {}, "events": [], "secondary_executed": False}
    active = {"f8f0": False}

    def desc_at(uc) -> list[int]:
        ptr = uc.reg_read(UC_X86_REG_RDX)
        return list(struct.unpack("<6i", bytes(uc.mem_read(ptr, 24))))

    def hook(uc, address, _size, _user):
        if address == F8F0:
            active["f8f0"] = True
            desc = desc_at(uc)
            trace["descriptor"] = desc
            trace["key"] = desc[2] + (desc[5] * 5 - 1) * 2
            trace["addresses"]["dispatch"] = hex(address)
            trace["events"].append({"event": "dispatch", "address": hex(address)})
            return
        if address == FEF0:
            active["f8f0"] = False
            return
        if not active["f8f0"]:
            return
        if address == EAD0:
            trace["leaf"] = "FUN_18000ead0"
            trace["addresses"]["leaf"] = hex(address)
            trace["events"].append({"event": "leaf", "address": hex(address)})
        elif address == E050:
            trace["addresses"]["predicate"] = hex(address)
        elif address == E050_RETURN_TO_EAD0:
            trace["predicate"] = uc.reg_read(UC_X86_REG_RAX) & 0xFFFFFFFF
            trace["addresses"]["predicate_return"] = hex(address)
        elif address == PRIMARY_SCAN_RETURN:
            rsp = uc.reg_read(UC_X86_REG_RSP)
            trace["primary_scan"] = list(struct.unpack("<3i", bytes(uc.mem_read(rsp + 0x20, 12))))
            trace["addresses"]["primary_scan_return"] = hex(address)
        elif address == SECONDARY_SCAN_CALL:
            rsp = uc.reg_read(UC_X86_REG_RSP)
            trace["secondary_executed"] = True
            trace["secondary_input"] = list(struct.unpack("<2i", bytes(uc.mem_read(rsp + 0x90, 8))))
            trace["addresses"]["secondary_scan_call"] = hex(address)
        elif address == SECONDARY_SCAN_RETURN:
            result = uc.reg_read(UC_X86_REG_RAX)
            trace["secondary_scan"] = list(struct.unpack("<3i", bytes(uc.mem_read(result, 12))))
            trace["addresses"]["secondary_scan_return"] = hex(address)
        elif address == E3A0:
            poly = uc.reg_read(UC_X86_REG_RCX)
            trace["smoothness_n"] = struct.unpack("<f", bytes(uc.mem_read(poly + 0x38, 4)))[0]
            trace["extra_n"] = struct.unpack("<f", bytes(uc.mem_read(poly + 0x3C, 4)))[0]
            trace["scale_m"] = xmm_f32(loader, UC_X86_REG_XMM2)
            trace["scale_h"] = xmm_f32(loader, UC_X86_REG_XMM3)
            trace["addresses"]["emitter"] = hex(address)
        elif address == TRAPEZOID:
            trace["trap"] = {
                "p1": xmm_f32(loader, UC_X86_REG_XMM0),
                "p2": uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF,
                "p3": xmm_f32(loader, UC_X86_REG_XMM2),
            }
            trace["addresses"]["trapezoid"] = hex(address)
        elif address == TRAPEZOID_RETURN_TO_E3A0:
            trace["trap"]["weight"] = xmm_f32(loader, UC_X86_REG_XMM0)
            trace["addresses"]["trapezoid_return"] = hex(address)
        elif address == APPEND:
            rsp = uc.reg_read(UC_X86_REG_RSP)
            trace["append"] = {
                "return_address": hex(struct.unpack("<Q", bytes(uc.mem_read(rsp, 8)))[0]),
                "weight": xmm_f32(loader, UC_X86_REG_XMM2),
            }
            trace["addresses"]["append"] = hex(address)

    addresses = [
        F8F0, FEF0, EAD0, E050, E050_RETURN_TO_EAD0,
        PRIMARY_SCAN_RETURN, SECONDARY_SCAN_CALL, SECONDARY_SCAN_RETURN,
        E3A0, TRAPEZOID, TRAPEZOID_RETURN_TO_E3A0, APPEND,
    ]
    handle = loader.uc.hook_add(UC_HOOK_CODE, hook, begin=min(addresses), end=max(addresses))
    c280 = call_c280_entry(loader, ss, x, y)
    loader.uc.hook_del(handle)
    trace["c280_first_vertex"] = c280["vertices"][0]
    return trace


def close(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    aex = trace_aex_f8f0()
    port = json.loads(subprocess.check_output([str(args.adapter)], text=True))
    secondary_branch_equal = aex["secondary_executed"] == port["secondary_executed"]
    secondary_values_equal = (
        not aex["secondary_executed"]
        or (
            aex.get("secondary_input") == port.get("secondary_input")
            and aex.get("secondary_scan") == port.get("secondary_scan")
        )
    )
    comparison = {
        "descriptor_equal": aex["descriptor"] == port["descriptor"],
        "inner_key_equal": aex["key"] == port["key"],
        "predicate_equal": aex["predicate"] == port["predicate"],
        "primary_scan_equal": aex["primary_scan"] == port["primary_scan"],
        "secondary_branch_executed_equal": secondary_branch_equal,
        "secondary_values_equal_if_executed": secondary_values_equal,
        "scale_m_equal_1e-6": close(aex["scale_m"], port["scale_m"]),
        "scale_h_equal_1e-6": close(aex["scale_h"], port["scale_h"]),
        "trap_p1_equal_1e-6": close(aex["trap"]["p1"], port["trap"]["p1"]),
        "trap_p2_equal": aex["trap"]["p2"] == port["trap"]["p2"],
        "trap_p3_equal_1e-6": close(aex["trap"]["p3"], port["trap"]["p3"]),
        "weight_equal_1e-6": close(aex["trap"]["weight"], port["trap"]["weight"]),
    }
    all_comparisons_equal = all(comparison.values())
    result = {
        "verdict": "PASS_LOCAL_CLASSIFIER_0X40_F8F0_BOUNDARY_REGRESSION",
        "scope": "Mac-only local AEX emulation and portable model evidence; not Windows/AE truth",
        "aex_identity": {
            "path": str(AEX_PATH.relative_to(ROOT)),
            "sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(),
        },
        "aex": aex,
        "portable": port,
        "comparison": comparison,
        "all_comparisons_equal": all_comparisons_equal,
        "claims_not_made": [
            "No Windows or After Effects execution or host binding.",
            "No AE-exact or production-fix claim.",
            "No live case_0004/case_0012 mapping.",
        ],
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    required = (
        aex.get("leaf") == "FUN_18000ead0"
        and aex.get("key") == 1
        and all_comparisons_equal
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())
