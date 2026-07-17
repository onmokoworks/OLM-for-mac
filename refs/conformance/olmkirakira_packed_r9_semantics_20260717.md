# OLMKiraKira packed R9 semantics

Date: 2026-07-17

## Result

- Status: **PASS_CLASSIFIED_FAIL_CLOSED_STOP**
- `RSI` at `0x18115110a` is `FUN_181150790`'s `param_7`, loaded from the caller's original `RSP+0x30`; the separate `param_8` branch selector is `2` at original `RSP+0x38`.
- The builder makes `R9 = RSI | 0x100000000`, then passes it to `FUN_181280bc0`.
- The packed-size interpretation is low dword `width=param_7` (kernel-width lane), high dword `height=1`.
- In this run `param_7=0x80000000`, which sets bit 31; `0x100000000` independently sets bit 32.

## Evidence

- Static asm/decomp checks and actual-AEX builder, ABI-spill, and reload observations all passed.
- The unmodified `FilterEngine` stop remained the terminal boundary.

## Limits

- Mac-only Unicorn execution of the pinned Windows PE; no Windows/After Effects host claim.
- No value patch or assertion suppression.
