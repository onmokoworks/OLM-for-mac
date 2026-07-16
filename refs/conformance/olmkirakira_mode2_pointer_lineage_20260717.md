# OLMKiraKira Mode2 pointer-lineage harness (2026-07-17)

Status: **BLOCKED, fail-closed**
AE exact: **false**
Scope: Mac-only Unicorn execution of the checked-in Windows PE AEX.

The harness executes `FUN_18114ffd0` through its direct actual-AEX boundary,
records the Mode2 float output and pre-clamp `XMM0..XMM3`/`RDI` state, then
executes the actual PF32 writer `FUN_181230c20` in the same Unicorn instance.
At the writer entry it records `XMM0..XMM3`, `[RSP+0x28]`, and destination
bytes before and after mutation.

The PF32 call is explicitly control-only. The pinned Mode2 target returns
after its float stores and contains no call to any typed writer. Therefore the
Python-mediated transfer of four float values is not natural AEX pointer/data
lineage and is rejected by the lineage gate. No proof is promoted.

Anchors checked: dispatch `FUN_18114f4a0`, callsite `0x18114fc28`, output
checkpoint `0x181150022`, pre-clamp `0x181150112`, PF32 callsites
`0x18114e5d7`/`0x18114e739`, and writer `FUN_181230c20`.

Exact report: `refs/conformance/olmkirakira_mode2_pointer_lineage_20260717.json`.
