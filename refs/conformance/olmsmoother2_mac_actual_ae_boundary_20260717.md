# OLMSmoother2 Mac actual-AE boundary probe - 2026-07-17

- Verdict: `MAC_AE_BOUNDARY_RENDER_COMPLETED_NOT_AE_EXACT`
- Case: `legacy_case_0012_gamma5_red_blue_current_aex`; witness pixel `(x=92, y=841)`.
- Mac run: After Effects 2026, Software renderer, 8bpc, straight-alpha input, Gamma Correction `2`, Gamma Value `2.16954731941223`, five gamma colors.
- Installed Mac plug-in binary SHA-256: `a7b9747dec20e97c019de8ffd402c6476eb39dcab14a6b8648772e0af1539c69`.

## Boundary

- Windows actual-AEX witness: descriptor `[92,841,1,92,842,2]`, `e170 c=7`, first append observed.
- Windows center RGBA: `[233, 233, 233, 237]`.
- Mac center RGBA: `[218, 218, 218, 238]`.
- Center equal: `False`; 3x3 neighborhood equal: `False`.

The render completed through the Mac AE host and installed Mac plug-in. This is a host-boundary residual measurement, not an internal Mac producer trace and not AE exactness.

## Reproduction

```sh
python3 tools/emulation/probe_olmsmoother2_mac_actual_ae_boundary_20260717.py
```
