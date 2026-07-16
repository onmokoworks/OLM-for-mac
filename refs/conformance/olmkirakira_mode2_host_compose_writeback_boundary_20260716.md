# OLMKiraKira Mode 2 host compose/writeback boundary

Date: 2026-07-16
Status: **pass / static-only bounded evidence**
AE exact: **false**

## Result

The checked-in decomp/assembly and AEX loader evidence narrow Mode 2 to an intermediate float RGBA buffer. The target reads the pinned float64 threshold `0.001`, performs five-ray accumulation, applies four clamps, stores float channels, and returns. It does not call the separate byte/word/float writer helpers.

The writer candidates are `FUN_181230b90` (byte stores), `FUN_181230bd0` (word stores), and `FUN_181230c20` (float stores). No unique host compose/writeback chain from the Mode-2 output pointer to those helpers is statically bound here.

## FACT

- Mode 2 dispatch uses vtable slot `+0x10`; the target is `FUN_18114ffd0 @ 0x18114ffd0`.
- `DAT_181489990 @ 0x181489990` is loaded by `AexLoader` as little-endian float64 `0.001`.
- `FUN_18114ffd0` ends after the four `FUN_181156740` calls and float stores at `RET 0x18115019e`.
- Separate writer helper instruction bodies are present, but no same-run host binding is present in checked-in evidence.

## INFERENCE

- The post-clamp float buffer is an intermediate result; its later host compose and writeback semantics remain unresolved.
- This witness is static-only and does not promote AE exactness.

## Verification

```text
python3 tools/emulation/test_olmkirakira_mode2_host_compose_writeback_boundary_20260716.py
=> status=pass; static=13/13; threshold=0.001
```

## Missing evidence

- Same-run Windows/AE trace with AEX hash and selected Mode-2 target.
- Output pointer after the final clamp, host compose inputs/formula, typed pre-writeback RGBA, writer entry/conversion, and destination address.
- Same-pixel AE output comparison; PNG-only evidence is insufficient.

No production source, ledger, or PNG was changed.
