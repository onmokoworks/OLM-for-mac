# Windows AE Runner Startup Diagnostics

Date: `2026-07-03`

This request is not a plugin-local witness trace.

Its only purpose is to prove how far the Windows AE runtime-trace harness gets
before the request dispatch path stalls.

## Scope

Use the same exact-case request sets that recently stalled:

- `smoother2_legacy_full_current_aex_recapture_20260621`
  - case: `legacy_case_0004_current_aex`
- `directionalblur_context_scale_20260606`
  - case: `db_existing_case_0001_software_pair`

Do not start with plugin-local witness breakpoints.
Do not treat module-load absence as the primary mystery anymore.

The primary mystery is now:

- did the AE runner script start?
- did it discover the request directory?
- did it enumerate the request JSON?
- did it begin dispatching the requested case?

## Required stage ledger

Return one ordered startup ledger showing whether each stage was reached:

1. AE launched
2. startup scripts initialized
3. JSX runner script invoked
4. `OLM_AE_REQUEST_DIR` or equivalent request path resolved
5. request JSON enumerated / loaded
6. requested case id resolved
7. dispatch into render path started
8. target plugin module load reached

For each stage, return one of:

- `reached`
- `not reached`
- `unknown`

and attach the best concrete evidence line.

## Minimum evidence to return

- exact command / launcher invocation used
- exact request directory path handed to the runner
- exact case id handed to the runner
- whether `ae_runner_log.txt` creation was attempted
- whether `run_complete.json` creation was attempted
- whether the request JSON file was opened or enumerated
- whether the request count / case count was computed
- exact last emitted log line before timeout
- any runner stdout/stderr tail
- if a fallback/default request directory is used, return that path explicitly

## Useful implementation hints

- Instrument the runner before plugin load, not after.
- If the wrapper script can emit a tiny `RUNNER_STAGE=...` breadcrumb file, that
  is ideal.
- If environment variables are involved, log their final values as seen by the
  JSX side, not only the PowerShell/Python side.

## Non-answers

These do not count as progress:

- repeating only AE startup banners
- repeating only `sxe ld:<module>` setup
- another timeout without runner-stage evidence
- another plugin-local breakpoint attempt before request dispatch is proven
