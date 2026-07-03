# OLMRadialBlur Zoom Source-Candidates Audit

- Case: `case_0009`
- Witness: `(6, 0)`
- Source: `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- Current sample_u8: `[20, 3, 3, 255]`
- Windows reference_u8: `[20, 3, 3, 254]`

## Lane Facts

- center alpha_u8: `255`
- center validity_alpha_u8: `113`
- center gap: `143`
- largest same-row alpha-validity gap: `x=8 gap=208`
- propagated-validity diff: `{'max_diff': 1, 'mean_diff': 0.004613474151234568, 'nonzero_px': 31119, 'verify_stdout': '=== verify reference_manifest.json ===\n[DIFF]    case_0009            max=1 mean=0.0046 nz=31119/2073600\n---\nok=0 fail=1 missing=0 total=1\nreport_json=/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/manifest_diff.json\nreport_csv=/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/manifest_diff.csv\n'}`
- propagated-validity reading: Replacing outer alpha with a same-kernel propagated validity plane leaves the current Zoom residual unchanged (`max=1 mean=0.0046`). This does not supply the missing 254/255 split by itself.

## Source Candidates

| Rank | Site | Function | Line | Why live | Allowed change shape |
| --- | --- | --- | ---: | --- | --- |
| 1 | `zoom_polar_population_and_validity_capture` | `RenderZoom8` | `709` | The remaining Zoom split is no longer RGB or final-byte broad drift; it is the caller-collapse state between sampler return and final alpha, so source-polar population and preserved-validity capture stay first. | typed caller-collapse input / preserved-validity capture only |
| 2 | `zoom_alpha_accumulation_and_denominator_state` | `RenderZoom8` | `732` | Windows already truncates to the stored byte exactly, and the local propagated-validity probe is inert, so the live question is the alpha coverage denominator or equivalent normalization state before final inverse sampling. | alpha accumulation / denominator state only; no broad geometry rewrite |
| 3 | `zoom_final_inverse_sample_and_u8_writeback` | `RenderZoom8` | `805` | This is second-order only. Reopen it only if a Windows typed witness proves upstream caller-collapse state already matches while the 254/255 split still appears at final sampling. | only with explicit Windows contradiction to the current caller-collapse reading |

## Decision Ladder

1. If Windows typed witness shows the alpha split is already present in caller-collapse inputs -> Constrain changes to polar population / preserved-validity capture in RenderZoom8
2. If Windows proves sampler return is right but the denominator or collapse state differs before final inverse sampling -> Constrain changes to alpha accumulation / denominator state only
3. If Windows shows caller-collapse state already matches but the 254/255 split still appears at final sampling -> Only then reopen final inverse-sample / writeback logic

## Forbidden Actions

- Do not promote direct use of the current preserved-validity plane as final alpha.
- Do not promote a same-kernel propagated-validity plane as the fix.
- Do not retune final byte conversion while Windows already matches the stored byte from traced pre-writeback floats.

## Contract

- Outer witness contract: `refs/conformance/olmradialblur_outer_witness_contract_20260701.md`

