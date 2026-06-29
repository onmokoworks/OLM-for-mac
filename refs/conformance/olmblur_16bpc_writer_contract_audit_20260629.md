# OLMBlur 16bpc Writer Contract Audit - 2026-06-29

## Summary

- Current Mac source non-legacy store16 path: `nearbyintf(v)` then clamp `0..32768` then cast to `u_short`.
- Current Mac source legacy store16 path: `floorf(v + 0.5f)` then clamp `0..32768` then cast to `u_short`.
- Windows standard 16bpc writer asm: `round-add-helper-truncate-word-store`.
- Windows alternate 16bpc writer asm: `direct-memory-truncate-word-store`.

## Contract Comparison

| Question | Result |
| --- | --- |
| Mac non-legacy source uses `nearbyintf` | `True` |
| Windows standard writer is add-half then truncate | `True` |
| Mac non-legacy source exactly matches Windows standard 16bpc rounding expression | `False` |
| Mac legacy source matches Windows add-half family | `True` |

## Residual Context

- Non-legacy sign-mixed one-word cases: `6/6`.
- Legacy `case_0007` classification: `legacy-border-plus-one-word`.

## Decision

- `source-writer-mismatch-real-but-not-yet-sufficient-for-global-swap`

## Interpretation

- The current Mac source uses `nearbyintf(v)` for non-legacy 16bpc store16, while Windows standard 16bpc asm is `+0.5 -> helper -> CVTTSS2SI -> word store`.
- This is a real source-vs-asm contract mismatch at the writer boundary.
- But the current 16bpc residual family is sign-mixed one-word across all non-legacy cases, so the evidence still does not support a blind global `nearbyintf -> floorf(v + 0.5f)` swap without proving pre-writeback/helper state.
- Legacy already matches the add-half family in source, so `case_0007` remains a separate border/seed/all-same investigation rather than proof for the non-legacy store path.
