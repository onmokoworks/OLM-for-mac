# Known Host Limitation

The supplied `WINDOWS_AE_REQUEST_FEEDBACK_LOG.md` reports that on the AE2025
host this case exits even when CDB is attach-only and the debugger command is
only `g`; a no-CDB control succeeds. This request is therefore packaging-ready
but is not a claim of practical executability on that host.

The common runner preserves launcher, CDB, AfterFX, process, and trace
diagnostics. A missing run, missing event, or mixed identity is an
`exact_bind_failure`. Packaging and smoke success do not promote the request
to a Windows observation, and no final-writer bytes or PNG/export is accepted.
