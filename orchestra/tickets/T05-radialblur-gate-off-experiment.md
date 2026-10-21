## Goal
Measure what the RadialBlur port would output if its admission gates did not refuse.
This decides whether the gates hide working code (lift them) or missing code (implement).

## Facts
- T03 census: `reports/fuzz/radialblur_refusals_20261021.md`. Top gates:
  1 `RenderZoomTyped:unadmitted-zoom-profile` (204/204), 2 `RenderWorld:generic-world-not-admitted`
  (120/96), 3 `RenderRotationTyped:unadmitted-rotation-profile` (30/30), 4 `type3-zero-noise`,
  5 `unadmitted-zoom-noise-inner-profile`, 7 `unadmitted-two-stage-profile`.
- Guards are tagged via `OLM_RADIAL_REFUSAL(tag)` in `mac/OLMRadialBlur/OLMRadialBlur.cpp`.

## Steps
1. EXPERIMENT ONLY, never committed to production: add a compile-time switch
   (e.g. `-DOLM_RADIAL_EXPERIMENT_BYPASS="tag1,tag2"` or a set of `#ifdef`s) so a
   scratch build skips chosen guards and falls through to the code that would run next.
   If a guard has no meaningful fall-through (nothing implemented after it), record
   "no fall-through path" for that guard instead of inventing one.
   The default build (no define) must be byte-identical in behavior: re-verify
   `tools/fuzz` corpus replay 35/35.
2. Let the fuzzer use the bypass build (add an optional `--candidate-define` or env
   to the RadialBlur adapter; default off).
3. For each top gate separately, and then all of them together, run `--n 500 --seed 1`
   with a scratch `--corpus`. Report per gate: cases unblocked, of those exact /
   mismatch / crash / new error, and mismatch clusters.
4. Run sanitizer build (ASan/UBSan, find existing flags) for the all-bypass variant on
   the unblocked cases; report any memory errors (these mean the gate protects real UB).

## Done when
A table per gate: unblocked N, exact, mismatch, crash/UB. Commit the switch only if it
is compile-time-off by default; commit reports under `reports/fuzz/`.
