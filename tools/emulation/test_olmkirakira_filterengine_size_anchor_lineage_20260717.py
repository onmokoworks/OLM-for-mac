#!/usr/bin/env python3
"""Prove the actual-AEX producer lineage of KiraKira FilterEngine geometry.

This is an evidence runner only.  It reuses the existing natural common-owner
fixture, records the actual-AEX CPU observations already exposed by that
runner, and checks the corresponding static assembly.  It never writes the
invalid values, changes the FilterEngine object, or suppresses the exception.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmkirakira_filterengine_size_anchor_lineage_20260717.json"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"

sys.path.insert(0, str(ROOT / "tools/emulation"))
common = importlib.import_module("test_olmkirakira_mode2_common_owner_20260717")

EXPECTED_ASM = {
    "source_geometry_words": [
        "18128257a  MOV dword ptr [RBX + 0x8],R15D",
        "18128257e  MOV dword ptr [RBX + 0xc],R14D",
    ],
    "filterengine_stores": [
        "1812b9b34  MOV RAX,qword ptr [RBP + -0x59]",
        "1812b9b38  MOV qword ptr [RDI + 0x14],RAX",
        "1812b9b3c  MOV ECX,dword ptr [RDX + 0xc]",
        "1812b9b3f  MOV EAX,dword ptr [R8 + 0xc]",
        "1812b9b49  MOV RAX,qword ptr [RBP + -0x59]",
        "1812b9b4d  MOV qword ptr [RDI + 0x1c],RAX",
    ],
    "assertion_reads": [
        "1812b9b77  MOV R14D,dword ptr [RDI + 0x14]",
        "1812b9b7b  CMP EAX,R14D",
        "1812b9b84  MOV EAX,dword ptr [RDI + 0x20]",
        "1812b9b8f  CMP EAX,dword ptr [RDI + 0x18]",
    ],
}


def static_witness() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    # Keep the checked-in register-producing stores explicit so a different
    # disassembly cannot silently pass.
    observed = {
        name: [line for line in lines if line in asm]
        for name, lines in EXPECTED_ASM.items()
    }
    return {
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "asm_sha256": hashlib.sha256(ASM.read_bytes()).hexdigest(),
        "expected": EXPECTED_ASM,
        "observed": observed,
        "all_expected_present": all(len(observed[name]) == len(lines) for name, lines in EXPECTED_ASM.items()),
        "producer_function": "FUN_181281e90",
        "filterengine_function": "FUN_1812b98e0 cv::FilterEngine::init",
    }


def compact_runtime(runtime: dict[str, object]) -> dict[str, object]:
    assertion = runtime.get("filter_assertion_capture", {})
    stores = [
        item for item in runtime.get("filter_lineage_trace", [])
        if item.get("kind") == "filterengine_store_post"
        and item.get("address") in {"0x1812b9b3c", "0x1812b9b51"}
    ]
    source_writes = runtime.get("row_sum_target_store_capture", [])
    reads = [
        item for item in runtime.get("filter_lineage_trace", [])
        if item.get("kind") == "filterengine_source_read_site"
        and item.get("instruction_rip") in {"0x1812b9b27", "0x1812b9b3c", "0x1812b9b3f", "0x1812b9b46"}
    ]
    row_trace = runtime.get("row_sum_runtime_trace", [])
    row_generation = [
        item for item in row_trace
        if item.get("address") in {"0x181281f04", "0x181281f05", "0x181281f07", "0x181281f0c"}
    ]
    return {
        "status": runtime.get("status"),
        "execution_stop": runtime.get("execution_stop"),
        "filterengine_assertion": assertion,
        "filterengine_stores": stores,
        "source_object_writes": source_writes,
        "source_reads": reads,
        "row_geometry_generation_trace": row_generation,
        "parameter_checkout_values": [
            {"disk_id": item.get("disk_id"), "name": item.get("name"), "value": item.get("grounded_value")}
            for item in runtime.get("callback", {}).get("param_checkout", [])
        ],
    }


def main() -> int:
    static = static_witness()
    runtime = common.run_owner_probe()
    compact = compact_runtime(runtime)
    assertion = compact["filterengine_assertion"]
    stores = compact["filterengine_stores"]
    source_writes = compact["source_object_writes"]
    store_values = {item.get("address"): item.get("store_source") for item in stores}
    source_values = {
        "0x18128257a": next((item.get("r15d_before_store") for item in source_writes if item.get("address") == "0x18128257a"), None),
        "0x18128257e": next((item.get("r14d_before_store") for item in source_writes if item.get("address") == "0x18128257a"), None),
    }
    checks = {
        "static_asm_present": static["all_expected_present"],
        "actual_filterengine_assertion_observed": assertion.get("rip") == "0x1812b9da8",
        "actual_invalid_fields_observed": assertion.get("compared_fields") == {
            "+0x14 ksize.width": -2147483648,
            "+0x18 ksize.height": 1,
            "+0x1c anchor.x": -1073741824,
            "+0x20 anchor.y": 0,
        },
        "ksize_store_from_r8_object": store_values.get("0x1812b9b3c") == "0x180000000" and stores[0].get("source_objects", {}).get("R8") is not None,
        "anchor_store_from_r8_object": store_values.get("0x1812b9b51") == "0xc0000000" and stores[-1].get("source_objects", {}).get("R8") is not None,
        "source_words_actual_writes": source_values.get("0x18128257a") == 0x80000000 and source_values.get("0x18128257e") == 0xC0000000,
        "no_value_patch_or_assertion_suppression": assertion.get("stop_without_mutation") is True,
    }
    report = {
        "kind": "olmkirakira_filterengine_size_anchor_lineage",
        "schema": 1,
        "date": "2026-07-17",
        "status": "PASS_LINEAGE_FAIL_CLOSED_STOP" if all(checks.values()) else "FAILED",
        "ae_exact_claim": False,
        "platform_scope": "Mac-only Unicorn actual-AEX execution of checked-in Windows PE; no Windows/AE claim",
        "question": "Which AEX object fields and instructions generate ksize.width=-2147483648 and anchor.x=-1073741824?",
        "answer": {
            "object": "FUN_1812b98e0 cv::FilterEngine::init object in RDI",
            "fields": {"RDI+0x14": "ksize.width", "RDI+0x1c": "anchor.x"},
            "immediate_store_instructions": ["0x1812b9b38", "0x1812b9b4d"],
            "immediate_store_sources": {"0x1812b9b38": "RAX=0x0000000180000000", "0x1812b9b4d": "RAX=0x00000000c0000000"},
            "upstream_generator": "FUN_181281e90 row-geometry branch; R15D=0x80000000 and R14D=0xc0000000 are written at 0x18128257a/0x18128257e, then consumed as R8 object fields at +0x08/+0x0c",
            "host_parameter_conclusion": "No host parameter checkout value is the raw source of either geometry word; parameter checkout is recorded only as negative control.",
        },
        "checks": checks,
        "static": static,
        "runtime": compact,
        "limits": [
            "No invalid value was patched into any object or source plane.",
            "The cv::FilterEngine assertion was not bypassed or suppressed.",
            "No typed writer, Windows execution, After Effects host binding, final pixel, or AE-exactness claim.",
            "Only this new runner and its two new evidence files are owned by this task.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "report": str(REPORT)}, sort_keys=True))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
