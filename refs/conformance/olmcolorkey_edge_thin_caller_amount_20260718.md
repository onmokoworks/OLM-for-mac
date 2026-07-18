# OLMColorKey Edge Thin caller amount contract

Date: 2026-07-18

## Result

The hash-pinned Windows AEX proves that Edge Thin uses an integer parameter,
not the float parameter path previously used by the Mac port.

- Disk ID `0x0d` is loaded by `FUN_18000DCD0`, whose terminal accessor
  `FUN_180013B00` copies the parameter's 32-bit integer field unchanged.
- The render record stores that value at `+0x28`.
- `FUN_180009000` loads it with `MOVD` and converts it exactly once with
  `CVTDQ2PS`.
- Positive Edge Thin copies an unmatched source pixel when
  `distance <= amount`.
- Negative Edge Thin removes a matched pixel when
  `distance < abs(amount)`. Equality remains matched.
- Distance types 1, 2, and 3 select different distance primitives, but use
  the same amount conversion and comparison instructions.

The bounded actual-AEX matrix covers integer amounts
`-4000, -2, -1, 0, 1, 2, 4000` and 54 threshold-adjacent comparisons across
all three distance types. Every observation matches the rules above.

## Ownership correction

Earlier files named `edge_thin_actual_caller` followed `record+0x40 -> XMM1 ->
FUN_180008320`. The decompilation and exact instruction addresses show that
this is the separate Edge Blur apply path. Edge Thin is `record+0x28` and is
implemented by the inline loops in `FUN_180009000`.

The Mac source correction is therefore limited to the proven host boundary:

- register Edge Thin Amount with `PF_ADD_SLIDER`;
- read `u.sd.value`;
- store it as `A_long`.

The existing distance implementation and its explicit type-dependent
translation are not changed by this evidence. This report does not claim AE
exactness or prove the distance primitive outputs.

## Reproduce

```text
tools/emulation/.venv/bin/python tools/emulation/audit_olmcolorkey_edge_thin_caller_amount_20260718.py
tools/emulation/.venv/bin/python tools/emulation/test_olmcolorkey_edge_thin_caller_amount_20260718.py
```

Machine-readable fixture:
`refs/conformance/olmcolorkey_edge_thin_caller_amount_20260718.json`.
