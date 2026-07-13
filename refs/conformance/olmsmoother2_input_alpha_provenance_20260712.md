# OLMSmoother2 Input/Alpha Provenance A/B

Date: 2026-07-12

## Scope

Mac AE 26.3 diagnostics for
`legacy_case_0012_gamma5_red_blue_current_aex`. These are input provenance
experiments only; no production source was changed.

Reference output: the current Windows Software PNG for case 0012.

## Results

| Input | AE alpha mode | Target `(91,841)` | max_diff | mean_diff | differing pixels |
| --- | --- | --- | ---: | ---: | ---: |
| Windows `before_effects_frame` | default | `[32,32,32,91]` | 115 | 0.161655 | 19,486 |
| Windows `before_effects_frame` | `PREMULTIPLIED` | `[0,0,0,0]` | 254 | 0.440839 | 20,069 |
| Windows `before_effects_frame` | `STRAIGHT` | `[32,32,32,91]` | 115 | 0.161655 | 19,486 |
| Windows `before_effects_frame` | `IGNORE` | `[16,16,16,65]` | diagnostic only | diagnostic only | diagnostic only |
| original `current_olm_cells.png` | default | `[0,0,0,0]` | 254 | 0.551869 | 20,000 |
| original `current_olm_cells.png` | `PREMULTIPLIED` | `[26,26,26,82]` | 148 | 0.171156 | 21,381 |

## FACT

- A target-pixel match can be produced by changing the input artifact or alpha
  interpretation while the full-frame result becomes worse.
- The existing `before_effects_frame` and original `current_olm_cells.png`
  are not interchangeable evidence for this case.
- The input provenance and alpha mode must be recorded in any future Windows
  and Mac AE comparison package.

## INFERENCE

- No alpha mode is promoted as the Windows contract from these A/Bs.
- The remaining Smoother2 case must be compared using a same-run input artifact,
  parameters, host mode, and complete output frame. A target-only match is
  insufficient.
- The next useful Windows witness remains the live class/config and producer
  binding, together with explicit input alpha provenance.

## Verification

Each row was rendered through `scripts/run_ae_single_case.py` and compared over
the complete `1920x1080x4` PNG, not just the target pixel.
