# ColorKeep current installed count9 replay (2026-08-13)

Status: `PASS_COLORKEEP_CURRENT_INSTALLED_COUNT9_PUBLIC5_REJECT136_AE_FREE`

- Both Universal slices, Classic PF8/PF16 and Smart PF8/PF16/PF32: 5/5 exact per slice.
- Windows exported Smart owner hashes are live-checked.
- Canonical rejects: 136/136 precommit-atomic per slice.
- x86_64 runs under Rosetta; AE was not launched.

Boundary: Both current installed Universal slices of ColorKeep reproduce the pinned count9 public contract at Classic PF8/PF16 and Smart PF8/PF16/PF32, and all 136 canonical reject controls remain precommit-atomic on each slice. The x86_64 route runs under Rosetta. The output relation is also live-checked against the pinned Windows exported Smart owner hashes. This is AE-free dlopen evidence limited to the exact 4x3 source, palette, parameters and layout.
