# OLM plugin orchestration snapshot 2026-07-15

This snapshot records the current parallel review result and the immediate
send/analysis queue. It is not a completion claim; `AE exact` remains the only
completion status.

## Windows exchange

Canonical next resend:

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
- The first return was `exact_bind_failure` because
  `ae_result_case_0001.json` was absent. It is not proof and does not satisfy
  this request. Resend the same canonical artifact only after the exchange
  folder is available and empty.

## Prepared behind the active request

These artifacts are ready locally but are not copied over the active NAS
request. They remain evidence requests, not compatibility results.

| Order | Plug-in / lane | Sendable artifact | SHA-256 | Acceptance boundary |
| ---: | --- | --- | --- | --- |
| 1 | `OLMDirectionalBlur` row755 | `refs/runtime_trace_packages/windows_witness_olmdirectionalblur_row755_20260713.zip` | `13aa1658788e7e114866b7a8f5718bef1dbbca857b6ef97b86851227e49c94db` | Production `row_end=2176`, stride `2206`, and same-run destination/denominator/alpha typed state. |
| 2 | `OLMSmoother2` case_0012 | `refs/runtime_trace_packages/windows_witness_olmsmoother2_case0012_20260713.zip` | `59d9c26d1b165f4fb3de7f1c420ad980c92fedcda2a3c64a880eadfcaac6892b` | Seven cce0 config bytes, pointer-bound c280 fixed scale, class/append stages, and writer corroboration at `(91,841)`. |
| 3 | `OLMRadialBlur` case_0009 | `refs/runtime_trace_packages/windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.zip` | `4ca37375d603399bebb3b4143b9fbedcc52a075e6a83e909b220bf766b53d92f` | Full-frame `(7,0)/(8,0)/(24,0)` with 66/66 typed fields, live cell addresses, queue/export binding, and same-run export bytes. |
| 4 | `OLMKiraKira` Mode 3 | `refs/runtime_trace_packages/olm_runtime_trace_olmkirakira_mode3_live_gaussian_20260713.zip` | `4124c54a390b92edbd38869448be53c52fff8b87e88c652140cea7edea434aa3` | Hash-pinned 84-byte, 21-word little-endian float32 Gaussian return from one bound run. |
| 5 | `OLMColorKey` + `OLMToonDilate` 32bpc control | `refs/runtime_trace_packages/olm_windows_colorkey_toondilate_32bpc_control_20260715.zip` | `21b9a111ea3875e76899567fa6225372db2f9f18d3e6f533a61d0da09fa0d972` | Same-comp no-effect/effect-on FLOAT EXR controls with Software/color/template/input/AEX identity. ColorKey's nine historical Windows pairs are already audited; this package remains the canonical explicit-ID control request. |
| 6 | `OLMSmoother v1` 16/32bpc | `handoffs/windows_batch/olmsmoother_v1_bitdepth_16_32bpc_software_20260715.zip` | `f674a72954345a4e1732b15acddcb165ac4b04073344b033d8e799c899af2136` | Canonical readback is limited to the three v1 parameters; 16bpc is exact-eligible after return and 32bpc remains FLOAT EXR probe-only. |

## Prepared Mac validation lanes

These contracts use the imported Windows FLOAT EXRs as references but do not
become `AE exact` until a fresh Mac AE effect/control pair passes every
identity and raw-sample gate. They are deliberately outside the Windows
reference queue.

