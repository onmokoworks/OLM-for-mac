# OLMDistanceGradation case0026 current `-m -r` return

Date: 2026-07-14

## Verdict

This return is `exact_bind_failure` at `jsx_launch`. It is a launcher/AfterFX
execution failure, not plugin evidence. It must not change the
OLMDistanceGradation correctness status.

## Return

- Request: `windows_witness_olmdistancegradation_case0026_16bpc_livefield_20260713`
- Return: `refs/windows_returns/20260714/20260714_014745__RETURN__dg_case0026_current_m_mode_jsx_launch.zip`
- SHA-256: `64c51c3a30aa7e7c1cd99fbf2b5d31bcb7bcf466ba6921464a52526d6adbe848`
- Windows AE: 2025
- Launch command observed in the returned CDB log: `AfterFX.exe -m -r queue.jsx`

## Evidence

Present:

- `WITNESS_CDB_BOOTSTRAP_ARMED`
- `WITNESS_CDB_AFTERFX_INITIAL_BREAK`
- `afterfx_bootstrap_cdb_trace.txt`
- `afterfx_process_diagnostics.json`
- the launched queue JSX

Missing:

- `queue_bootstrap.log`
- `WITNESS_QUEUE_BOOTSTRAP`
- plugin load marker
- typed `ENTRY/FIELD/SOURCE/RETURN` records
- `same_run_identity`
- render artifact

The returned manifest reports `record_count=0`; therefore no address,
parameter, pixel, or algorithm conclusion can be drawn from this run.

## Decision

The `-m` CDB bootstrap fix is verified only up to the initial breakpoint.
The next Windows action is to diagnose why the launched or retry AfterFX
instance does not execute `queue.jsx`, preserving the queue bootstrap log and
process command lines. Do not resend the full witness batch or tune the Mac
implementation based on this return.
