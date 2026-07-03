# Windows Outstanding Queue - 2026-07-03

Status: `consolidated-share-published`

The shared Windows handoff folder has been republished as a consolidated queue
so multiple live asks can coexist in `/Volumes/onmk/olm_pr/new`.

## Published queue

Current share payload:

- `olm_runtime_trace_windows_ae_addproperty_stall_diagnostics_20260703.zip`
- `olm_reference_requests_pending_20260703.zip`
- `olm_reference_request_16bpc_toondilate_exact_20260703.zip`
- `olm_reference_request_32bpc_colorkey_probe_20260703.zip`

## Reason

The previous one-at-a-time publish flow left only the most recent artifact in
`new`, which made it too easy for older still-live asks to silently fall out of
view.

The consolidated staging publish fixes that operationally without changing any
individual request contents.

## Local verification

Bit-depth generation smoke was rerun after materializing the new bit-depth
artifacts:

- `python3 refs/scripts/smoke_generate_bitdepth_reference_request.py`

Result:

- passed
- still regenerates the mixed 16bpc request as `48` cases
- still confirms focused `OLMColorKey` 32bpc (`9` cases)
- still confirms focused `OLMToonDilate` 32bpc (`3` cases)

## Practical consequence

Windows-side work can now pick up:

1. the host `addProperty` diagnostic
2. the pending reference bundle
3. the focused `OLMToonDilate` 16bpc request
4. the focused `OLMColorKey` 32bpc probe

without requiring another republish between each item.
