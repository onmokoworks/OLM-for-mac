# OLMRadialBlur Zoom case_0009 Sample-Target Gate Contract

## Grounded Facts

The 2026-07-10 raw liveness return executed `OLMRadialBlur+0x5e5b` and
`+0x5e6d`. The disassembly establishes that this is the nested sample loop:
`EBX` is x, `R13D` is y, `RDX` is the current cell record, `R8D=R15D`, and
`R9D=R12D` immediately before `FUN_180009d80`.

The old `+0x7404/+0x7409` final-write hypothesis did not execute and is not
part of this request.

## Required Same Run

Render package-local Zoom `case_0009` once. At both `+0x5e5b` (call) and
`+0x5e6d` (return), capture only `(EBX,R13D)=(7,0),(8,0),(24,0)`.

For every call hit record all registers, stack floats at `rsp+0x28` and
`rsp+0x30`, the `RDX` cell-address window, and the source/pool pointer in RCX.
For every return hit record all registers and the cell-address window. Keep the
three x coordinates in the same CDB/AE run.

## Acceptance

`answered` needs six target hits (call+return for all three x values) and CDB
proof. `answered_partial` may contain a subset only when the AE render result
and the exact missed coordinates are present. No final plane or output value is
to be inferred here.
