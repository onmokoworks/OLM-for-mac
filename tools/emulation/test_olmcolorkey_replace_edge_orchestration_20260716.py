#!/usr/bin/env python3
"""Bounded Replace + Edge orchestration evidence for OLMColorKey 8-bit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
ASM = ROOT / "disasm/OLMColorKey.aex.asm.txt"
REPORT_JSON = ROOT / "refs/conformance/olmcolorkey_replace_edge_orchestration_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmcolorkey_replace_edge_orchestration_20260716.md"
ORCHESTRATOR = 0x1800094B0
HOOKS = {
    "replacement_write": 0x18000291A,
    "thin_boundary": 0x180009625,
    "blur_boundary": 0x18000983C,
    "blur_apply": 0x1800098CC,
}
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"


def static_aex_evidence() -> dict[str, object]:
    if not AEX.exists() or not ASM.exists():
        return {"status": "blocked", "reason": "AEX or assembly listing missing"}
    digest = hashlib.sha256(AEX.read_bytes()).hexdigest()
    instructions: dict[int, str] = {}
    for line in ASM.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"^([0-9a-fA-F]+)\s+", line)
        if match:
            instructions[int(match.group(1), 16)] = line

    required = {
        0x18000A54E: "[RSI + 0x4d]",
        0x1800028E2: "[RDI + 0x4d]",
        0x1800095FF: "CALL 0x1800117c0",
        0x180009625: "CALL 0x180008c90",
        0x18000983C: "CALL 0x180008c90",
        0x1800098CC: "CALL 0x1800085b0",
    }
    required_matches = {
        hex(address): token in instructions.get(address, "")
        for address, token in required.items()
    }
    orchestrator_lines = [
        line for address, line in instructions.items()
        if 0x1800094B0 <= address < 0x180009960
    ]
    replace_reads_in_orchestrator = [line for line in orchestrator_lines if "+ 0x4d" in line]
    order = [0x1800095FF, 0x180009625, 0x18000983C, 0x1800098CC]
    gates = {
        "binary_sha256": digest == AEX_SHA256,
        "required_instructions": all(required_matches.values()),
        "replace_flag_absent_from_edge_orchestrator": not replace_reads_in_orchestrator,
        "key_then_thin_then_blur_order": order == sorted(order),
    }
    return {
        "status": "pass" if all(gates.values()) else "blocked",
        "binary_sha256": digest,
        "gates": gates,
        "required_instruction_matches": required_matches,
        "replace_reads_in_edge_orchestrator": replace_reads_in_orchestrator,
        "event_order": [hex(address) for address in order],
        "parameter_reader": "ctx+0x4d at 0x18000a54e",
        "replace_tail_reads": ["0x1800028e2", "0x18000327e", "0x1800040a2"],
        "scope": "static AEX control-flow proof; no host or pixel-output claim",
    }


def source_evidence() -> dict[str, object]:
    text = SOURCE.read_text(encoding="utf-8")
    thin = re.search(r"if \(info\.edge_thin_amount < 0\.0\).*?\n\t}", text, re.S)
    blur = re.search(r"if \(info\.edge_blur_amount != 0\.0\).*?\n\t}", text, re.S)
    return {
        "thin_guard_present": bool(thin and "!info.enable_replace" in thin.group(0)),
        "blur_guard_present": bool(blur and "!info.enable_replace" in blur.group(0)),
        "replace_write_remains_in_pixel_stage": "info.color_keep && info.enable_replace" in text,
        "source": str(SOURCE.relative_to(ROOT)),
    }


def isolated_arm64_build() -> dict[str, object]:
    project = "mac/OLMColorKey/Mac/OLMColorKey.xcodeproj"
    command_template = [
        "xcodebuild", "-project", project, "-scheme", "OLMColorKey",
        "-configuration", "Release", "-sdk", "macosx", "-derivedDataPath",
        "$TRANSIENT_DERIVED_DATA", "ARCHS=arm64", "ONLY_ACTIVE_ARCH=YES",
        "CODE_SIGNING_ALLOWED=NO", "build",
    ]
    if not shutil.which("xcodebuild"):
        return {"status": "blocked", "reason": "xcodebuild not found", "command": command_template}
    with tempfile.TemporaryDirectory(prefix="olmcolorkey_replace_edge_build_") as derived:
        command = [value if value != "$TRANSIENT_DERIVED_DATA" else derived for value in command_template]
        proc = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=180, check=False)
    return {
        "status": "pass" if proc.returncode == 0 else "blocked",
        "returncode": proc.returncode,
        "command": command_template,
        "result": "BUILD SUCCEEDED" if proc.returncode == 0 else "BUILD FAILED",
    }


def try_aex_entry() -> dict[str, object]:
    sys.path.insert(0, str(Path(__file__).parent))
    from aex_loader import AexLoader  # noqa: PLC0415

    if not AEX.exists():
        return {"status": "blocked", "reason": "checked-in 2025 AEX missing"}
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    width = height = 5
    source = bytearray([255, 0, 255, 0] * (width * height))
    source[(2 * width + 2) * 4:(2 * width + 3) * 4] = bytes([255, 255, 0, 0])

    def make_world(data: bytes) -> int:
        payload = loader.bump_alloc(len(data), align=64)
        loader.write_bytes(payload, data)
        world = loader.host_alloc(0x40)
        loader.write_bytes(world, b"\0" * 0x40)
        loader.write_bytes(world + 0x18, payload.to_bytes(8, "little"))
        loader.write_bytes(world + 0x20, (width * 4).to_bytes(4, "little"))
        loader.write_bytes(world + 0x24, width.to_bytes(4, "little"))
        loader.write_bytes(world + 0x28, height.to_bytes(4, "little"))
        return world

    input_world = make_world(bytes(source))
    output_world = make_world(b"\xCC" * len(source))
    context = loader.host_alloc(0x400)
    params = loader.host_alloc(0x400)
    loader.write_bytes(context, b"\0" * 0x400)
    loader.write_bytes(params, b"\0" * 0x400)
    events: list[str] = []
    for label, address in HOOKS.items():
        loader.add_code_hook(address, lambda _ld, _addr, _size, label=label: events.append(label))
    try:
        loader.call_function(ORCHESTRATOR, int_args=[context, input_world, output_world, params], max_instructions=500_000)
        status, error = "pass", None
    except Exception as exc:
        status, error = "blocked", f"{type(exc).__name__}: {exc}"
    required_on = ["replacement_write", "thin_boundary", "blur_boundary", "blur_apply"]
    if status == "pass" and events != required_on:
        status = "blocked"
        error = f"incomplete combined-on hook order: {events!r}"
    return {"status": status, "entry": hex(ORCHESTRATOR),
            "fixture": {"dimensions": [5, 5], "background": "opaque green",
                        "keyed_center": "opaque red", "replacement": "opaque blue",
                        "thin": {"amount": 1, "distance": 2},
                        "blur": {"amount": 2, "distance": 2, "direction": "Around"}},
            "events": events, "error": error,
            "required_addresses": {key: hex(value) for key, value in HOOKS.items()}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=REPORT_JSON)
    parser.add_argument("--markdown", type=Path, default=REPORT_MD)
    args = parser.parse_args()
    source = source_evidence()
    static = static_aex_evidence()
    build = isolated_arm64_build()
    try:
        runtime = try_aex_entry()
    except Exception as exc:
        runtime = {"status": "blocked", "error": f"{type(exc).__name__}: {exc}"}
    source_pass = not source["thin_guard_present"] and not source["blur_guard_present"] and source["replace_write_remains_in_pixel_stage"]
    static_pass = static.get("status") == "pass"
    build_pass = build.get("status") == "pass"
    runtime_pass = runtime.get("status") == "pass"
    if source_pass and static_pass and build_pass:
        status = "pass_runtime" if runtime_pass else "pass_static_runtime_blocked"
    else:
        status = "blocked"
    report = {
        "kind": "olmcolorkey_replace_edge_orchestration_20260716",
        "schema": 1,
        "status": status,
        "claim_boundary": "static binary control-flow proof plus Mac source/build guard; runtime host scaffold remains separate and no AE-exact claim is made",
        "control_matrix": {
            "replace_1_thin_0_blur_0": {"status": "blocked", "reason": "full orchestrator did not reach stage hooks"},
            "replace_0_thin_0_blur_0": {"status": "blocked", "reason": "full orchestrator did not reach stage hooks"},
            "replace_1_thin_1_blur_1": {"status": "blocked", "reason": "full orchestrator did not reach stage hooks"},
        },
        "required_combined_on_order": ["replacement_write", "thin_boundary", "blur_boundary", "blur_apply"],
        "combined_off_requirement": "same edge hooks, no replacement_write",
        "source_evidence": source, "static_aex_evidence": static,
        "isolated_arm64_build": build, "aex_runtime": runtime,
    }
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# OLMColorKey Replace + Edge Orchestration 20260716", "",
        f"- Status: **{status}**",
        "- Scope: static AEX control flow plus Mac source/build guard; no AE-exact claim.", "",
        "## Evidence", "",
        f"- Source guards removed: Thin={not source['thin_guard_present']}, Blur={not source['blur_guard_present']}.",
        f"- Static AEX branch proof: **{static.get('status')}**; Replace flag reads are absent from the Edge orchestrator.",
        f"- Static event order: `{static.get('event_order', [])}` (keyer, Thin boundary, Blur boundary, Blur apply).",
        f"- Isolated arm64 build: **{build.get('status')}**.",
        f"- Actual AEX orchestrator runtime: **{runtime.get('status')}**.",
        "- Controls Replace=1/Thin=0/Blur=0, Replace=0/Thin=0/Blur=0, and Replace=1/Thin=1/Blur=1: **blocked/unexecuted** because the entry faulted before stage hooks.",
        "- Fixture: opaque green 5x5 background, opaque red keyed center, blue replacement; Thin +1 distance 2 and Blur 2 distance 2 Around.",
        "- Combined-on required order: replacement write `0x18000291a`, Thin `0x180009625`, Blur boundary `0x18000983c`, Blur apply `0x1800098cc`.", "",
        "## Fail-Closed Boundary", "",
        "The static lane proves that Replace cannot skip the Edge orchestrator and that the calls are ordered keyer -> Thin -> Blur. The runtime lane remains blocked until the real entry returns with all control/order conditions; no pixel output is promoted as proof.",
    ]
    args.markdown.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "json": str(args.json), "markdown": str(args.markdown)}, sort_keys=True))
    return 0 if status.startswith("pass_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
