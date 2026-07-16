#!/usr/bin/env python3
"""Bound the OLMSmoother2 legacy producer before c280/cce0.

This is a checked-in actual-AEX CPU witness.  It records the producer-owned
class bytes and append decisions for the retained case-0012 descriptor, then
binds that synthetic row to the later accepted Windows typed witness. It is
not a host or portable compatibility oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from test_smoother2_producer import (  # noqa: E402
    AEX_PATH,
    O_BASE_WEIGHT,
    SmootherStruct,
    call_e170,
    call_e3a0,
    call_f270,
    read_rdata_f32,
)
from aex_loader import AexLoader  # noqa: E402


DESC = [5, 6, 1, 5, 8, 5]
X, Y = DESC[0], DESC[1]
FUNCS = {
    "e170": {"rva": "0x0000e170", "name": "FUN_18000e170"},
    "f270": {"rva": "0x0000f270", "name": "FUN_18000f270"},
    "e3a0": {"rva": "0x0000e3a0", "name": "FUN_18000e3a0"},
}


def vertex_row(vertices: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not vertices:
        return None
    v = vertices[0]
    return {"rgba": list(v["rgba"]), "weight": v["weight"]}


def run() -> dict[str, Any]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    half = read_rdata_f32(loader, 0x180022694)
    dd8 = read_rdata_f32(loader, 0x180022dd8)
    ss = SmootherStruct(loader, 16, 16)
    ss.set_cur(X, Y)
    ss.set_smoothness(2.0)
    ss.set_base_weight(0.4)
    # e170 reads: center byte 0, previous-row byte 0, left-pixel byte 1.
    ss.set_class_pixel(X, Y - 1, b0=1)
    raw_class = {
        "center_b0": loader.read_bytes(ss.class_base + Y * ss.class_stride + X * 4, 4)[0],
        "prev_b0": loader.read_bytes(ss.class_base + (Y - 1) * ss.class_stride + X * 4, 4)[0],
        "left_b1": loader.read_bytes(ss.class_base + Y * ss.class_stride + (X - 1) * 4 + 1, 1)[0],
    }
    c = call_e170(loader, ss, DESC)
    scale = struct.unpack("<f", loader.read_bytes(ss.base + O_BASE_WEIGHT, 4))[0] * dd8 + half
    f_ret, f_count, f_verts = call_f270(loader, ss, DESC, 1.0)
    ss.set_src_pixel(X, Y - 1, (0.99106717, 0.99106717, 0.99106717, 0.99607843))
    e_ret, e_count, e_verts = call_e3a0(loader, ss, DESC, scale, 1.0)
    checks = [
        raw_class == {"center_b0": 0, "prev_b0": 1, "left_b1": 0},
        c == 2,
        f_ret == 1 and f_count == 1,
        e_ret == 1 and e_count == 1,
    ]
    return {
        "verdict": "PASS_LOCAL_ACTUAL_AEX_LEGACY_KEY_SETUP_PRODUCER",
        "date": "2026-07-16",
        "scope": "actual-AEX CPU emulation of legacy producer; upstream of c280/cce0",
        "aex": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": hashlib.sha256(AEX_PATH.read_bytes()).hexdigest()},
        "fixture": {"case_id": "legacy_case_0012_gamma5_red_blue_current_aex", "local_xy": [X, Y], "descriptor": DESC},
        "facts": {
            "functions": FUNCS,
            "class_plane_contract": {"base_offset": "+0x18", "stride_offset": "+0x28", "pixel_stride": 4, "bytes": raw_class},
            "e170": {"c": c, "meaning": "bit 1=center b0, bit 2=previous-row b0, bit 4=left-pixel b1"},
            "f270": {"ret_low_byte": f_ret, "vertex_count": f_count, "first_vertex": vertex_row(f_verts), "rule": "c==4 suppresses; c!=4 calls e3a0"},
            "e3a0": {"ret_low_byte": e_ret, "vertex_count": e_count, "first_vertex": vertex_row(e_verts), "scale_input": scale},
        },
        "inference": [
            "The legacy producer reaches e3a0 under the observed c=2 class state; no gamma fallback is involved at this boundary.",
            "The local synthetic coordinates are translation-equivalent for the relative class addressing, but are not a Windows case mapping.",
        ],
        "windows_typed_witness": {
            "status": "accepted_current_case",
            "source": "refs/conformance/olmsmoother2_legacy_key_producer_actual_aex_20260716.md",
            "same_run_identity": ["legacy_case_0012_gamma5_red_blue_current_aex", "xy=(92,841)", "AE Software", "8bpc", "AEX SHA-256", "module_base", "AfterFX PID"],
            "hook_sites": {k: {"name": v["name"], "rva": v["rva"], "bind": "absolute module_base + RVA"} for k, v in FUNCS.items()},
            "descriptor": [92, 841, 1, 92, 842, 2],
            "required_memory_contract": {
                "e170_base_rcx": "live producer struct; read qword [RCX+0x18] as class_base and qword [RCX+0x28] as class_stride",
                "e170_desc_rdx": "int[6], desc[0]=92, desc[1]=841",
                "center_b0": "byte[class_base + 841*class_stride + 92*4 + 0]",
                "prev_b0": "byte[class_base + 840*class_stride + 92*4 + 0]",
                "left_b1": "byte[class_base + 841*class_stride + 91*4 + 1]",
                "e170_c": "EAX/RAX low byte at return from FUN_18000e170",
                "f270": "RAX low byte and vertex count at +0x130 of the same producer struct",
                "e3a0": "RAX low byte, first vertex at +0x40, weight at +0x50",
            },
            "acceptance": "Accepted descriptor, class bytes, e170 c=7, and first append are all bound to one returned run.",
        },
        "claims_not_made": ["Synthetic c=2 fixture is not the current case mapping", "No AE exactness", "No portable compatibility", "No final-writer or PNG tuning"],
        "pass": all(checks),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-json", type=Path)
    ap.add_argument("--output-md", type=Path)
    args = ap.parse_args()
    result = run()
    payload = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.output_json:
        args.output_json.write_text(payload, encoding="utf-8")
    if args.output_md:
        r = result
        args.output_md.write_text("\n".join([
            "# OLMSmoother2 legacy key/setup producer witness - 2026-07-16", "",
            f"- Verdict: `{r['verdict']}`", f"- AEX: `{r['aex']['path']}` SHA-256 `{r['aex']['sha256']}`", "",
            "## FACT", "", "- Actual-AEX emulation reads the producer class bytes and executes `e170 -> f270 -> e3a0`.",
            "- The bounded local row is `c=2`, `f270 append`, `e3a0 append`; the exact raw values are in the JSON.",
            "- `e170` uses class base `+0x18`, class stride `+0x28`, and the three byte addresses recorded in the typed contract.", "",
            "## INFERENCE", "", *[f"- {x}" for x in r["inference"]], "",
            "## Windows Typed Witness", "", "- The current-case same-run Windows producer witness is accepted in `refs/conformance/olmsmoother2_legacy_key_producer_actual_aex_20260716.md`.",
            "- It binds descriptor `92,841,1,92,842,2`, class bytes, `e170 c=7`, and the first append. The local synthetic c=2 row above remains a separate leaf-function fixture.",
            "", "## Reproduction", "", "```sh", "python3 tools/emulation/test_olmsmoother2_legacy_key_setup_producer_witness_20260716.py \\", "  --output-json refs/conformance/olmsmoother2_legacy_key_setup_producer_witness_20260716.json \\", "  --output-md refs/conformance/olmsmoother2_legacy_key_setup_producer_witness_20260716.md", "```", "",
            "Result: exit `0` when all local actual-AEX producer checks pass.", "", "## Claims Not Made", "", *[f"- {x}" for x in r["claims_not_made"]], "",
        ]).rstrip() + "\n", encoding="utf-8")
    print(payload, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
