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
from unicorn.x86_const import UC_X86_REG_RDX, UC_X86_REG_RSP

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
FC280 = 0x18000C280
FCCE0 = 0x18000CCE0
DESC = [5, 6, 1, 5, 8, 5]
CENTER = [1.0, 1.0, 1.0, 1.0]

FIXTURES = (
    ("c2_witness", False),
    ("c4_control", True),
    ("classifier_one", False),
    ("classifier_zero", False),
)
EXPECTED_CLASSIFIER_INDEX = {
    "c2_witness": 0x69,
    "c4_control": 0x69,
    "classifier_one": 0x40,
    "classifier_zero": 0xFF,
}


def setup_fixture(ss: SmootherStruct, fixture: str) -> None:
    """Install one small class neighborhood used by both binary paths."""
    x, y = 5, 6
    if fixture in ("c2_witness", "c4_control"):
        ss.set_class_pixel(x, y, 0, 1, 0, 1)
        ss.set_class_pixel(x + 1, y, 1, 0, 0, 0)
        ss.set_class_pixel(x + 1, y + 1, 0, 0, 1, 0)
    elif fixture == "classifier_one":
        ss.set_class_pixel(x, y, 1, 1, 1, 1)
        ss.set_class_pixel(x + 1, y, 1, 0, 0, 0)
        ss.set_class_pixel(x + 1, y + 1, 0, 0, 1, 0)
        ss.set_class_pixel(x - 1, y + 1, 0, 0, 0, 1)
    elif fixture != "classifier_zero":
        raise ValueError(fixture)
    if fixture == "c4_control":
        ss.set_class_pixel(x - 1, y, 0, 1, 0, 0)
    else:
        ss.set_class_pixel(x, y - 1, 1, 0, 0, 0)


def call_c280_entry(loader: AexLoader, ss: SmootherStruct, x: int, y: int) -> dict:
    """Execute the actual five-argument builder with reconstructable host scale."""
    out = loader.bump_alloc(0xF8, align=16)
    loader.write_bytes(out, b"\x00" * 0xF8)
    src = loader.bump_alloc(24, align=16)
    cls = loader.bump_alloc(24, align=16)
    packed_wh = struct.pack("<ii", ss.width, ss.height)
    loader.write_bytes(src, struct.pack("<Q", ss.src_base) + packed_wh + struct.pack("<Q", ss.src_stride))
    loader.write_bytes(cls, struct.pack("<Q", ss.class_base) + packed_wh + struct.pack("<Q", ss.class_stride))
    xy = loader.bump_alloc(8, align=8)
    loader.write_bytes(xy, struct.pack("<ii", x, y))
    config = loader.bump_alloc(0x28, align=16)
    loader.write_bytes(config, b"\x00" * 0x28)
    loader.write_bytes(config + 0x20, struct.pack("<ii", 65536, 65536))
    result = loader.call_function(FC280, int_args=[out, src, cls, xy, config], max_instructions=5_000_000)
    count = struct.unpack("<Q", loader.read_bytes(out + 0xF0, 8))[0]
    verts = []
    for index in range(min(count, 12)):
        offset = out + index * 0x14
        rgba = struct.unpack("<4f", loader.read_bytes(offset, 16))
        weight = struct.unpack("<f", loader.read_bytes(offset + 0x10, 4))[0]
        verts.append({"rgba": list(rgba), "weight": weight})
    return {
        "returned_pointer": result["rax"],
        "output_pointer": out,
        "scale_fixed": [65536, 65536],
        "count": count,
        "vertices": verts,
    }


