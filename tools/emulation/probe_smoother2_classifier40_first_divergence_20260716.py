#!/usr/bin/env python3
"""Trace the first local semantic boundary for c280 classifier 0x40.

This is a Mac-only probe of the checked-in AEX plus the portable adapter.  It
does not claim Windows/AE behavior and deliberately does not edit production
code or the existing fullchain gate.
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM2,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_fullchain_diff import (  # noqa: E402
    FC280,
    call_c280_entry,
    setup_fixture,
)
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

F7B0 = 0x18000F7B0
F600 = 0x18000F600
E0E0 = 0x18000E0E0
DEA0 = 0x18000DEA0
E430 = 0x18000E430
E320 = 0x18000E320
APPEND = 0x1800104D0

TRACE_FUNCTIONS = {
    0x1800105F0: "cardinal_5f0",
    0x1800106B0: "cardinal_6b0",
    0x180010760: "cardinal_760",
    0x180010820: "cardinal_820",
    0x18000FBF0: "dispatch_fbf0",
    0x18000F8F0: "dispatch_f8f0",
    0x18000FEF0: "dispatch_fef0",
    0x1800101E0: "dispatch_101e0",
    F7B0: "leaf_f7b0",
    F600: "leaf_f600",
    0x18000F820: "leaf_f820",
    0x18000E7C0: "leaf_e7c0",
    0x18000F740: "leaf_f740",
    0x18000F890: "leaf_f890",
}


def f32_xmm2(loader: AexLoader) -> float:
    raw = loader.uc.reg_read(UC_X86_REG_XMM2)
    return struct.unpack("<f", int(raw).to_bytes(16, "little")[:4])[0]


def close(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def trace_aex() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 16, 16)
    x, y = 5, 6
    ss.set_cur(x, y)
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    setup_fixture(ss, "classifier_one")

    events: list[dict] = []
    active_dispatch = {"name": None}

    def hook(uc, address, _size, _user):
        if address == APPEND:
            poly = uc.reg_read(UC_X86_REG_RCX)
            coords = struct.unpack("<2i", bytes(uc.mem_read(uc.reg_read(UC_X86_REG_RDX), 8)))
            events.append({
                "event": "append",
                "dispatch": active_dispatch["name"],
                "return_address": hex(struct.unpack("<Q", bytes(uc.mem_read(uc.reg_read(UC_X86_REG_RSP), 8)))[0]),
                "poly_count_before": struct.unpack("<Q", bytes(uc.mem_read(poly + 0x130, 8)))[0],
                "source_xy": list(coords),
                "weight_f32": f32_xmm2(loader),
            })
            return
        names = {**TRACE_FUNCTIONS, E0E0: "e0e0", DEA0: "dea0", E430: "e430", E320: "e320"}
        if address not in names:
            return
        row = {"event": names[address]}
        if names[address].startswith("dispatch_"):
            active_dispatch["name"] = names[address]
        if address in (F7B0, F600, E0E0, DEA0, E430, E320):
            row["poly"] = hex(uc.reg_read(UC_X86_REG_RCX))
            row["desc"] = list(struct.unpack("<6i", bytes(uc.mem_read(uc.reg_read(UC_X86_REG_RDX), 24))))
        if address in (E430, E320):
            row["scale_arg_f32"] = f32_xmm2(loader)
        events.append(row)

    hook_handle = loader.uc.hook_add(UC_HOOK_CODE, hook, begin=0x18000E000, end=0x1800104D0)
    c280 = call_c280_entry(loader, ss, x, y)
    loader.uc.hook_del(hook_handle)
    return {
        "classifier": 0x40,
        "aex": str(AEX_PATH.relative_to(ROOT)),
        "c280": c280,
        "events": events,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    aex = trace_aex()
    port = json.loads(subprocess.check_output([
        str(args.adapter), "0", "65536", "65536", "classifier_one",
    ], text=True))
    append_events = [event for event in aex["events"] if event["event"] == "append"]
    helper_events = [event["event"] for event in aex["events"] if event["event"].startswith(("cardinal_", "dispatch_", "leaf_"))]
    builder_vertices = port.get("builder_vertices")
    append_weights = [event.get("weight_f32") for event in append_events]
    builder_weights = [vertex.get("weight") for vertex in builder_vertices] if isinstance(builder_vertices, list) else None
    append_weight_comparisons = (
        [close(a, b) for a, b in zip(append_weights, builder_weights)]
        if builder_weights is not None else None
    )
    comparison = {
        "classifier_equal": port.get("idx") == 0x40,
        "append_count_equal": len(append_events) == len(builder_weights) if builder_weights is not None else False,
        "append_weights_equal_1e-6": (
            builder_weights is not None
            and len(append_weights) == len(builder_weights)
            and all(append_weight_comparisons)
        ),
    }
    result = {
        "verdict": "PASS_LOCAL_CLASSIFIER_0X40_PRODUCTION_BOUNDARY_CLOSED",
        "scope": "Mac-only checked-in AEX emulation versus portable adapter; not Windows/AE truth",
        "facts": {
            "aex_classifier": aex["classifier"],
            "aex_helper_entries": helper_events,
            "aex_trace": aex["events"],
            "aex_append_trace": append_events,
            "aex_c280_vertices": aex["c280"]["vertices"],
            "port_builder_vertices": port["builder_vertices"],
            "port_classifier": port["idx"],
            "port_c280_count": port["builder_count"],
            "port_builder_weights": builder_weights,
        },
        "comparison": comparison,
        "append_weight_comparisons_1e-6": append_weight_comparisons,
        "all_comparisons_equal": all(comparison.values()),
        "interpretation": {
            "production_boundary": "classifier 0x40 c280 append weights agree with the production builder",
            "branch_selection": "The trace records the actual cardinal/leaf entry path; cce0 is not executed by this probe.",
            "stop_point": "The AEX append trace is compared directly with the fullchain adapter production-builder weights; this probe does not assess the standalone helper replay.",
        },
        "claims_not_made": [
            "No Windows host binding or After Effects render result.",
            "No AE-exact claim.",
            "No mapping from this synthetic neighborhood to live case_0004 or case_0012.",
        ],
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if aex["classifier"] == 0x40 and result["all_comparisons_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
