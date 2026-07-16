# OLMColorKey Replace + Edge orchestration callback

- Status: `pass`
- Scope: checked-in hash-pinned AEX under Mac-local Unicorn; not AE exact.

## FACT

- The entry callback contract is
  `callback(refcon, output_world, params, 0, 0) -> PF_Err`.
- The synthetic `5x5` world invokes the actual AEX Iterate8 callback 25 times.
- The unique stage order is exactly `replacement_write -> thin_boundary ->
  blur_boundary -> blur_apply`.
- The Handle Suite and World Suite scaffolds release their acquired suites;
  cleanup is observed and no emulation error remains.
- The checked-in AEX SHA-256 equals the expected pin recorded in the JSON.

## Boundary

This closes the bounded host-callback and stage-order wiring. It does not prove
the numerical Replace, Edge Thin, or Edge Blur outputs for a Windows AE case,
and it does not promote `CLI exact` or `AE exact`.

## Verification

`python3 tools/emulation/test_olmcolorkey_replace_edge_orchestration_callback_20260716.py`