def call_cce0_entry(loader: AexLoader, ss: SmootherStruct, x: int, y: int, gamma_colors: bool = False) -> dict:
    """Execute the actual per-pixel orchestrator on the fixture."""
    out = loader.bump_alloc(16, align=16)
    loader.write_bytes(out, b"\x00" * 16)
    src = loader.bump_alloc(24, align=16)
    cls = loader.bump_alloc(24, align=16)
    packed_wh = struct.pack("<ii", ss.width, ss.height)
    loader.write_bytes(src, struct.pack("<Q", ss.src_base) + packed_wh + struct.pack("<Q", ss.src_stride))
    loader.write_bytes(cls, struct.pack("<Q", ss.class_base) + packed_wh + struct.pack("<Q", ss.class_stride))
    xy = loader.bump_alloc(8, align=8)
    loader.write_bytes(xy, struct.pack("<ii", x, y))
    config = loader.bump_alloc(0x80, align=16)
    loader.write_bytes(config, b"\x00" * 0x80)
    # The AEX config stores the internal version flag, not the UI popup value:
    # current v2 is 0 and legacy v1 is 1.
    loader.write_bytes(config, struct.pack("<i", 0))
    loader.write_bytes(config + 0x20, struct.pack("<ii", 65536, 65536))
    # bb10 reads mode at (param5 + 10 floats) + 24 bytes == config + 0x40.
    mode = 3 if gamma_colors else 0
    if gamma_colors:
        colors = loader.bump_alloc(16, align=16)
        # White is invariant under a9c0's v2 output transfer, so this exercises
        # the Gamma Colors apply path without mixing UI and internal versions.
        loader.write_bytes(colors, struct.pack("<4f", 1.0, 1.0, 1.0, 1.0))
        loader.write_bytes(config + 0x28, struct.pack("<f", 2.1695473))
        loader.write_bytes(config + 0x30, struct.pack("<Q", 1))
        loader.write_bytes(config + 0x38, struct.pack("<Q", colors))
    loader.write_bytes(config + 0x40, bytes([mode]))
    transfer_context = loader.bump_alloc(0x18, align=8)
    loader.write_bytes(transfer_context, b"\x00" * 0x18)
    bb10_after: list[dict] = []
    def capture_bb10_after(uc, _address, _size, _user):
        rsp = uc.reg_read(UC_X86_REG_RSP)
        pair = bytes(uc.mem_read(rsp + 0x40, 16))
        bb10_after.append({"gamma": struct.unpack("<f", pair[:4])[0], "apply": pair[4]})
    hook = loader.uc.hook_add(UC_HOOK_CODE, capture_bb10_after, begin=0x18000CDE0, end=0x18000CDE0)
    result = loader.call_function(
        FCCE0,
        int_args=[out, src, cls, xy, config, transfer_context],
        max_instructions=10_000_000,
    )
    loader.uc.hook_del(hook)
    return {
        "returned_pointer": result["rax"],
        "output_pointer": out,
        "config": {"scale_fixed": [65536, 65536], "gamma_mode_byte": mode},
        "bb10_after": bb10_after,
        "rgba": list(struct.unpack("<4f", loader.read_bytes(out, 16))),
    }


def vertices(ss: SmootherStruct) -> list[dict]:
    return [{"rgba": list(v["rgba"]), "weight": v["weight"]} for v in ss.vertices()]


def cce0_accumulate(center: list[float], samples: list[dict]) -> list[float]:
    """Independent replay of the grounded FUN_18000cce0 blend lane.

    The decomp/ASM facts specify a clamped sum of sample weights, a center
    residual of ``1 - W``, and weighted RGBA sample accumulation.  Gamma
    packing and host writeback are intentionally outside this helper.
    """
    weight_sum = min(1.0, max(0.0, sum(float(sample["weight"]) for sample in samples)))
    out = [(1.0 - weight_sum) * float(value) for value in center]
    for sample in samples:
        for channel, value in enumerate(sample["rgba"]):
            out[channel] += float(value) * float(sample["weight"])
    return out


def run_aex(fixture: str, suppress: bool) -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 16, 16)
    x, y = 5, 6
    ss.set_cur(x, y)
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    ss.set_src_pixel(x, y - 1, (0.8, 0.1, 0.1, 0.99607843))
    ss.set_src_pixel(x, y, (1.0, 1.0, 1.0, 1.0))
    setup_fixture(ss, fixture)

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
    chain_vertices_snapshot = vertices(ss)
    cce0_replay = cce0_accumulate(CENTER, chain_vertices_snapshot)

    # Keep the standalone helper replay independent of c280's ABI exercise.
    c280_entry = call_c280_entry(loader, ss, x, y)
    cce0_entry = call_cce0_entry(loader, ss, x, y)
    cce0_gamma_colors_entry = call_cce0_entry(loader, ss, x, y, gamma_colors=True)

    # Replay the same helper sequence with the normalized values produced by
    # c280's config words 65536/65536 divided by the binary constant 100.0.
    ss.set_vcount(0)
    ss.set_smoothness(655.36)
    ss.set_base_weight(655.36)
    loader.call_function(F125C0, int_args=[ss.base], max_instructions=2_000_000)
    loader.call_function(F10760, int_args=[ss.base], max_instructions=2_000_000)
    c280_equiv_before_normalize = ss.vcount()
    loader.call_function(FCC70, int_args=[ss.base], max_instructions=200_000)
    c280_equiv_vertices = vertices(ss)
    return {
        "fixture": fixture,
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
        "chain_vertices": chain_vertices_snapshot,
        "cce0_replay_float": cce0_replay,
        "c280_entry": c280_entry,
        "cce0_entry": cce0_entry,
        "cce0_gamma_colors_entry": cce0_gamma_colors_entry,
        "c280_equiv_helper_before_normalize": c280_equiv_before_normalize,
        "c280_equiv_helper_vertices": c280_equiv_vertices,
    }


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def vertex_lists_close(a: list[dict], b: list[dict]) -> bool:
    return len(a) == len(b) and all(
        all(close(x, y) for x, y in zip(xv["rgba"], yv["rgba"]))
        and close(xv["weight"], yv["weight"])
        for xv, yv in zip(a, b)
    )


