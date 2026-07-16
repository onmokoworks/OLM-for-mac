# OLMKiraKira Mode 2 actual-AEX merge boundary

Date: 2026-07-17
Status: **pass**
AE exact: **false**

## Result

The narrowest checked-in AEX fixture executes `FUN_18114ffd0 @ 0x18114ffd0`
directly in Unicorn with one pixel, five one-float ray planes, five inline
RGBA color records, and five per-ray flags. It distinguishes the raw
accumulation path from the conditional `FUN_181232080` color path before the
same float RGBA accumulation and four clamps.

| Case | Actual output RGBA f32 bits | Instructions |
| --- | --- | ---: |
| Raw accumulation control | `0x3f000000, 0x3f400000, 0x3f800000, 0x3e4ccccd` | 209 |
| One merge flag through color helper | `0x3f800000, 0x00000000, 0x00000000, 0x3e4ccccd` | 266 |
| Five active rays with clamp | `0x3f800000, 0x3f000000, 0x00000000, 0x3f800000` | 269 |

## FACT

- The pinned AEX SHA-256 is `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Static dispatch selects the distinct Mode-2 target through the merge-mode
  vtable path; the target visits five ray slots and compares each ray against
  `DAT_181489990` (`0.001`).
- With flags clear, the active ray adds selected RGB directly and adds raw ray
  value to alpha. The five-active case confirms the four channel clamps.
- Setting one per-ray flag reaches `FUN_181232080 @ 0x181232080` and changes
  the selected color before aggregation.
- The target returns float RGBA and contains no call to the PF8/PF16/PF32
  writer entries `0x181230b90`, `0x181230bd0`, or `0x181230c20`.

## INFERENCE

- Merge Mode 2 is bounded here to aggregation dispatch plus a conditional
  per-ray color path inside the selected aggregation target.
- This fixture does not establish a later host compose formula or writer
  selection. Existing PF8/PF16/PF32 writer facts remain unchanged.

## Verification

```text
python3 tools/emulation/test_olmkirakira_mode2_actual_aex_merge_boundary_20260717.py
=> status=pass; static=8/8; actual_aex=3/3
```

The witness is direct checked-in-AEX Unicorn execution, not Windows/After
Effects host execution. No production source, ledger, or PNG was changed.
