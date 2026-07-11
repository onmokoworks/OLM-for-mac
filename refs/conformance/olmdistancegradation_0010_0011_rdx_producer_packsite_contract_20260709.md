# OLMDistanceGradation 0010/0011 rdx producer / pack-site witness contract

Date: 2026-07-09

Request id:
`olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709`

## Purpose

The previous field-world pack/read return stopped at
`DistanceGradation+0x1170814` and captured a live read-side candidate pointer in
`rdx`, but it did not identify who produced that buffer. This request narrows
the next Windows debugger pass to the upstream writes that populate the `rdx`
read-side buffer for the sparse 16bpc `case_0010/0011` residual.

## Required input

Use the exact normalized Software 16bpc request:

`ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`

Start with:

`olmdistancegradation_extended__case_0010`

Primary pixels:

- `(6,40)`
- `(901,394)`

Optional confirming pixel:

- `olmdistancegradation_extended__case_0011` `(915,392)`

## Known anchor facts

From the accepted pointer-map and partial field-read returns:

- output PF16 formula: `out = base + y * 0x3c00 + x * 8`
- pixel size: `8`
- `(6,40)` output offset: `0x96030`
- `(901,394)` output offset: `0x5c7428`
- retained-run boundary: `DistanceGradation+0x1170814`
- retained-run relation: `rdx = rdi - 0xfe0000`

The `rdx = rdi - 0xfe0000` relation is an observed same-run relation, not a
constant address. Recompute it from live `rdi` addresses after module load.

## Required trace

For each primary pixel:

1. Capture the live final `rdi` destination at `DistanceGradation+0x1170814`.
2. Derive the candidate `rdx` read-side address for that same run.
3. Set a data watch on writes to the derived `rdx` address before the final
   writer boundary.
4. Identify the producer instruction/function and callsite that last writes
   the bytes/words consumed through `rdx`.
5. Record the stored words/bytes and any corresponding float value before
   invert/compose.
6. Record raw distance, threshold/clamp value, denominator/min-max, or other
   field-prep scalar visible at the producer site.
7. Reconfirm the final boundary values at `DistanceGradation+0x1170814`:
   `rdi`, `rdx`, source words, `xmm2_alpha`, output word.

## Acceptance

Satisfactory:

- both primary pixels bind the producer of their `rdx` read-side buffer;
- the return includes the producer instruction/function, stored words/bytes,
  and field/pre-compose scalar values;
- the return explains whether the floor/ceil split is introduced before
  field-world packing, at field-world packing, or after readback.

Partial:

- one primary pixel is fully typed, or
- both primary `rdx` addresses are derived and watched, but the watchpoint miss
  is explained with exact addresses, instruction ranges, and logs.

Failure:

- broad PF interleave/final-writer hits only;
- final PNG/display bytes only;
- package-local recomputation;
- a repeated field-world pack/read boundary stop without upstream producer
  identification.
