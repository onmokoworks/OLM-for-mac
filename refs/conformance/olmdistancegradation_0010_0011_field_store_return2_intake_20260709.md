# OLMDistanceGradation 0010/0011 Field/Store Return2 Intake

Date: 2026-07-09

Return archive:
`/Volumes/onmk/olm_pr/new/20260709_194824__olmdistancegradation_0010_0011_field_store_witness_failed_partial_windows.zip`

Request id:
`olmdistancegradation_0010_0011_field_store_witness_20260709`

## Classification

`failed_partial`, not implementation proof.

This return improves the debugger tactic evidence but still does not answer the
field/store/export rule for the requested pixels.

## Useful Facts

- `DistanceGradation.aex` module-load stop is now reliable.
- The live callback/store path remains `DistanceGradation+0x1170480`.
- Entry witnesses were captured repeatedly, but `edx=0` and `r8d` values did not
  map directly to the requested output pixels.
- Direct target callback coordinate rebinding failed for the requested contract
  pixels.
- Persistent software or hardware breakpoints at `DistanceGradation+0x1170509`
  emitted no store samples and destabilized or failed before the requested
  values.
- Frozen hardware-entry stepping reached `DistanceGradation+0x117051c`, the main
  sampled compose path.
- An earlier frozen storeband run stepped into
  `PF!PF_Interleave1to4<float>+0x1557` with `rdi/rdx/r8/r9` retained.

## Missing Required Evidence

- same-run source RGBA16 for the requested pixels;
- same-run raw/normalized field for the requested pixels;
- same-run pre-store float for the requested pixels;
- same-run PF16 stored words for the requested pixels;
- true16/TIFF/EXR exported value tied to the same store witness.

## Next Retry Shape

Do not resend the old package unchanged. Do not use resident breakpoints at
`DistanceGradation+0x1170509` for this render shape.

Continue from hardware-entry freeze and follow the main sampled compose path
past `DistanceGradation+0x117051c` into PF interleave/writeback. Avoid CDB `.if`
conditions directly on `PF!PF_Interleave1to4<float>`; resolve address/range
first, or use compact symbol-free step logging and `ln @rip` postprocessing.

