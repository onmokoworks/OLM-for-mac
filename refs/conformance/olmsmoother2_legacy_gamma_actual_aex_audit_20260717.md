# OLMSmoother2 legacy/gamma and actual-AEX audit - 2026-07-17

## Decision

Legacy/key/gamma remains a guarded residual. The new Mac-only host probe is
completed, but it is not AE exact: the accepted witness pixel `(92,841)` is
`[233,233,233,237]` for the Windows current-AEX reference and
`[218,218,218,238]` for the installed Mac plug-in under AE 2026 Software/8bpc.
The complete 3x3 neighborhood differs.

## Evidence Boundaries

- **Windows actual AEX:** the corrected same-run witness binds case
  `legacy_case_0012_gamma5_red_blue_current_aex`, descriptor
  `[92,841,1,92,842,2]`, `e170 c=7`, and the first append. It is accepted in
  `refs/conformance/olmsmoother2_legacy_key_producer_actual_aex_20260716.md`.
- **Local actual-AEX emulation:** `e170 -> f270 -> e3a0` passes on the
  synthetic `c=2` row with one append. This is a helper/producer check, not a
  live case mapping and not a final-pixel claim.
- **Gamma:** the a9c0 correction is binary-grounded and improves CLI gamma
  residuals, but the retained Mac AE gamma result is still non-exact. It does
  not identify c280, cce0, or the final writer as the cause.
- **Mac actual AE:** the new report records the installed plug-in hash,
  parameters, host mode, Windows witness, output hash, center pixel, and 3x3
  neighborhood. It measures the host boundary only.

## Remaining Next Boundary

The next useful probe is an internal Mac producer/class-plane capture at the
same `(92,841)` descriptor, followed by c280 input and cce0 output capture.
The current host render alone cannot distinguish producer selection from the
downstream classifier, composite, or writer. Do not retune gamma or final
writeback from this residual.

## Reproduction

```sh
python3 tools/emulation/probe_olmsmoother2_mac_actual_ae_boundary_20260717.py
python3 tools/emulation/test_olmsmoother2_legacy_key_setup_producer_witness_20260716.py
```
