# OLMRadialBlur Zoom case_0009 AEX Witness

- Case: `case_0009`
- XY: `[6, 0]`
- AEX: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
- AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- Input SHA-256: `7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4`
- Manifest SHA-256: `7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565`
- Entry reached: `True`
- Classification: `direct-python-prefill-candidate-hooks-reached`

## Execution

- `elapsed_seconds`: `150.2674081325531`
- `render_instructions`: `150000000`
- `render_fault`: ``
- `max_instructions`: `150000000`
- `zoom_setup_a7e0_calls`: `1`
- `zoom_setup_a810_calls`: `1`
- `zoom_branch_hits_0x1800072d3`: `0`
- `zoom_callsite_hits_0x1800072fd`: `0`
- `prepass_calls`: `1`
- `scatter_calls`: `1`
- `staging_loop_hits_0x180007811`: `None`
- `render_stop_rip`: `0x90000000`

## Geometry

- `width`: `1920`
- `height`: `1080`
- `min_radius`: `0`
- `max_radius_plus`: `1103`
- `radial_count`: `1104`
- `quality_step`: `0.20000000298023224`
- `angle_step`: `0.003490658476948738`
- `angle_count`: `1800`
- `radius_raw`: `1096.22802734375`
- `angle_raw`: `3.656665325164795`
- `radius_index`: `1096.22802734375`
- `angle_index`: `1047.557459233642`

## Pointers

- `zoom_param1`: `0x25eec000`
- `zoom_param2`: `0x400003c0`
- `accum_0x842`: `0x25ef0300`
- `denom_0x843`: `0x27d42b00`
- `final_7`: `0x284d7500`

## Final Sample

- Mac AEX final-plane sample float: `[0.0, 0.0, 0.0, 1.0]`
- Mac AEX trunc u8: `[0, 0, 0, 255]`
- Mac output-world RGBA: `[0, 0, 0, 0]`
- Windows trace float: `[0.08224078267812729, 0.014130095019936562, 0.014130095019936562, 0.9999999403953552]`
- Windows final u8: `[20, 3, 3, 254]`

## Same-run point samples

| XY | radius / angle index | final float RGBA | trunc u8 | output-world RGBA |
| --- | --- | --- | --- | --- |
| `[7, 0]` | `1095.35791015625` / `1047.6863449042787` | `[0.0, 0.0, 0.0, 1.0]` | `[0, 0, 0, 255]` | `[0, 0, 0, 0]` |
| `[8, 0]` | `1094.488037109375` / `1047.8153671786997` | `[0.0, 0.0, 0.0, 1.0]` | `[0, 0, 0, 255]` | `[0, 0, 0, 0]` |
| `[24, 0]` | `1080.599853515625` / `1049.908205458495` | `[0.0, 0.0, 0.0, 1.0]` | `[0, 0, 0, 255]` | `[0, 0, 0, 0]` |

## Witness Cells

### Denominator `param_1[0x843]`
- `a0_r0`: `1.0`
- `a0_r1`: `1.0`
- `a1_r0`: `1.0`
- `a1_r1`: `0.9999999403953552`

### Final polar `param_1[7]`
- `a0_r0`: `[0.0, 0.0, 0.0, 1.0]`
- `a0_r1`: `[0.0, 0.0, 0.0, 1.0]`
- `a1_r0`: `[0.0, 0.0, 0.0, 1.0]`
- `a1_r1`: `[0.0, 0.0, 0.0, 0.9999999403953552]`

### Accum RGBA `param_1[0x842]`
- `a0_r0`: `[0.0, 0.0, 0.0, 1.0]`
- `a0_r1`: `[0.0, 0.0, 0.0, 1.0]`
- `a1_r0`: `[0.0, 0.0, 0.0, 1.0]`
- `a1_r1`: `[0.0, 0.0, 0.0, 0.9999999403953552]`

## Reading

This is a full-size direct-core harness witness with the hot Zoom polar input prefill replaced by a Python implementation derived from FUN_1800056f0 and the repeat-border bilinear samplers. It is stronger than the synthetic fast-forward because source planes and geometry participate. The prefill formula is exact against the original AEX at reduced geometry (`max_abs_diff=0.0`; see `refs/conformance/olmradialblur_zoom_python_prefill_validation_20260708.md`), but the full-frame result remains a local candidate until its host/output binding is compared with a same-run Windows witness.
