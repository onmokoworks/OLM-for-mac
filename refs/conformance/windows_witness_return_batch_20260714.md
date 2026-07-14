# Windows witness return batch: common launcher failure

Date: 2026-07-14

## Verdict

This batch is `answered_partial` at the transport level but contains no plugin
witness. All four returns fail closed at `cdb_launch` with the same missing
field: `cdb_bootstrap_exit`.

The diagnostics do show that AfterFX.exe was launched and observed by process
enumeration. They do not show the CDB bootstrap marker, queue bootstrap marker,
plugin load claim, typed capture, or render artifact. These returns must not
change any plugin correctness status.

## Returns

| Plugin/request | Return SHA-256 | Status | Evidence missing |
| --- | --- | --- | --- |
| OLMBlur case0006 | `9ab9ec0ca3ce0c75e8ab294af21fea5921f0dcaae0bec10d42777abe51425bee` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |
| OLMDirectionalBlur row755 | `15565688cf7aedc386ec49f867e94e40092290376021f0af8e1f2ca7ac0e62b5` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |
| OLMDistanceGradation case0026 | `2bf25d4e1f42eb7da821dcfa82085d7dd48d562485298ec0c87b07e9b790472c` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |
| OLMSmoother2 case0012 | `b0bdd40f04c50079d76a5b6de8c8e285da2fea40d89f1f67baca130532bb72a3` | `exact_bind_failure` | `cdb_bootstrap_exit`, typed witness |

## Observed common facts

- The launcher uses CDB with `-o -pd -g -G -cf boot.cdb`.
- The observed AfterFX command line is `AfterFX.exe -r queue.jsx`.
- `bootstrap_host_image_marker_observed=false`.
- `queue_bootstrap_marker_observed=false`.

## Direct launcher gate retry

The direct-AfterFX gate was executed on Windows, but it failed before CDB
bootstrap because an existing After Effects process was still running:

- Return: `RETURN_OLMDISTANCEGRADATION_CASE0026_16BPC_LIVEFIELD_direct_gate_20260714.zip`
- SHA-256: `d362f42485ba88d4ca98c5f9454ba3b0c392d25f1ca8ab20a15517caa1876356`
- Status: `exact_bind_failure`
- Stage: `desktop_launch`
- Missing field: `fresh_AfterFX_process`
- `bootstrap_host_image_marker_observed=false`
- `queue_bootstrap_marker_observed=false`

This is a host precondition failure, not plugin or algorithm evidence. The
request and return were archived together under
`/Volumes/onmk/olm_pr/old/20260714_002900__intake_direct_gate_afterfx_already_running/`.
The gate must be retried only after After Effects is fully closed.

## Direct launcher gate retry 2

The retry started CDB, but no uniquely observable desktop `AfterFX.exe` was
created. The returned bootstrap trace contains only the CDB log-open line; it
does not contain either explicit initial-break marker.

- Return SHA-256: `d256616828358291a69258ddcb2449b8e53c80cac56081415eef6588541211bc`
- Status: `exact_bind_failure`
- Stage: `cdb_launch`
- Missing fields: `one_desktop_AfterFX_process`, `cdb_bootstrap`
- `bootstrap_host_image_marker_observed=false`
- `queue_bootstrap_marker_observed=false`
- Typed artifacts: none

This is still a launcher/host failure, not plugin evidence. Do not resend the
full witness batch until the direct launch can produce a visible AfterFX
process and both bootstrap markers.

## Root cause found in CDB argument contract

The Windows machine's `cdb.exe -?` output shows that `--` is not a generic
argument separator. It is an alias for `-G -g -o -p -1 -d -pd`; in particular,
`-g` suppresses the initial debuggee breakpoint. The direct launcher therefore
contradicted its own initial-break gate while still carrying `--` in the
argument vector. The launcher and its contract smokes now omit `--` entirely,
leaving the executable path as the first positional CDB target. Local witness
smoke and all 19 unit tests pass after this change. No Windows algorithm claim
is made until a fresh gate return contains both initial-break markers.
- No returned artifact was produced.
- The same failure appears across four different plugins, so this batch cannot
  distinguish plugin behavior.

## Decision

Reopen the common Windows launcher gate. Do not send additional plugin witness
requests through this launcher until a minimal real-Windows gate observes both
the CDB bootstrap exit and the queue binding marker. The next fix must preserve
the archived CDB output and `boot.log` so a failed gate is diagnosable.

## Replacement gate sent

The launcher was changed locally to start `AfterFX.exe -r <queue>` directly
under CDB, leave the initial breakpoint enabled, emit an explicit initial-break
marker, and detach with `qd`. The old `cmd.exe` child wrapper and
`ld:AfterFX.exe` filter are no longer used.

