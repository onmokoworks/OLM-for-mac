"""
Milestone 1 smoke test for the Unicorn-based .aex emulation harness.

Two checks:

  1. FUN_180001a90 -- a pure leaf function (no imports, no branches) that
     writes three hard-coded 32-bit constants into a caller-supplied buffer
     and returns the buffer pointer in RAX. Ground truth is read directly
     off the disassembly (disasm/OLMRadialBlur.aex.asm.txt lines ~666-668):

         180001a90  MOV dword ptr [RCX],0x3e4ccccd
         180001a96  MOV RAX,RCX
         180001a99  MOV dword ptr [RCX+0x4],0x3b64c388
         ...        MOV dword ptr [RCX+0x8],0x438f3d4c   (see decomp)

     0x3e4ccccd == 0.2f, 0x3b64c388 == 0.0035f-ish, 0x438f3d4c == 286.48f.
     Exact expected floats are decoded from the hex in this script (no
     rounding guesses) and compared bit-for-bit against emulator output.

  2. FUN_180001000 -- the bilinear-interpolation resampler documented at
     decomp/OLMRadialBlur.aex.c.txt lines 1-73. Called with a small 4x4
     float RGBA "polar plane" buffer and fractional (x, y) coordinates,
     its output is cross-checked against a pure-Python re-implementation
     of the same decomp logic (independent of the emulator).

Run with:  tools/emulation/.venv/bin/python tools/emulation/test_m1_smoke.py
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"

FUN_180001a90 = 0x180001A90
FUN_180001000 = 0x180001000

REPORT_PATH = Path(__file__).parent / "M1_REPORT.md"


def f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def check1_leaf_constants(loader: AexLoader, report_lines: list[str]) -> bool:
    print("\n=== Check 1: FUN_180001a90 (leaf, constant-store function) ===")
    buf = loader.bump_alloc(16)
    loader.write_bytes(buf, b"\xAA" * 16)  # poison so we know it was overwritten

    result = loader.call_function(FUN_180001a90, int_args=[buf])

    out = loader.read_bytes(buf, 12)
    got = struct.unpack("<3I", out)
    expected = (0x3E4CCCCD, 0x3B64C388, 0x438F3D4C)

    got_floats = tuple(f32(v) for v in got)
    expected_floats = tuple(f32(v) for v in expected)

    ok_bits = got == expected
    ok_rax = result["rax"] == buf

    print(f"  buffer addr        = 0x{buf:x}")
    print(f"  expected (hex)      = {[hex(v) for v in expected]}")
    print(f"  got      (hex)      = {[hex(v) for v in got]}")
    print(f"  expected (float)    = {expected_floats}")
    print(f"  got      (float)    = {got_floats}")
    print(f"  RAX == buf pointer  = {ok_rax} (RAX=0x{result['rax']:x})")
    print(f"  instructions executed = {result['instructions']}")
    print(f"  imports called      = {[l.name for l in loader.import_log]}")
    print(f"  RESULT: {'PASS' if ok_bits and ok_rax else 'FAIL'}")

    report_lines.append("## Check 1: FUN_180001a90 (leaf constant-store function)\n")
    report_lines.append(f"- Buffer address: `0x{buf:x}`")
    report_lines.append(f"- Expected words (hex): `{[hex(v) for v in expected]}`")
    report_lines.append(f"- Got words (hex): `{[hex(v) for v in got]}`")
    report_lines.append(f"- Expected as float: `{expected_floats}`")
    report_lines.append(f"- Got as float: `{got_floats}`")
    report_lines.append(f"- RAX == buffer pointer: `{ok_rax}` (RAX=0x{result['rax']:x})")
    report_lines.append(f"- Instructions executed: {result['instructions']}")
    report_lines.append(f"- Imports called: {[l.name for l in loader.import_log] or 'none'}")
    report_lines.append(f"- **Result: {'PASS' if ok_bits and ok_rax else 'FAIL'}**\n")

    return ok_bits and ok_rax


def python_reference_resample(plane, row_stride_floats, x, y):
    """
    Pure-Python re-implementation of FUN_180001000 (decomp lines 1-73),
    independent of the emulator, used as ground truth.

    plane: flat list of floats, RGBA per pixel, row-major.
    row_stride_floats: this is `param_4` in the decomp/disasm. Tracing the
           pointer arithmetic (`pfVar4 = (iVar3*4 + lVar6)*4 + param_1` with
           `lVar6 = iy*param_4`) shows `param_4` must be the row stride
           measured in *floats* (i.e. width_in_pixels * 4 for an RGBA plane),
           not in pixels -- otherwise `iVar3*4` (column term, already scaled
           by 4 channels) and `iy*param_4` (row term) would use inconsistent
           units. This was confirmed empirically: using pixel-stride here
           produced wrong row addressing (verified via a hand-computed
           bilinear result for a 4x4 test plane, see check2 below).
    x, y: the fractional polar-plane coordinates (param_5, param_6).
    """
    ix = int(x)
    iy_row_base = int(y) * row_stride_floats  # already in floats

    fx = x - ix
    fy = y - int(y)
    one = 1.0
    gx = one - fx
    gy = one - fy

    def px(col, row_base_floats):
        base = col * 4 + row_base_floats
        return plane[base : base + 4]

    p00 = px(ix, iy_row_base)
    p10 = px(ix + 1, iy_row_base)
    # next row down: advance by one row stride (in floats) -- same units as
    # the pointer arithmetic `pfVar5 = pfVar4 + param_4 + 3`.
    next_row_base = iy_row_base + row_stride_floats
    p01 = px(ix, next_row_base)
    p11 = px(ix + 1, next_row_base)

    w00 = gy * gx
    w10 = gy * fx
    w01 = fy * gx
    w11 = fy * fx

    out = [0.0, 0.0, 0.0, 0.0]
    for w, p in ((w00, p00), (w10, p10), (w01, p01), (w11, p11)):
        a = w * p[3]
        out[3] += a
        out[2] += a * p[2]
        out[1] += a * p[1]
        out[0] += a * p[0]

    if out[3] != 0.0:
        norm = 1.0 / out[3]
        out[0] *= norm
        out[1] *= norm
        out[2] *= norm
        # out[3] (alpha) is intentionally left as pre-normalization sum in
        # the decomp -- param_2[3] is never reassigned in the final if-block.

    return out


def check2_resampler(loader: AexLoader, report_lines: list[str]) -> bool:
    print("\n=== Check 2: FUN_180001000 (bilinear resampler) ===")

    width = 4  # pixels per row
    height = 4
    # Build a deterministic 4x4 RGBA float plane: pixel (col,row) = (col, row, col+row, 1.0)
    plane = []
    for row in range(height):
        for col in range(width):
            plane.extend([float(col), float(row), float(col + row), 1.0])

    plane_addr = loader.bump_alloc(len(plane) * 4, align=16)
    loader.write_f32_array(plane_addr, plane)

    out_addr = loader.bump_alloc(16, align=16)
    loader.write_bytes(out_addr, b"\xAA" * 16)

    x = 1.25  # fractional coordinate: between column 1 and 2
    y = 0.5   # fractional coordinate: between row 0 and 1

    # FUN_180001000(longlong param_1, float *param_2, int param_3, int param_4,
    #               float param_5, float param_6)
    # param_1 = plane base pointer (int arg 0, RCX)
    # param_2 = output float[4] pointer (int arg 1, RDX)
    # param_3 = column-wraparound bound (compared against int(param_5) via
    #           `iVar3 = param_3-1`), not exercised by this in-bounds test
    #           (int arg 2, R8)
    # param_4 = row stride, in FLOATS (not pixels) -- confirmed by tracing
    #           the pointer arithmetic in disasm/OLMRadialBlur.aex.asm.txt
    #           around 0x180001073-0x1800010b7: `iVar3*4` (column term,
    #           already *4 for channels) is added directly to `iy*param_4`
    #           (row term) before a final *4, so param_4 must already be in
    #           float units for the two terms to be commensurate. For an
    #           RGBA plane that is `width_in_pixels * 4`. (int arg 3, R9)
    # param_5 = x coordinate, param_6 = y coordinate -- these are the 5th/6th
    #           positional arguments, which the Windows x64 ABI places on
    #           the caller's stack (verified: the callee's prologue at
    #           0x18000101c/0x18000102c loads them via
    #           `MOVSS XMM6/XMM7, dword ptr [RSP+0x58]/[RSP+0x50]`, i.e. from
    #           stack slots the caller must have populated -- not XMM0/XMM1).
    row_stride_floats = width * 4
    stack_x_bits = struct.unpack("<I", struct.pack("<f", x))[0]
    stack_y_bits = struct.unpack("<I", struct.pack("<f", y))[0]

    result = loader.call_function(
        FUN_180001000,
        int_args=[plane_addr, out_addr, height, row_stride_floats, stack_x_bits, stack_y_bits],
    )

    got = loader.read_f32_array(out_addr, 4)
    expected = python_reference_resample(plane, row_stride_floats, x, y)

    def close(a, b, tol=1e-5):
        return abs(a - b) <= tol * max(1.0, abs(b))

    ok = all(close(g, e) for g, e in zip(got, expected))

    print(f"  plane addr = 0x{plane_addr:x}, out addr = 0x{out_addr:x}")
    print(f"  x={x}, y={y}")
    print(f"  expected (python ref) = {expected}")
    print(f"  got      (emulator)   = {got}")
    print(f"  instructions executed = {result['instructions']}")
    print(f"  imports called        = {[l.name for l in loader.import_log]}")
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")

    report_lines.append("## Check 2: FUN_180001000 (bilinear resampler)\n")
    report_lines.append(f"- Plane address: `0x{plane_addr:x}`, output address: `0x{out_addr:x}`")
    report_lines.append(f"- Input: 4x4 RGBA float plane, pixel(col,row) = (col, row, col+row, 1.0); x={x}, y={y}")
    report_lines.append(f"- Expected (independent Python re-implementation of decomp): `{expected}`")
    report_lines.append(f"- Got (emulator): `{got}`")
    report_lines.append(f"- Instructions executed: {result['instructions']}")
    report_lines.append(f"- Imports called: {[l.name for l in loader.import_log] or 'none'}")
    report_lines.append(
        "- **Argument-passing caveat**: param_5/param_6 are the 5th/6th "
        "positional arguments, which the Windows x64 ABI places on the "
        "stack (as 8-byte slots holding the 32-bit float bit pattern in the "
        "low 4 bytes), *not* in XMM0/XMM1. This test passes them via "
        "`int_args` stack-argument slots for that reason -- verified by "
        "reading `disasm/OLMRadialBlur.aex.asm.txt` for FUN_180001000's "
        "prologue, which loads these via `[RSP+...]` stack offsets rather "
        "than XMM register moves."
    )
    report_lines.append(
        f"- **param_4 unit caveat (found via this test)**: param_4 is the "
        f"row stride in FLOATS (width_in_pixels * 4 for RGBA), not in "
        f"pixels. The decomp's `iVar3*4 + lVar6` (with `lVar6 = iy*param_4`) "
        f"only produces the correct row-major float offset if param_4 is "
        f"already float-scaled; a first attempt at this test used a "
        f"pixel-count stride and got channel-swapped/row-shifted garbage "
        f"(R and G swapped, e.g. got `[0.0, 1.75, 1.75, 1.0]` instead of "
        f"the correct `[1.25, 0.5, 1.75, 1.0]`). Confirmed against "
        f"disasm 0x180001073-0x1800010b7 (`LEA RDX,[0xc+RSI*4]` computing "
        f"the byte delta to the next row's alpha channel) before fixing "
        f"the test's row_stride_floats = width * 4."
    )
    report_lines.append(f"- **Result: {'PASS' if ok else 'FAIL'}**\n")

    return ok


def main() -> int:
    if not AEX_PATH.exists():
        print(f"ERROR: .aex not found at {AEX_PATH}")
        return 1

    report_lines: list[str] = []
    report_lines.append("# Milestone 1 Report -- OLMRadialBlur.aex Unicorn Emulation Smoke Test\n")
    report_lines.append(f"- Binary under test: `{AEX_PATH.relative_to(REPO_ROOT)}`")
    report_lines.append("")

    loader = AexLoader(str(AEX_PATH), verbose=True)

    report_lines.append(f"- Image base (load): `0x{loader.load_base:x}`")
    report_lines.append(f"- SizeOfImage: `0x{loader.size_of_image:x}`")
    report_lines.append(f"- Imports resolved: {len(loader.import_slots)}")
    report_lines.append("")

    ok1 = check1_leaf_constants(loader, report_lines)
    ok2 = check2_resampler(loader, report_lines)

    overall = ok1 and ok2
    report_lines.append("## Overall\n")
    report_lines.append(f"- Check 1 (leaf constants): {'PASS' if ok1 else 'FAIL'}")
    report_lines.append(f"- Check 2 (bilinear resampler): {'PASS' if ok2 else 'FAIL'}")
    report_lines.append(f"- **Milestone 1 smoke test: {'PASS' if overall else 'FAIL'}**")

    REPORT_PATH.write_text("\n".join(report_lines) + "\n")
    print(f"\nWrote report to {REPORT_PATH}")
    print(f"\n=== OVERALL: {'PASS' if overall else 'FAIL'} ===")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
