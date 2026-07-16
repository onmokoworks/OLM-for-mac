# OLMToonDilate Seeded PF32 Live-Path Witness - 2026-07-17

## Result

- Status: **PASS_PF32_SEEDED_LIVE_RAW_NO_POSTPASS**
- AEX: `aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex`
- SHA-256: `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`
- Worker: `0x1801a6800`; typed PF32 helper: `0x1801ac8e0`
- Execution: macOS-local Unicorn through the existing `AexLoader`; no PNG, Windows, NAS, or AE host.

## FACT

- Fixture: x0 opaque seed; x1 semi-alpha propagated destination; x2 semi-alpha straight-RGB witness; radius 1.
- x2 is beyond the copy radius but remains in the same worker invocation that hits the live PF32 helper at x1.
- The worker returned and raw output memory was read immediately after return.
- x1 became the raw opaque source; x2 retained `(A=0.5, R=0.75, G=0.25, B=0.125)` exactly.
- The RGB*=alpha alternative for x2 is `(A=0.5, R=0.375, G=0.125, B=0.0625)` and was not observed.
- Gates: `{"opaque_to_semi_destination_propagation_observed": true, "padding_preserved": true, "pf_copy_callback_observed": true, "propagated_destination_equals_raw_opaque_source": true, "radius_two_semi_witness_alpha_unchanged": true, "radius_two_semi_witness_not_rgb_times_alpha": true, "radius_two_semi_witness_survives_raw": true, "typed_pf32_helper_observed_live": true, "worker_returned": true}`

## INFERENCE

- Required classification: **seeded live PF32 path preserves surviving semi-alpha RGB/alpha raw; no final RGB*=alpha postpass is present**.
- This is candidate/CLI/binary-grounded evidence, not AE exact or broad host-conversion proof.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf32_raw_copy_witness_20260717.py
```
