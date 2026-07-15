# OLMKiraKira Mode 2 inner-compose witness

Date: 2026-07-16
Status: **pass / bounded local evidence**
AE exact: **false**

## Scope

This is the narrowest Windows-free witness implemented for the KiraKira lane:
one pixel through the Mode 2 target `FUN_18114ffd0 @ 0x18114ffd0`, with three
synthetic ray cases. It stops at the target's four-channel clamp and does not
claim the later source/glow compose or final PNG writeback.

## FACT

- The pinned decomp and disassembly both identify `FUN_18114ffd0`.
- The target zero-fills output, loops over five ray slots, skips a ray at or
  below `DAT_181489990`, adds selected RGB directly, and adds raw ray to alpha.
- The target calls `FUN_181156740` four times for independent channel clamps.
- The pinned AEX stores little-endian float64 `0.001` at
  `DAT_181489990 @ 0x181489990`; the harness reads this value from the loaded
  image instead of assuming a threshold.
- The harness checks those facts in both `decomp/OLMKiraKira.aex.c.txt` and
  `disasm/OLMKiraKira.aex.asm.txt`.
- Independent float32 model cases pass: zero-ray no-op, one short active ray,
  below/above-threshold selection, and five active rays with RGB/alpha
  saturation.

## INFERENCE

The model's float32 bit patterns are a local replay of the observed operation
order using the pinned AEX's resolved `0.001` threshold.

## Verification

```text
python3 tools/emulation/test_olmkirakira_mode2_compose_witness_20260716.py
=> status=pass; static=7/7; model=4/4
```

The generated JSON records the source hashes, all static checks, case outputs,
FACT/INFERENCE labels, and the explicit `ae_exact_claim=false` boundary.

## Limits

No production source, conformance ledger, Windows runtime, host binding, PNG
tuning, or broad image search was used or changed. The witness does not justify
a production renderer change.
