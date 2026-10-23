# F48: fuzz framework — os.killpg PermissionError during shrink timeout cleanup

## Facts
In S01, DistanceGradation seed105 cases 50 and 123 lost their result rows: shrinking raised
`PermissionError: [Errno 1] Operation not permitted` at `os.killpg` in `tools/fuzz/core.py:35`; the campaign exited 2.
See `orchestra/reports/S01-wide-mismatch-sweep/retry-procedure.md` and the saved traces.

## Do
1. Reproduce (likely the process group already exited / was reaped, or the child is in a different group).
2. Make timeout cleanup robust: treat ProcessLookupError/PermissionError for an already-gone group as done, verify no orphan stays (kill the pid directly as a fallback), and never let cleanup errors drop a case row — record the case as unresolved with the reason instead.
3. Unit test for the cleanup path. Re-run DG seed 105 n300 and show it exits 0 with all 300 rows.

## Rules
Framework-only change; no plugin code. Do not change result classification of any completed case.
