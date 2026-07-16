#!/usr/bin/env python3
"""Bound case0012 polygon state after f270 and unconditional f130.

Mac-only checked-in AEX CPU emulation versus the current portable leaf path.
Neither path calls cce0; both snapshots are taken before that stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from aex_loader import AexLoader  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
DESC = [92, 841, 1, 92, 842, 2]
KEY = 20
E170 = 0x18000E170
F270 = 0x18000F270
DF30 = 0x18000DF30
F130 = 0x18000F130
TOL = 1e-6

FIRST_RGBA = [0.18447503, 0.18447503, 0.18447503, 0.68235296]
SECOND_RGBA = [0.125, 0.25, 0.75, 0.625]


def close(a: float, b: float) -> bool:
    return abs(float(a) - float(b)) <= TOL


def snapshot(ss: SmootherStruct, boundary: str) -> dict:
    return {"boundary": boundary, "count": ss.vcount(), "vertices": ss.vertices()}


def call(loader: AexLoader, function: int, base: int, desc_ptr: int) -> int:
    result = loader.call_function(function, int_args=[base, desc_ptr, 0], float_args={2: (1.0, "f")}, max_instructions=500_000)
    return result["rax"] & 0xFF


def run_aex() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 128, 850)
    ss.set_cur(DESC[0], DESC[1])
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    # This class neighborhood is the accepted c=7 local realization.
    ss.set_class_pixel(92, 841, b0=255)
    ss.set_class_pixel(92, 840, b0=255)
    ss.set_class_pixel(91, 841, b0=0, b1=255)
    ss.set_src_pixel(92, 840, FIRST_RGBA)
    ss.set_src_pixel(92, 843, SECOND_RGBA)
    desc_ptr = loader.bump_alloc(24, align=16)
    loader.write_bytes(desc_ptr, struct.pack("<6i", *DESC))

    e170 = call(loader, E170, ss.base, desc_ptr)
    before = ss.vcount()
    f270 = call(loader, F270, ss.base, desc_ptr)
    after_f270 = snapshot(ss, "immediately_after_f270_before_f130")
    df30 = call(loader, DF30, ss.base, desc_ptr)
    f130 = call(loader, F130, ss.base, desc_ptr)
    after_f130 = snapshot(ss, "immediately_after_unconditional_f130_before_cce0")
    return {
        "engine": "checked_in_aex_unicorn_mac_local",
        "descriptor": DESC,
        "key": KEY,
        "entry": {"e170_c": e170, "df30": df30},
        "calls": {"f270_return_low": f270, "f130_return_low": f130, "count_before": before},
        "snapshots": {"after_f270": after_f270, "after_f130": after_f130},
        "cce0_called": False,
    }


def vertex_close(a: dict, b: dict) -> bool:
    return all(close(x, y) for x, y in zip(a["rgba"], b["rgba"])) and close(a["weight"], b["weight"])


def compare(aex: dict, portable: dict) -> dict:
    trace = aex
    a270 = trace["snapshots"]["after_f270"]
    p270 = portable["snapshots"]["after_f270"]
    a130 = trace["snapshots"]["after_f130"]
    p130 = portable["snapshots"]["after_f130"]
    checks = {
        "descriptor_equal": trace["descriptor"] == portable["descriptor"],
        "key_equal": trace["key"] == portable["key"],
        "e170_c_equal": trace["entry"]["e170_c"] == portable["entry"]["e170_c"] == 7,
        "df30_equal": trace["entry"]["df30"] == portable["entry"]["df30"],
        "f270_return_equal": trace["calls"]["f270_return_low"] == portable["calls"]["f270_return_low"],
        "f130_return_equal": trace["calls"]["f130_return_low"] == portable["calls"]["f130_return_low"],
        "after_f270_count_equal": a270["count"] == p270["count"] == 1,
        "after_f270_vertices_equal": len(a270["vertices"]) == len(p270["vertices"]) and all(vertex_close(a, b) for a, b in zip(a270["vertices"], p270["vertices"])),
        "after_f130_count_equal": a130["count"] == p130["count"] == 2,
        "after_f130_vertices_equal": len(a130["vertices"]) == len(p130["vertices"]) and all(vertex_close(a, b) for a, b in zip(a130["vertices"], p130["vertices"])),
        "first_vertex_expected": all(close(got, want) for got, want in zip(a270["vertices"][0]["rgba"], FIRST_RGBA)),
        "second_source_expected": all(close(got, want) for got, want in zip(a130["vertices"][1]["rgba"], SECOND_RGBA)),
        "no_cce0_aex": trace["cce0_called"] is False,
        "no_cce0_portable": portable["cce0_called"] is False,
    }
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    aex = run_aex()
    portable = json.loads(subprocess.check_output([str(args.adapter)], text=True))
    comparison = compare(aex, portable)
    result = {
        "verdict": "PASS_MAC_CASE0012_POST_LEAF_BOUNDARY" if all(comparison.values()) else "FAIL_MAC_CASE0012_POST_LEAF_BOUNDARY",
        "scope": "Mac-only actual-AEX CPU emulation versus current portable f270/f130 path; polygon captured before cce0; not AE exact",
        "case": {"id": CASE_ID, "descriptor": DESC, "key": KEY},
        "aex": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(), "trace": aex},
        "portable": portable,
        "comparison": comparison,
        "claims_not_made": ["No After Effects host execution", "No live Windows post-f130 polygon capture", "No AE-exact claim", "No production or PNG change"],
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
