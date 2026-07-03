# OLMToonDilate 16bpc Single-Case Host Probe - 2026-07-03

Status: `ae-exact-batch-rerun-confirmed`

The new Windows `16bpc` Software reference for `OLMToonDilate` was imported
from:

- [refs/win_references/olm_reference_return_windows_20260703_combined/OLMbit-depthconformancebatch/reference_manifest.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olm_reference_return_windows_20260703_combined/OLMbit-depthconformancebatch/reference_manifest.json)

We then materialized a focused Mac AE request:

- [handoff/ae_pixel_validation_20260618/requests/ae_pixel_olm_bitdepth_16bpc_toondilate_exact_20260703](/Users/onmk/Documents/Projects/Personal/OLM%20as/handoff/ae_pixel_validation_20260618/requests/ae_pixel_olm_bitdepth_16bpc_toondilate_exact_20260703)

## What happened

An earlier batch AE validation attempt reported `PNG was not written` for all
three cases. We then narrowed the lane with isolated single-case AE rendering,
which succeeds for all three cases and compares exact:

- `olmtoondilate__case_0001` writes successfully and compares exact
- `olmtoondilate__case_0002` writes successfully and compares exact when run in
  its own output directory
- `olmtoondilate__case_0003` writes successfully and compares exact

After removing the duplicate plug-in backup from `MediaCore` and rerunning the
same batch request in a fresh workspace path, the full batch now succeeds too:

- [handoff/ae_pixel_validation_20260618/batch_run_20260703_145742/AE_PIXEL_VALIDATION_BATCH_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/handoff/ae_pixel_validation_20260618/batch_run_20260703_145742/AE_PIXEL_VALIDATION_BATCH_RESULT.json)
- verifier report:
  `/private/tmp/verify_toondilate16_batch_20260703/reports/ae_pixel_all_exact.json`

So the current lane outcome is:

- `single-case / isolated output dir` -> works, exact
- `fresh batch rerun in workspace` -> works, exact
- earlier `PNG was not written` batch failure is now treated as a stale host-state / environment incident, not a current algorithm or harness blocker

## Exact evidence

### case_0001

- Mac AE single-case result:
  [AE_SINGLE_CASE_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_case0001_20260703/AE_SINGLE_CASE_RESULT.json)
- Candidate PNG:
  [case_0001 output](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_allcases_20260703/olm_bitdepth_16bpc_toondilate_exact_20260703__software_16bpc__fr24__olmtoondilate__case_0001.png)
- Direct compare result:
  `max_diff=0`, `mean_diff=0.0`, `nonzero_px=0`

### case_0003

- Mac AE single-case result:
  [AE_SINGLE_CASE_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_case0003_20260703/AE_SINGLE_CASE_RESULT.json)
- Candidate PNG:
  [case_0003 output](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_case0003_20260703/olm_bitdepth_16bpc_toondilate_exact_20260703__software_16bpc__fr24__olmtoondilate__case_0003.png)
- Direct compare result:
  `max_diff=0`, `mean_diff=0.0`, `nonzero_px=0`

### case_0002

- Mac AE single-case result:
  [AE_SINGLE_CASE_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_case0002_20260703/AE_SINGLE_CASE_RESULT.json)
- Candidate PNG:
  [case_0002 output](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_case0002_20260703/olm_bitdepth_16bpc_toondilate_exact_20260703__software_16bpc__fr24__olmtoondilate__case_0002.png)
- Direct compare result:
  `max_diff=0`, `mean_diff=0.0`, `nonzero_px=0`

### Earlier failure witness

- Shared-output single-case failure log:
  [AE_SINGLE_CASE.log](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_allcases_20260703/AE_SINGLE_CASE.log)
- Shared-output single-case failure result:
  [AE_SINGLE_CASE_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_olmtoondilate_16bpc_allcases_20260703/AE_SINGLE_CASE_RESULT.json)

Observed sequence:

- effect loads
- `Search Radius` is applied successfully
- `saveFrameToPng returned`
- target PNG does not exist on disk afterward

This remains useful only as historical evidence that the lane once failed in a
host/environment-specific way. It is no longer the current state of the lane.

## Decision

Do not reopen the `OLMToonDilate` algorithm from this lane.

The current grounded interpretation is:

1. `case_0001`, `case_0002`, and `case_0003` all have `AE exact` behavior in
   live Mac AE under the new `16bpc` Windows reference.
2. That claim is now supported by both isolated single-case runs and a fresh
   batch rerun.
3. The active next step for `OLMToonDilate` is no longer host-debugging; it is
   simply broader bit-depth expansion or final holdout use, not algorithm
   retuning.
