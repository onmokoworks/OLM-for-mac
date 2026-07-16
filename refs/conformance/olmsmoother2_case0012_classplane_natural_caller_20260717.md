# OLMSmoother2 case0012 natural class-plane caller

## Verdict

`PASS_MAC_NATURAL_CLASSPLANE_CALLER_WITH_EXACT_LIVE_INPUT_BOUNDARY`

Actual AEX `FUN_18000ada0` reaches the compiler-generated `FUN_18000ac00` worker through a continuation-safe serial implementation of `VCOMP140!_vcomp_fork`. The worker naturally calls `FUN_18000ae10` once per pixel and fills the requested class rectangle before c280.

## Checkpoint Result

- Actual chain: `0x18000ada0 -> VCOMP140!_vcomp_fork -> 0x18000ac00 -> 0x18000ae10`.
- Runtime: `54625` fully counted guest instructions, one worker, `256` ae10 calls.
- The translated retained source fixture regenerates the central `3x4` class window exactly; this is the largest rectangular output window whose ae10 dependencies are wholly covered by the retained `5x5` source setup.
- Actual c280 consumes that newly generated plane and returns polygon count `1`.

## Live Boundary

The VCOMP runtime boundary is locally closed. The three Windows returns provide a later c280 source-plane pointer but no post-frame-setup source floats and no ada0 config snapshot, so the corrected live neighborhood still cannot be regenerated.

Exact next checkpoint: `FUN_18000ada0 entry: RCX=source FPlane*, RDX=class FPlane*, R8=rect*, R9=config*; capture source neighborhood and config before _vcomp_fork`.

Required same-run fields are the float source neighborhood, config `+0x1c/+0x70/+0x74`, rectangle, and both descriptor strides. Process pointers without bytes remain non-replayable.

## Reproduction

```sh
python3 tools/emulation/test_olmsmoother2_case0012_classplane_natural_caller_20260717.py \
  --output-json refs/conformance/olmsmoother2_case0012_classplane_natural_caller_20260717.json \
  --output-md refs/conformance/olmsmoother2_case0012_classplane_natural_caller_20260717.md
```

## Claims Not Made

- No recovered corrected Windows class plane.
- No Windows or After Effects execution claim.
- No production correctness or AE exact claim.
- No ledger or production-source change.
