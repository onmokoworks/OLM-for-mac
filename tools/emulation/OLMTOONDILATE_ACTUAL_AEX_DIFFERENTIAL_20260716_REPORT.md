# OLMToonDilate Actual-AEX Differential - 2026-07-16

## Result

- Status: **BLOCKED**
- AEX: `aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex`
- Worker: `0x1801a6150`
- Execution: checked-in PE AEX under local Unicorn on macOS; no AE or Windows.
- The portable side is independent and covers alpha threshold, boundary, and 8bpc premultiply quantization.

## ABI Stop Point

- Effective worker call: `RCX=context, RDX=0, R8=input world, R9=output world, stack arg 5=float* radius`.
- Stop RIP: `0xc3`
- Callback args observed: `[['0x1234', '0x40000000', '0x40000080', '0x0']]`
- The synthetic status callback returned zero once; the next return path fetched unmapped `0xc3`.

## alpha_threshold_center

- Status: `BLOCKED`
- Match: `None`
- Stop RIP: `0xc3`
- Instructions: `not returned`
- Callback calls: `1`
- Imports: `none`

## boundary_corner

- Status: `BLOCKED`
- Match: `None`
- Stop RIP: `0xc3`
- Instructions: `not returned`
- Callback calls: `1`
- Imports: `none`

## semi_alpha_quantization

- Status: `BLOCKED`
- Match: `None`
- Stop RIP: `0xc3`
- Instructions: `not returned`
- Callback calls: `1`
- Imports: `none`

## Interpretation

This is a bounded actual-AEX worker differential; no AE-exact claim is made. The checked-in typed-core model was not used as an oracle. The AEX is a Windows PE artifact exercised through Unicorn; the host callback is synthetic and only satisfies the worker status gate.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_actual_aex_differential_20260716.py
```
