# OLMDistanceGradation FUN_181174760 helper differential

- Status: `pass`
- Scope: **helper parity only; not full AE field-generation parity**.
- AEX SHA-256 pin matched: `True` (`a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`).
- Geometry: three `17x11` staged-mask cases using the existing fieldgen harness detours.

## FACT

- `param8=1`, raw threshold `0`, `ds_scale=1`: strict-threshold anchors are `(0,1,1)`: `True`.
- `param8=0`, raw threshold `4`, `ds_scale=1`: AEX and current core ramp are float32 exact: `True`.
- Repeating the ramp with explicit `ds_scale=0.5` exposes a field difference: `True`.
- Detour, callback, import, and sample-count guards all matched: `True`.
- Requested PF8 anchors attained: `{"10": false, "2": false, "64": true}`.
- `For a 17x11 EDT containing a zero source, the smallest positive raw distance is 1 and the largest possible raw distance is sqrt(356); normalization therefore cannot produce PF8 codes 2 or 10. Code 64 is attained by the four-pixel ramp.`
- The JSON records each source 8U mask, staged dimensions, raw threshold, param8, ds_scale, and all 187 AEX/core float32 and PF8 samples per case.

## INFERENCE

- The ds_scale=0.5 difference is consistent with the current Mac caller scaling the raw threshold while FUN_181174760 receives the raw threshold in this direct helper call.
- This bounded direct-call result does not cover AE host masks, resize to a different shape, full field construction, compose, or render output.

## Smoke

- Command: `tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_actual_aex_differential_20260716.py`
- Result: `pass`.
