# OLMToonDilate Bit-Depth Conformance Audit - 2026-07-15

## FACT

- The declared 8bpc ToonDilate slice is `3/3 AE exact`, with `max_diff=0`.
- The declared 16bpc ToonDilate slice is `3/3 AE exact`, with `max_diff=0`.
- The standalone 32bpc witness is ToonDilate-only, `32bpc`, `SOFTWARE`, and
  `OLM EXR 32 Float` scoped.
- The 32bpc witness creates its source inside AE, uses one shared source comp
  for no-effect/effect-on renders, and changes only branch enabled state.
- The witness contract requires no-effect and effect-on EXR artifacts and has
  no PNG artifacts in the package.

## INFERENCE

- The 8/16bpc implementation should remain unchanged; the exact slices provide
  no evidence for PNG or pixel-math tuning.
- The typed 32bpc package is the narrow next evidence gate for ToonDilate. It
  removes imported-input conversion as an uncontrolled variable, but it is not
  itself a cross-host `AE exact` result until a validated Windows return and a
  matching Mac typed record are compared.

## Targeted Gate

```sh
python3 refs/scripts/smoke_olmtoondilate_bitdepth_conformance.py
```

The gate checks the existing 8/16 exact counts and the standalone 32bpc
typed-procedural witness contract. It deliberately rejects PNG promotion and
does not inspect or modify the combined ColorKey package, ledgers, or
orchestration.
