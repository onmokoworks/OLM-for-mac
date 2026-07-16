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
from unicorn import UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE
from unicorn.x86_const import (
    UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9,
    UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RBP, UC_X86_REG_RSI,
    UC_X86_REG_RDI, UC_X86_REG_R10, UC_X86_REG_R11, UC_X86_REG_R12,
    UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R15,
    UC_X86_REG_RIP, UC_X86_REG_RSP, UC_X86_REG_XMM2, UC_X86_REG_XMM3,
    UC_X86_REG_XMM5, UC_X86_REG_XMM6,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_iterate8_natural_prerender_followup_20260717.json"
POPULATE = 0x180006980
ROTATE = 0x180001EC0
OUTPUT = 0x180006B30
ROTATE_SAMPLE = 0x180002064
ROTATEBACK_CALL = 0x180005628
ROTATEBACK_RETURN = 0x18000562D
OUTPUT_ITERATE_CALL = 0x180005665
PRIVATE_STACK = 0x60000000
PRIVATE_STACK_SIZE = 0x10000
PRIVATE_RETURN = 0x820FFFF0
GLOBAL_RETURN = 0x90000000


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


def u64_bytes(loader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def register_snapshot(loader, address: int) -> dict:
    registers = {
        "rax": UC_X86_REG_RAX, "rbx": UC_X86_REG_RBX,
        "rcx": UC_X86_REG_RCX, "rdx": UC_X86_REG_RDX,
        "rsi": UC_X86_REG_RSI, "rdi": UC_X86_REG_RDI,
        "rbp": UC_X86_REG_RBP, "rsp": UC_X86_REG_RSP,
        "r8": UC_X86_REG_R8, "r9": UC_X86_REG_R9,
        "r10": UC_X86_REG_R10, "r11": UC_X86_REG_R11,
        "r12": UC_X86_REG_R12, "r13": UC_X86_REG_R13,
        "r14": UC_X86_REG_R14, "r15": UC_X86_REG_R15,
    }
    values = {name: loader.uc.reg_read(reg) for name, reg in registers.items()}
    pointer_names = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "r8", "r9")
    pointers = {}
    for name in pointer_names:
        value = values[name]
        try:
            pointers[name] = {"address": hex(value), "qword": hex(u64_bytes(loader, value))}
        except Exception:
            pointers[name] = {"address": hex(value), "qword": None}
    xmm = {}
    for name, reg in (("xmm2", UC_X86_REG_XMM2), ("xmm3", UC_X86_REG_XMM3),
                      ("xmm5", UC_X86_REG_XMM5), ("xmm6", UC_X86_REG_XMM6)):
        raw = loader.uc.reg_read(reg).to_bytes(16, "little")
        xmm[name] = {"low_f32": struct.unpack("<f", raw[:4])[0], "raw": raw.hex()}
    return {
        "rip": hex(address),
        "registers": {name: hex(value) for name, value in values.items()},
        "readable_pointer_qwords": pointers,
        "xmm": xmm,
    }


def main() -> int:
    fixture = load_fixture()
    state: dict = {
        "writer_cell": None, "source_ready": False, "private_calls": 0,
        "continuations": [],
    }
    events: list[dict] = []
    checkpoints: dict[str, dict] = {}
    callback_slots: dict[str, str] = {}

    class TracingLoader(fixture.AexLoader):
        last = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.write_events: list[dict] = []
            self.uc.mem_map(PRIVATE_STACK, PRIVATE_STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
            TracingLoader.last = self

            def trace_write(uc, _access, address, size, value, _user_data):
                cell = state["writer_cell"]
                if cell is not None and address < cell + 16 and address + size > cell:
                    self.write_events.append({
                        "address": hex(address), "size": size, "value": hex(value),
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                    })

            self.uc.hook_add(UC_HOOK_MEM_WRITE, trace_write)
            self.add_code_hook(
                ROTATE_SAMPLE,
                lambda ld, address, _size: checkpoints.setdefault(
                    "rotate_sample_0x180002064", register_snapshot(ld, address)
                ),
            )
            for address, label in (
                (ROTATEBACK_CALL, "rotateback_call_0x180005628"),
                (ROTATEBACK_RETURN, "rotateback_return_0x18000562d"),
                (OUTPUT_ITERATE_CALL, "output_iterate_call_0x180005665"),
            ):
                self.add_code_hook(
                    address,
                    lambda ld, hit, _size, label=label: checkpoints.setdefault(
                        label, register_snapshot(ld, hit)
                    ),
                )

        def install_callback(self, label, handler):
            address = super().install_callback(label, handler)
            callback_slots[hex(address)] = label
            return address

    def call_actual_callback(loader, address: int, args: list[int], max_instructions: int = 10000) -> dict:
        """Run real callback code without stopping or overwriting the outer render frame."""
        saved = loader.uc.context_save()
        outer_rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        outer_frame = loader.read_bytes(outer_rsp, 0x68)
        stack_top = PRIVATE_STACK + PRIVATE_STACK_SIZE - 0x100
        stack_top &= ~0xF
        stack_pointer = stack_top - 8
        loader.write_bytes(stack_pointer, struct.pack("<Q", PRIVATE_RETURN))
        for index, value in enumerate(args[4:]):
            loader.write_bytes(
                stack_pointer + 0x28 + index * 8,
                struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF),
            )
        for reg, value in zip(
            (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9), args
        ):
            loader.uc.reg_write(reg, value)
        loader.uc.reg_write(UC_X86_REG_RSP, stack_pointer)
        loader.uc.reg_write(UC_X86_REG_RIP, address)
        before = loader.instructions_executed
        try:
            loader.uc.emu_start(address, PRIVATE_RETURN, count=max_instructions)
            result = {
                "instructions": loader.instructions_executed - before,
                "rax": loader.uc.reg_read(UC_X86_REG_RAX),
                "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
                "return_target": hex(PRIVATE_RETURN),
            }
            if loader.uc.reg_read(UC_X86_REG_RIP) != PRIVATE_RETURN:
                raise RuntimeError(
                    "real callback did not return to private sentinel: "
                    f"entry=0x{address:x} rip={result['rip']}"
                )
        finally:
            loader.uc.context_restore(saved)
        frame_after = loader.read_bytes(outer_rsp, 0x68)
        if frame_after != outer_frame:
            raise RuntimeError("outer PF_Iterate8 callback frame changed during real callback")
        state["private_calls"] += 1
        result["outer_frame_preserved"] = True
        return result

    def actual_populate(loader, params: int, y: int, x: int, pixel: bytes) -> None:
        pixel_ptr = loader.bump_alloc(4, align=4)
        loader.write_bytes(pixel_ptr, pixel)
        callback_rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        first_frame = None
        if x == 0 and y == 0 and not events:
            first_frame = {
                "rsp": hex(callback_rsp),
                "return_rip": hex(u64_bytes(loader, callback_rsp)),
                "rect_rsp_0x28": hex(u64_bytes(loader, callback_rsp + 0x28)),
                "refcon_rsp_0x30": hex(u64_bytes(loader, callback_rsp + 0x30)),
                "callback_rsp_0x38": hex(u64_bytes(loader, callback_rsp + 0x38)),
                "dst_rsp_0x40": hex(u64_bytes(loader, callback_rsp + 0x40)),
                "raw_0x00_0x67": loader.read_bytes(callback_rsp, 0x68).hex(),
            }
        result = call_actual_callback(loader, POPULATE, [params, x, y, pixel_ptr])
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
                "iterate8_frame": first_frame,
                "params": hex(params), "callback_result": call_summary(result),
                "source_base_0x8078": hex(source_base), "writer_base_0x8090": hex(writer_base),
                "source_cell": hex(source_cell), "writer_cell": hex(writer_cell),
                "source_rgba_f32": f32_cell(loader, source_cell),
                "writer_rgba_f32_before_downstream": f32_cell(loader, writer_cell),
            })

    def actual_output(loader, params: int, y: int, x: int, out: bytearray, out_ptr: int, width: int) -> None:
        del out, width
        result = call_actual_callback(loader, OUTPUT, [params, x, y, 0, out_ptr])
        if state["source_ready"]:
            checkpoints.setdefault("real_output_callback_0x180006b30", {
                "entry": hex(OUTPUT), "xy": [x, y], "params": hex(params),
                "out_ptr": hex(out_ptr), "callback_result": call_summary(result),
                "pixels_copied_to_host_model": False,
            })

    fixture.AexLoader = TracingLoader
    fixture.model_populate = actual_populate
    fixture.model_output = actual_output
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
        live_loader = TracingLoader.last
        if live_loader is not None:
            for attempt in range(1, 5):
                start = live_loader.uc.reg_read(UC_X86_REG_RIP)
                if start == GLOBAL_RETURN:
                    break
                record = {"attempt": attempt, "start_rip": hex(start)}
                try:
                    live_loader.uc.emu_start(start, GLOBAL_RETURN, count=20000000)
                    record["end_rip"] = hex(live_loader.uc.reg_read(UC_X86_REG_RIP))
                except Exception as exc:
                    record.update({
                        "end_rip": hex(live_loader.uc.reg_read(UC_X86_REG_RIP)),
                        "error": type(exc).__name__, "message": str(exc),
                    })
                state["continuations"].append(record)
                if "error" in record or record["end_rip"] == hex(GLOBAL_RETURN):
                    break
                if record["end_rip"] == record["start_rip"]:
                    record["error"] = "no-progress"
                    break
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
    required_checkpoints = (
        ("real_populate_return_0x180006980", bool(events),
         "real 0x180006980 callback return and preserved PF_Iterate8 frame"),
        ("rotate_sample_0x180002064", "rotate_sample_0x180002064" in checkpoints,
         "live rotate registers and readable pointer state at 0x180002064"),
        ("rotateback_call_0x180005628", "rotateback_call_0x180005628" in checkpoints,
         "natural worker state reaching the rotateback call at 0x180005628"),
        ("rotateback_return_0x18000562d", "rotateback_return_0x18000562d" in checkpoints,
         "ABI/state required for FUN_180001ec0 to return to 0x18000562d"),
        ("output_iterate_call_0x180005665", "output_iterate_call_0x180005665" in checkpoints,
         "natural PF_Iterate8 output-call frame at 0x180005665"),
        ("real_output_callback_0x180006b30", "real_output_callback_0x180006b30" in checkpoints,
         "second PF_Iterate8 ABI/state invoking real callback 0x180006b30"),
    )
    first_missing = next((item for item in required_checkpoints if not item[1]), None)
    blocked = None
    if first_missing is not None:
        fixture_blocked = fixture_report.get("blocked", {})
        blocked = {
            "reason": "missing-natural-abi-state",
            "first_missing_checkpoint": first_missing[0],
            "required": first_missing[2],
            "fixture_reason": fixture_blocked.get("reason"),
            "fixture_message": fixture_blocked.get("message"),
            "fixture_last_rip": (
                fixture_blocked.get("last_rip")
                or (fixture_blocked.get("last_rips") or [None])[-1]
            ),
        }
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_iterate8_natural_prerender_followup",
        "status": "blocked" if blocked else "pass",
        "claim_scope": "Natural Mac-local 8bpc AEX continuation; no modeled pixel output",
        "blocked": blocked,
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
            "fixture_report_phase": "before explicit live-state continuation",
            "fixture_blocked": fixture_report.get("blocked"),
            "continuation_boundary": {
                "kind": ("second-real-output-callback"
                          if "real_output_callback_0x180006b30" in checkpoints
                          else "first-missing-natural-abi-state"),
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
                "old_global_return_with_emu_stop": hex(0x90000000),
                "private_return_without_emu_stop": hex(PRIVATE_RETURN),
                "private_stack": [hex(PRIVATE_STACK), hex(PRIVATE_STACK + PRIVATE_STACK_SIZE)],
                "private_callback_calls": state["private_calls"],
                "outer_continuations": state["continuations"],
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
            "natural_continuation_checkpoints": checkpoints,
            "required_checkpoint_order": [
                {"checkpoint": name, "observed": observed, "required_state": required}
                for name, observed, required in required_checkpoints
            ],
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
    # Missing natural state is an evidence result, not a harness crash.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
