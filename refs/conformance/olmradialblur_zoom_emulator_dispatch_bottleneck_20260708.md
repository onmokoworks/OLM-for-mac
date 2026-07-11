# OLMRadialBlur Zoom Emulator Dispatch Bottleneck - 2026-07-08

## Verdict

The current Zoom `case_0009` local AEX witness is blocked before the Zoom core
dispatch. This is an emulator-entry/staging bottleneck, not a semantic proof
about the RadialBlur output algorithm.

## FACTS

- `refs/conformance/olmradialblur_zoom_case0009_aex_witness_20260708.md`
  reports that parameter setup reaches `blur_type=1`.
- The same witness does not observe `FUN_1800056f0`, `FUN_18000a7e0`, or
  `FUN_18000a810` within the render instruction cap.
- The stopped RIP is around `0x180007811`, which is before the useful Zoom core
  evidence and appears to be in full-frame staging / buffer initialization.
- `refs/conformance/olmradialblur_zoom_staging_loop_probe_20260708.md`
  confirms that the `0x180007811` loop is full-frame-sized:
  `bound_x=1920`, `bound_y=1080`, with 16-byte `rdi/rsi` pixel strides and
  `16380` loop hits within a 1,000,000-instruction probe.
- Therefore this witness must not be used to change Mac RadialBlur output code.

## Next Mac-Only Actions

1. Add or run a small witness around `0x180007811` to identify which staging
   plane and bounds are consuming the instruction budget.
2. Read `0x1800072d3..0x180007344` and `0x1800077c0..0x18000785e` together in
   Ghidra/objdump to find a safe post-staging entry point.
3. Prepare a direct `FUN_1800056f0` single-function harness only after its work
   buffer contract is pinned.

## Forbidden From This Evidence

- Do not tune RadialBlur visually.
- Do not change Mac source from this partial witness.
- Do not requeue Windows for Zoom before shrinking the local emulator entry
  bottleneck, unless a new project-level priority supersedes this lane.
