# OLMDistanceGradation 16bpc rerun via AE batch wrapper

- Date: `2026-06-29`
- Runner:
  `python3 scripts/run_ae_validation_batch.py`
- Request:
  `ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate output:
  `refs/reports/ae_batch_distancegradation_extended_rerun_20260629/candidate/bitdepth16_olmdistancegradation_extended_exact/`
- Verification report:
  `refs/reports/ae_batch_distancegradation_extended_rerun_20260629/verify/reports/ae_pixel_16bpc_extended_exact.json`

## Why this rerun matters

The old AE batch path could pick up stale request selection state. A new wrapper
now injects request ids through environment variables, matching the reliable
single-case launch path.

## Result

The rerun is host-stable, but it does **not** promote the current
DistanceGradation 16bpc state to a better global classification yet.

Authoritative 16bpc verification still reports:

- `ok=1`, `fail=15`, `total=16`
- exact only: `case_0008`
- unchanged residual families remain present:
  - `case_0012 max=16476 mean=332.8368 nz=285406`
  - `case_0016 max=9710 mean=26.6457 nz=14196`
  - `case_0020 max=61165 mean=0.0144 nz=1`
  - `case_0022 max=61165 mean=2.7663 nz=192`
  - `case_0026 max=11480 mean=2.9254 nz=902747`

## Important correction

Some earlier spot comparisons on single-case PNGs used an 8-bit image-loading
path and produced small-looking numbers like `max=65` or `-1/-2` RGB at viewer
space. Those are useful as quick visual witnesses, but they are **not**
authoritative 16bpc conformance results.

The authoritative result for 16bpc remains the verifier-backed batch compare in
`verify_ae_pixel_validation_result.py`, which still shows the broader residual
families above.

## Takeaway

The new batch wrapper is a real infrastructure improvement: it gives us a
reliable way to rerun targeted AE validation batches without stale
`REQUEST_IDS.txt` state.

For algorithm status, though, the current narrow Layer/no-bg source patch should
still be treated as local evidence only. The next accepted moves remain:

1. witness-bounded Layer/no-bg cleanup for `case_0012/0016`
2. Constant boundary ownership proof for `case_0020/0022`
3. no broad "looks closer in PNG" reclassification
