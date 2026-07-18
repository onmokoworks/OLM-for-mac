# OLMRadialBlur checkpoint and hook audit (2026-07-18)

- Status: `pass_audit_no_existing_entry_checkpoint`
- Scope: read-only serialized-header and source-contract audit.
- Protected PID `59481`: not stopped or signalled.

## Findings

All six existing natural checkpoints are genuine `test_zoom_case0009` AEX-loader
states with direct-core, synthetic-prefill, and worker-detour flags clear. Their
RIPs are `0x18000af57`, `0x18000af50`, `0x18000af04`, `0x18000afd4`,
`0x18000affd`, and `0x18000af9a`; every one is inside `FUN_18000a9d0`.

Checkpoints 1 and 2 are independent roots. Checkpoints 3 through 6 form a
continuation from checkpoint 2. No existing checkpoint is at the genuine caller
callsite `0x180005c90` or worker entry `0x18000a9d0`.

`test_zoom_case0009.py` already supports the correct mechanism: install a
checkpoint hook at `0x180005c90`, save before that instruction executes, and
stop. The next valid run must begin from a genuine natural pre-call state. A
forward resume from progress 6 cannot create an entry checkpoint, and changing
RIP or registers would be synthetic state construction.

## Rejected

- Rewinding a mid-A9D0 checkpoint by editing RIP or registers.
- Direct-core or synthetic-prefill setup.
- Worker detours or no-op substitutions.
- Treating a checkpoint inside A9D0 as an A9D0 entry checkpoint.

The focused test writes the machine-readable companion report
`olmradialblur_checkpoint_hook_audit_20260718.json`.
