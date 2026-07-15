# OLMToonDilate Portable Typed-Core Model - 2026-07-16

## FACT

- The Mac source advertises `PF_OutFlag2_FLOAT_COLOR_AWARE` and dispatches
  Smart Render through `extra->input->bitdepth`.
- The typed branches are present for `PF_Pixel16` and `PF_PixelFloat`.
- The legacy `PF_Cmd_RENDER` callback remains an 8/16bpc boundary through
  `PF_WORLD_IS_DEEP(output)`; it is not evidence for 32bpc execution.
- The bounded portable model passes 4/4 tests:
  - 16bpc opaque seed propagation and out-of-bounds edge skipping
  - 16bpc semi-alpha non-seed behavior and `(rgb * alpha + 16383) / 32768`
    quantization
  - 32bpc semi-alpha float multiplication and opaque seed behavior
  - static source dispatch and float-aware contract checks
- The existing covered 16bpc fixture slice remains `3/3 AE exact` with
  `max_diff=0`.
- The available 32bpc Mac effect/control pair remains classified
  `blocked-by-host-input-conversion`: the Mac control and effect are equal,
  but the cross-host control residual is `6,220,800` RGB float samples.

## INFERENCE

- The local typed storage, alpha threshold, boundary, and quantization model
  is internally consistent with the current Mac source for 16/32bpc.
- The model duplicates the production formulas and uses static source guards;
  it does not execute the production render path and is not an independent
  binary oracle.
- The current evidence does not justify a production pixel-math change or a
  cross-host 32bpc exactness claim.
- The next useful 32bpc gate is a same-contract float EXR control return whose
  no-effect worlds match before comparing effect output.

## Verification

```sh
python3 -m unittest tests/test_olmtoondilate_typed_core.py
python3 refs/scripts/smoke_olmtoondilate_bitdepth_conformance.py
python3 refs/scripts/smoke_audit_olmtoondilate_mac_depth_contract_20260715.py
```

No ledger, package, Windows/SSH artifact, or unrelated production file was
changed for this lane advancement.
