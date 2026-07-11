# OLMDirectionalBlur Angle-0 Helper Gate Return Acceptance - 2026-07-07

- Request: `olmdirectionalblur_angle0_helper_gate_retry_20260702`
- Return: `20260707_180927__olm_directionalblur_return_20260707.zip`
- Intake comparison: `refs/reports/runtime_trace_comparisons/olmdirectionalblur_dense_sampler.md`
- Status: `answered_partial`
- Decision: `reachability-proven-per-pixel-typed-witness-missing`

## FACT

- Windows AE rendered in Software mode for AE `26.2x49`.
- The previous execution blocker was environmental, not algorithmic:
  `OLM_REQUEST_DIR` pointed at an empty directory, so the JSX runner could not
  see the request JSON.
- After fixing the request path, `OLMDirectionalBlur` loaded.
- The return directly observed broad breakpoint reachability at:
  - `+0x13e0` front scatter helper
  - `+0x38d0` rowdriver / rotate stage
  - `+0x4a20` normalize stage
  - `+0x6b30` output 8bpc writer
  - `+0x4880` rotate-back stage
- The return did not isolate typed witness values for `(494,169)` or
  `(579,169)`.
- The front-helper `gc` auto-continue strategy caused a large hit storm, so the
  requested per-pixel values were not retained.

## INFERENCE

- This return proves that the target plug-in and relevant broad stage offsets
  are reachable in the real Windows AE run.
- It does not prove rowdriver/group membership, helper-local source mapping,
  denominator, validity/alpha side-channel, pre-writeback values, or final
  writer values for the two angle-0 witnesses.
- Therefore no `cli/OLMDirectionalBlur` or `mac/OLMDirectionalBlur` algorithm
  change should be made from this return alone.

## Next Windows Shape

Do not send a broad DirectionalBlur package. Reuse the same narrow contract, but
change execution from broad auto-continue to conditional or single-shot witness
gating.

Required same-pass fields for both `(494,169)` and `(579,169)`:

- normalized consumed parameters
- output-to-A/B or output-to-rotated-buffer coordinate mapping
- helper-local source x/y
- actual touched destination x range on row `y=169`
- rowdriver/group membership
- denominator value
- `alpha_or_valid` or equivalent validity side-channel
- accumulation numerator RGBA
- pre-writeback RGBA float/hex
- final stored RGBA bytes

Classify the next return as partial/failure again if it reports only module
load, broad breakpoint reachability, final bytes, or omits helper-local
destination range.

