# OLMSmoother2 Full-Chain Local Differential

Date: 2026-07-11

## Verdict

`PASS_REPLAYED_BOUNDARIES_WITH_EXACT_HOST_STATE_BLOCKERS`

This is local binary-semantic evidence only. It is not Windows AE truth.

## FACT

- The test uses two 16x16 float/class-plane fixtures with identical serialized
  values on the AEX and current-port sides. Both classify as `idx=0x69` in the
  independently reproduced `FUN_18000c280` index expression.
- The c=2 witness has `(center_b0,prev_b0,left_b1)=(0,1,0)`. Direct descriptor
  `[5,6,1,5,8,5]` produces `c=2`, one append, copied RGBA
  `[0.991067171,0.991067171,0.991067171,0.996078432]`, and weight
  `0.428160906` on both the actual AEX and current port.
- The c=4 control has `(0,0,1)`. The same direct descriptor produces `c=4`, no
  append, and an empty polygon on both sides.
- Actual AEX `FUN_1800125c0` and current-port `win_FUN_1800125c0` do not append
  for either fixture.
- Actual AEX `FUN_180010760` and current-port `win_cardinal_6` both generate
  descriptor `[5,6,1,5,6,0]` from the available fixture bytes.
- For c=2 that generated chain appends one identical vertex. After actual AEX
  `FUN_18000cc70` and current-port normalization, both weights are
  `0.321428567`. For c=4 both chain polygons remain empty.
- The focused smoke test compares descriptor, c, append, vertex RGBA, vertex
  weight, polygon count, generated cardinal descriptor, and normalized chain
  vertices. Every replayed comparison passes at absolute tolerance `1e-6`.
- Port-only composite floats are `[0.996175289,0.996175289,0.996175289,
  0.426481843]` for c=2 and `[1,1,1,0]` for c=4. They are diagnostic values,
  not an AEX comparison.

Machine-readable values are in
`refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json`.

## Exact Blockers

1. `FUN_18000c280` execution: the AEX entry consumes five arguments. The fifth
   is a live host/config object read at least at `+0x20` and `+0x24`; no accepted
   identical-memory binding for that opaque object exists in the local evidence.
   The test therefore reproduces and checks the index expression but does not
   claim execution of the AEX builder entry.
2. Recorded descriptor continuation: the known class bytes are sufficient for
   `idx=0x69` and the three `e170` predicates, but actual scanners produce
   `[5,6,1,5,6,0]`, not recorded `[5,6,1,5,8,5]`. The missing class-plane bytes
   needed to extend the second scan to y=8/class=5 are not present in the local
   witness record. Fabricating them would cease to be identical-memory replay.
3. `FUN_18000cce0` final float: the AEX orchestrator consumes gamma, key, and
   parameter context beyond this polygon fixture. There is no accepted complete
   local binding for that context. The test reports port composite output only
   and does not compare or infer an AEX final float.

## INFERENCE

- Agreement through the direct recorded descriptor and through the independently
  generated `125c0 -> 10760 -> e170/f270/e3a0 -> cc70` lane supports semantic
  equivalence of those exercised local helpers for these two fixtures.
- It does not establish that the reconstructed fixture equals live Windows AE
  memory at `(91,841)`, nor that the active Windows divergence is in these helpers.

## Focused Command

```sh
python3 refs/scripts/smoke_smoother2_fullchain_diff.py
```

Result: exit `0`; `PASS smoother2 fullchain local differential`.
Compilation emitted 12 pre-existing warnings from the included production port
and CLI shim (deprecated shim `sprintf`, unused production functions/parameters).
No adapter or test warning was emitted.

The smoke script runs these effective commands:

```sh
clang++ -std=c++17 -O2 -Wall -Wextra \
  -Icli/OLMSmoother2/shim -Imac/OLMSmoother2/Mac \
  tools/emulation/smoother2_fullchain_port_adapter.cpp \
  -o /tmp/olmsmoother2_fullchain_diff/port_adapter
python3 tools/emulation/test_smoother2_fullchain_diff.py \
  --adapter /tmp/olmsmoother2_fullchain_diff/port_adapter \
  --output refs/conformance/olmsmoother2_fullchain_local_diff_20260711.json
```

