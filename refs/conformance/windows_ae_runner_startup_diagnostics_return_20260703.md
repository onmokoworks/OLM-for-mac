# Windows AE Runner Startup Diagnostics Return

Date: `2026-07-03`

Source return:

- `refs/returns/windows/20260703_runner_startup_diag/olm_runtime_trace_windows_ae_runner_startup_diagnostics_20260703_return_windows.zip`

## Result

The previous startup-stall theory is now retired.

For both:

- `db_existing_case_0001_software_pair` (`OLMDirectionalBlur`)
- `legacy_case_0004_current_aex` (`OLMSmoother2`)

the Windows return proves:

1. AE launched
2. startup scripts initialized
3. JSX runner invoked
4. request dir resolved without fallback
5. request JSON enumerated and loaded
6. case id resolved
7. dispatch started
8. target plugin module load reached

The first non-advancing point is now after:

- `about_to_add_effect ...`
- target module load

and before:

- `effect added ...`
- parameter application
- `saveFrameToPng returned`
- `run_complete.json`

## Important facts

- `fallback_used=false` for both cases
- `ae_runner_log_exists=true` for both cases
- `run_complete_exists=false` for both cases
- last JSX breadcrumb is the pre-`addProperty` line
- the return explicitly classifies the stall as post-module-load

## Interpretation

The active blocker moved from `binary-proof` back into `host-fix` territory for
these two exact-case runtime lanes.

The next Windows ask should classify the `addProperty(...)` boundary itself:

- returned success
- threw a catchable error
- opened a hidden/modal dialog
- never returned because native/plugin init held control
