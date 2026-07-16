# OLMKiraKira Mode 2 immediate caller/output boundary

Date: 2026-07-17
Status: **pass**
AE exact: **false**

## Result

The immediate caller is `FUN_18114f4a0 @ 0x18114f4a0`. Its indirect vtable
dispatch uses `+0x8` for Mode 1 and `+0x10` for Mode 2. The Mode-2 callsite
forwards the caller's output argument as target `param_7`; `FUN_18114ffd0`
writes the proven float RGBA result there.

After the indirect call returns, the caller only performs vector cleanup,
deallocation, stack-cookie cleanup, and returns. It does not read the output
buffer, invoke a host compose operation, or call the PF8/PF16/PF32 writers.

## FACT

- Pinned AEX SHA-256: `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Static callsite: `FUN_18114f4a0` indirect vtable `+0x10` to Mode 2.
- Static argument flow: caller `[RBP-0x20]` is placed at `[RSP+0x30]`, the
  target's `param_7` slot; the target receives it as `RDI` and stores float
  RGBA channels there.
- Direct actual-AEX target execution wrote
  `0000003f0000403f0000803fcdcc4c3e` for the one-pixel control fixture.
- No immediate-caller call to `0x181230b90`, `0x181230bd0`, or `0x181230c20`
  occurs after the Mode-2 call.

## INFERENCE

- Merge Mode participates before the caller-owned float aggregation buffer,
  through selection of the aggregation target. This slice does not place
  Merge Mode in later writer selection.
- The next consumer of the float buffer is outside this immediate AEX caller
  slice and is therefore host-side or in an unbound caller not represented by
  the checked-in evidence.

## First unavailable ABI

Executing `FUN_18114f4a0` end to end requires its `param_1` host-owned
vtable/channel object, including vtable slots, channel allocation state,
callbacks, and upstream buffers. The checked-in `AexLoader` can execute the
selected target directly, but cannot provide that host object ABI. This is the
first unavailable boundary; no host compose/writeback claim is made beyond it.

## Verification

```text
python3 tools/emulation/test_olmkirakira_mode2_caller_output_boundary_20260717.py
=> status=pass; static=8/8; actual_aex_target=True
```

No completed 20260717 files, production source, ledger, PNG, or AE exactness
claim was changed.
