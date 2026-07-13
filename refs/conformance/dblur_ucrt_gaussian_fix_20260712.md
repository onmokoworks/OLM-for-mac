# OLMDirectionalBlur UCRT Gaussian Table Fix

Date: 2026-07-12

## Verdict

`binary-grounded / known-red`

The Windows x64 UCRT return validates all `336` Gaussian result words used by
the Alpha Fade case. The captured `ucrtbase.dll!expf` words are reproduced by
preserving the AEX float argument, evaluating double `exp`, and rounding once
to float. The previous macOS `expf(float)` differs by one ULP at `n=96/i=47`
and `n=240/i=7`.

The shared core, CLI, and Mac fallback now use the validated model. This closes
the platform-libm portion of the residual, but does not make Alpha Fade
`AE exact`.

## FACT

- Accepted Windows run id: `c98e98ab-b69f-4eb0-b7d8-0e810e06e0ab`.
- Windows process and OS architecture: `X64`, 64-bit.
- UCRT version: `10.0.22621.3593 (WinBuild.160101.0800)`.
- UCRT SHA-256: `d93ce42cd625510b2355de086bcd19e2c11307ccade7bad62b09c7f340a866ba`.
- `n=96`: double-exp-then-float `96/96`; macOS expf `95/96`.
- `n=240`: double-exp-then-float `240/240`; macOS expf `239/240`.
- Focused C++ smoke matches the validated return table at `336/336` words.
- Mac AE 26.3 Software, 8bpc, PREMULTIPLIED input against the hash-pinned
  current-2025-AEX reference improves from `563` differing pixels to `226`.
- Remaining result: `max_diff=3`, `mean_diff=0.0000617284`, `226` differing
  pixels, all in the previously identified `x=1308`, `y=184..517` family.
- The first run after installation used the runner's default input alpha
  interpretation and produced a broad max-60 mismatch. It is excluded from
  conformance. The accepted rerun explicitly set `PREMULTIPLIED`, matching the
  Windows capture contract.

## INFERENCE

- The broad arm64-versus-macOS-x86_64 split was caused by platform `expf` and
  is closed by the UCRT-grounded model.
- The surviving `226`-pixel column is independent of the two Gaussian table
  word differences. Its next boundary is the first divergent prepass,
  rowdriver/scatter, or rotate-back intermediate at the affected column.
- No channel bias, pixel lookup, or PNG-derived correction is authorized.

## Evidence

- `refs/reports/dblur_ucrt_expf_return/20260712_132106__RETURN__olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711__answered_portable_analysis.md`
- `refs/reports/dblur_ucrt_expf_return/20260712_132106__RETURN__olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711__answered_portable_validated_tables.json`
- `refs/scripts/smoke_dblur_ucrt_gaussian_model.py`
- `refs/conformance/dblur_ucrt_gaussian_mac_ae_20260712.json`
