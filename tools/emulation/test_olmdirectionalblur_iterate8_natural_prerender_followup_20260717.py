#!/usr/bin/env python3
"""Follow the natural 8bpc render gates and fail closed on missing writes."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

from PIL import Image
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import (
    UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9,
    UC_X86_REG_RAX, UC_X86_REG_RIP, UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_iterate8_natural_prerender_followup_20260717.json"
POPULATE = 0x180006980
ROTATE = 0x180001EC0
OUTPUT = 0x180006B30


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_fixture():
    sys.path.insert(0, str(FIXTURE_PATH.parent))
    import dblur_fullrender_host_fixture_20260711 as fixture  # noqa: E402

    return fixture


def f32_cell(loader, address: int) -> list[float]:
    return list(struct.unpack("<4f", loader.read_bytes(address, 16)))


def call_summary(result: dict) -> dict:
    return {key: result[key] for key in ("instructions", "rax", "rip") if key in result}


def main() -> int:
    fixture = load_fixture()
    state: dict = {"writer_cell": None, "source_ready": False}
    events: list[dict] = []
    callback_slots: dict[str, str] = {}

    class TracingLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.write_events: list[dict] = []
            TracingLoader.last = self

            def trace_write(uc, _access, address, size, value, _user_data):
                cell = state["writer_cell"]
                if cell is not None and address < cell + 16 and address + size > cell:
                    self.write_events.append({
                        "address": hex(address), "size": size, "value": hex(value),
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                    })

            self.uc.hook_add(UC_HOOK_MEM_WRITE, trace_write)

        def install_callback(self, label, handler):
            address = super().install_callback(label, handler)
            callback_slots[hex(address)] = label
            return address

    def actual_populate(loader, params: int, y: int, x: int, pixel: bytes) -> None:
        pixel_ptr = loader.bump_alloc(4, align=4)
        loader.write_bytes(pixel_ptr, pixel)
        # call_function() owns the shared loader stack and cannot be nested
        # inside PF_Iterate8. Save the outer AEX context and use a private,
        # mapped return target so RET resumes this callback, not a stub slot.
        saved = loader.uc.context_save()
        try:
            result = loader.call_function(
                POPULATE, int_args=[params, x, y, pixel_ptr], max_instructions=10000,
            )
            callback_rax = result["rax"]
        finally:
            loader.uc.context_restore(saved)
        result = {"instructions": result.get("instructions"), "rax": callback_rax,
                  "return_target": hex(0x90000000)}
        source_base = fixture.u64(loader, params + 0x8078)
        writer_base = fixture.u64(loader, params + 0x8090)
        stride = fixture.u32(loader, params + 0x80A0)
        row0 = fixture.u32(loader, params + 0x8098)
        col0 = fixture.u32(loader, params + 0x809C)
        index = (row0 + y) * stride + col0 + x
        source_cell = source_base + index * 16
        writer_cell = writer_base + index * 16
        if x == 0 and y == 0 and stride == 26 and not state["source_ready"]:
            state.update({"writer_cell": writer_cell, "source_ready": True})
            events.append({
                "event": "real_populate_return", "entry": hex(POPULATE), "xy": [x, y],
                "params": hex(params), "callback_result": call_summary(result),
                "source_base_0x8078": hex(source_base), "writer_base_0x8090": hex(writer_base),
                "source_cell": hex(source_cell), "writer_cell": hex(writer_cell),
                "source_rgba_f32": f32_cell(loader, source_cell),
                "writer_rgba_f32_before_downstream": f32_cell(loader, writer_cell),
            })

    def downstream_output_checkpoint(loader, params: int, y: int, x: int, out: bytearray, out_ptr: int, width: int) -> None:
        # The requested witness stops at the first transform write. Do not
        # replace that write with a host-side output model or fabricate output.
        del loader, params, y, x, out, out_ptr, width

    fixture.AexLoader = TracingLoader
    fixture.model_populate = actual_populate
    fixture.model_output = downstream_output_checkpoint
    with tempfile.TemporaryDirectory(prefix="olm_directionalblur_prerender_followup_") as name:
        temp = Path(name)
        source = temp / "source_16x16.png"
        Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
        output = temp / "fixture.json"
        sys.argv = [
            str(FIXTURE_PATH), "--source", str(source), "--output", str(output),
            "--angle", "0", "--downsample-num", "1", "--downsample-den", "1",
            "--front-strength", "8", "--size-variation", "0", "--front-sharp-tail", "0",
            "--back-strength", "0", "--back-alpha-fade", "0", "--noise-variation", "0",
            "--world-area", "0", "0", "16", "16", "--row-padding", "12",
            "--no-detour-rotate", "--max-instructions", "20000000",
        ]
        fixture_status = fixture.main()
        fixture_report = json.loads(output.read_text(encoding="utf-8"))

    loader = TracingLoader.last
    if loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: no natural loader")
    downstream = [event for event in loader.write_events if event["rip"] != hex(POPULATE)]
    first = downstream[0] if downstream else None
    branches = fixture_report["execution"]["early_branches"]
    gates = [item for item in branches if item["label"] in {
        "render_worker_entry", "depth_read", "checkout_input_return", "checkout_output_return",
        "depth_dispatch_compare", "8bpc_setup_error_test", "param_read_return",
        "param_read_error_test", "call_8bpc_worker",
    }]
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_iterate8_natural_prerender_followup",
        "status": "pass" if first else "blocked",
        "claim_scope": "Natural Mac-local 8bpc AEX path; first distinct writer-cell write only if observed",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
            "fixture": str(FIXTURE_PATH.relative_to(ROOT)), "fixture_sha256": sha256(FIXTURE_PATH),
            "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE),
        },
        "natural_prerender_owner": {
            "owner": "FUN_180007bd0",
            "depth_owner": "param_6[0]+0x2c, read into R12W at 0x180007c12",
            "8bpc_condition": "R12W == 8 at 0x180007c65; otherwise branch leaves 8bpc path",
            "error_conditions": [
                "PF checkout_input return in EBX must be zero before 0x180007c53",
                "PF checkout_output return in EBX must be zero before 0x180007cb7",
                "FUN_180006c50 return in EBX must be zero before 0x180007cde",
            ],
            "observed_gates": gates,
            "fixture_status": fixture_report["status"],
            "fixture_blocked": fixture_report.get("blocked"),
            "continuation_boundary": {
                "kind": ("actual-rotate-helper-boundary"
                          if "first_iterate" in fixture_report["execution"]["checkpoints"]
                          and "rotate" in fixture_report["execution"]["checkpoints"]
                          and len(fixture_report["execution"].get("rowdriver_calls", [])) == 0
                          else ("post-first-iterate-worker-return"
                                if "first_iterate" in fixture_report["execution"]["checkpoints"]
                                and "rotate" in fixture_report["execution"]["checkpoints"]
                                and len(fixture_report["execution"]["iterate_calls"]) == 1
                                else "fixture-reported-boundary")),
                "last_rip": (fixture_report.get("blocked", {}).get("last_rips", [])[-1]
                             if fixture_report.get("blocked", {}).get("last_rips") else None),
                "raw_fixture_reason": fixture_report.get("blocked", {}).get("reason"),
                "raw_fixture_message": fixture_report.get("blocked", {}).get("message"),
                "function": hex(ROTATE),
                "worker_loop": fixture_report["execution"].get("worker_loop", []),
                "rowdriver_calls": len(fixture_report["execution"].get("rowdriver_calls", [])),
                "rotate_entries": len(fixture_report["execution"].get("rotate_entry", [])),
            },
            "synthetic_callback_target": {
                "fault_rip": fixture_report.get("blocked", {}).get("last_rip"),
                "fault_callback_slot": callback_slots.get(fixture_report.get("blocked", {}).get("last_rip")),
                "callback_slots": callback_slots,
                "grounded_populate_return": hex(0x90000000),
            },
            "downstream_reach": {
                "first_iterate": "first_iterate" in fixture_report["execution"]["checkpoints"],
                "rotate": "rotate" in fixture_report["execution"]["checkpoints"],
                "downstream_iterate": len(fixture_report["execution"]["iterate_calls"]) > 1,
                "output_callback": "final_host_output" in fixture_report["execution"]["checkpoints"],
            },
        },
        "target": {
            "real_populate": events[0] if events else None,
            "first_distinct_write_0x8078_to_0x8090": first,
            "all_distinct_writes": downstream[:16],
            "transform_entry": hex(ROTATE),
            "writer_entry": hex(OUTPUT),
        },
        "fail_closed": {
            "production_source_edited": False, "ledger_edited": False,
            "windows_values_fabricated": False, "output_fabricated": False,
            "ae_exact_claim": False,
        },
        "command": "python3 tools/emulation/test_olmdirectionalblur_iterate8_natural_prerender_followup_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(REPORT.relative_to(ROOT)),
                      "fixture_status": fixture_status, "first_write_rip": first["rip"] if first else None}))
    # A missing write is an evidence result, not a harness crash. The JSON
    # status remains blocked and the null write field is the fail-closed claim.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
