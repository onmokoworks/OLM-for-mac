"""Actual-AEX PF8 worker tie-break witness for a radius-1 3x1 row."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_R10,
    UC_X86_REG_R12,
    UC_X86_REG_RSP,
    UC_X86_REG_RDI,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmtoondilate_pf16_pf32_copy_boundary_20260716 import (  # noqa: E402
    alloc,
    context_and_suite,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
REPORT = ROOT / "refs/conformance/olmtoondilate_pf8_tie_break_20260717.md"
JSON_REPORT = REPORT.with_suffix(".json")
WORKER = 0x1801A6150
HELPER = 0x1801AC880
TIE_BRANCH = tuple(range(0x1801A63E1, 0x1801A645A))
COPY_CALL = 0x1801A64DD
COPY_RESUME = 0x1801A64E2
FUNCTION_HASH_SIZE = 0x100
EXPECTED_AEX_SHA256 = "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"
EXPECTED_WORKER_FUNCTION_SHA256 = "500bda28032d0ecf005415cc9488e8348c1b20e5b99f7c0c61f976cbae10f647"
WIDTH = 3
PIXEL_BYTES = 4
ROWBYTES = WIDTH * PIXEL_BYTES + 4
PADDING = b"\xA5" * 4
T = bytes((0, 0, 0, 0))
A = bytes((255, 10, 20, 30))
B = bytes((255, 90, 80, 70))


def make_world(loader: AexLoader, values: list[bytes]) -> tuple[int, int]:
    payload = bytearray(ROWBYTES)
    for index, value in enumerate(values):
        payload[index * PIXEL_BYTES:(index + 1) * PIXEL_BYTES] = value
    payload[WIDTH * PIXEL_BYTES:] = PADDING
    payload_ptr = alloc(loader, bytes(payload), align=64)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload_ptr)
    struct.pack_into("<i", header, 0x20, ROWBYTES)
    struct.pack_into("<i", header, 0x24, WIDTH)
    struct.pack_into("<i", header, 0x28, 1)
    struct.pack_into("<H", header, 0x2C, 32)
    return alloc(loader, bytes(header)), payload_ptr


def raw(loader: AexLoader, address: int, size: int) -> list[int]:
    return list(loader.read_bytes(address, size))


def provenance() -> dict[str, object]:
    actual_aex = hashlib.sha256(AEX.read_bytes()).hexdigest() if AEX.exists() else None
    result: dict[str, object] = {
        "aex_sha256": actual_aex,
        "expected_aex_sha256": EXPECTED_AEX_SHA256,
        "worker": hex(WORKER),
        "worker_function_hash_size": FUNCTION_HASH_SIZE,
        "expected_worker_function_sha256": EXPECTED_WORKER_FUNCTION_SHA256,
    }
    if actual_aex != EXPECTED_AEX_SHA256:
        result["first_unavailable_abi"] = "AEX provenance hash mismatch; native worker not attempted"
        return result
    try:
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        actual_worker = hashlib.sha256(bytes(loader.read_bytes(WORKER, FUNCTION_HASH_SIZE))).hexdigest()
        result["worker_function_sha256"] = actual_worker
        if actual_worker != EXPECTED_WORKER_FUNCTION_SHA256:
            result["first_unavailable_abi"] = "worker byte-window hash mismatch; native worker not attempted"
    except Exception as exc:
        result["first_unavailable_abi"] = f"{type(exc).__name__}: {exc}"
    return result


def run_one(label: str, source: list[bytes], gate: dict[str, object]) -> dict[str, object]:
    item: dict[str, object] = {"order": label, "input": [list(v) for v in source], "status": "BLOCKED"}
    if "first_unavailable_abi" in gate:
        item["first_unavailable_abi"] = gate["first_unavailable_abi"]
        return item
    try:
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        source_world, source_payload = make_world(loader, source)
        destination_world, destination_payload = make_world(loader, [T, T, T])
        worlds = {
            source_world: {"payload": source_payload, "width": WIDTH, "height": 1, "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
            destination_world: {"payload": destination_payload, "width": WIDTH, "height": 1, "rowbytes": ROWBYTES, "pixel_size": PIXEL_BYTES},
        }
        events: list[dict[str, object]] = []
        context = context_and_suite(loader, events, worlds)
        radius = alloc(loader, struct.pack("<f", 1.0), align=16)
        tie_events: list[dict[str, object]] = []
        helper_events: list[dict[str, object]] = []
        copy_events: list[dict[str, object]] = []

        def regs(current: AexLoader) -> dict[str, object]:
            rsp = current.uc.reg_read(UC_X86_REG_RSP)
            return {
                "r8d": current.uc.reg_read(UC_X86_REG_R8),
                "r9d": current.uc.reg_read(UC_X86_REG_R9),
                "r10d": current.uc.reg_read(UC_X86_REG_R10),
                "r12d": current.uc.reg_read(UC_X86_REG_R12),
                "edi": current.uc.reg_read(UC_X86_REG_RDI),
                "return_address": hex(struct.unpack("<Q", current.read_bytes(rsp, 8))[0]),
            }

        def on_tie(current: AexLoader, address: int, _size: int) -> None:
            snapshot = regs(current)
            snapshot["address"] = hex(address)
            tie_events.append(snapshot)

        def on_helper(current: AexLoader, _address: int, _size: int) -> None:
            rcx = current.uc.reg_read(UC_X86_REG_RCX)
            rdx = current.uc.reg_read(UC_X86_REG_RDX)
            helper_events.append({"source": hex(rcx), "destination": hex(rdx),
                                  "source_raw_before": raw(current, rcx, PIXEL_BYTES),
                                  "destination_raw_before": raw(current, rdx, PIXEL_BYTES)})

        def on_copy(current: AexLoader, address: int, _size: int) -> None:
            copy_events.append({"address": hex(address), "source": hex(current.uc.reg_read(UC_X86_REG_RCX)),
                                "destination": hex(current.uc.reg_read(UC_X86_REG_RDX))})

        def on_resume(_current: AexLoader, address: int, _size: int) -> None:
            copy_events.append({"address": hex(address), "kind": "copy_resume"})

        for address in TIE_BRANCH:
            loader.add_code_hook(address, on_tie)
        loader.add_code_hook(HELPER, on_helper)
        loader.add_code_hook(COPY_CALL, on_copy)
        loader.add_code_hook(COPY_RESUME, on_resume)
        call = loader.call_function(WORKER, int_args=[context, 0, source_world, destination_world, radius], max_instructions=2_000_000)
        output = raw(loader, destination_payload, ROWBYTES)
        item.update({
            "status": "RETURN",
            "worker_return_rax": hex(call["rax"]),
            "worker_instructions": call["instructions"],
            "tie_branch_events": tie_events,
            "helper_events": helper_events,
            "copy_call_resume_events": copy_events,
            "output_raw_immediately_after_worker_return": output,
            "output_pixels": [output[i * PIXEL_BYTES:(i + 1) * PIXEL_BYTES] for i in range(WIDTH)],
            "padding_preserved": output[WIDTH * PIXEL_BYTES:] == list(PADDING),
            "events": events,
        })
        return item
    except Exception as exc:
        item["first_unavailable_abi"] = f"{type(exc).__name__}: {exc}"
        return item


def run() -> dict[str, object]:
    gate = provenance()
    paired = [run_one("A,T,B", [A, T, B], gate), run_one("B,T,A", [B, T, A], gate)]
    gates = {
        "provenance_hash_gate_passed": "first_unavailable_abi" not in gate,
        "both_workers_returned": all(x.get("status") == "RETURN" for x in paired),
        "both_tie_branches_observed": all(x.get("tie_branch_events") for x in paired),
        "both_helpers_observed": all(x.get("helper_events") for x in paired),
        "copy_call_and_resume_observed": all({COPY_CALL, COPY_RESUME} <= {int(e["address"], 16) for e in x.get("copy_call_resume_events", [])} for x in paired),
        "raw_captured_after_return": all("output_raw_immediately_after_worker_return" in x for x in paired),
        "center_retains_first_forward_winner": paired[0].get("output_pixels", [[], [], []])[1] == list(A) and paired[1].get("output_pixels", [[], [], []])[1] == list(B),
        "padding_preserved": all(x.get("padding_preserved") is True for x in paired),
    }
    status = "PASS_PF8_WORKER_TIE_BREAK" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    return {
        "status": status,
        "aex": str(AEX.relative_to(ROOT)),
        "worker": hex(WORKER),
        "worker_abi": "(context, unused, source_world, destination_world, radius_ptr)",
        "helper": hex(HELPER),
        "tie_branch": [hex(TIE_BRANCH[0]), hex(TIE_BRANCH[-1])],
        "copy_call": hex(COPY_CALL),
        "copy_resume": hex(COPY_RESUME),
        "fixture": {"width": WIDTH, "height": 1, "rowbytes": ROWBYTES, "radius": 1.0, "pixel_format": "PF8 ARGB", "paired_orders": ["A,T,B", "B,T,A"]},
        "pixels": {"A": list(A), "T": list(T), "B": list(B), "padding": list(PADDING)},
        "provenance": gate,
        "paired_runs": paired,
        "gates": gates,
        "claim_boundary": "Bounded actual-AEX PF8 worker tie-break observation under local Unicorn; no general distance, host/AE exact, all tie-order, or case0003 closure claim.",
    }


def main() -> int:
    payload = run()
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text("\n".join([
        "# OLMToonDilate PF8 Worker Tie-Break - 2026-07-17", "", "## Result", "",
        f"- Status: **{payload['status']}**", f"- AEX: `{payload['aex']}`", f"- AEX SHA-256: `{payload['provenance'].get('aex_sha256')}`",
        f"- Worker ABI: `{payload['worker_abi']}`", f"- Worker/helper: `{payload['worker']}` / `{payload['helper']}`",
        "- Fixture: PF8 3x1, radius 1, rowbytes 16 with a four-byte `0xA5` sentinel.",
        "- Paired inputs are `[A,T,B]` and `[B,T,A]`; output is read immediately after native worker return.",
        "", "## FACT", "", "- Instrumentation records the tie branch, helper entry, copy call `0x1801A64DD`, and resume `0x1801A64E2`.",
        "- The decisive bounded observation is center output equal to x0 in both paired runs.",
        "- Hash mismatch or execution failure remains `BLOCKED_FAIL_CLOSED` and exits nonzero.",
        "", "## Limits", "", "- This does not claim general distance semantics, host/AE exactness, all tie orders, or case0003 closure.",
        "", "## Reproduce", "", "```sh", "tools/emulation/.venv/bin/python tools/emulation/probe_olmtoondilate_pf8_tie_break_20260717.py", "```", "",
    ]) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS_PF8_WORKER_TIE_BREAK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
