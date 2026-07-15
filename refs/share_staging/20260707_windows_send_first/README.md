# Windows Send First

The authoritative selector is:

```bash
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

This project-local staging folder is generated from
`refs/reports/pending_runtime_trace_packages.json`.

## Package

- Request: `olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712`
- File: `olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip`
- Source: `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip`
- SHA-256: `8017e17f2010778d032a68d8cb23785395ef5141ce306b2fc90b79e8e5a3deae`

## Why This One

- OLMDistanceGradation PF8 typed field/compose/host boundary

## Acceptance

- `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712/README_RUNTIME_TRACE.md`

## Stop Condition

Return answered only for 15 typed records plus PF8>0/PF32=0, one run/PID/base/hash/depth identity, and one output address within each case. Otherwise exact_bind_failure with raw logs.

## Share Check

```bash
test -f /Volumes/onmk/olm_pr/new/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip \
  && shasum -a 256 /Volumes/onmk/olm_pr/new/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip
```