| Plug-in / lane | Contract | Local execution state |
| --- | --- | --- |
| `OLMBlur` 16bpc current-plugin revalidation | `refs/conformance/olmblur_16bpc_current_plugin_revalidation_20260715.md` | Current-plugin AE revalidation is `5/7 exact`; plugin SHA-256 is `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`. `case_0006` is exact and its output SHA-256 is `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`. Cases `0003`/`0004` remain unlocalized before the final exported word; current evidence does not justify changing the writer or global rounding. |
| `OLMBlur` 32bpc | `refs/mac_validation_requests/olmblur_32bpc_mac_validation_20260715.json` | Fail-closed runner/reporter smoke ready; Mac AE render pending. |
| `OLMColorKey` 32bpc | `refs/mac_validation_requests/olmcolorkey_32bpc_mac_validation_20260715.json` | Historical Windows aliases are manifest-, artifact-, AE-, color-, and output-template-pinned; Mac AE render pending. |
| `OLMToonDilate` 32bpc | `refs/conformance/olmtoondilate_mac_depth_contract_20260715.json` | Isolated typed-procedural runner/comparator smoke ready; Mac AE render pending. |
| `OLMDistanceGradation` 32bpc | `refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json` | Fail-closed runner/reporter smoke ready; independent from the active 8bpc typed-boundary resend. |
| `OLMSmoother2` no-key 32bpc | `refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json` | Package/runner/reporter smoke ready; makes no legacy/key claim. |
| `OLMDirectionalBlur` 32bpc | `refs/mac_validation_requests/olmdirectionalblur_32bpc_mac_validation_20260715.json` | Single-case FLOAT runner/reporter smoke ready; mixed advanced features remain separate from the 8bpc row755 proof. |
| `OLMRadialBlur` 32bpc | `refs/mac_validation_requests/olmradialblur_32bpc_mac_validation_20260715.json` | Minimal Zoom and Rotation runners/reporters ready; 8bpc case_0009 downstream cells remain a separate binary-proof lane. |
| `OLMKiraKira` Mode 2 32bpc | `refs/mac_validation_requests/olmkirakira_mode2_32bpc_mac_validation_20260715.json` | Fully pinned 42-property Mode 2 runner/reporter ready; unresolved Mode 3 Gaussian is excluded. |

## Parallel plugin lanes

| Plug-in | Current lane | Next useful action | Do not do |
| --- | --- | --- | --- |
| `OLMBlur` 16bpc | `current-plugin-revalidated` | Preserve the `5/7` exact result and capture same-run pre-store float bits, writer input, stored PF16 word, and exported word for cases `0003` and `0004`; case `0006` provenance/output is closed. | Change the worker, helper, writer, or global rounding from PNG/portable replay alone, or treat the old bundle language as current-plugin evidence. |
| `OLMDistanceGradation` | `binary-proof` | The 2026-07-15 exact-coordinate retry completed all three AE cases and armed PF8/PF32, but `(397,281)` produced zero PF8 target hits and the return omitted the AEX hash. Replace that condition with one hash-pinned PF8 coordinate-liveness census before selecting a typed point. | Repeat depth-control or the zero-hit exact-coordinate condition, tune from PNGs, or use CLI/AEX fixture output as Windows AE truth. |
| `OLMDirectionalBlur` | `binary-proof` | After the active DG return, run the corrected row755 package. It accepts production `row_end=2176` while requiring destination/denominator/alpha typed state. | Treat the 2026-07-14 row755 `exact_bind_failure` as algorithm evidence or broaden to diagonal/variation modes. |
| `OLMRadialBlur` | `binary-proof` | Run the hardened semantic full-frame witness at `(7,0)`, `(8,0)`, `(24,0)` with live cell addresses and same-run export binding. | Use the old `32x32`, quality-step-90 probe as full-frame truth or tune visuals. |
| `OLMKiraKira` | `binary-proof` | Run the hardened v5 live Gaussian package; accept only the hash-pinned 21 little-endian float32 coefficients. | Promote the Unicorn uniform-kernel result or sidecar OpenCV-only result to production truth. |
| `OLMSmoother2 legacy/key/gamma` | `binary-proof` | Run the hardened `(91,841)` live config/class-plane package; all class/config/gamma/append/writer stages must bind in one run. | Request final writer bytes again or change global fallback/alpha/index/gamma from synthetic replay. |
| `OLMColorKey` | `bitdepth-expand` | Preserve 8/16bpc exact slices; run the nine-case Mac 32bpc FLOAT EXR effect/control validation and compare raw samples with the audited Windows pairs. | Compensate for host input conversion in plug-in code or claim 32bpc exact before the Mac control/effect pair is bound. |
| `OLMToonDilate` | `bitdepth-expand` | Preserve exact 8/16bpc slices; run the isolated Mac typed-procedural FLOAT EXR pair and compare it with the matching Windows contract. | Reopen the 8bpc dilation algorithm or treat Mac no-op parity as cross-host exact. |
| `ColorKeep` | `parked` | Keep as support/helper unless a real Windows Software reference is requested. | Treat synthetic helper output as OLM compatibility. |
| `OLMSmoother v1` | `parked` | Keep the new 16/32bpc package behind the hard lanes; 16bpc is a real expansion request and 32bpc is explicitly probe-only. | Mix v1/v2 behavior or promote the 32bpc pass-through branch without typed AE evidence. |

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
- `python3 refs/scripts/smoke_windows_witness_olmdirectionalblur_row755_20260713.py`
  passed with 22 positive/negative witness checks.
