# OLMBlur case_0006 Unverified Windows Value Audit

Date: 2026-07-10

## Verdict

The 2026-07-01 `answered` classification for
`olmblur_case0006_helper_prestore_witness_20260630` is invalid. The numeric
`windows_*` fields are not backed by a retained Windows CDB/runtime target and
must not be used as binary proof.

The request is now classified `invalid_unverified_values`. The earlier claim
that Windows and Mac agree on `1100.5 -> 1100` and `363.5 -> 364` is retracted.

## FACT

- The original 2026-06-30 return status is
  `failed_breakpoint_watchpoint` and says:
  `No TARGET_OLMBLUR_CASE0006_* block was captured.`
- Its `windows_pre_store_rgb_float`,
  `windows_helper_or_last_upstream_rgb_hex`, and
  `windows_internal_word_store` fields are all `null`.
- The later 2026-07-01 return changes the result status to `answered` and fills
  the `windows_*` fields with the same values already present in the
  `mac_live_*` fields, while still saying the exact CDB bind was missed.
- The later ZIP contains no new debug-dump artifact that could establish those
  values as Windows measurements.
- The CDB console is byte-identical across the failed and later returns:
  `78b3ef9a6dd49666dd0d3e2cb13e75370704cac76161bd766bbe57868973d53e`.
- The probe JSX is also byte-identical:
  `2dc4bc6653cdaa274b50c8125b63ecad5cb98faf20864aa12c96a92b9448f17a`.
- The later return's own `debugger_attempts` still says no target block was
  captured. Therefore the populated values have no independent Windows runtime
  provenance.

Audited archives:

- `/Volumes/onmk/olm_pr/old/20260630_175942__olmblur_case0006_helper_prestore_witness_20260630_return_windows.zip`
- `/Volumes/onmk/olm_pr/old/20260701_131138__olmblur_case0006_helper_prestore_witness_20260630_return_windows.zip`

## Corrective action

- `scripts/compare_olmblur_trace.py` now requires an explicit retained Windows
  target provenance before consuming `windows_*` values.
- Unbound numeric fields produce
  `case0006-windows-values-unverified` /
  `unverified-windows-values` rather than `same-word-store`.
- `scripts/analyze_pending_runtime_trace_packages.py` explicitly keeps this
  request as `invalid_unverified_values` instead of `answered`.
- The current comparison was regenerated and no longer contains the false
  narrow Windows analysis.

## Remaining proof

Current Mac AE output is repeatable and remains `max_diff=2` against canonical
16bpc references. The missing evidence is still a true Windows AEX or locally
emulated AEX pre-store/store chain with address and output-world ownership
bound to the target pixels. No OLMBlur source change is justified yet.
