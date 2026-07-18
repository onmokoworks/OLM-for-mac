#!/usr/bin/env python3
"""Prove the first signed geometry boundary before KiraKira's assertion.

This is an evidence-only runner over the natural actual-AEX Unicorn fixture.
It does not patch the packed argument, write a replacement object field, or
skip the FilterEngine failure.  The proof is deliberately narrower than the
existing packed-size lineage reports: it follows the two raw dwords from the
row-geometry registers into the source object and then into FilterEngine's
signed fields.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_signed_geometry_boundary_20260718.json"
MARKDOWN = ROOT / "refs/conformance/olmkirakira_signed_geometry_boundary_20260718.md"

sys.path.insert(0, str(ROOT / "tools/emulation"))
common = importlib.import_module("test_olmkirakira_mode2_common_owner_20260717")

RAW_WIDTH = 0x80000000
RAW_ANCHOR_X = 0xC0000000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed_i32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def static_witness() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    asm_tokens = [
        "181281ef8  MOV R14D,dword ptr [RBP + 0x7f]",
        "181281efc  TEST R14D,R14D",
        "181281eff  JNS 0x181281f0c",
        "181281f01  MOV EAX,R15D",
        "181281f04  CDQ",
        "181281f05  SUB EAX,EDX",
        "181281f07  SAR EAX,0x1",
        "181281f09  MOV R14D,EAX",
        "18128257a  MOV dword ptr [RBX + 0x8],R15D",
        "18128257e  MOV dword ptr [RBX + 0xc],R14D",
        "1812b9b38  MOV qword ptr [RDI + 0x14],RAX",
        "1812b9b4d  MOV qword ptr [RDI + 0x1c],RAX",
        "1812b9b77  MOV R14D,dword ptr [RDI + 0x14]",
        "1812b9b7b  CMP EAX,R14D",
    ]
    decomp_tokens = [
        "FUN_181281e90",
        "if (param_5 < 0)",
        "param_5 = param_4 / 2",
        "FUN_1812b98e0",
        "FUN_181280fa0",
    ]
    return {
        "aex_sha256": sha256(AEX),
        "asm_sha256": sha256(ASM),
        "decomp_sha256": sha256(DECOMP),
        "asm_tokens": asm_tokens,
        "asm_tokens_present": {token: token in asm for token in asm_tokens},
        "decomp_tokens": decomp_tokens,
        "decomp_tokens_present": {token: token in decomp for token in decomp_tokens},
        "raw_to_signed_i32": {
            "0x80000000": signed_i32(RAW_WIDTH),
            "0xc0000000": signed_i32(RAW_ANCHOR_X),
        },
    }


def run() -> dict[str, object]:
    runtime = common.run_owner_probe()
    stores = runtime.get("row_sum_target_store_capture", [])
    source_reads = [
        item for item in runtime.get("filter_lineage_trace", [])
        if item.get("kind") == "filterengine_source_read_site"
    ]
    filter_stores = [
        item for item in runtime.get("filter_lineage_trace", [])
        if item.get("kind") == "filterengine_store_post"
    ]
    assertion = runtime.get("filter_assertion_capture", {})
    return {
        "status": runtime.get("status"),
        "execution_stop": runtime.get("execution_stop"),
        "row_geometry_register_store": stores,
        "source_reads": source_reads,
        "filterengine_stores": filter_stores,
        "filterengine_assertion": assertion,
    }


def source_geometry_observed(source_reads: list[dict[str, object]]) -> dict[str, object] | None:
    for read in source_reads:
        r8 = read.get("r8", {})
        if not isinstance(r8, dict):
            continue
        i32_values = r8.get("i32", {})
        raw = r8.get("raw_hex", "")
        if isinstance(i32_values, dict) and i32_values.get("+0x08") == signed_i32(RAW_WIDTH) and i32_values.get("+0x0c") == signed_i32(RAW_ANCHOR_X):
            return {"object": r8, "raw_geometry_hex": raw}
    return None


def main() -> int:
    static = static_witness()
    runtime = run()
    stores = runtime["row_geometry_register_store"]
    source = source_geometry_observed(runtime["source_reads"])
    filter_stores = runtime["filterengine_stores"]
    assertion = runtime["filterengine_assertion"]

    row_store = stores[-1] if stores else {}
    width_register = int(row_store.get("r15d_before_store", -1))
    anchor_register = int(row_store.get("r14d_before_store", -1))
    ksize_store = next((item for item in filter_stores if item.get("label", "").startswith("ksize.width")), {})
    anchor_store = next((item for item in filter_stores if item.get("label", "").startswith("anchor.x")), {})
    compared = assertion.get("compared_fields", {})

    checks = {
        "static_asm_boundary_present": all(static["asm_tokens_present"].values()),
        "static_decomp_context_present": all(static["decomp_tokens_present"].values()),
        "row_register_width_raw": width_register == RAW_WIDTH,
        "row_register_anchor_raw": anchor_register == RAW_ANCHOR_X,
        "default_anchor_generation_present": all(
            static["asm_tokens_present"][token]
            for token in (
                "181281ef8  MOV R14D,dword ptr [RBP + 0x7f]",
                "181281f01  MOV EAX,R15D",
                "181281f04  CDQ",
                "181281f05  SUB EAX,EDX",
                "181281f07  SAR EAX,0x1",
                "181281f09  MOV R14D,EAX",
            )
        )
        and all(
            static["decomp_tokens_present"][token]
            for token in ("if (param_5 < 0)", "param_5 = param_4 / 2")
        ),
        "source_object_signed_width": bool(source and source["object"].get("i32", {}).get("+0x08") == signed_i32(RAW_WIDTH)),
        "source_object_signed_anchor": bool(source and source["object"].get("i32", {}).get("+0x0c") == signed_i32(RAW_ANCHOR_X)),
        "filterengine_width_store_raw": ksize_store.get("store_source") == "0x180000000",
        "filterengine_anchor_store_raw": anchor_store.get("store_source") == "0xc0000000",
        "assertion_signed_fields": compared == {
            "+0x14 ksize.width": signed_i32(RAW_WIDTH),
            "+0x18 ksize.height": 1,
            "+0x1c anchor.x": signed_i32(RAW_ANCHOR_X),
            "+0x20 anchor.y": 0,
        },
        "assertion_unmodified_fail_closed": assertion.get("stop_without_mutation") is True,
    }
    status = "PASS_SIGNED_GEOMETRY_BOUNDARY_FAIL_CLOSED" if all(checks.values()) else "FAIL_CLOSED"
    report = {
        "kind": "olmkirakira_signed_geometry_boundary",
        "schema": 1,
        "date": "2026-07-18",
        "status": status,
        "classification": "AEX_GENERATED_SIGNED_FILTER_GEOMETRY" if status.startswith("PASS_") else "UNRESOLVED",
        "ae_exact_claim": False,
        "platform_scope": "Mac-only Unicorn actual-AEX execution of checked-in Windows PE; no Windows/After Effects claim",
        "question": "Where is 0xc0000000 first generated, and how does it reach the signed FilterEngine geometry that fails the assertion?",
        "answer": {
            "width": "R15D=0x80000000 -> source object +0x08 -> FilterEngine ksize.width=-2147483648",
            "anchor_x": "FUN_181281e90 default-anchor branch: param_5 < 0 -> param_4 / 2 -> R14D=0xc0000000, then source object +0x0c -> FilterEngine anchor.x=-1073741824",
            "interpretation_boundary": "The first proven generation of 0xc0000000 is FUN_181281e90's default-anchor calculation. The row-geometry object store is the next observed boundary, and later FilterEngine fields preserve the same 32-bit words as signed int32 values.",
            "not_host_parameter": "The observed geometry words are register/object values in the AEX lineage, not a parameter checkout value.",
        },
        "checks": checks,
        "static": static,
        "runtime": runtime,
        "limits": [
            "No argument, object, source, or assertion value was patched.",
            "The FilterEngine assertion remained the terminal boundary.",
            "No Windows execution, After Effects host binding, final pixel, or AE-exactness claim.",
            "This proof does not establish why the upstream algorithm intentionally produced these words; it only fixes their first observed AEX geometry boundary.",
        ],
        "fact_inference": {
            "FACT": [
                "The checked-in assembly contains the listed register stores, object stores, FilterEngine stores, and assertion compare.",
                "The natural actual-AEX run observed the raw register words and the signed assertion fields without mutation.",
            ],
            "INFERENCE": [
                "The invalid geometry is generated inside the AEX row-geometry path rather than being directly copied from the host parameter surface.",
                "A future fix must explain or replace this upstream geometry construction; changing only the assertion or final pixels would violate the evidence boundary.",
            ],
        },
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# OLMKiraKira signed geometry boundary

Date: 2026-07-18

## Result

- Status: **{status}**
- Classification: **{report['classification']}**
- This is a Mac-only Unicorn actual-AEX proof, not an AE exact result.

## FACT

- `FUN_181281e90` stores `R15D=0x80000000` at source `+0x08` and `R14D=0xc0000000` at source `+0x0c`.
- The same raw words reach FilterEngine's `ksize.width` and `anchor.x` stores.
- The unmodified assertion observes `ksize.width=-2147483648` and `anchor.x=-1073741824`, then stops without mutation.

## INFERENCE

The first proven generation of `0xc0000000` is the `FUN_181281e90` default-anchor branch: when `param_5 < 0`, the AEX computes `param_4 / 2` (`CDQ; SUB; SAR`) and writes the result to `R14D`. The value is then stored at source `+0x0c` and forwarded to FilterEngine as signed `anchor.x`. The values are generated AEX geometry, not a direct host-parameter value. This does not justify a patch yet.

## Verification

```text
python3 tools/emulation/test_olmkirakira_signed_geometry_boundary_20260718.py
```

The JSON report contains the full runtime evidence, static hashes, gates, and limits.
"""
    MARKDOWN.write_text(md, encoding="utf-8")
    print(json.dumps({"status": status, "classification": report["classification"], "checks": checks, "report": str(REPORT)}, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
