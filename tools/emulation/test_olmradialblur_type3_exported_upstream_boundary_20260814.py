#!/usr/bin/env python3
"""Pin the upstream Windows exported-render boundary for Radial Type 3.

This is deliberately a static, read-only boundary.  It proves that the pinned
Windows AEX passes an uninitialized stack member as the destination of a
0x78-byte PF_LayerDef copy when Noise Type is Layer.  It does not turn an
emulator crash observation into native-AE evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex"
ASM = ROOT / "disasm/OLMRadialBlur.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMRadialBlur.aex.c.txt"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
TYPED = ROOT / "refs/conformance/olmradialblur_type3_all_depth_public_closure_20260813.json"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_exported_upstream_boundary_20260814.json"
DOC = ROOT / "refs/conformance/olmradialblur_type3_exported_upstream_boundary_20260814.md"

PINS = {
    "aex": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "asm": "feaf9366c4cff7fc726bea62af94f8b6a638d08fb597844463e3a6274c0b3971",
    "decomp": "6d3f0cfc60883762d129940de2a717b8c6dd1efea7e06c254da259fef6b0e2f1",
    "source": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_block(text: str, name: str) -> str:
    marker = f"; === {name} @ "
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"missing assembly function {name}")
    end = text.find("\n; === FUN_", start + len(marker))
    return text[start:] if end < 0 else text[start:end]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def generate() -> dict[str, Any]:
    live = {name: sha256(path) for name, path in {
        "aex": AEX, "asm": ASM, "decomp": DECOMP, "source": SOURCE,
    }.items()}
    require(live == PINS, f"pinned input drift: {live}")
    asm = ASM.read_text()
    caller = function_block(asm, "FUN_1800040f0")
    materialize = function_block(asm, "FUN_180008690")
    copy_param = function_block(asm, "FUN_18000d9d0")
    copy_world = function_block(asm, "FUN_180019f20")

    # The 0xb0-byte render-info object begins at RSP+0x40.  No instruction or
    # prior callee receives/writes the member at +0xa8 (RSP+0xe8) before the
    # materializer is called.
    before_call = caller.split("1800041c7  CALL 0x180008690", 1)[0]
    require("1800041b9  LEA R9,[RSP + 0x40]" in caller, "render-info base call ABI drift")
    require("[RSP + 0xe8]" not in before_call, "render-info +0xa8 is now initialized")
    require("1800041a6  LEA RCX,[RSP + 0xf0]" in before_call, "adjacent helper-object layout drift")

    # Noise Type 3 loads the untouched member and passes it as the destination
    # pointer for parameter 0x15 (the Noise Layer).
    required_materialize = [
        "1800088b0  CMP dword ptr [RDI + 0x50],0x3",
        "1800088b6  MOV R9,qword ptr [RDI + 0xa8]",
        "1800088bd  MOV R8D,0x15",
        "1800088c9  CALL 0x18000d9d0",
    ]
    for token in required_materialize:
        require(token in materialize, f"missing Type3 materializer anchor: {token}")
    require(materialize.count("[RDI + 0xa8]") == 1, "unexpected +0xa8 access count")

    # The pointer is forwarded as RDX to a fixed 0x78-byte PF_LayerDef copy.
    for token in (
        "18000d9f4  MOV RBP,R9",
        "18000da58  MOV RDX,RBP",
        "18000da60  CALL 0x180019f20",
    ):
        require(token in copy_param, f"missing layer-copy forwarding anchor: {token}")
    stores = re.findall(r"MOV(?:UPS|SD) (?:xmmword|qword) ptr \[RDX(?: \+ 0x([0-9a-f]+))?\]", copy_world)
    normalized = [0 if value == "" else int(value, 16) for value in stores]
    require(normalized == [0, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70],
            f"PF_LayerDef copy stores drift: {normalized}")

    typed = json.loads(TYPED.read_text())
    require(typed.get("status") == "pass" and len(typed.get("rows", [])) == 45,
            "bounded typed-owner closure drift")
    return {
        "schema": "olmradialblur.type3-exported-upstream-boundary/1",
        "status": "PASS_STATIC_UPSTREAM_EXPORTED_TYPE3_DESTINATION_UNINITIALIZED_TYPED_OWNER_RETAINED",
        "identities": {
            "aex_sha256": live["aex"],
            "assembly_sha256": live["asm"],
            "decomp_sha256": live["decomp"],
            "production_source_sha256": live["source"],
            "typed_owner_report": str(TYPED.relative_to(ROOT)),
            "typed_owner_report_sha256": sha256(TYPED),
        },
        "static_chain": {
            "render_info_stack_base": "RSP+0x40",
            "noise_layer_member": "+0xa8 (RSP+0xe8)",
            "initialized_before_materializer": False,
            "noise_type_layer_value": 3,
            "parameter_index": "0x15",
            "member_load_rva": "0x1800088b6",
            "materializer_call_rva": "0x1800088c9",
            "copy_forward_call_rva": "0x18000da60",
            "fixed_copy_rva": "0x180019f20",
            "fixed_copy_bytes": 0x78,
        },
        "production_policy": {
            "windows_exported_type3_is_numerical_oracle": False,
            "bounded_windows_typed_owner_retained": True,
            "mac_public_45_row_admission_unchanged": True,
            "unlisted_source_layer_tuple_geometry_fail_closed": True,
        },
        "claims_not_made": [
            "No native Windows After Effects execution",
            "No durable dynamic crash-register or crash-address claim",
            "No claim that AEXCompat caused or repairs the upstream destination",
            "No arbitrary Type3 source, Layer, tuple, geometry, or layout claim",
        ],
    }


def validate(report: dict[str, Any]) -> None:
    require(set(report) == {"schema", "status", "identities", "static_chain", "production_policy", "claims_not_made"},
            "top-level schema drift")
    require(report["schema"] == "olmradialblur.type3-exported-upstream-boundary/1", "schema mismatch")
    require(report["status"] == "PASS_STATIC_UPSTREAM_EXPORTED_TYPE3_DESTINATION_UNINITIALIZED_TYPED_OWNER_RETAINED", "status mismatch")
    require(set(report["identities"]) == {"aex_sha256", "assembly_sha256", "decomp_sha256", "production_source_sha256", "typed_owner_report", "typed_owner_report_sha256"}, "identity schema drift")
    require(report["static_chain"] == generate()["static_chain"], "static chain drift")
    require(report["production_policy"] == {
        "windows_exported_type3_is_numerical_oracle": False,
        "bounded_windows_typed_owner_retained": True,
        "mac_public_45_row_admission_unchanged": True,
        "unlisted_source_layer_tuple_geometry_fail_closed": True,
    }, "production policy drift")
    require(report["claims_not_made"] == generate()["claims_not_made"], "claim boundary drift")
    live = generate()["identities"]
    require(report["identities"] == live, "identity drift")


def markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OLMRadialBlur Type 3 exported upstream boundary (2026-08-14)",
        "",
        f"Status: `{report['status']}`",
        "",
        "The pinned Windows AEX exported render constructs its local render-info object at `RSP+0x40`, but does not initialize the Noise Layer destination member at `+0xa8` before calling the parameter materializer. Noise Type 3 loads that member at `0x1800088b6`; the downstream helper forwards it as the destination of the fixed 0x78-byte PF_LayerDef copy at `0x180019f20`.",
        "",
        "Therefore the exported Type 3 route is not a usable numerical oracle. The bounded typed Windows owner remains the authority for the existing 45 exact Mac public rows. Production admission is unchanged and every unlisted source/Layer/tuple/geometry/layout remains fail-closed.",
        "",
        "This is static AEX evidence only. It does not claim native Windows AE execution or durable dynamic crash registers/addresses.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    # validate() regenerates only from pinned read-only inputs.
    validate(live)
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(live))
    else:
        require(REPORT.is_file() and DOC.is_file(), "canonical evidence missing")
        saved = json.loads(REPORT.read_text())
        validate(saved)
        require(saved == live and DOC.read_text() == markdown(live), "canonical evidence drift")
    print("PASS_OLMRADIALBLUR_TYPE3_EXPORTED_UPSTREAM_STATIC_BOUNDARY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
