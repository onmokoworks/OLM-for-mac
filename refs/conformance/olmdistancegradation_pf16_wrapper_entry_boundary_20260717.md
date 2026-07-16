# OLMDistanceGradation PF16 wrapper boundary probe

Date: 2026-07-17 (Mac)

This is a bounded same-loader Unicorn probe for the 16bpc path. It enters
`FUN_181170ff0` at `0x181170ff0`, uses the callback-backed parameter/world
scaffold, and then enters the caller's `FUN_181170280` at `0x181170280`.
It does not edit the AEX or the conformance ledger.

## Exact run

```text
python3 -m py_compile tools/emulation/probe_dg_pf16_wrapper_entry_20260717.py
python3 tools/emulation/probe_dg_pf16_wrapper_entry_20260717.py > /tmp/dg_wrapper_final.json
```

The probe completed with process exit status 0 and reported:

```text
status blocked wrapper 1 field 2 compose 0 returned True
blocker FUN_181170280 returned before FUN_181170480; PF Iterate16 suite callback did not reach compose
```

## Observed contract

- `FUN_181170ff0` was entered once and returned.
- `FUN_181174760` was entered twice by the actual wrapper path.
- The caller acquired `PF iterate16 Suite`, version `1`, through the AEX
  SPBasic acquire callback. The returned suite object's first function was
  entered once.
- The live iterate call had register arguments
  `(RCX,RDX,R8,R9) = (0x400003a0, 0x0, 0x5, 0x40000250)`.
- Its stack contract was:
  `RSP+0x28=0x40000c6c`, `RSP+0x30=0x40000b40`,
  `RSP+0x38=0x181170480`, `RSP+0x40=0x400002d0`, and
  `RSP+0x48=0x40000240`.
- `callback_invocations` was `0`. The first unimplemented boundary is the
  host-owned PF Iterate16 callback driver that must invoke the function
  pointer at `RSP+0x38` with per-pixel output storage.

Therefore this evidence proves actual wrapper staging and fieldgen reachability
and the PF16 compose dispatch contract, but it does not claim compose execution,
padding preservation, or final PF16 equality against the Mac source oracle.
