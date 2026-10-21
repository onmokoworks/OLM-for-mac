# Windows Send First

The authoritative selector is:

```bash
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

This project-local staging folder is generated from
`refs/reports/pending_runtime_trace_packages.json`.

## Package

- Request: `olm_runtime_trace_olm_math_ucrt_batch_20260814`
- File: `olm_runtime_trace_olm_math_ucrt_batch_20260814.zip`
- Source: `refs/runtime_trace_packages/olm_runtime_trace_olm_math_ucrt_batch_20260814.zip`
- SHA-256: `9edb35a89d0af02e6c1087026c10e1515f6f48233369403b9b18106c4f3ce5dc`

## Why This One

- AE-free native System32 UCRT capture: 494 exact DirectionalBlur expf vectors plus 787 actual-call DirectionalBlur powf keys and 63 exact DistanceGradation powf vectors in one x64 process.

## Hard Lane Context

Current highest-value external action. It is AE-free and closes only the exact expf/powf leaves; promotion still requires strict keyed validation and final six-plus-eight public-output replay.

## Evidence Note

- `refs/conformance/olm_math_ucrt_batch_request_20260814.json`

## Acceptance

- `refs/runtime_trace_packages/olm_runtime_trace_olm_math_ucrt_batch_20260814.zip::olm_runtime_trace_olm_math_ucrt_batch_20260814/README.md`

## Stop Condition

Return all 1,344 keyed float32 results with one exact 64-bit %WINDIR%\System32\ucrtbase.dll identity; do not launch AE or aerender.

## Share Check

```bash
test -f new/mac_requests/olm_runtime_trace_olm_math_ucrt_batch_20260814.zip \
  && shasum -a 256 new/mac_requests/olm_runtime_trace_olm_math_ucrt_batch_20260814.zip
```
