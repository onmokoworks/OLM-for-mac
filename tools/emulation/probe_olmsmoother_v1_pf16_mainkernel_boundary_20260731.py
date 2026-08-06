#!/usr/bin/env python3
"""Reproduce the run5 PF16 boundary call in the hash-pinned Windows AEX.

This is deliberately narrower than a render oracle.  It invokes the original
Windows ``FUN_180004b80`` with the exact arguments observed in the Mac run5
dump, intercepts its first call to ``FUN_180005f60``, and records the generated
coordinates before that callee can touch either image world.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.x86_const import (
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RIP,
    UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from aex_loader import AexLoader, STACK_BASE, STACK_SIZE  # noqa: E402

AEX_PATH = ROOT / "plugins_2025" / "OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
MAC_SOURCE_PATH = ROOT / "mac" / "OLMSmoother" / "Mac" / "OLMSmoother_port.cpp"
RUN5_DUMP_PATH = (
    ROOT
    / "refs"
    / "mac_validation_runs"
    / "olmsmoother_v1_32bpc_20260731_run5"
    / "crash_evidence"
    / "af0e9ca2-fd49-4729-b153-2e46a6f52b67.dmp"
)
RUN5_DUMP_SHA256 = "9095691989c52a95d1d9106aa728b308ac33b61cb2e630bb0fba0fd86d4d629c"

MAIN_INTERP_KERNEL16 = 0x180004B80
INTERP_EXECUTOR16 = 0x180005F60
RUN5_EVALUATOR_ENTRY_RSP_DELTA = -0x120
RUN5_EVALUATOR_SIZE = 0x14
RUN5_EVALUATOR_VTABLE = 0x18000D1D8

TABLE_ADDRESSES = {
    "reverse_0": 0x18000F000,
    "reverse_1": 0x18000F028,
    "reverse_2": 0x18000F050,
    "reverse_3": 0x18000F078,
    "pair_id": 0x18000F0A0,
    "dx": 0x18000F0C8,
    "dy": 0x18000F0F0,
}
EXPECTED_WINDOWS_TABLES = {
    "reverse_0": [6, 3, 0, 7, 4, 1, 8, 5, 2],
    "reverse_1": [2, 5, 8, 1, 4, 7, 0, 3, 6],
    "reverse_2": [3, 0, 1, 6, 4, 2, 7, 8, 5],
    "reverse_3": [1, 2, 5, 0, 4, 8, 3, 6, 7],
    "pair_id": [8, 7, 6, 5, 4, 3, 2, 1, 0],
    "dx": [-1, 0, 1, -1, 0, 1, -1, 0, 1],
    "dy": [-1, -1, -1, 0, 0, 0, 1, 1, 1],
}
MAC_TABLE_NAMES = {
    "reverse_0": "DAT_18000f000",
    "reverse_1": "DAT_18000f028",
    "reverse_2": "DAT_18000f050",
    "reverse_3": "DAT_18000f078",
    "pair_id": "DAT_18000f0a0",
    "dx": "DAT_18000f0c8",
    "dy": "DAT_18000f0f0",
}

# Exact MainInterpKernel16 entry arguments recovered from the run5 dump.
# Signed values are kept as Python ints; AexLoader writes their low 64 bits
# according to the Windows x64 ABI.
RUN5_ARGS = [
    0,   # state, replaced at runtime
    0,   # neighbor table, replaced at runtime
    0,   # center x
    3,   # center y
    5,   # direction
    2,   # kernel mode
    0,   # flag 1
    1,   # flag 2
    -1,  # endpoint A x
    4,   # endpoint A y
    0,   # endpoint B x
    3,   # endpoint B y
    0,   # endpoint C x
    3,   # endpoint C y
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def read_u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def signed_i32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def read_mac_source_tables() -> dict[str, list[int]]:
    source = MAC_SOURCE_PATH.read_text(encoding="utf-8")
    result: dict[str, list[int]] = {}
    for label, symbol in MAC_TABLE_NAMES.items():
        match = re.search(
            rf"static\s+const\s+int32_t\s+{re.escape(symbol)}\[(\d+)\]\s*=\s*\{{([^}}]+)\}}\s*;",
            source,
        )
        require(match is not None, f"Mac source table declaration missing: {symbol}")
        declared_count = int(match.group(1))
        values = [int(value.strip()) for value in match.group(2).split(",")]
        require(declared_count == len(values), f"{symbol} declaration/value count mismatch")
        result[label] = values
    return result


def execute() -> dict[str, object]:
    observed_sha = hashlib.sha256(AEX_PATH.read_bytes()).hexdigest()
    require(observed_sha == AEX_SHA256, f"Windows AEX SHA drift: {observed_sha}")
    observed_dump_sha = hashlib.sha256(RUN5_DUMP_PATH.read_bytes()).hexdigest()
    require(observed_dump_sha == RUN5_DUMP_SHA256, f"run5 dump SHA drift: {observed_dump_sha}")

    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    windows_tables = {
        name: list(struct.unpack("<9i", loader.read_bytes(address, 9 * 4)))
        for name, address in TABLE_ADDRESSES.items()
    }
    require(
        windows_tables == EXPECTED_WINDOWS_TABLES,
        f"Windows direction-table bytes drifted: {windows_tables!r}",
    )
    mac_source_tables = read_mac_source_tables()
    require(
        mac_source_tables == windows_tables,
        f"Mac source direction tables differ from the pinned Windows AEX: {mac_source_tables!r}",
    )

    state = loader.host_alloc(0x80, align=16)
    loader.write_bytes(state, b"\0" * 0x80)

    # Mode 2 must not inspect pixel words before choosing the intercepted
    # executor call.  Allocate exactly the nine 3x3 slots so index 9 lands in
    # uninitialized allocator padding rather than a convenient tenth pixel.
    pixels = loader.host_alloc(9 * 8, align=16)
    for index in range(9):
        words = (0x8000, 0x0100 + index, 0x0200 + index, 0x0300 + index)
        if index == 4:
            # Exact center (0,3) PF16 words extracted from the pinned run5 dump.
            words = (0x8000, 0x0B8C, 0x30B1, 0x4BCC)
        elif index == 5:
            # Exact east (1,3) PF16 words extracted from the pinned run5 dump.
            words = (0x8000, 0x8000, 0x7AFB, 0x2828)
        loader.write_bytes(
            pixels + index * 8,
            struct.pack("<4H", *words),
        )
    loader.add_read_trace_range(pixels, pixels + 9 * 8, "pf16_pixels")

    neighbors = loader.host_alloc(9 * 8, align=16)
    neighbor_ptrs = [pixels + index * 8 for index in range(9)]
    for index in (0, 3, 6):
        neighbor_ptrs[index] = 0  # exact left-edge topology from the run5 dump
    loader.write_bytes(neighbors, struct.pack("<9Q", *neighbor_ptrs))

    # Shadow-initialization policy for every mutable region this bounded call
    # may inspect.  The PE image and loader-owned TEB are immutable inputs;
    # stack and host regions are checked byte-for-byte.
    initialized_host = set(range(state, state + 0x80))
    initialized_host.update(range(pixels, pixels + 9 * 8))
    initialized_host.update(range(neighbors, neighbors + 9 * 8))
    initialized_stack: set[int] = set()
    uninitialized_reads: list[dict[str, object]] = []
    unexpected_writes: list[dict[str, object]] = []
    entry_rsp: list[int] = []

    def at_main_entry(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        require(not entry_rsp, "MainInterpKernel16 entry executed more than once")
        entry_rsp.append(rsp)
        initialized_stack.update(range(rsp, rsp + 8))  # synthetic return address
        for index in range(len(RUN5_ARGS) - 4):
            start = rsp + 0x28 + index * 8
            initialized_stack.update(range(start, start + 8))

    def stop_for_uninitialized_read(uc, _access, address, size, _value, _user_data) -> None:
        tracked: set[int] | None = None
        region = ""
        if STACK_BASE <= address < STACK_BASE + STACK_SIZE:
            tracked = initialized_stack
            region = "stack"
        elif 0x40000000 <= address < 0x40400000:
            tracked = initialized_host
            region = "host"
        if tracked is None:
            return
        missing = [byte for byte in range(address, address + size) if byte not in tracked]
        if missing:
            uninitialized_reads.append(
                {
                    "region": region,
                    "address": hex(address),
                    "size": size,
                    "first_missing": hex(missing[0]),
                    "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                }
            )
            uc.emu_stop()

    def track_or_reject_write(uc, _access, address, size, _value, _user_data) -> None:
        if STACK_BASE <= address < STACK_BASE + STACK_SIZE:
            if not entry_rsp:
                unexpected_writes.append(
                    {
                        "region": "stack_before_entry",
                        "address": hex(address),
                        "size": size,
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                    }
                )
                uc.emu_stop()
                return
            low = entry_rsp[0] - 0x400
            high = entry_rsp[0] + 0x80
            if address < low or address + size > high:
                unexpected_writes.append(
                    {
                        "region": "stack_outside_active_frame",
                        "address": hex(address),
                        "size": size,
                        "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                    }
                )
                uc.emu_stop()
                return
            initialized_stack.update(range(address, address + size))
            return
        if 0x40000000 <= address < 0x40400000:
            unexpected_writes.append(
                {
                    "region": "host_fixture",
                    "address": hex(address),
                    "size": size,
                    "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                }
            )
            uc.emu_stop()

    loader.add_code_hook(MAIN_INTERP_KERNEL16, at_main_entry)
    loader.uc.hook_add(UC_HOOK_MEM_READ, stop_for_uninitialized_read)
    loader.uc.hook_add(UC_HOOK_MEM_WRITE, track_or_reject_write)

    capture: list[dict[str, object]] = []

    def intercept(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        evaluator = read_u64(ld, rsp + 0x48)
        capture.append(
            {
                "state": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
                "direction": signed_i32(ld.uc.reg_read(UC_X86_REG_RDX)),
                "start": [
                    signed_i32(ld.uc.reg_read(UC_X86_REG_R8)),
                    signed_i32(ld.uc.reg_read(UC_X86_REG_R9)),
                ],
                "color_a": hex(read_u64(ld, rsp + 0x28)),
                "end": [
                    signed_i32(read_u64(ld, rsp + 0x30)),
                    signed_i32(read_u64(ld, rsp + 0x38)),
                ],
                "color_b": hex(read_u64(ld, rsp + 0x40)),
                "evaluator": hex(evaluator),
                "use_source": read_u64(ld, rsp + 0x50) & 0xFF,
                "leading_span": signed_i32(read_u64(ld, rsp + 0x58)),
                "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
            }
        )
        ld.uc.emu_stop()

    loader.add_code_hook(INTERP_EXECUTOR16, intercept)
    call_args = list(RUN5_ARGS)
    call_args[0] = state
    call_args[1] = neighbors
    call_result = loader.call_function(
        MAIN_INTERP_KERNEL16,
        int_args=call_args,
        max_instructions=250_000,
    )

    require(len(capture) == 1, f"expected exactly one intercepted executor call, got {len(capture)}")
    actual = capture[0]
    require(actual["rip"] == hex(INTERP_EXECUTOR16), "intercept RIP drift")
    require(actual["state"] == hex(state), "state pointer drift")
    require(actual["direction"] == 5, "direction drift")
    require(actual["start"] == [1, 3], f"unexpected generated start {actual['start']}")
    require(actual["end"] == [-1, 4], f"unexpected generated end {actual['end']}")
    require(actual["color_a"] == hex(neighbor_ptrs[4]), "center-color pointer drift")
    require(actual["color_b"] == hex(neighbor_ptrs[5]), "direction-color pointer drift")
    require(actual["use_source"] == 1, "source-selection flag drift")
    require(actual["leading_span"] == -1, "leading-span drift")
    evaluator = int(str(actual["evaluator"]), 16)
    require(entry_rsp, "MainInterpKernel16 entry RSP was not captured")
    active_frame_low = entry_rsp[0] - 0x400
    active_frame_high = entry_rsp[0] + 0x80
    expected_evaluator = entry_rsp[0] + RUN5_EVALUATOR_ENTRY_RSP_DELTA
    require(
        evaluator == expected_evaluator,
        "evaluator address/layout drift: "
        f"got 0x{evaluator:x}, expected entry_rsp{RUN5_EVALUATOR_ENTRY_RSP_DELTA:+#x} "
        f"= 0x{expected_evaluator:x}",
    )
    require(
        active_frame_low <= evaluator
        and evaluator + RUN5_EVALUATOR_SIZE <= active_frame_high,
        f"evaluator object is not fully inside the active frame: 0x{evaluator:x}",
    )
    require(
        set(range(evaluator, evaluator + RUN5_EVALUATOR_SIZE)) <= initialized_stack,
        "evaluator object layout is not fully initialized",
    )
    require(
        read_u64(loader, evaluator) == RUN5_EVALUATOR_VTABLE,
        "evaluator vtable drift: "
        f"got 0x{read_u64(loader, evaluator):x}, expected 0x{RUN5_EVALUATOR_VTABLE:x}",
    )
    require(not loader.read_trace, f"unexpected PF16 pixel reads before boundary: {loader.read_trace!r}")
    require(not uninitialized_reads, f"uninitialized read before boundary: {uninitialized_reads!r}")
    require(not unexpected_writes, f"unexpected write before boundary: {unexpected_writes!r}")
    require(not loader.import_log, f"unexpected import call before boundary: {loader.import_log!r}")
    require(not loader.callback_log, f"unexpected callback before boundary: {loader.callback_log!r}")

    return {
        "schema_version": 1,
        "status": "pass",
        "scope": "OLMSmoother v1 PF16 MainInterpKernel16 boundary only",
        "aex": {
            "path": str(AEX_PATH),
            "sha256": observed_sha,
        },
        "run5_dump": {
            "path": str(RUN5_DUMP_PATH),
            "sha256": observed_dump_sha,
            "argument_binding": "manually transcribed from the symbolicated pinned dump",
            "pixel_binding": "center/east exact; other pixel words synthetic and proven unread",
        },
        "entry": hex(MAIN_INTERP_KERNEL16),
        "intercept": hex(INTERP_EXECUTOR16),
        "run5_mainkernel_args": RUN5_ARGS[2:],
        "mac_source_direction_tables": mac_source_tables,
        "windows_direction_tables": windows_tables,
        "windows_first_executor_call": actual,
        "pixel_reads_before_intercept": len(loader.read_trace),
        "uninitialized_reads_before_intercept": len(uninitialized_reads),
        "unexpected_writes_before_intercept": len(unexpected_writes),
        "import_calls_before_intercept": len(loader.import_log),
        "callback_calls_before_intercept": len(loader.callback_log),
        "source_tables_match_windows": mac_source_tables == windows_tables,
        "instructions_before_intercept": call_result["instructions"],
        "verdict": (
            "Given the Mac run5 MainInterpKernel16 arguments, the original Windows AEX "
            "generates executor coordinates (1,3)->(-1,4), not the Mac crash's "
            "(-1,4)->(-1,4). The pinned AEX stores nine-entry 3x3 direction tables; "
            "the Mac port's reconstructed eight-entry tables are the direct divergence."
        ),
        "claims_not_made": [
            "No Windows After Effects execution.",
            "No Mac After Effects execution.",
            "No SubHandler16 parity result.",
            "No rendered-output or AE-exact result.",
        ],
    }


def main() -> int:
    print(json.dumps(execute(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
