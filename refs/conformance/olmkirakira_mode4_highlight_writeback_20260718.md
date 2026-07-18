# OLMKiraKira Mode4 Highlight writeback and normalization (2026-07-18)

Status: **PASS_MODE4_BOUNDED_WRITEBACK_NORMALIZATION**
AE exact: **false**
Production edit: **none**

## Bounded result

The Mac-only actual-AEX witness reaches the shared Mode4 tail at `0x181150f3d`
after the recurrence and produces a changed `CV_32FC1` destination buffer.
That proves scalar-buffer output writeback for this bounded synthetic witness.

Static decomp/asm also bounds the caller-side semantics: Mode4 makes three
`FUN_181280bc0` passes, squares the scalar gain twice, and the shared five-layer
combiner normalizes RGB by accumulated alpha and uses source-over alpha union.

## Limits

This does not prove the full AE-host caller, Highlight Color parameter binding,
final PF pixel encoding, Windows behavior, or AE-exact equivalence. No
production source or AEX bytes were changed.

Verification: `python3 tools/emulation/audit_olmkirakira_mode4_highlight_writeback_20260718.py`
