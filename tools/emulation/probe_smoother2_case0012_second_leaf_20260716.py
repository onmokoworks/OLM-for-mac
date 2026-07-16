#!/usr/bin/env python3
"""Mac-local witness for the case0012 gamma second leaf.

The accepted current-case binding is used only to gate the exact descriptor
and first-append fact. The second-leaf observation is local checked-in AEX
execution plus a portable adapter; no Windows second-leaf internals are made
up or imported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402
from test_smoother2_producer import (  # noqa: E402
    AEX_PATH,
    SmootherStruct,
    FUN_18000e170,
    FUN_18000f270,
)

F_DF30 = 0x18000DF30
F_F130 = 0x18000F130
F_FEF0 = 0x18000FEF0
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
DESCRIPTOR = [92, 841, 1, 92, 842, 2]
BINDING_JSON = ROOT / "refs/conformance/olmsmoother2_legacy_key_setup_producer_witness_20260716.json"
BINDING_MD = ROOT / "refs/conformance/olmsmoother2_legacy_key_producer_actual_aex_20260716.md"


def require_binding() -> dict:
    if not BINDING_JSON.exists() or not BINDING_MD.exists():
        raise RuntimeError("current-case binding unavailable: accepted JSON/MD pair is required")
    binding = json.loads(BINDING_JSON.read_text(encoding="utf-8"))
    accepted = binding.get("windows_typed_witness", {})
    if (
        binding.get("fixture", {}).get("case_id") != CASE_ID
        or accepted.get("status") != "accepted_current_case"
        or accepted.get("descriptor") != DESCRIPTOR
        or "e170_c=7" not in BINDING_MD.read_text(encoding="utf-8")
        or "vertex_count=1" not in BINDING_MD.read_text(encoding="utf-8")
    ):
        raise RuntimeError("current-case binding failed closed: case id, descriptor, e170=7, or first count=1 missing")
    return {"case_id": CASE_ID, "descriptor": DESCRIPTOR, "accepted_first_count": 1, "accepted_e170": 7}


def call(loader: AexLoader, function: int, base: int, desc: int, float_arg: float = 1.0) -> int:
    result = loader.call_function(function, int_args=[base, desc, 0], float_args={2: (float_arg, "f")}, max_instructions=500_000)
    return result["rax"] & 0xFF


def run_aex() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    loader.register_libm_impls()
    ss = SmootherStruct(loader, 128, 850)
    ss.set_cur(DESCRIPTOR[0], DESCRIPTOR[1])
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    ss.set_class_pixel(92, 841, b0=255)
    ss.set_class_pixel(92, 840, b0=255)
    ss.set_class_pixel(91, 841, b0=0, b1=255)
    ss.set_vcount(0)
    d = loader.bump_alloc(24, align=16)
    loader.write_bytes(d, __import__("struct").pack("<6i", *DESCRIPTOR))
    before = ss.vcount()
    first_pred = call(loader, FUN_18000e170, ss.base, d)
    first_ret = call(loader, FUN_18000f270, ss.base, d)
    after_first = ss.vcount()
    second_pred = call(loader, F_DF30, ss.base, d)
    second_ret = call(loader, F_F130, ss.base, d)
    after_second = ss.vcount()
    vertices = ss.vertices()
    returned = None
    if after_second > after_first:
        returned = {"source_xy": [DESCRIPTOR[3], DESCRIPTOR[4] + 1], "rgba": list(vertices[-1]["rgba"]), "weight": vertices[-1]["weight"]}
    ss.set_vcount(0)
    loader.call_function(F_FEF0, int_args=[ss.base, d], max_instructions=1_000_000)
    dispatch_count = ss.vcount()
    return {
        "engine": "checked_in_aex_unicorn_mac_local",
        "entry": {"first_predicate_e170": first_pred, "second_predicate_df30": second_pred},
        "first_leaf": {"name": "f270->e3a0", "return_low": first_ret, "append": after_first > before, "count_before": before, "count_after": after_first},
        "second_leaf": {"name": "f130->e290", "return_low": second_ret, "append": after_second > after_first, "count_before": after_first, "count_after": after_second, "returned_vertex": returned},
        "dispatcher": {"name": "fef0", "key": DESCRIPTOR[2] - 1 + DESCRIPTOR[5] * 10, "count_after": dispatch_count},
        "vertices_total": after_second,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    binding = require_binding()
    aex = run_aex()
    portable = json.loads(subprocess.check_output([str(args.adapter)], text=True))
    comparison = {
        "descriptor_equal": portable["descriptor"] == DESCRIPTOR,
        "first_predicate_matches_binding": aex["entry"]["first_predicate_e170"] == binding["accepted_e170"],
        "aex_portable_second_predicate_equal": aex["entry"]["second_predicate_df30"] == portable["entry"]["second_predicate_df30"],
        "aex_portable_second_append_equal": aex["second_leaf"]["append"] == portable["second_leaf"]["append"],
        "aex_portable_count_after_equal": aex["second_leaf"]["count_after"] == portable["second_leaf"]["count_after"],
        "aex_portable_dispatch_count_equal": aex["dispatcher"]["count_after"] == portable["dispatcher"]["count_after"],
        "dispatcher_selects_two_leaf_case": aex["dispatcher"]["key"] == 0x14 and aex["dispatcher"]["count_after"] == 2,
        "local_count_exceeds_accepted_first_count": aex["second_leaf"]["count_after"] > binding["accepted_first_count"],
    }
    result = {
        "verdict": "PASS_MAC_CASE0012_SECOND_LEAF_BOUNDARY" if all(comparison.values()) else "FAIL_MAC_CASE0012_SECOND_LEAF_BOUNDARY",
        "scope": "Accepted current-case descriptor plus checked-in AEX and portable dispatcher; live Windows evidence ends at first count=1",
        "binding": binding,
        "aex": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest(), "trace": aex},
        "portable": portable,
        "comparison": comparison,
        "claims_not_made": ["No live Windows f130/df30/e290 return values", "No live Windows post-second-leaf polygon capture", "No AE-host execution", "No production-source change"],
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