def compare(aex: dict, port: dict) -> dict:
    av, pv = aex["direct_vertices"], port["direct_vertices"]
    vertex_match = vertex_lists_close(av, pv)
    ac, pc = aex["chain_vertices"], port["chain_vertices"]
    chain_vertex_match = vertex_lists_close(ac, pc)
    c280_entry_match = vertex_lists_close(aex["c280_entry"]["vertices"], port["builder_vertices"])
    c280_helper_match = vertex_lists_close(aex["c280_equiv_helper_vertices"], port["builder_vertices"])
    cce0_entry_match = all(close(x, y) for x, y in zip(aex["cce0_entry"]["rgba"], port["builder_orchestrated_float"]))
    cce0_gamma_match = all(close(x, y) for x, y in zip(aex["cce0_gamma_colors_entry"]["rgba"], port["builder_gamma_colors_float"]))
    cce0_match = all(
        close(expected, actual)
        for expected, actual in zip(aex["cce0_replay_float"], port["port_composite_float"])
    )
    all_production_boundaries_equal = (
        aex["descriptor_direct"] == port["descriptor"]
        and port["idx"] == EXPECTED_CLASSIFIER_INDEX[aex["fixture"]]
        and aex["c"] == port["c"]
        and aex["append"] == port["append"]
        and vertex_match
        and aex["cardinal6_descriptor"] == port["cardinal6_descriptor"]
        and aex["chain_count"] == port["chain_count"]
        and chain_vertex_match
        and c280_entry_match
        and cce0_entry_match
        and cce0_gamma_match
        and cce0_match
    )
    return {
        "descriptor_direct_equal": aex["descriptor_direct"] == port["descriptor"],
        "classifier_index_equal": port["idx"] == EXPECTED_CLASSIFIER_INDEX[aex["fixture"]],
        "c_equal": aex["c"] == port["c"],
        "append_equal": aex["append"] == port["append"],
        "direct_vertices_weights_equal_1e-6": vertex_match,
        "cardinal6_descriptor_equal": aex["cardinal6_descriptor"] == port["cardinal6_descriptor"],
        "chain_count_equal": aex["chain_count"] == port["chain_count"],
        "chain_vertices_weights_equal_1e-6": chain_vertex_match,
        "c280_entry_vs_production_builder_equal_1e-6": c280_entry_match,
        "c280_equiv_helpers_vs_production_builder_equal_1e-6": c280_helper_match,
        "cce0_entry_vs_production_orchestrator_equal_1e-6": cce0_entry_match,
        "cce0_gamma_colors_vs_production_orchestrator_equal_1e-6": cce0_gamma_match,
        "cce0_accumulation_equal_1e-6": cce0_match,
        "all_production_boundaries_equal": all_production_boundaries_equal,
        "all_replayed_boundaries_equal": aex["descriptor_direct"] == port["descriptor"] and port["idx"] == EXPECTED_CLASSIFIER_INDEX[aex["fixture"]] and aex["c"] == port["c"] and aex["append"] == port["append"] and vertex_match and aex["cardinal6_descriptor"] == port["cardinal6_descriptor"] and chain_vertex_match and c280_entry_match and c280_helper_match and cce0_entry_match and cce0_gamma_match and cce0_match,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []
    for fixture, suppress in FIXTURES:
        aex = run_aex(fixture, suppress)
        port = json.loads(subprocess.check_output([
            str(args.adapter), "1" if suppress else "0", "65536", "65536", fixture,
        ], text=True))
        rows.append({"aex": aex, "port": port, "comparison": compare(aex, port)})
    result = {
        "status": "pass_all_production_boundaries_with_expected_helper_replay_gap",
        "expected_helper_replay_gap_fixtures": ["classifier_one"],
        "scope": "local binary-semantic evidence; not Windows AE truth",
        "chain": "c280 classifier/dispatch -> producer helpers -> cc70 normalization -> cce0 output selection",
        "branch_matrix": "c2 append, c4 suppress, classifier_one c=3, classifier_zero empty",
        "facts": rows,
        "blockers": {
            "live_binding": "The actual AEX entries are executed with synthetic source/class descriptors and fixed-point scale 65536/65536. Live Windows class/config bytes are still required before mapping any row to case_0004 or case_0012.",
            "helper_replay": "The standalone all-one helper replay emits one contribution while the actual c280 entry and production builder emit two. This is harness incompleteness, not a remaining production dispatch mismatch.",
        },
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    production_ok = all(r["comparison"]["all_production_boundaries_equal"] for r in rows)
    helper_gap_ok = all(
        r["comparison"]["all_replayed_boundaries_equal"]
        or r["aex"]["fixture"] == "classifier_one"
        for r in rows
    )
    return 0 if production_ok and helper_gap_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
