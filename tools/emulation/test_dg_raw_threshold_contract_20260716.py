#!/usr/bin/env python3
"""Focused source/binary regression for DG raw-threshold ownership.

This test does not claim full After Effects or render-output parity. It checks
only the threshold argument contract at the Windows helper callsites and the
corresponding Mac helper call.
"""

from __future__ import annotations

import ctypes
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
AEX = ROOT / "plugins_2025/DistanceGradation.aex"
BRIDGE = ROOT / "tools/emulation/dg_fieldgen_actual_aex_bridge_20260716.cpp"
EXPECTED_AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
FUN_FIELDGEN = 0x181174760

# (threshold-load VA, call VA, raw UI config field)
CALLSITES = (
    (0x181171A3E, 0x181171A70, "0xbc"),
    (0x181171AFE, 0x181171B12, "0xb8"),
    (0x181171B42, 0x181171B52, "0xbc"),
    (0x18117274E, 0x181172780, "0xbc"),
    (0x18117280E, 0x181172822, "0xb8"),
    (0x181172852, 0x181172862, "0xbc"),
    (0x18117345E, 0x181173490, "0xbc"),
    (0x18117351E, 0x181173532, "0xb8"),
    (0x181173562, 0x181173572, "0xbc"),
)


def function_text(source: str, marker: str) -> str:
    start = source.rindex(marker)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated function after {marker}")


def check_source_contract() -> None:
    source = SOURCE.read_text()
    helper = function_text(source, "static void dt_to_normalized(\n\tconst u_char *mask")
    builder = function_text(source, "static void build_distance_field(")

    assert "ds_scale" not in helper, "dt_to_normalized must not accept or apply ds_scale"
    assert "(float)threshold, constant_interp" in helper
    assert not re.search(r"threshold\s*\*|\*\s*ds_scale", helper)
    assert "p.inside_threshold, ds" not in builder
    assert "p.outside_threshold, ds" not in builder

    # This is a source ownership guard only. Blur behavior itself is out of scope.
    assert "bs = (long)((float)p.blur_size * ds + 0.5f);" in builder


def check_binary_contract() -> None:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256
    pe = pefile.PE(str(AEX), fast_load=True)
    image = AEX.read_bytes()
    image_base = pe.OPTIONAL_HEADER.ImageBase
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)

    for load_va, call_va, config_offset in CALLSITES:
        start = pe.get_offset_from_rva(load_va - image_base)
        instructions = list(decoder.disasm(image[start : start + (call_va - load_va) + 5], load_va))
        assert instructions[0].mnemonic == "mov"
        assert instructions[0].op_str == f"r9d, dword ptr [r15 + {config_offset}]"
        call = next(instruction for instruction in instructions if instruction.address == call_va)
        assert call.mnemonic == "call" and int(call.op_str, 16) == FUN_FIELDGEN

        # Width/height staging is carried independently in stack arguments.
        # Single-side sites load R9D before staging; Both sites load it after.
        window_start_va = min(load_va, call_va - 0x30)
        window_start = pe.get_offset_from_rva(window_start_va - image_base)
        call_end = pe.get_offset_from_rva(call_va - image_base) + 5
        window = list(decoder.disasm(image[window_start:call_end], window_start_va))
        stack_args = {instruction.op_str.split(",", 1)[0] for instruction in window if instruction.mnemonic == "mov"}
        assert {"dword ptr [rsp + 0x20]", "dword ptr [rsp + 0x28]", "dword ptr [rsp + 0x30]", "dword ptr [rsp + 0x38]"} <= stack_args


def compile_bridge(tmp: Path) -> ctypes.CDLL:
    compiler = shutil.which("clang++")
    assert compiler, "clang++ is required"
    dylib = tmp / "libdg_raw_threshold_contract_20260716.dylib"
    subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-O2",
            "-arch",
            "arm64",
            "-dynamiclib",
            str(ROOT / "core/olmdistancegradation_fieldgen.cpp"),
            str(BRIDGE),
            "-o",
            str(dylib),
        ],
        cwd=ROOT,
        check=True,
    )
    return ctypes.CDLL(str(dylib))


def run_helper(library: ctypes.CDLL, raw_threshold: float) -> bytes:
    width, height = 17, 11
    mask = (ctypes.c_uint8 * (width * height))(*([255] * (width * height)))
    for y in range(height):
        for x in (0, 8, 16):
            mask[y * width + x] = 0
    output = (ctypes.c_float * (width * height))()
    helper = library.dg_distance_to_normalized_u8_20260716
    helper.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_float,
        ctypes.c_int,
    ]
    helper.restype = ctypes.c_int
    assert helper(mask, width, height, output, raw_threshold, 0) == 1
    if raw_threshold == 4.0:
        anchors = tuple(output[5 * width + x] for x in (0, 1, 2, 4))
        assert anchors == (0.0, 0.25, 0.5, 1.0)
    return bytes(output)


def check_helper_invariance() -> None:
    with tempfile.TemporaryDirectory(prefix="dg_raw_threshold_contract_20260716_") as name:
        library = compile_bridge(Path(name))
        outputs = {ds_scale: run_helper(library, 4.0) for ds_scale in (1.0, 0.5)}
        assert outputs[1.0] == outputs[0.5]

        # Fixture sensitivity: the removed threshold*0.5 behavior must differ.
        assert outputs[0.5] != run_helper(library, 2.0)


def main() -> int:
    check_source_contract()
    check_binary_contract()
    check_helper_invariance()
    print("RESULT: DG raw-threshold source/binary contract PASS")
    print(f"FACT: {len(CALLSITES)} hash-pinned AEX callsites pass raw +0xb8/+0xbc in R9D")
    print("FACT: helper outputs are byte-identical for ds_scale=1 and ds_scale=0.5")
    print("SCOPE: blur output and full AE render exactness are not tested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
