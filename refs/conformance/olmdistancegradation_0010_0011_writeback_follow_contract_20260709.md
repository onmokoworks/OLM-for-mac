# OLMDistanceGradation 0010/0011 Writeback Follow Witness Contract

Date: 2026-07-09

Request id:
`olmdistancegradation_0010_0011_writeback_follow_witness_20260709`

## Purpose

This is the narrowed successor to the broad
`olmdistancegradation_0010_0011_field_store_witness_20260709` / prewarm lane.

The 2026-07-09 19:47 return is still `failed_partial`, but it changes the
debugger strategy:

- `DistanceGradation.aex` module-load stop is reliable.
- The live callback/store path remains `DistanceGradation+0x1170480`.
- Frozen hardware-entry stepping reaches `DistanceGradation+0x117051c`, the main
  sampled compose path.
- Persistent software or hardware breakpoints at `DistanceGradation+0x1170509`
  emitted no store samples and destabilized or failed before the requested
  values.
- An earlier frozen storeband run stepped into
  `PF!PF_Interleave1to4<float>+0x1557`, but the requested target PF16/export
  values were not captured.

The next proof should therefore follow the execution path after
`DistanceGradation+0x117051c` into PF interleave/writeback, not retry the old
resident `+0x1170509` breakpoint tactic.

## Required Case Path

Use the exact 16bpc Software request:

`handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/`

Primary case:

- `olmdistancegradation_extended__case_0010`

Primary pixels:

- `(6,40)`:
  - Mac debug: `field_x=0.9002838730812073`
  - `out_a=0.09971612691879272`
  - `out_a*32768=3267.498046875`
  - Mac `store_a=3267`
  - Windows-implied `store_a=3268`
- `(901,394)`:
  - Mac debug: `field_x=0.6985930800437927`
  - `out_a=0.3014069199562073`
  - `out_a*32768=9876.501953125`
  - Mac `store_a=9877`
  - Windows-implied `store_a=9876`

Optional control:

- `olmdistancegradation_extended__case_0011` at `(915,392)`
  - Mac debug: `field_x=0.1345367729663849`
  - `out_a=0.8654632568359375`
  - `out_a*32768=28359.5`
  - Mac `store_a=28360`
  - Windows-implied `store_a=28359`

## Capture Strategy

1. Prove or reuse `DistanceGradation.aex` module load in the exact case path.
2. Enter via the stable hardware-entry/freeze route.
3. Continue past `DistanceGradation+0x117051c`.
4. Follow into PF interleave/writeback.
5. Capture target-pixel typed values from the same render.

Avoid resident breakpoints at `DistanceGradation+0x1170509` unless the script
uses a new guard that avoids the previous no-sample/stability failure.

Avoid CDB `.if` conditions directly on `PF!PF_Interleave1to4<float>` if symbol
resolution is fragile. Prefer resolving the address/range first, or use compact
symbol-free step logging and `ln @rip` postprocessing.

## Values To Capture

For each primary pixel, capture as many as possible from the same render:

- source RGBA16 consumed by the effect callback, if still available;
- normalized field value consumed by compose;
- compose `out_a`;
- final compose RGBA float immediately before PF interleave/writeback;
- PF interleave input/output registers or memory words near the target sample;
- PF_Pixel16 stored RGBA words immediately after writeback;
- exported true16 TIFF/EXR sample tied to the same store witness.

PNG/display bytes alone are not sufficient.

## Acceptance Rule

Satisfactory:

- both primary `case_0010` pixels have a same-run chain from
  `DistanceGradation+0x117051c` through PF interleave/writeback to PF16
  store/export; and
- the data classifies the sign-flipping one-word alpha split as pre-store float,
  PF16 conversion, or export behavior.

Partial:

- one primary pixel is fully typed; or
- module/load/writeback path addresses are proven and the exact downstream
  blocker is returned with enough address/register context for the next retry.

Failed:

- only PNG/display bytes are returned;
- package-local recomputation or Windows-implied store words are returned instead
  of live values;
- broad hit counts are returned without typed target values;
- the old `+0x1170509` resident breakpoint tactic fails again without new
  address context.

