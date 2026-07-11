# OLMDistanceGradation depthgate true16 reverify

Date: 2026-07-09

## Decision

The earlier `7/16` depthgate checkpoint must not be used as a true16
conformance count. Re-verifying the same `/tmp/olmdg_16ext_depthgate2` output
with the canonical 16bpc verifier gives `5/16`, matching the current integrated
batch shape for the non-Layer families.

This removes the suspected "current integrated vs depthgate provenance delta".
The real open work is the true16 residual families that were hidden by an
8-bit/PIL-style comparison path:

- `0010/0011`: max `2`, sparse.
- `0012/0013/0014/0016`: Layer/no-bg family, now much improved in the current
  integrated build but not exact.
- `0024..0028`: true16 quantization/field/export family, not merely the older
  max=1 byte-view near-miss.

## Command Evidence

```sh
python3 scripts/verify_ae_pixel_validation_result.py \
  --run-dir refs/reports/ae_validation_batch_olmdistancegradation_16bpc_depthgate_singlecase_reverify_20260709 \
  handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625 \
  /tmp/olmdg_16ext_depthgate2
```

Output:

```text
=== verify reference_manifest.json ===
[OK]      olmdistancegradation_extended__case_0008 max=0 mean=0.0000
[DIFF]    olmdistancegradation_extended__case_0010 max=2 mean=0.0002 nz=351/2073600
[DIFF]    olmdistancegradation_extended__case_0011 max=2 mean=0.0002 nz=501/2073600
[DIFF]    olmdistancegradation_extended__case_0012 max=16384 mean=332.1975 nz=278028/2073600
[DIFF]    olmdistancegradation_extended__case_0013 max=16384 mean=239.5012 nz=167383/2073600
[DIFF]    olmdistancegradation_extended__case_0014 max=16384 mean=416.1758 nz=378683/2073600
[DIFF]    olmdistancegradation_extended__case_0016 max=9710 mean=26.6437 nz=14131/2073600
[OK]      olmdistancegradation_extended__case_0020 max=0 mean=0.0000
[OK]      olmdistancegradation_extended__case_0021 max=0 mean=0.0000
[OK]      olmdistancegradation_extended__case_0022 max=0 mean=0.0000
[OK]      olmdistancegradation_extended__case_0023 max=0 mean=0.0000
[DIFF]    olmdistancegradation_extended__case_0024 max=20 mean=0.3274 nz=1051915/2073600
[DIFF]    olmdistancegradation_extended__case_0025 max=6 mean=0.2896 nz=860084/2073600
[DIFF]    olmdistancegradation_extended__case_0026 max=4 mean=0.2682 nz=900709/2073600
[DIFF]    olmdistancegradation_extended__case_0027 max=4 mean=0.1176 nz=451535/2073600
[DIFF]    olmdistancegradation_extended__case_0028 max=3080 mean=7.2604 nz=457177/2073600
---
ok=5 fail=11 missing=0 total=16
```

## Correction

- FACT: `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`
  remains valid evidence for the depth-gated source-mask rule and for closing
  `case_0023`.
- FACT: its `7/16` exact count is superseded for true16 conformance.
- FACT: the current integrated canonical batch and the depthgate single-case
  artifacts agree on the non-Layer true16 residual shape when both are checked
  with the canonical verifier.
- INFERENCE: do not spend more time looking for a current-vs-depthgate source
  delta. The next bounded DG work is direct true16 residual classification and
  a narrow implementation/proof path for those remaining families.
