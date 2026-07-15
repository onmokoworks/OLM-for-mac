# OLM plugin orchestration snapshot 2026-07-15

This snapshot records the current parallel review result and the immediate
send/analysis queue. It is not a completion claim; `AE exact` remains the only
completion status.

## Windows exchange

Sent to NAS:

- `/Volumes/onmk/olm_pr/new/REQUEST__OLMDISTANCEGRADATION_8BPC_TYPED_BOUNDARY_20260715.zip`
- Source archive:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip`
- SHA-256:
  `8017e17f2010778d032a68d8cb23785395ef5141ce306b2fc90b79e8e5a3deae`

Acceptance rule:

- The return must satisfy
  `scripts/classify_olmdistancegradation_8bpc_typed_boundary_return.py`.
- It must bind all three cases `case_0001`, `case_0015`, `case_0029` in one
  consistent Windows AE run, with hash-pinned DistanceGradation AEX,
  8bpc/Software, typed `FIELD_IN`, `FIELD_OUT`, `COMPOSE_IN`, `COMPOSE_OUT`,
  and `HOST_STORE` observations.

## Parallel plugin lanes

| Plug-in | Current lane | Next useful action | Do not do |
| --- | --- | --- | --- |
| `OLMDistanceGradation` | `binary-proof` | Intake the 8bpc typed-boundary return first; locally, use `tools/emulation/test_dg_compose.py` and existing compose fixtures only to classify known boundary math, not as Windows truth. | Repeat depth-control, tune from PNGs, or use CLI/AEX fixture output as Windows AE truth. |
| `OLMDirectionalBlur` | `binary-proof` | Re-run the row755 witness only after accepting `row_end=2176`, or send the two-point angle-0 single-shot witness for `(494,169)` and `(579,169)` with rowdriver/group/helper coverage. | Treat the 2026-07-14 row755 `exact_bind_failure` as algorithm evidence or broaden to diagonal/variation modes. |
| `OLMRadialBlur` | `binary-proof` | Keep the semantic full-frame witness at `(7,0)`, `(8,0)`, `(24,0)` for Zoom, requiring inverse index, four cell IDs/addresses, accum/denom/valid/final RGBA, bilinear weights, alpha, and export byte. | Use the old `32x32`, quality-step-90 probe as full-frame truth or tune visuals. |
| `OLMKiraKira` | `binary-proof` | Get the v5 live Gaussian return with the hash-pinned 21 little-endian float32 coefficients from the Windows desktop run. | Promote the Unicorn uniform-kernel result or sidecar OpenCV-only result to production truth. |
| `OLMSmoother2 legacy/key/gamma` | `binary-proof` | Capture one live config/class-plane witness for `legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`: class bytes, `e170.c`, c280 config pointer/raw scale, cce0 gamma context, append, and writer corroboration. | Request final writer bytes again or change global fallback/alpha/index/gamma from synthetic replay. |
| `OLMColorKey` | `bitdepth-expand` | Preserve 8/16bpc exact slices; for 32bpc, obtain same-contract Windows no-effect FLOAT EXR with host/template/AEX binding before classifying cross-host residuals. | Compensate for host input conversion in plug-in code or claim PNG-only 32bpc exact. |
| `OLMToonDilate` | `bitdepth-expand` | Preserve exact 8/16bpc slices; use the repaired typed-procedural common-core package only as parser/transport validation until same-contract Windows no-effect FLOAT EXR exists. | Reopen the 8bpc dilation algorithm or treat Mac no-op parity as cross-host exact. |
| `ColorKeep` | `parked` | Keep as support/helper unless a real Windows Software reference is requested. | Treat synthetic helper output as OLM compatibility. |
| `OLMSmoother v1` | `parked` | Leave parked while Smoother2 compatibility remains the stronger lane. | Mix v1/v2 behavior without an explicit policy. |

## Local verification performed

- `python3 refs/scripts/smoke_olmdistancegradation_8bpc_current_aex_typed_boundary_package.py refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip`
  passed.
- `python3 refs/scripts/smoke_windows_witness_olmdistancegradation_8bpc_20260713.py`
  passed after updating the smoke for the common launcher `directQueueLaunch`
  branch.
- `python3 refs/scripts/smoke_windows_witness_olmsmoother2_case0012_20260713.py`
  passed after the same launcher-smoke update.
- `python3 refs/scripts/smoke_windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.py`
  passed after the same launcher-smoke update.
- `python3 refs/scripts/smoke_windows_witness_olmtoondilate_32bpc_typed_procedural_samecomp_20260713.py`
  passed after updating the ToonDilate postprocess hook for the current common
  launcher validation tail.

The earlier `smoke_all_algorithm_clis.py --profile nonhard` run started before
those smoke repairs and therefore reported the same three launcher-smoke
failures plus the ToonDilate generator failure. The individual reruns above
are the authoritative post-fix checks for this change.
