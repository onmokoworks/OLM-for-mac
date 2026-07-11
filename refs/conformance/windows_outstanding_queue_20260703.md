# Windows Outstanding Queue - 2026-07-03

Status: `consolidated-share-published`

The shared Windows handoff folder has been republished as a consolidated queue
so multiple live asks can coexist in `/Volumes/onmk/olm_pr/new`.

## Published queue

Current share payload:

- `olm_reference_request_32bpc_full_probe_exr_rerun_20260703.zip`

Runtime-trace pending asks are tracked separately in:

- `refs/reports/pending_runtime_trace_packages.md`

That report now carries the current hard-lane context for each live debugger ask,
so the shared-folder payload can stay small while the proof intent remains
explicit in-repo.

32bpc status authority:

- `refs/conformance/bitdepth_32bpc_probe_status_20260703.md`
- `refs/conformance/bitdepth_32bpc_compare_policy_20260703.md`

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
- still confirms focused `OLMColorKey` 32bpc (`9` cases), but only as
  `probe-only-png-return`
- still confirms focused `OLMToonDilate` 32bpc (`3` cases)

## Practical consequence

Windows-side work can now pick up:

1. the broad `32bpc` EXR-first full-probe rerun bundle

without requiring another republish between each item.

For runtime-trace work, use `refs/reports/pending_runtime_trace_packages.md`
as the source of truth for which request is still live, why it exists, and what
exact witness it must return.
