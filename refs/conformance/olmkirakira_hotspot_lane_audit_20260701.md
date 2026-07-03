# OLMKiraKira Hotspot Lane Audit

- Case: `kk_vertical_len50_brightness1_strength100`
- Witness: `(934, 118)`
- Decision: `hotspot-proof-shifted-to-reference-or-witness-placement`
- Reason: The answered 2026-07-01 Windows hotspot witness no longer supports a KiraKira compose or pre-writeback patch. At `(934,118)`, the Windows trace reports the same glow-after-opacity alpha, the same composed float, the same pre-writeback float, and the same final sampled RGBA8 as the current Mac compose-boundary witness: 144, not the canonical Windows reference 131. That moves the live lane away from broad compose/gain/quantization tuning and toward reference/export provenance or witness-placement drift.
- Forbidden action: Do not reopen BT.709, boxFilter, ray-helper, global compose scale, hotspot-local attenuation, or final quantization tuning from this witness alone.
- Next allowed action: Treat the hotspot algorithm lane as provisionally matched through the traced writeback sample, and only spend more effort here on reference/export provenance, witness-placement validation, or the still-missing endgame control coverage.

## Mac Compose-Boundary Witness

- src_rgba_float: `[0.117647059, 0.117647059, 0.117647059, 1.0]`
- glow_rgba_float: `[1.0, 1.0, 1.0, 0.507505655]`
- out_prequantized_rgba_float: `[0.565446138, 0.565446138, 0.565446138, 1.0]`
- out_u8: `[144, 144, 144, 255]`
- canonical Windows reference: `[131, 131, 131, 255]`

## Windows Hotspot Witness

- glow_after_opacity_rgba_float: `[1.0, 1.0, 1.0, 0.507505655]`
- composed_rgba_float: `[0.5654461661764706, 0.5654461661764706, 0.5654461661764706, 1.0]`
- pre_writeback_rgba_float: `[0.5654461661764706, 0.5654461661764706, 0.5654461661764706, 1.0]`
- final_writeback_or_png_rgba: `[144, 144, 144, 255]`

## Agreement Checks

- same glow-after-opacity: `True`
- same compose float: `True`
- same pre-writeback float: `True`
- same final writeback/sample RGBA: `True`
- writeback minus canonical reference: `[13, 13, 13, 0]`

## Control-Ratio Sanity Check

- projected hotspot u8 from grayscale control ratio: `138`
- extra u8 drop formerly needed beyond control ratio: `7`
- Windows hotspot alpha midpoint implied by canonical ref: `0.44888888888888884`

## Runtime Request Record

- Request: `kirakira_hotspot_compose_writeback_witness_20260701`
- Status: `answered`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_kirakira_hotspot_compose_writeback_witness_20260701.zip`
- Latest known result status: ``
- Latest known result summary: ``

## Reading

- This witness does not say the exported Windows reference PNG is wrong; it says the traced hotspot sample no longer justifies changing KiraKira compose math.
- The traced Windows hotspot matches the current Mac compose-boundary values through pre-writeback and sampled RGBA8, while the canonical reference PNG still says 131.
- So the algorithm lane is no longer a broad compose/gain/quantization lane. The remaining lane is reference/export provenance, witness placement, or other endgame coverage outside this hotspot trace.

