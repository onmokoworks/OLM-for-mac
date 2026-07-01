# OLMBlur case_0006 Source Audit - 2026-06-30

This note maps the current non-Legacy `case_0006` witness to the exact Mac
source sites that can still plausibly explain it.

Primary evidence:

- `refs/conformance/olmblur_case0006_nonlegacy_helper_witness_20260630.md`
- `refs/reports/runtime_trace_returns/olmblur_case0006_helper_prestore_failed_20260630/summary.md`
- `refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_failed_20260630/olmblur_case0006_helper_prestore_witness.md`

Target file:

- `mac/OLMBlur/OLMBlur.cpp`

## What the live witness already rules out

- The remaining pair is still sign-mixed:
  - `(314,14)` wants Windows internal word `1101` while Mac stores `1100`
  - `(29,71)` wants Windows internal word `363` while Mac stores `364`
- Mac helper dumps already diverge before `store16()`.
- Therefore the first suspect is not the final 16bpc store rule by itself.

## Candidate source sites

### 1. Non-Legacy horizontal accumulation

File facts:

- `blur_1d_horizontal(...)`
- left scan: `x - k`, stop on first zero alpha
- right scan: `x + k`, stop on first zero alpha
- both sides include `k == 0` only once
- normalization uses `1.0f / sumW`

Relevant lines:

- `mac/OLMBlur/OLMBlur.cpp:113`
- `mac/OLMBlur/OLMBlur.cpp:136`
- `mac/OLMBlur/OLMBlur.cpp:149`
- `mac/OLMBlur/OLMBlur.cpp:162`

Why it still matters:

- The current witness says the two tracked pixels already split during helper
  accumulation even when sample-count / span structure looks the same.
- That leaves source-history differences, edge-stop behavior, or per-iteration
  carry entering this helper as the most likely source-side cause.

### 2. Non-Legacy vertical accumulation

File facts:

- `blur_1d_vertical(...)`
- up scan: `y - k`, stop on first zero alpha
- down scan: `y + k`, stop on first zero alpha
- normalization again uses `1.0f / sumW`

Relevant lines:

- `mac/OLMBlur/OLMBlur.cpp:181`
- `mac/OLMBlur/OLMBlur.cpp:201`
- `mac/OLMBlur/OLMBlur.cpp:215`
- `mac/OLMBlur/OLMBlur.cpp:229`

Why it still matters:

- The strongest live split for the tracked pair is visible in the vertical
  helper output of the last iteration.
- If the next Windows witness proves the helper-local values are already split
  in the same direction, this function becomes the most likely fix boundary.

### 3. Final 16bpc writer remains secondary, not eliminated

The pending Windows package still asks for:

- helper-local / last upstream value
- pre-store float
- final stored internal word

That is still the correct contract because the final writer is only actionable
if Windows later shows:

- helper values match Mac, but
- stored word does not

Until then, writer-only surgery is still too broad.

## Operational takeaway

If the next Windows retry finally returns typed values for `(314,14)` and
`(29,71)`, the safest read order is:

1. compare helper-local / pre-store values first
2. reopen `store16` only if helper/pre-store already match

That is the narrowest route to a bounded source change.
