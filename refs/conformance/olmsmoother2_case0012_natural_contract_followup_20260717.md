# OLMSmoother2 case0012 natural caller contract follow-up

## Verdict

`PASS_FAIL_CLOSED_FUN_18000ADA0_ENTRY_CONTRACT_ORACLE`

The checked-in AEX and decomp independently ground the FUN_18000ada0 ABI before the local address oracle runs.

## Grounded Contract

- Arguments: `RCX=source_fplane, RDX=class_fplane, R8=rect, R9=config`.
- Both source and class FPlane records are 24 bytes: pointer at `+0x00`, width/height at `+0x08/+0x0c`, and byte row stride at `+0x10`.
- Rect is four int32 values `[left, top, right, bottom]`, with right and bottom exclusive in the worker loop.
- Config `+0x1c` is the ae10 threshold numerator; `+0x70` gates hysteresis; `+0x74` is its float multiplier.

## Independent Check

- Padded source/class strides `96/24` were addressed correctly.
- Non-tight rect `[1, 1, 4, 3]` visited `6` pixels and left `14` pixels untouched.

Claims are local binary/decomp layout evidence only. No Windows return, AE host, production source, or ledger claim is made.
