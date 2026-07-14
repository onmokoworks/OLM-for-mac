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

- OLMDistanceGradation current-AEX 8bpc field staging, compose, and host store

## Acceptance

- `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712/README_RUNTIME_TRACE.md`

## Stop Condition

PENDING: do not send or classify this package as answered. The current runner is retained only as a historical failed attempt until a separate typed-boundary implementation is reviewed.

## Share Check

```bash
test -f /Volumes/onmk/olm_pr/new/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip \
  && shasum -a 256 /Volumes/onmk/olm_pr/new/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip
```
