# OLMRadialBlur tiny Rotation Return Acceptance - 2026-07-01

This note explains how to judge the next narrow Windows runtime-trace return
for tiny Rotation only.

## Current narrow package

- request id:
  `olmradialblur_tiny_rotation_substitute_path_followup_20260701`
- target:
  `OLMRadialBlur case_0010 (1614,6)`
- expected post-import report:
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_followup_20260701.md`
  from `scripts/compare_radialblur_trace.py`, which now carries the frozen
  local tiny-Rotation lane context beside the Windows typed witness.

## `answered`

Classify the package as fully `answered` only if it returns an actionable typed
upstream chain that explains why Windows lands on white while the current Mac
candidate stays black.

That means at least one of these must be true:

1. the return isolates the exact substitute/fallback branch and shows the typed
   RGB/A values that replace the near-black inverse-sampler result, or
2. the return isolates the exact source-population / neighbor-contribution path
   and shows which nearby bright contribution should have been present before
   final inverse sampling.

In either case, the return must include:

- exact target case and XY
- typed values, not only screenshots
- enough stage placement to map the rule back to Mac source structure

## `answered_partial`

Use `answered_partial` if the return is useful but still not enough to guide a
safe implementation change, for example:

- final white byte is reconfirmed
- same near-black inverse-sampler return is reconfirmed
- substitute/fallback is only suspected, not isolated
- neighborhood structure is shown, but the decisive branch/value is missing

## `trace-too-sparse` / `not isolated`

Use these if the return misses the requested proof boundary:

- closest call only, wrong site
- only final bytes
- only PNGs
- only branch guesses with no typed values

## Forbidden promotion

Do not treat "white final byte exists" as an answered state.

The point of this follow-up is not to prove the output again. It is to prove
the upstream branch or contribution ownership that creates that output.
