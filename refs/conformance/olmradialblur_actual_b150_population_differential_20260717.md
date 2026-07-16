# OLMRadialBlur actual-AEX B150 population differential (2026-07-17)

- Status: `blocked`
- Classification: `blocked-gate-failure`
- Scope: Mac Unicorn only; actual polar prefill, first B150 callsite, one B150 entry/return; no AE, Windows, or production claim.
- Target cells: `(1047,1095)`, `(1047,1096)`, `(1048,1095)`, `(1048,1096)`; controls `(1047,1094)`, `(1048,1097)`.

- Actual prefill hits: `4`; callsite hits: `1`; B150 returns: `1`.
- Before/after raw float32 cells and plane hashes are preserved in JSON.
