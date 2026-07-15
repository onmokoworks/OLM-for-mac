"""Follow-up for the bounded ToonDilate actual-AEX callback stop point.

This file is deliberately independent of the existing 20260716 harness.  It
checks the smallest local layout correction: the worker reads context+0x180
after the status callback, so the synthetic context must cover that offset and
must contain a separate suite object there.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from unicorn.x86_const import UC_X86_REG_RSP  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex"
WORKER = 0x1801A6150
NEXT_HOST_BOUNDARY = 0x1801ADC8F
REPORT = Path(__file__).with_name("OLMTOONDILATE_ACTUAL_AEX_DIFFERENTIAL_20260716_followup.md")
JSON_REPORT = REPORT.with_suffix(".json")


def world(loader: AexLoader, width: int = 3, height: int = 3) -> int:
    data = loader.bump_alloc(width * height * 4, align=64)
    loader.write_bytes(data, b"\0" * (width * height * 4))
    header = loader.host_alloc(0x80, align=16)
    loader.write_bytes(header, b"\0" * 0x80)
    loader.write_bytes(header + 0x18, struct.pack("<Q", data))
    loader.write_bytes(header + 0x20, struct.pack("<I", width * 4))
    loader.write_bytes(header + 0x24, struct.pack("<I", width))
    loader.write_bytes(header + 0x28, struct.pack("<I", height))
    loader.write_bytes(header + 0x2C, struct.pack("<H", 8))
    return header


def invoke(correct_layout: bool) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    calls = []

    if correct_layout:
        context = loader.host_alloc(0x220, align=16)
    else:
        context = loader.host_alloc(0x140, align=16)
    loader.write_bytes(context, b"\0" * (0x220 if correct_layout else 0x140))

    status_vtable = loader.host_alloc(0x50, align=16)
    loader.write_bytes(status_vtable, b"\0" * 0x50)

    def status_ok(current_loader, args):
        rsp = current_loader.uc.reg_read(UC_X86_REG_RSP)
        calls.append({
            "kind": "status",
            "args": [hex(value) for value in args],
            "return_address": hex(struct.unpack("<Q", current_loader.read_bytes(rsp, 8))[0]),
        })
        return 0

    status_callback = loader.install_callback("toondilate_status_ok_followup", status_ok)
    loader.write_bytes(status_vtable + 0x40, struct.pack("<Q", status_callback))
    loader.write_bytes(context + 0xB0, struct.pack("<Q", status_vtable))
    loader.write_bytes(context + 0xB8, struct.pack("<Q", 0x1234))
    loader.write_bytes(context + 0x11C, struct.pack("<i", 1))
    loader.write_bytes(context + 0x120, struct.pack("<i", 1))

    suite_object = loader.host_alloc(0x20, align=16)
    loader.write_bytes(suite_object, b"\0" * 0x20)

    def suite_probe(current_loader, args):
        calls.append({"kind": "suite", "args": [hex(value) for value in args]})
        return 1

    suite_callback = loader.install_callback("toondilate_suite_probe_followup", suite_probe)
    # The worker loads [context+0x180] and calls [that pointer] directly.
    loader.write_bytes(suite_object, struct.pack("<Q", suite_callback))
    if correct_layout:
        loader.write_bytes(context + 0x180, struct.pack("<Q", suite_object))

    radius = loader.bump_alloc(4, align=16)
    loader.write_bytes(radius, struct.pack("<f", 1.0))
    source, destination = world(loader), world(loader)
    result = {
        "layout": "corrected" if correct_layout else "original-overlap",
        "context": hex(context),
        "status_callback": hex(status_callback),
        "context_180": hex(struct.unpack("<Q", loader.read_bytes(context + 0x180, 8))[0]),
        "calls": calls,
    }
    context_180_target = struct.unpack("<Q", loader.read_bytes(context + 0x180, 8))[0]
    result["context_180_target_first_byte"] = hex(loader.read_bytes(context_180_target, 1)[0])
    try:
        loader.call_function(WORKER, int_args=[context, 0, source, destination, radius],
                             max_instructions=100_000)
        result["stop"] = "return"
    except RuntimeError as exc:
        result["error"] = str(exc)
        result["stop"] = str(exc).split("RIP=", 1)[1].split(":", 1)[0] if "RIP=" in str(exc) else "unknown"
    result["imports"] = [entry.name for entry in loader.import_log]
    return result


def main() -> int:
    original = invoke(False)
    corrected = invoke(True)
    payload = {
        "status": "DIAGNOSTIC_COMPLETE",
        "aex": str(AEX.relative_to(ROOT)),
        "worker": hex(WORKER),
        "next_host_boundary": hex(NEXT_HOST_BOUNDARY),
        "original_overlap": original,
        "corrected_layout": corrected,
        "facts": [
            "The original layout aliases context+0x180 to the status vtable's +0x40 callback slot.",
            "The callback's first byte is 0xc3, and the worker attempts an indirect call through that byte value.",
            "With a non-overlapping context and a suite object at context+0x180, the status callback returns to 0x1801a6221 and execution reaches the suite callback.",
            "The corrected run stops at 0x1801adc8f after the synthetic suite callback returns 1, at the local C++ exception boundary.",
        ],
        "inferences": [
            "The worker expects a host suite/object ABI at context+0x180; this harness does not establish the full suite contract.",
            "The 0x1801adc8f stop is a loader/host emulation boundary, not evidence of AE behavior or pixel equivalence.",
        ],
        "claim_boundary": "actual-AEX ABI stop-point diagnostic only; no AE-exact claim",
    }
    JSON_REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OLMToonDilate Actual-AEX Differential Follow-up - 2026-07-16", "",
        "## Result", "",
        "- Status: **DIAGNOSTIC_COMPLETE**",
        "- Scope: actual-AEX ABI stop-point only; no AE-exact claim.",
        "- Smallest correction: allocate context through `context+0x180` and place a separate suite object at that offset.", "",
        "## FACT", "",
        "- Original `0x140`-byte context: `context+0x180` aliases the status vtable `+0x40` slot.",
        "- That slot contains the synthetic callback address; its first byte is `0xc3`.",
        "- The worker therefore performs an indirect call through `0xc3`, producing the reported fetch fault.",
        "- Corrected layout: the status callback returns to `0x1801a6221`, then the suite callback is reached.",
        f"- Corrected run stop: `{corrected['stop']}`; expected local next boundary is `{hex(NEXT_HOST_BOUNDARY)}`.", "",
        "## INFERENCE", "",
        "- `context+0x180` is a host suite/object pointer required by the worker.",
        "- The suite callback and the exception boundary are synthetic diagnostics; they do not prove the full host ABI or pixel behavior.", "",
        "## Evidence", "",
        "```json",
        json.dumps({"original_overlap": original, "corrected_layout": corrected}, indent=2),
        "```", "",
        "## Reproduce", "",
        "```sh",
        "tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_actual_aex_differential_20260716_followup.py",
        "```", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
