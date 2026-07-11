# OLMRadialBlur Zoom CLI Polar Alpha Candidate Probe

Date: 2026-07-08

## Verdict

`near-inert_candidate_not_promoted`

The combined candidate `--zoom-grid-mode aex-float --rgba-sampler-alpha-mode repeat-raw-f32 --outer-caller-collapse-mode polar-alpha` does not close `case_0009`. It slightly reduces nonzero pixels but leaves the primary witness `(6,0)` at `[20,3,3,255]` instead of Windows `[20,3,3,254]`.

## Result

- Baseline current: `max=1 mean=0.0046 nonzero_px=31119`
- Candidate: `max=1 mean=0.0046 nonzero_px=31097`
- Witness sample: `[20,3,3,255]`
- Witness alpha: `1`
- Witness cell alpha: `[1,1,1,1]`

## Interpretation

The AEX/Python prefill candidate remains useful, but this direct CLI translation is not enough. The remaining implementation gap is likely the exact AEX polar cell coordinate/float sequence or plane selection before the final sample, not final byte packing. Keep this as a rejected/narrowing CLI candidate rather than promoting it to Mac source.
