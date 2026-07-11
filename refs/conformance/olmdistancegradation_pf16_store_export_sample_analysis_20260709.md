# OLMDistanceGradation 16bpc PF16 store/export sample analysis

Date: 2026-07-09

## Summary

This is a local arithmetic audit of retained Mac AE debug-store samples. It does not prove Windows internals, but it narrows what kind of witness is still needed.

## Facts

- `case_0012 (438,0)`: Mac debug store `a=32499 r=21330`, Mac PNG `42307`, Windows ref `42309`. The Windows value is explainable from the same store words by a round-style premultiplied export formula, while the Mac PNG is consistent with floor-style export.
- `case_0012 (1034,1)`: Mac debug store `a=32388 r=27884`, Mac PNG `55119`, Windows ref `55121`. Same pattern: the Windows value can be explained without changing the stored PF16 word if export rounding differs.
- `case_0014 (448,0)` under the current BOTH-only rule: prior Mac debug store `a=18076 r=18117`, Mac PNG `19985`, Windows ref `19989`. Simple round-style export from the same store word does not fully explain the Windows value; a store-side increase of roughly `+1..+2` in RGB, or an equivalent pre-store float difference, is required.
- `case_0014 (448,0)` under the deferred all-modes dominant-channel probe: Mac debug store changed to `a=18076 r=18119` and the same point reached Windows PNG `19989`. This supports the direction of the source/store hypothesis but is not an adoptable rule by itself.
- Reverted BOTH-only spot-check: `scripts/run_ae_single_case.py` still reports `case_0010/0011 max=2`, so single-case output is diagnostic here, not the canonical 16bpc exact-count gate.

## Inference

- The remaining Layer/no-bg family should be split: `case_0012` may be dominated by export rounding, while `case_0014` still needs a store/pre-store discriminator.
- Next useful proof is not a broad PNG sweep. It is either a canonical batch run for candidate validation, or a same-run Windows/Mac PF16 store/export witness for one `case_0012` point and one `case_0014` point.

## Candidate formulas checked

- `2 * floor(r * a / 32768) - 1`
- `2 * floor(r * a / 32768) + 1`
- `2 * round(r * a / 32768) - 1`
- `round(r * a * 65535 / (32768 * 32768))`
- `floor(r * a * 65535 / (32768 * 32768))`

