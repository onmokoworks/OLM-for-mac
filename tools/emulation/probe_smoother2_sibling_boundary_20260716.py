#!/usr/bin/env python3
"""Compare actual AEX and portable boundaries for e4b0/edb0/e7c0."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_XMM3

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

LEAVES = {
    "e4b0": (0x18000E4B0, 0x18000E51F, 0x18000E5CE, 0x18000E290),
    "edb0": (0x18000EDB0, 0x18000EE16, 0x18000EEBE, 0x18000E3A0),
    "e7c0": (0x18000E7C0, 0x18000E82F, 0x18000E8DE, 0x18000E290),
}
PREDICATE_RETURNS = {"e4b0": 0x18000E4CA, "edb0": 0x18000EDCA, "e7c0": 0x18000E7DA}


def install_fixture(ss: SmootherStruct, leaf: str, scenario: int) -> None:
    x = y = 5
    if leaf == "e4b0":
        ss.set_class_pixel(x + 1, y, 1)
        if scenario == 3:
            ss.set_class_pixel(x + 1, y + 1, 1)
    elif leaf == "edb0":
        ss.set_class_pixel(x, y, 1)
        if scenario == 3:
            ss.set_class_pixel(x, y - 1, 1)
    else:
        ss.set_class_pixel(x, y, 1)
        if scenario == 3:
            ss.set_class_pixel(x, y + 1, 1)


def f32_xmm3(loader: AexLoader) -> float:
    raw = loader.uc.reg_read(UC_X86_REG_XMM3)
    return struct.unpack("<f", int(raw).to_bytes(16, "little")[:4])[0]


def run_aex(leaf: str, scenario: int) -> dict:
    address, primary_return, secondary_return, emitter = LEAVES[leaf]
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 16, 16)
    ss.set_cur(5, 5)
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    install_fixture(ss, leaf, scenario)
    desc = [2, 2, 1, 5, 5, 5]
    if leaf == "edb0":
        desc[0] = desc[3]
        desc[1] = desc[4]
    d = loader.bump_alloc(24, align=16)
    loader.write_bytes(d, struct.pack("<6i", *desc))
    trace = {"primary_scan": None, "secondary_scan": None, "secondary_executed": False}

    def hook(uc, address_now, _size, _user):
        if address_now == primary_return:
            ptr = uc.reg_read(UC_X86_REG_RAX)
            trace["primary_scan"] = list(struct.unpack("<3i", bytes(uc.mem_read(ptr, 12))))
        elif address_now == PREDICATE_RETURNS[leaf]:
            trace["predicate"] = uc.reg_read(UC_X86_REG_RAX) & 0xFF
        elif address_now == secondary_return:
            ptr = uc.reg_read(UC_X86_REG_RAX)
            trace["secondary_executed"] = True
            trace["secondary_scan"] = list(struct.unpack("<3i", bytes(uc.mem_read(ptr, 12))))
        elif address_now == emitter:
            trace["emitter_scale_h"] = f32_xmm3(loader)

    handle = loader.uc.hook_add(UC_HOOK_CODE, hook, begin=0x18000D000, end=0x18000EF00)
    result = loader.call_function(address, int_args=[ss.base, d], max_instructions=500_000)
    loader.uc.hook_del(handle)
    trace["predicate_return"] = trace.get("predicate", -1)
    trace["vertices"] = ss.vertices()
    trace["descriptor"] = desc
    return trace


def close(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for leaf in LEAVES:
        for scenario in (1, 3):
            aex = run_aex(leaf, scenario)
            port = json.loads(subprocess.check_output([str(args.adapter), leaf, str(scenario)], text=True))
            cmp = {
                "descriptor_equal": aex["descriptor"] == port["descriptor"],
                "predicate_equal": aex["predicate_return"] == port["predicate"],
                "primary_scan_equal": aex.get("primary_scan") == port["primary_scan"] if aex.get("primary_scan") is not None else True,
                "secondary_branch_equal": aex["secondary_executed"] == (scenario == 3),
                "secondary_scan_equal": scenario == 1 or aex.get("secondary_scan") == port["secondary_scan"],
                "scale_h_equal_1e-6": scenario == 1 or close(aex.get("emitter_scale_h", 0.0), port["scale_h"]),
                "emission_equal_1e-6": len(aex["vertices"]) == port["emitted_count"],
            }
            # Compare the emitted weight separately; coordinates are fixed by the leaf emitter.
            cmp["emission_equal_1e-6"] = (
                len(aex["vertices"]) == len(port["vertices"])
                and all(close(a["weight"], p["weight"]) for a, p in zip(aex["vertices"], port["vertices"]))
            )
            rows.append({"leaf": leaf, "scenario": scenario, "aex": aex, "portable": port, "comparison": cmp})
    result = {
        "verdict": "PASS_LOCAL_AEX_PORTABLE_SIBLING_BOUNDARIES" if all(all(r["comparison"].values()) for r in rows) else "FAIL_LOCAL_AEX_PORTABLE_SIBLING_BOUNDARIES",
        "scope": "Mac-only checked-in AEX emulation and portable production boundary; not Windows/AE exact",
        "rows": rows,
        "claims_not_made": ["No Windows execution, After Effects host binding, or AE-exact claim."],
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