The minimal gate package sent to Windows is
`windows_witness_launcher_gate_direct_afterfx_20260714.zip` with SHA-256
`703253f6507e68654a1984884ff81e3b40115cc6f455989b0ccc11ddf84c61d1`.
It reuses only the DG case0026 package as a launch vehicle; no DG algorithm
claim is made from this gate.

The subsequent Windows retry was stale: its `afterfx_process_diagnostics.json`
still records the old `--` argument. It is archived as host-tooling noise and
must not be used to judge the fix. The no-double-dash package was copied to
the explicit Windows path
`C:\\olm_short\\incoming_20260714_direct_dg_case0026_no_double_dash\\REQUEST.zip`;
the extracted launcher was independently checked to contain no `--` in
`$launchArgumentValues`.

## Current `-m -r` retry

The current package was then executed after terminating the existing
AfterFX/CDB processes. This run did reach both CDB initial-break markers, but
it still failed before queue execution:

- Return SHA-256: `64c51c3a30aa7e7c1cd99fbf2b5d31bcb7bcf466ba6921464a52526d6adbe848`
- Status: `exact_bind_failure`
- Stage: `jsx_launch`
- Missing field: `queue_bootstrap.log`
- `bootstrap_host_image_marker_observed=true`
- `queue_bootstrap_marker_observed=false`
- Typed records: `0`

This confirms the CDB initial-break portion of the launcher fix, but does not
validate queue dispatch or any OLM plugin behavior. The next debugging target
is AfterFX queue execution and process binding, not the Mac algorithm.

## One-click six-job batch (2026-07-14 16:06 JST)

This is a separate batch from the older launcher-failure returns above. The
outer return was archived at
`refs/windows_returns/20260714/20260714_160633__RETURN__windows_witness_batch_20260714.zip`
with SHA-256
`8e38b07439bad2e045eb881473683e2f2a6a6c8beea41f6f225cdc2e4615c825`.
The transport result is `partial_success`; all six job return archives were
created, but no job may be promoted to `AE exact` from this batch.

### Facts

- `OLMKiraKira` job006 reached `KK_WRAPPER`, `KK_CREATE`,
  `KK_KERNEL_ENTRY`, and `KK_KERNEL_RETURN` in one run.
- The live kernel entry recorded `ecx=21`, `xmm1=2.5`, and `r8=5`.
- The return recorded `word_count=21`, `raw_bytes=84`, and `element=float32`.
- The actual 84-byte coefficient artifact was not present in the returned ZIP;
  therefore the Gaussian coefficient values remain unconfirmed.
- OLMBlur case0006, DG 8bpc typed boundary, Smoother2 case0012, and DG case0026
  each ended with `typed_hit_count=0` and `cdb_exited_without_typed_hit`.
- DirectionalBlur row755 failed in the AE runner before rendering because its
  input PNG path was not valid after batch extraction.
- The batch launcher reported no remaining AfterFX/CDB processes after cleanup;
  a late orphaned AfterFX tree was explicitly terminated and checked again.

### Intake decision

The fail-closed batch intake currently rejects this archive because the KiraKira
job's auxiliary `ae_result_*.json` has an empty `request_id` and is included in
`returned_statuses`. This is a witness packaging/intake contract defect, not a
plugin correctness result. Fix the contract and re-run intake before changing
KiraKira source or promoting any status.

## Individual retries after artifact-preservation fix (2026-07-14 17:15 JST)

The local runner was changed to preserve files written beside a CDB short trace
before deleting the temporary `C:\Users\Public\OLMWitness` directory. The
KiraKira CDB template now writes the Gaussian coefficient dump through the
dedicated `ARTIFACT_PATH` placeholder. Local package/compiler/unit smoke passed.

The first Windows retry did not reach the witness:

- Return: `refs/windows_returns/20260714/20260714_1715__RETURN__OLMKIRAKIRA_MODE3__artifact_preservation_retry.zip`
- SHA-256: `dcbd455387d37651554a124f6282921fd3ecd8453ea5797797da59a84204e997`
- Status: `exact_bind_failure`
- Stage: `jsx_launch`
- Missing field: `queue_bootstrap.log`
- `bootstrap_host_image_marker_observed=false`
- `queue_bootstrap_marker_observed=false`
- Typed witness count: `0`
- Returned artifacts: none

This is a Windows AE launcher failure and provides no new KiraKira algorithm
evidence. The artifact-preservation change remains unvalidated on real output;
the next retry must first restore a successful queue bootstrap, then inspect
the returned 84-byte coefficient file.
