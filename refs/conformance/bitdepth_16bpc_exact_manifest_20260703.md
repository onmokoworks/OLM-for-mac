# Covered 16bpc Exact Slices

This note freezes the 16bpc slices that can currently be re-verified
locally against Windows AE Software references with zero diff.

- Generated at: `2026-07-07T13:38:57Z`
- Total cases: `12`

## Totals

- AE exact: `12`

## By Plug-in

| Plug-in | Total | AE exact | AE residual |
| --- | ---: | ---: | ---: |
| OLMColorKey | 9 | 9 | 0 |
| OLMToonDilate | 3 | 3 | 0 |

## Suites

### OLMColorKey

- Feature: `OLMColorKey covered 16bpc slice`
- Bit depth: `16bpc`
- Request: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmcolorkey_exact_20260625`
- Result dir: `handoff/ae_pixel_validation_20260618/results/bitdepth16_olmcolorkey_exact`
- Counts: `{'AE exact': 9}`
- Notes: Live Mac AE verification against the imported Windows Software 16bpc request currently passes 9/9 with max_diff=0.

### OLMToonDilate

- Feature: `OLMToonDilate covered 16bpc slice`
- Bit depth: `16bpc`
- Request: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_olm_bitdepth_16bpc_toondilate_exact_20260703`
- Result dir: `handoff/ae_pixel_validation_20260618/results/olm_bitdepth_16bpc_toondilate_exact`
- Counts: `{'AE exact': 3}`
- Notes: Live Mac AE verification against the imported Windows Software 16bpc request currently passes 3/3 with max_diff=0.

## Interpretation

- These rows are narrow covered slices only. They do not imply whole-plugin 16bpc completion.
- `OLMColorKey` and `OLMToonDilate` can already be held to 16bpc `AE exact` for the declared covered cases.
- `OLMBlur`, `OLMDistanceGradation`, and the unresolved hard plugins still need separate 16bpc proof lanes.
