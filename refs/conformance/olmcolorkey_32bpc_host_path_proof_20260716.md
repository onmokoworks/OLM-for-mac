# OLMColorKey 32bpc Mac Host-Path Static Audit - 2026-07-16

## FACT

- `SmartRender` reads `extra->input->bitdepth`, captures the float entry only at bit depth 32, and dispatches that explicit depth to `RenderWorld`.
- `RenderWorld` has a `bitdepth == 32` branch using `RenderTyped<PF_PixelFloat>`; the float traits read native float channels.
- The plug-in declares both `PF_OutFlag2_SUPPORTS_SMART_RENDER` and `PF_OutFlag2_FLOAT_COLOR_AWARE`.
- The 2026-07-12 Mac case `0002` pair is classified `blocked-by-host-input-conversion`, and is not `AE exact`.
- The existing 32bpc exactness gate remains closed pending a raw-float Mac/Windows comparison.

## INFERENCE

- The supported Mac 32bpc contract is the Smart Render path with an explicit float depth; the legacy callback cannot establish 32bpc conformance.
- The current pair does not justify changing ColorKey comparison, Edge Thin, Edge Blur, or PNG handling.

## Audit Boundary

- Source SHA-256: `71154319ac6f8582af99325ae7e72eac2cba58435f6dd55514dfc5b30e4a0d1f`
- Static audit: `python3 scripts/audit_olmcolorkey_32bpc_host_path_20260716.py`
- Contract smoke: `python3 refs/scripts/smoke_audit_olmcolorkey_32bpc_host_path_20260716.py`
- This checks source structure and retained evidence labels; it does not execute Smart Render or revalidate the raw EXR pair.
