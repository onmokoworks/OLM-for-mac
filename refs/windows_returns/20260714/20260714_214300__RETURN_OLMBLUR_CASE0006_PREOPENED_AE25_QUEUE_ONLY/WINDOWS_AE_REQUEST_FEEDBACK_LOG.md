# Windows AE request feedback log

This file is intended to travel with the Windows return artifacts. It records runner issues seen on the Windows host and concrete suggestions for the next request package.

## Host defaults that worked best

- After Effects: `C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe`
- OLM plug-ins: `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM`
- OLMBlur AEX: `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMBlur.aex`
- AE 2025 normal launch can stay alive as a single interactive process.

## Recurring runner issues observed

### AE launch / JSX dispatch

- `AfterFX.exe -m` is unreliable on this host. It often exits before queue JSX can run.
- `AfterFX.exe -r <jsx>` is not reliably enough by itself. In several attempts, AE did not emit the expected ready marker.
- Pre-opened AE 2025 queue-only mode improved process stability, but dispatch still failed before `ae_ready.marker`.

### Scheduled task details

- Avoid scheduled task names beginning with a double backslash such as `\\OLM...`.
- Use either a plain task name or a single leading backslash such as `\OLM...`.
- `schtasks /Delete` for a non-existent task can surface as a PowerShell native command error and prevent RETURN generation if not isolated.
- Wrap cleanup deletes so they never block `RETURN_*.json` / `RETURN_*.zip`.

### Failure artifact behavior

- Every runner should always produce a deterministic `RETURN_*.zip`, even when the failure happens in preflight, scheduled-task creation, queue dispatch, or cleanup.
- In a few packages, the runner produced JSON only on success or was interrupted by cleanup errors before packaging.
- If CDB is never reached, the return artifact should still include launch/dispatch diagnostics.

## Minimum failure diagnostics requested

Please include these in every failed return package:

- Exact AE launch command or scheduled task command.
- Exact JSX dispatch command or scheduled task command.
- Absolute queue JSX path.
- Observed `AfterFX.exe` process list: PID, executable path, command line, session ID.
- Marker paths and existence booleans.
- Wrapper stdout/stderr for launch and dispatch.
- AE queue log, AE result JSON, and AE log if any were created.
- CDB script/stdout/stderr/trace if CDB was reached.
- Whether the runner modified or expected environment variables.

## Current OLMBlur case_0006 status

Latest attempted package:

- `20260714_211500__REQUEST__OLMBLUR_CASE0006_PREOPENED_AE25_QUEUE_ONLY.zip`

Observed result:

- AE 2025 was opened normally and remained as exactly one process.
- Runner dispatch did not produce `ae_ready.marker`.
- Status returned: `exact_bind_failure`
- Stage: `readiness`
- Missing field: `ae_ready.marker`

Local runner patch needed for return generation:

- The runner initially failed while deleting a non-existent scheduled task in `Finish()`.
- Local copy was patched so `schtasks /Delete` cleanup cannot prevent RETURN JSON generation.

## Suggested next retry shape

The most useful next package would be a queue-dispatch experiment that focuses only on proving JSX reaches the already-open AE process.

Suggested contract:

1. User/Codex opens AE 2025 normally.
2. Runner verifies exactly one AE 2025 process.
3. Runner dispatches a tiny diagnostic JSX first.
4. Tiny JSX writes a marker and a log containing `app.version`, current project path, and timestamp.
5. Only after that succeeds, dispatch the OLMBlur queue JSX.
6. If tiny JSX fails, return immediately with launch/dispatch diagnostics.

This separates "Can Windows reliably inject JSX into pre-opened AE?" from "Can OLMBlur witness capture run?".

## Naming suggestion

For future requests, include the dispatch strategy in the zip name, for example:

- `REQUEST__OLMBLUR_CASE0006_PREOPENED_AE25_TINY_JSX_PROBE.zip`
- `REQUEST__OLMBLUR_CASE0006_PREOPENED_AE25_QUEUE_AFTER_PROBE.zip`

## Next operator procedure

The next retry should be exercised on the Windows desktop, because the current
unknown is JSX delivery into an already-open interactive After Effects process.
SSH/session-0 execution is not a valid substitute for this check.

1. Open exactly one copy of After Effects 2025 normally and leave it open.
2. Extract the request ZIP and run the PowerShell runner from that interactive
   Windows desktop session as the normal logged-in user.
3. Confirm that the tiny JSX probe creates `ae_dispatch_probe.marker` and
   `AE_DISPATCH_PROBE.log` in the run work directory.
4. Only when the probe succeeds, inspect the OLMBlur queue result and CDB trace.

Interpretation:

- Probe marker missing: classify as JSX dispatch/host failure; do not tune the
  OLMBlur algorithm and do not claim a Windows witness.
- Probe marker present but `ae_ready.marker` missing: classify as queue JSX or
  AE project setup failure.
- Probe and queue markers present but CDB fields missing: classify as debugger
  binding/hook failure.
- CDB fields and same-run PNG present: only then pass the return package to the
  OLMBlur classifier.
