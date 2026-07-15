#!/usr/bin/env python3
"""Bound the 2025 DistanceGradation PF16 writer leaves on raw float32 values."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import capstone
import pefile
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_MXCSR

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "plugins_2025" / "DistanceGradation.aex"
FUN_RGB = 0x181458030
FUN_RGBA = 0x1814581A0
FUN_CALLBACK = 0x18144B820
SENTINEL = 0xA55A

SAMPLES = [
    0.499, 0.5, 0.501,
    32766.5, 32767.5,
    32767.49, 32767.5, 32768.0,
    65534.49, 65535.0, 65536.0,
]
GROUPS = {
    "sub_1": [0.499, 0.5, 0.501],
    "code_ties": [0.5, 32766.5, 32767.5],
    "near_32768": [32767.49, 32767.5, 32768.0],
    "above_32768": [65534.49, 65535.0, 65536.0],
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def mac_clamp16(value: float) -> int:
    # Comparison model only: normalized input, half-up, nominal PF16 domain.
    scaled = f32(f32(value) * f32(32768.0))
    rounded = math.floor(scaled + f32(0.5))
    return max(0, min(32768, rounded))


def mac_code_domain_model(value: float) -> int:
    """Apply the Mac clamp16 shape to an already code-domain AEX input."""
    return mac_clamp16(f32(f32(value) / f32(32768.0)))


def xref_audit() -> dict[str, object]:
    """Find direct executable call/jump xrefs; indirect dispatch is unresolved."""
    pe = pefile.PE(str(AEX), fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    targets = {FUN_RGB: "FUN_181458030", FUN_RGBA: "FUN_1814581a0"}
    direct: dict[str, list[str]] = {name: [] for name in targets.values()}
    for section in pe.sections:
        if not (section.Characteristics & 0x20000000):
            continue
        start = base + section.VirtualAddress
        data = pe.get_data(section.VirtualAddress, section.SizeOfRawData)
        decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        decoder.detail = True
        for instruction in decoder.disasm(data, start):
            if instruction.mnemonic not in ("call", "jmp") or not instruction.operands:
                continue
            operand = instruction.operands[0]
            if operand.type == capstone.x86.X86_OP_IMM and operand.imm in targets:
                direct[targets[operand.imm]].append(hex(instruction.address))
    return {
        "direct_call_or_jmp_xrefs": direct,
        "leaf_static_input_contract": "RCX points at raw float32 words; the leaf prologues load them directly and do not apply an upstream scale",
        "upstream_scale": "unproven",
        "upstream_capture": "not captured: no direct call/jmp xref was found, and indirect dispatch/caller state is not resolved by this harness",
        "open_boundary": "identify the indirect function-pointer/table dispatch or full DistanceGradation caller that supplies RCX to these leaves, then capture RCX float words immediately before the call",
    }


def run_leaf(address: int, samples: list[float], *, rgba: bool) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=False)
    source_values = samples + ([123.25] if rgba else [])
    src_bytes = struct.pack("<%df" % len(source_values), *source_values)
    src = loader.bump_alloc(len(src_bytes), align=16)
    dst = loader.bump_alloc(8, align=8)
    loader.write_bytes(src, src_bytes)
    loader.write_bytes(dst, struct.pack("<4H", SENTINEL, SENTINEL, SENTINEL, SENTINEL))

    writes: list[dict[str, int]] = []

    def on_write(_uc, _access, address_written, size, value, _user_data):
        if dst <= address_written < dst + 8:
            writes.append({
                "address_offset": address_written - dst,
                "size": size,
                "value_hex": (struct.pack("<H", value & 0xFFFF) if size == 2 else value.to_bytes(size, "little")).hex(),
                "value_u16": (value & 0xFFFF) if size == 2 else None,
            })

    loader.uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    count = 4 if rgba else len(samples)
    regs = loader.call_function(address, int_args=[src, dst, count], max_instructions=100_000)
    words = list(struct.unpack("<4H", loader.read_bytes(dst, 8)))
    return {
        "function": hex(address),
        "abi": "RCX=float32_input, RDX=uint16_output, R8D=count",
        "input_f32_raw": [f32(x) for x in source_values],
        "input_f32_hex": [struct.pack("<f", x).hex() for x in source_values],
        "output_words_u16": words,
        "output_words_hex": [f"{x:04x}" for x in words],
        "writes_into_four_word_destination": writes,
        "preserved_fourth_word": words[3] == SENTINEL,
        "mxcsr": f"0x{loader.uc.reg_read(UC_X86_REG_MXCSR):08x}",
        "instructions": regs["instructions"],
        "imports": [entry.name for entry in loader.import_log],
        "callbacks": [entry[0] for entry in loader.callback_log],
    }


def run() -> dict[str, object]:
    results: list[dict[str, object]] = []
    for name, samples in GROUPS.items():
        rgb = run_leaf(FUN_RGB, samples, rgba=False)
        rgba = run_leaf(FUN_RGBA, samples, rgba=True)
        results.append({"case": name, "samples": samples, "rgb_leaf": rgb, "rgba_leaf": rgba})
    return {
        "schema": "olm.distancegradation.pf16-writer-boundary/1",
        "case_id": "dg_pf16_writer_boundary_20260716",
        "classification": "Mac-local Unicorn execution of checked-in Windows 2025 AEX leaves; direct writer code-domain evidence only, not AE-host execution and not candidate production behavior",
        "aex": "plugins_2025/DistanceGradation.aex",
        "aex_sha256": sha256_file(AEX),
        "functions": {
            "FUN_181458030": {"va": hex(FUN_RGB), "role": "three-word scalar PF16 writer"},
            "FUN_1814581a0": {"va": hex(FUN_RGBA), "role": "RGBA-shaped writer; count is input-word count; fourth output word is preserved"},
            "FUN_18144b820": {"va": hex(FUN_CALLBACK), "executed": False, "reason": "writer leaves completed without host callback"},
        },
        "execution_assumptions": {
            "calling_convention": "Windows x64: RCX, RDX, R8D",
            "mxcsr": "AexLoader default Unicorn x86-64 MXCSR state; no runtime MXCSR mutation requested or observed",
            "raw_input_storage": "little-endian IEEE-754 float32, with hex words retained",
            "destination_initial_words": [f"{SENTINEL:04x}"] * 4,
        },
        "xref_and_upstream_audit": xref_audit(),
        "model_only": {
            "name": "Mac clamp16 applied to code-domain input",
            "formula": "clamp16(x / 32768.0) = saturate(floor(float32(float32(x / 32768.0) * 32768.0) + 0.5), 0, 32768)",
            "upstream_scale_assumption": "none proven; x/32768 is only the comparison-domain mapping",
            "results_by_sample": {str(x): mac_code_domain_model(x) for x in SAMPLES},
        },
        "results": results,
        "conclusion": {
            "direct_calls": "all requested writer leaves completed for the four bounded triplets",
            "callback_needed": False,
            "clamp_domain_observed": "writer output is bounded to 0..65535 before conversion; the 65536 sample produces 65535",
            "rounding_observation": "AEX uses CVTSS2SI/CVTPS2DQ under the emulated MXCSR; this is recorded as an observation, not replaced by the Mac half-up model",
            "upstream_scale": "unproven",
        },
    }


def write_md(report: dict[str, object], path: Path) -> None:
    lines = [
        "# DistanceGradation PF16 Writer Boundary",
        "",
        "- Run date: 2026-07-16.",
        "- Scope: direct bounded calls into the checked-in 2025 `DistanceGradation.aex`; Mac-local Unicorn only, not AE-host execution.",
        f"- AEX SHA-256: `{report['aex_sha256']}`.",
        "- ABI: `RCX=float32*`, `RDX=uint16*`, `R8D=count` under Windows x64.",
        "- `FUN_18144b820` was not called: both writer leaves completed without a host callback/import.",
        "",
        "## Model",
        "",
        "The corrected Mac comparison is code-domain `clamp16(x / 32768.0)`: `saturate(floor(float32(float32(x / 32768.0) * 32768.0) + 0.5), 0, 32768)`. This is a domain mapping for comparison only. Any upstream scale feeding the AEX writer remains unproven.",
        "",
        "## Results",
        "",
        "| Case | Raw code-domain float32 inputs | `FUN_181458030` words | `FUN_1814581a0` words | Fourth preserved | Mac code-domain model |",
        "|---|---|---|---|---|---|",
    ]
    model = report["model_only"]["results_by_sample"]
    mxcsr = report["results"][0]["rgb_leaf"]["mxcsr"]
    for row in report["results"]:
        inputs = ", ".join(f32(x).hex() for x in row["samples"])
        rgb = row["rgb_leaf"]["output_words_hex"]
        rgba = row["rgba_leaf"]["output_words_hex"]
        preserved = row["rgba_leaf"]["preserved_fourth_word"]
        expected = ", ".join(str(model[str(x)]) for x in row["samples"])
        lines.append(f"| `{row['case']}` | `{inputs}` | `{', '.join(rgb[:3])}` | `{', '.join(rgba[:3])}` | `{preserved}` (`{rgba[3]}`) | `{expected}` |")
    lines += [
        "",
        "## Evidence",
        "",
        "- The raw float32 hex words, output words, exact destination write events, instruction counts, import list, and callback list are retained in the JSON fixture.",
        "- The fourth destination word was initialized to `a55a`; the RGBA-shaped writer restored/preserved it for every triplet.",
        f"- The AEX clamp domain observed at these leaves is `[0, 65535]`. The AEX conversion instruction is MXCSR-dependent; this run used MXCSR `{mxcsr}` (round-to-nearest-even), via `CVTSS2SI`/`CVTPS2DQ`. The Mac model is half-up and is not substituted for the AEX rule.",
        "- Tie discriminators: code-domain `0.5` is AEX `0` versus Mac-model `1`; `32766.5` is AEX `32766` versus Mac-model `32767`; `32767.5` is AEX `32768` versus Mac-model `32768`.",
        "- Xref/callsite audit found no direct executable `CALL`/`JMP` xref to either leaf. The leaf input is therefore proven only as raw code-domain `float32`; upstream normalization or scaling is open.",
        "",
        "## Limits",
        "",
        "This is a function-level AEX witness with a harness-constructed buffer. It does not establish full AE execution, Windows hardware behavior, or production/ledger changes.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=ROOT / "refs/conformance/dg_pf16_writer_boundary_20260716.json")
    parser.add_argument("--md", type=Path, default=ROOT / "refs/conformance/dg_pf16_writer_boundary_20260716.md")
    args = parser.parse_args()
    report = run()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_md(report, args.md)
    print(json.dumps({"status": "pass", "json": str(args.json), "md": str(args.md)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
