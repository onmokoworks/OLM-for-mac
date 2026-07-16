# OLMToonDilate PF8 Worker Tie-Break - 2026-07-17

## Result

- Status: **PASS_PF8_WORKER_TIE_BREAK**
- AEX: `aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex`
- AEX SHA-256: `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`
- Worker ABI: `(context, unused, source_world, destination_world, radius_ptr)`
- Worker/helper: `0x1801a6150` / `0x1801ac880`
- Fixture: PF8 3x1, radius 1, rowbytes 16 with a four-byte `0xA5` sentinel.
- Paired inputs are `[A,T,B]` and `[B,T,A]`; output is read immediately after native worker return.

## FACT

- Instrumentation records the tie branch, helper entry, copy call `0x1801A64DD`, and resume `0x1801A64E2`.
- The decisive bounded observation is center output equal to x0 in both paired runs.
- Hash mismatch or execution failure remains `BLOCKED_FAIL_CLOSED` and exits nonzero.

## Limits

- This does not claim general distance semantics, host/AE exactness, all tie orders, or case0003 closure.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/probe_olmtoondilate_pf8_tie_break_20260717.py
```

