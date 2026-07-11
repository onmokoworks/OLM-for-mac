# OLMRadialBlur Zoom case_0009 Local Candidate Rejection

This is a Mac-side/local analysis note only. It does not promote
`OLMRadialBlur` to `AE exact` and does not justify a Mac source change.

## Scope

- Plug-in: `OLMRadialBlur`
- Case: `case_0009`
- Lane: 8bpc Zoom no-inner/no-noise, Windows Software reference
- Target anomaly: top row alpha `254` occurs only at `x = [6, 7, 12]`
- Current blocker: no same-run Windows typed final-plane cell witness has been
  captured yet.

## Facts

- The latest Windows return
  `refs/returns/windows/20260709_radialblur_zoom_case0009_final_plane_cells_failed_partial/20260709_return__olm_runtime_trace_olmradialblur_zoom_case0009_final_plane_cells_20260709_windows.zip`
  is `failed_partial`. It contains package-local candidate context, but no
  fresh Windows final-plane cell IDs, per-cell RGBA/alpha floats, bilinear
  weights, or retained hook/watchpoint failure artifact.
- `refs/conformance/olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.md`
  rejects pure final-sample arithmetic as the missing rule. Every epsilon
  variant misses all three Windows `254` pixels. Truncate variants either miss
  one or more targets or add false positives.
- The strongest final-sample truncate sequence,
  `f32_products_sum_double`, hits `[6, 7, 12]` but also emits
  `[0, 1, 2, 4, 5, 15, 16, 17, 18, 21, 25]` as false positives.
- `refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md`
  rejects a simple cell-offset patch. The best local cell-set candidate
  (`cpp-double`, angle offset `+1`, radius offset `-2`, truncate) hits all
  three target pixels but also emits `254` at
  `[3, 4, 8, 10, 11, 13, 24, 25, 26, 27, 28]`.
- `x=7` remains the discriminating pixel: local current final cells can all be
  alpha `1.0`, while Windows still stores alpha `254`.

## Rejected Local Fixes

| Candidate | Result | Reason |
| --- | --- | --- |
| Global alpha truncate | rejected | fixes some target bytes but creates broad false positives |
| Final-sample arithmetic order only | rejected | no arithmetic variant matches `[6, 7, 12]` without false positives |
| Uniform final-plane cell offset | rejected | best offset model hits all targets but also many controls |
| Late byte writer change | rejected for this lane | prior Windows witness shows pre-writeback floats already truncate to the Windows byte for `(6,0)` |

## Next Useful Proof

The next useful evidence is still the same-run Windows final-plane witness, but
it can be narrowed further:

1. Prioritize `(7,0)` first, because it separates coordinate/cell selection
   from ordinary sub-one-alpha interpolation.
2. Capture final inverse-sampler coordinate, four final-plane cell IDs, each
   cell's alpha/RGBA float, bilinear weights, and pre-byte alpha for `(7,0)`.
3. Add controls `(8,0)` and `(24,0)` because the second-best offset candidate
   hits `[6,7,8,24]`; these two controls can reject that model quickly.
4. Add `(6,0)` and `(12,0)` only after `(7,0)` has a typed cell witness, unless
   the hook naturally records all three in the same pass.

## Interpretation

The remaining Zoom `case_0009` alpha residual is not a cosmetic PNG tuning
problem. The local evidence points to final-polar coordinate/cell selection or
source-plane population. A Mac source edit should wait for a same-run Windows
typed witness or an exact hook/watchpoint failure artifact.
