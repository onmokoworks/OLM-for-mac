# OLMToonDilate PF16/PF32 Copy Boundary - 2026-07-16

## Result

- Status: **WORKER_COPY_GATE_PASS**
- Execution: checked-in Windows PE AEX under local Unicorn on macOS.
- Scope: worker entry/return and raw bytes immediately around the typed copy helpers.
- No AE-exact or production-fix claim is made.

## PF16

- Worker entry: `0x1801a5a90`
- Copy helper: `0x1801ac8b0`
- Worker outcome: `return`
- Worker return confirmed: `True`
- Deepest address: `return trampoline`
- Helper captures: `1`
- Full-worker semantic gate: `True`
- Gate requires helper source pixel == after-destination pixel byte-for-byte and preserves padding ownership.
- Row padding preserved: `[165, 165, 165, 165]`
- Host PF_COPY callback gate: `True`; resume hook: `0x1801a5b61`
- Helper source/destination both lie in output payload: `True`

## PF32

- Worker entry: `0x1801a6800`
- Copy helper: `0x1801ac8e0`
- Worker outcome: `return`
- Worker return confirmed: `True`
- Deepest address: `return trampoline`
- Helper captures: `1`
- Full-worker semantic gate: `True`
- Gate requires helper source pixel == after-destination pixel byte-for-byte and preserves padding ownership.
- Row padding preserved: `[165, 165, 165, 165]`
- Host PF_COPY callback gate: `True`; resume hook: `not instrumented`
- Helper source/destination both lie in output payload: `True`

## Direct Helper Semantic Gates

- These gates call the actual helper entries directly and are independent of the full-worker suite ABI.

### PF16

- Helper entry: `0x1801ac8b0`
- Helper return confirmed: `True`
- Semantic gate: `True`
- Source pixel: `[0, 64, 192, 93, 64, 31, 160, 15]`
- After-destination pixel: `[0, 64, 192, 93, 64, 31, 160, 15]`
- No internal-stage transformation model is used for classification.
- Padding after destination: `[165, 165, 165, 165]`
- Required: exact copy equality and unchanged sentinel padding.

### PF32

- Helper entry: `0x1801ac8e0`
- Helper return confirmed: `True`
- Semantic gate: `True`
- Source pixel: `[0, 0, 0, 63, 0, 0, 64, 63, 0, 0, 128, 62, 0, 0, 0, 62]`
- After-destination pixel: `[0, 0, 0, 63, 0, 0, 64, 63, 0, 0, 128, 62, 0, 0, 0, 62]`
- No internal-stage transformation model is used for classification.
- Padding after destination: `[165, 165, 165, 165]`
- Required: exact copy equality and unchanged sentinel padding.

## ABI Boundary

- The worker context is allocated through `context+0x180`.
- `context+0x180` points to a separate suite object with a callback-shaped first slot.
- The synthetic suite models acquire/release plus the observed handle-vtable slots at `+0x10` and `+0x18` used by worker cleanup.
- PF16 callback arguments are captured at `0x1801a5b5e`; the post-callback point `0x1801a5b61` proves output visible bytes equal raw input.
- The PF16 alpha matrix is binary-grounded worker evidence: only alpha `32768` observed the seed/propagation helper path.
- A worker is marked returned only when the loader reaches its return trampoline.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf16_pf32_copy_boundary_20260716.py
```
