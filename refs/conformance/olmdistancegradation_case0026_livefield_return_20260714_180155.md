# OLMDistanceGradation case0026 16bpc livefield return

Date: 2026-07-14

## Verdict

`exact_bind_failure` at `cdb_capture`. This return contains host-launch and
diagnostic evidence only. It is not evidence about the OLMDistanceGradation
algorithm and must not change its correctness status.

## Return

- Request: `windows_witness_olmdistancegradation_case0026_16bpc_livefield_20260713`
- Archive: `refs/windows_returns/20260714/20260714_180155__RETURN__OLMDISTANCEGRADATION_CASE0026_16BPC_LIVEFIELD.zip`
- SHA-256: `9fd8f46e54b6e25a521283bab85203ef657cc8b82cea784ebf53670b5714785f`
- Status: `exact_bind_failure`
- Stage: `cdb_capture`
- Missing field: `cdb_exit`

## Facts

- The returned manifest contains `artifacts=[]`.
- The return contains `ready_*.marker`, `continue_*.marker`, CDB traces,
  launcher diagnostics, and `queue_bootstrap.log`.
- No typed `FIELD`, `SOURCE`, `COMPOSE`, `STORE`, or `RETURN` record was
  accepted.
- No render or exported witness artifact was returned.

## Decision

This confirms that the launcher reached the ready phase but did not produce a
complete CDB capture. Do not infer livefield values, source ownership, store
behavior, or Mac-side algorithm changes from this archive. The next request
must preserve and report the CDB exit/termination state before any plugin
interpretation is attempted.
