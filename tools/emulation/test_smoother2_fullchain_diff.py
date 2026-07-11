#!/usr/bin/env python3
"""Test-only identical-fixture replay: local AEX binary versus current Mac port."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RDX

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_producer import (  # noqa: E402
    AEX_PATH, O_BASE_WEIGHT, O_SMOOTHNESS, SmootherStruct,
    call_e170, call_f270,
)

F125C0 = 0x1800125C0
F10760 = 0x180010760
FFEF0 = 0x18000FEF0
FCC70 = 0x18000CC70
DESC = [5, 6, 1, 5, 8, 5]


def vertices(ss: SmootherStruct) -> list[dict]:
    return [{"rgba": list(v["rgba"]), "weight": v["weight"]} for v in ss.vertices()]


def run_aex(suppress: bool) -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    ss = SmootherStruct(loader, 16, 16)
    x, y = 5, 6
    ss.set_cur(x, y)
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    ss.set_src_pixel(x, y - 1, (0.99106717, 0.99106717, 0.99106717, 0.99607843))
    ss.set_src_pixel(x, y, (1.0, 1.0, 1.0, 0.0))
    # Independent c280 classifier bytes: low nibble 9 and high nibble 6.
    ss.set_class_pixel(x, y, 0, 1, 0, 1)
    ss.set_class_pixel(x + 1, y, 1, 0, 0, 0)
    ss.set_class_pixel(x + 1, y + 1, 0, 0, 1, 0)
    if suppress:
        ss.set_class_pixel(x - 1, y, 0, 1, 0, 0)
    else:
        ss.set_class_pixel(x, y - 1, 1, 0, 0, 0)

    c = call_e170(loader, ss, DESC)
    _, direct_count, direct_verts = call_f270(loader, ss, DESC, 1.0)

    ss.set_vcount(0)
    pre_ret = loader.call_function(F125C0, int_args=[ss.base], max_instructions=2_000_000)["rax"] & 0xff
    after_125c0 = ss.vcount()
    captured: list[list[int]] = []

    def at_dispatch(uc, _address, _size, _user):
        ptr = uc.reg_read(UC_X86_REG_RDX)
        captured.append(list(struct.unpack("<6i", bytes(uc.mem_read(ptr, 24)))))

    hook = loader.uc.hook_add(UC_HOOK_CODE, at_dispatch, begin=FFEF0, end=FFEF0)
    loader.call_function(F10760, int_args=[ss.base], max_instructions=2_000_000)
    loader.uc.hook_del(hook)
    before_normalize = ss.vcount()
    loader.call_function(FCC70, int_args=[ss.base], max_instructions=200_000)
    return {
        "fixture": "c4_control" if suppress else "c2_witness",
        "descriptor_direct": DESC,
        "c": c,
        "append": direct_count != 0,
        "direct_count": direct_count,
        "direct_vertices": [{"rgba": list(v["rgba"]), "weight": v["weight"]} for v in direct_verts],
        "pre125c0_ret": pre_ret,
        "after_125c0_count": after_125c0,
        "cardinal6_descriptor": captured[0] if captured else None,
        "chain_before_normalize": before_normalize,
        "chain_count": ss.vcount(),
        "chain_vertices": vertices(ss),
    }


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def compare(aex: dict, port: dict) -> dict:
    av, pv = aex["direct_vertices"], port["direct_vertices"]
    vertex_match = len(av) == len(pv) and all(
        all(close(x, y) for x, y in zip(xv["rgba"], yv["rgba"])) and close(xv["weight"], yv["weight"])
        for xv, yv in zip(av, pv)
    )
    ac, pc = aex["chain_vertices"], port["chain_vertices"]
    chain_vertex_match = len(ac) == len(pc) and all(
        all(close(x, y) for x, y in zip(xv["rgba"], yv["rgba"])) and close(xv["weight"], yv["weight"])
        for xv, yv in zip(ac, pc)
    )
    return {
        "descriptor_direct_equal": aex["descriptor_direct"] == port["descriptor"],
        "c_equal": aex["c"] == port["c"],
        "append_equal": aex["append"] == port["append"],
        "direct_vertices_weights_equal_1e-6": vertex_match,
        "cardinal6_descriptor_equal": aex["cardinal6_descriptor"] == port["cardinal6_descriptor"],
        "chain_count_equal": aex["chain_count"] == port["chain_count"],
        "chain_vertices_weights_equal_1e-6": chain_vertex_match,
        "all_replayed_boundaries_equal": aex["descriptor_direct"] == port["descriptor"] and aex["c"] == port["c"] and aex["append"] == port["append"] and vertex_match and aex["cardinal6_descriptor"] == port["cardinal6_descriptor"] and chain_vertex_match,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []
    for suppress in (False, True):
        aex = run_aex(suppress)
        port = json.loads(subprocess.check_output([str(args.adapter), "1" if suppress else "0"], text=True))
        rows.append({"aex": aex, "port": port, "comparison": compare(aex, port)})
    result = {
        "scope": "local binary-semantic evidence; not Windows AE truth",
        "facts": rows,
        "blockers": {
            "c280": "AEX FUN_18000c280 requires the live five-argument host/config binding; this fixture does not fabricate the opaque parameter object.",
            "cce0_final_float": "AEX FUN_18000cce0 requires gamma/key/config state beyond the identical polygon fixture; only the port composite float is reported, not compared.",
        },
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return 0 if all(r["comparison"]["all_replayed_boundaries_equal"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
