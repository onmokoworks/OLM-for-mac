# OLMColorKey Type3 Boundary To Distance Witness - 2026-07-16

This is a bounded Mac-only Unicorn execution of the checked-in Windows PE. It
wraps the existing boundary-to-distance probe, reuses the proven HandleSuite
callback layout from the Edge Blur apply probe, and targets
`FUN_180007ec0` (`RCX=ctx, RDX=seed_world, R8=distance_world, XMM3=255.0`).
It is not AE-host execution and makes no AE-exact claim.

## FACT

- The boundary seed is produced at `FUN_180008c90` with `R8D=8`.
- The exact AEX identity is pinned by SHA-256 before loader construction; a
  mismatch blocks execution.
- The type3 context supplies `+0x120=255`, `+0x128=255`, and `+0x180` as the
  HandleSuite descriptor.
- The loader import log is recorded and must be empty; HandleSuite callbacks
  are host callbacks and are reported separately.
- The report records normal return, exactly one `width * height * 4` handle
  allocation (alongside smaller internal allocations), callback lifecycle
  order, cleanup, and the four-channel float32 payload. Status is pass only
  when all acceptance gates are true.
- The independent check is nearest-zero-seed Euclidean pixel distance. Exact
  observed values and instruction counts are in the JSON report.

## Regenerated Result

- AEX SHA-256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`
  (identity match).
- Loader import log: `[]`.
- Type3 return: `RAX=0`, 4,311 instructions.
- Handle allocations: 8 total, exactly 1 required 60-byte allocation.
- Lifecycle and cleanup: complete; suite release observed last.
- Float32 model comparison: exact match across all 5x3x4 values.

## INFERENCE

Agreement with the small Euclidean model scaled by the supplied `255.0` supports
the interpretation of this lane as a Euclidean distance output for the supplied
seed. It does not establish
the complete Replace+Edge path, real AE host ABI equivalence, or AE-exact output.

Run directly with:

```text
python3 tools/emulation/probe_olmcolorkey_boundary_to_distance_type3_actual_aex_20260716.py \
  --json refs/conformance/olmcolorkey_boundary_to_distance_type3_actual_aex_20260716.json
python3 tools/emulation/test_olmcolorkey_boundary_to_distance_type3_actual_aex_20260716.py
```