- `python3 refs/scripts/smoke_windows_witness_olmradialblur_case0009_fullframe_postnorm_typed_common_core_20260713.py`
  passed after full-frame cell/export hardening.
- `python3 refs/scripts/smoke_windows_witness_olmsmoother2_case0012_20260713.py`
  passed after class/config/gamma fail-closed hardening.
- `python3 refs/scripts/smoke_package_olmkirakira_mode3_live_gaussian_20260713.py`
  and `python3 refs/scripts/smoke_classify_olmkirakira_mode3_live_gaussian_return.py`
  passed after little-endian byte-hash binding.
- `python3 refs/scripts/smoke_package_windows_colorkey_toondilate_32bpc_control_20260715.py`
  passed.
- `python3 refs/scripts/smoke_analyze_olmblur_residual_locus_20260715.py`
  passed with verdict `separate-lanes`.
- `python3 refs/scripts/smoke_package_olmsmoother_v1_bitdepth_request_20260715.py`
  passed.
- `python3 -m unittest refs.scripts.test_check_reference_request_status`
  passed all 13 historical-alias drift tests.
- `python3 refs/scripts/smoke_olmblur_worker16_nonlegacy.py` passed both
  actual-AEX complete-worker fixtures after adding the optional pre-store
  observation API.
- `python3 refs/scripts/smoke_olmblur_16bpc_current_plugin_revalidation_20260715.py`
  passed: current-plugin AE result `5/7 exact`, case0006 SHA pinned, and
  cases0003/0004 recorded as the two unresolved residuals.
- `python3 refs/scripts/smoke_analyze_olmblur_residual_locus_20260715.py`
  passed both the historical `separate-lanes` branch and the identity-bound
  current-plugin `ae-exact-observed` branch.
- `xcodebuild -project mac/OLMBlur/Mac/OLMBlur.xcodeproj -configuration Debug -quiet`
  succeeded; the instrumented binary SHA-256 is
  `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
- AE PNG stable polling was validated for case0003: `stable waited_ms=41240`
  and `size_bytes=6156`.
- `tools/emulation/.venv-cv455/bin/python refs/scripts/smoke_kirakira_gaussian.py`
  passed. The local pinned-AEX Unicorn scaffold returns 63/63 words matching
  the portable uniform replay, but all 63 differ from OpenCV 4.5.5; this is an
  emulation-path witness only and does not replace the live Windows request.
- `python3 refs/scripts/smoke_smoother2_fullchain_diff.py` passed the local
  actual-AEX/portable matrix for classifier `0x69` append/suppress and `0xff`;
  classifier `0x40` remains an explicit local dispatch gap.
- `python3 tools/emulation/run_radialblur_case0009_b150_differential.py`
  passed: the actual AEX B150 worker changes its owned bounded RGBA/scalar
  slice while the paired no-op detour does not. This remains reduced-geometry
  binary evidence, not full-frame case0009 truth.
- The six common-core Windows witness renderers were regenerated with bounded
  PNG completion polling. Their focused witness smokes and all 22 common-core
  unit tests pass; the case0026 source-support copy was also synchronized.
- `olmblur_case0006_same_run_internal_20260713` is retired as `superseded`,
  not answered, after the identity-bound current-plugin AE-exact result.
- The no-AE Mac validation smokes for OLMBlur case_0006,
  DirectionalBlur 32bpc, RadialBlur 32bpc, KiraKira Mode 2 32bpc, and
  Smoother2 no-key 32bpc passed.
- The 96-check nonhard suite passed 95 checks and exposed one stale queue
  priority: project staging expected DirectionalBlur while the authoritative
  ledger and `print_next_olm_action.py` selected the DistanceGradation resend.
  After assigning that DG profile priority 1, regenerating the queue and
  staging, `smoke_windows_send_first_staging.py` passes with DG as queue head.

The earlier `smoke_all_algorithm_clis.py --profile nonhard` run started before
those smoke repairs and therefore reported the same three launcher-smoke
failures plus the ToonDilate generator failure. The individual reruns above
are the authoritative post-fix checks for this change.
