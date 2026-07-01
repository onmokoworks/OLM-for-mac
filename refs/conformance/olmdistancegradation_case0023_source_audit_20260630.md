# OLMDistanceGradation case_0023 Source Audit - 2026-06-30

This note maps the remaining Constant `case_0023` lane to the specific Mac
source sites that still plausibly own the residual.

Primary evidence:

- `refs/conformance/olmdistancegradation_16bpc_case0023_pointdebug_20260630.md`
- `refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.md`
- `refs/conformance/olmdistancegradation_16bpc_case0023_plateau_transition_20260701.md`
- `refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_case0023_outside0_witness.md`

Target file:

- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`

## What the current witness already proves

- Two surviving buckets remain:
  - `inside EDT = 1.0` with `outside EDT = 0.0`
  - `inside EDT ~= 36` with `outside EDT = 0.0`
- Live Mac point-debug proves the wrong endpoint is already decided before the
  final 16bpc store.
- Windows runtime evidence still classifies the lane as Constant
  threshold-ownership / plateau membership, not generic compose drift.
- The best local outside-side probe family (`trunc_plateau_binary`) is useful
  only as a hypothesis generator. A 2026-07-01 bucket transition audit shows it
  does not gently resolve the live `73px` residual; it explodes the whole frame
  to `182793px`, with broad new residuals across many inside-EDT buckets. So it
  should not be promoted as an implementation candidate, only as evidence that
  a broad plateau rewrite is too coarse.

## Candidate source sites

### 1. Constant thresholding in `dt_to_normalized(...)`

Relevant lines:

- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:411`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:417`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:419`

Current rule:

- for Constant interpolation:
  - `out[i] = (out[i] > t) ? 1.0f : 0.0f;`

Why it still matters:

- The remaining witness is exactly about threshold ownership, especially
  `Both + Outside Threshold=0`.
- The unresolved question is no longer “should Constant be binary?” but
  “which side owns equality / plateau membership at this threshold boundary?”

### 2. `BOTH` composition of inside/outside fields in `build_distance_field(...)`

Relevant lines:

- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:479`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:481`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:485`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:487`

Current rule:

- `df.x[i] = std::max(inside[i], outside[i]);`

Why it still matters:

- The active Windows ask is precisely about `selected_side_for_both_mode` and
  the `Outside Threshold=0` special lane.
- If Windows proves the decisive value is already wrong before compose, this
  `inside/outside -> max(...)` ownership path is the first place to revisit.

### 3. `compose_pixel(...)` is still second-order

Relevant lines:

- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:516`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:523`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:535`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:558`

Why it is not first:

- The Mac point-debug already shows `field_x` differs at the problematic
  threshold witnesses before final color writeback.
- The Windows follow-up comparison also points to
  `constant-boundary-threshold-ownership`, not compose-field-byte behavior.

`compose_pixel(...)` should only be reopened if a later typed Windows witness
shows that the field/ownership value already matches Mac but the endpoint still
does not.

## Operational takeaway

For the next real source change, the safest order is:

1. `dt_to_normalized(...)`
2. `build_distance_field(...)`
3. only then `compose_pixel(...)` if Windows contradicts the current read

That keeps the fix boundary aligned with the current witness quality.
