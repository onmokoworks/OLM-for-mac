# Milestone 1 Report -- OLMRadialBlur.aex Unicorn Emulation Smoke Test

- Binary under test: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`

- Image base (load): `0x180000000`
- SizeOfImage: `0x34000`
- Imports resolved: 61

## Check 1: FUN_180001a90 (leaf constant-store function)

- Buffer address: `0x20000000`
- Expected words (hex): `['0x3e4ccccd', '0x3b64c388', '0x438f3d4c']`
- Got words (hex): `['0x3e4ccccd', '0x3b64c388', '0x438f3d4c']`
- Expected as float: `(0.20000000298023224, 0.003490658476948738, 286.4788818359375)`
- Got as float: `(0.20000000298023224, 0.003490658476948738, 286.4788818359375)`
- RAX == buffer pointer: `True` (RAX=0x20000000)
- Instructions executed: 5
- Imports called: none
- **Result: PASS**

## Check 2: FUN_180001000 (bilinear resampler)

- Plane address: `0x20000010`, output address: `0x20000110`
- Input: 4x4 RGBA float plane, pixel(col,row) = (col, row, col+row, 1.0); x=1.25, y=0.5
- Expected (independent Python re-implementation of decomp): `[1.25, 0.5, 1.75, 1.0]`
- Got (emulator): `[1.25, 0.5, 1.75, 1.0]`
- Instructions executed: 134
- Imports called: none
- **Argument-passing caveat**: param_5/param_6 are the 5th/6th positional arguments, which the Windows x64 ABI places on the stack (as 8-byte slots holding the 32-bit float bit pattern in the low 4 bytes), *not* in XMM0/XMM1. This test passes them via `int_args` stack-argument slots for that reason -- verified by reading `disasm/OLMRadialBlur.aex.asm.txt` for FUN_180001000's prologue, which loads these via `[RSP+...]` stack offsets rather than XMM register moves.
- **param_4 unit caveat (found via this test)**: param_4 is the row stride in FLOATS (width_in_pixels * 4 for RGBA), not in pixels. The decomp's `iVar3*4 + lVar6` (with `lVar6 = iy*param_4`) only produces the correct row-major float offset if param_4 is already float-scaled; a first attempt at this test used a pixel-count stride and got channel-swapped/row-shifted garbage (R and G swapped, e.g. got `[0.0, 1.75, 1.75, 1.0]` instead of the correct `[1.25, 0.5, 1.75, 1.0]`). Confirmed against disasm 0x180001073-0x1800010b7 (`LEA RDX,[0xc+RSI*4]` computing the byte delta to the next row's alpha channel) before fixing the test's row_stride_floats = width * 4.
- **Result: PASS**

## Overall

- Check 1 (leaf constants): PASS
- Check 2 (bilinear resampler): PASS
- **Milestone 1 smoke test: PASS**
