# OLMDistanceGradation PF16 wrapper Iterate16 harness

Date: 2026-07-17 (Mac)

This is a bounded same-loader Unicorn probe for the 16bpc path. It enters
`FUN_181170ff0` at `0x181170ff0`, uses the callback-backed parameter/world
scaffold, then lets the actual caller `FUN_181170280` dispatch its host-owned
PF Iterate16 callback. The callback invokes the function pointer in the live
AEX frame with a private nested stack and restores the suspended CPU context
after each compose call. It does not edit the AEX, production source, or the
conformance ledger.

## Exact run

```text
python3 -m py_compile tools/emulation/probe_dg_pf16_wrapper_entry_20260717.py
python3 tools/emulation/probe_dg_pf16_wrapper_entry_20260717.py > /tmp/dg_pf16_final.json
```

The probe completed with process exit status 0 and reported:

```text
status PASS wrapper 1 field 2 compose 40 returned True
iterate_callback_invocations 40 nested_rip 0x90001000
padding_canary observable=True preserved=True
```

## Observed contract

- `FUN_181170ff0` was entered once and returned.
- `FUN_181174760` was entered twice by the actual wrapper path.
- The caller acquired `PF iterate16 Suite`, version `1`, through the AEX
  SPBasic acquire callback. The returned suite object's first function was
  entered once.
- The live iterate call had register arguments
  `(RCX,RDX,R8,R9) = (0x40000420, 0x0, 0x5, 0x40000250)`.
- Its stack contract was:
  `RSP+0x28=0x40000cfc`, `RSP+0x30=0x40000cc0`,
  `RSP+0x38=0x181170480`, `RSP+0x40=0x40000bc0`, and
  `RSP+0x48=0x40000240`.
- The callback function pointer was observed at `RSP+0x38`; its compose refcon
  was observed at `RSP+0x40`. The host callback invoked that real AEX pointer
  for all `8 * 5 = 40` pixels using per-pixel output storage.
- Each nested compose returned to the private sentinel `0x90001000`, after
  which the suspended outer callback context was restored.
- The active output bytes have SHA-256
  `f7d3ab8608430f32b72351c8c681a36de5845e61bf1c83d34340abbbb9ad4d5f`.
  The observable 12-byte row padding canary remained `0xA5`; its concatenated
  padding SHA-256 is
  `aabad596d9727bb3c8e76e49409af32b4457774332b964cbfde683b75e533360`.

Therefore this evidence proves actual wrapper staging, fieldgen reachability,
host-owned per-pixel PF16 compose dispatch, and padding preservation in this
fixture. The compose fixture uses the degenerate/use-background branch; this is
not an AE-exact claim, Windows claim, or final PF16 equality against a Mac
source oracle.
