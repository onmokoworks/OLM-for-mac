# OLMDistanceGradation 0010/0011 Compose Exact Address Witness Contract

Request id:
`olmdistancegradation_0010_0011_compose_exact_address_witness_20260710`

Profile:
`distancegradation-0010-0011-compose-exact-address-witness`

## Purpose

The previous compose-input return proved the register roles but missed the exact
target pixels because `rbp=y` is not a valid y-coordinate discriminator at the
compose sites. This request narrows the problem to address-bound exact pixels.

Do not repeat the previous broad `x=6` trace. This request should bind exact
memory addresses for the two residual pixels.

## Case

Use the exact normalized Software 16bpc request:

- request folder: `ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- primary case: `olmdistancegradation_extended__case_0010`
- target pixels:
  - `(6,40)`
  - `(901,394)`

Optional control if time permits:

- `olmdistancegradation_extended__case_0011` at `(915,392)`

## Required Binding

In the active Windows run, derive or log:

- field-world base pointer, rowbytes, pixel size, and channel layout;
- source/shade base pointer, rowbytes, pixel size, and channel layout;
- output base pointer, rowbytes, pixel size, and channel layout.

Then compute exact addresses:

- `field_addr = field_base + y * field_rowbytes + x * pixel_size`
- `source_addr = source_base + y * source_rowbytes + x * pixel_size`
- `output_addr = output_base + y * output_rowbytes + x * pixel_size`

If the callback uses a different row origin or sub-rect origin, return the
actual formula and all offset terms. Do not assume `rbp=y`.

## Sites To Capture

For each target pixel, capture these in the same run:

- `DistanceGradation+0x117057d`
  - instruction reads field-world green via `RCX+2`;
  - bind by `RCX == field_addr` or by a proven address-range formula;
  - record `RCX` words, `XMM1` after field read/mul, and `XMM2` after invert
    or field-side transform.
- `DistanceGradation+0x11705f1`
  - instruction reads source/shade green via `RDX+2`;
  - bind by `RDX == source_addr` or by a proven address-range formula;
  - record `RDX` words and source/shade scalars.
- `DistanceGradation+0x1170808`, `+0x1170814`, `+0x117081c`,
  `+0x1170824`
  - record final writer float/scalar inputs and stored PF16 words for
    `output_addr`.

If data watchpoints are practical, watch the exact `field_addr` backward to the
producer/pack site. Producer proof is helpful but secondary; the minimum useful
answer is exact consumed field/source/output values for the two pixels.

## Success Criteria

Satisfactory:

- both `(6,40)` and `(901,394)` have same-run exact-address `RCX` field words,
  `RDX` source words, compose scalars, and final writer/store words;
- the row/address formula is explicit enough for Mac-side comparison.

Partial:

- one target pixel is fully typed;
- or both target addresses are derived, but a hook/watchpoint misses with the
  exact failed condition and logs.

Failure:

- broad `r9=x` logs only;
- another `rbp=y` exact-gate attempt;
- final writer/PF interleave only without address-bound field/source reads;
- final PNG/display bytes only;
- package-local recomputation without live Windows stops.

## Return

Fill `RETURN_RUNTIME_TRACE_TEMPLATE.json` if possible, and include the CDB
scripts/logs used. A concise markdown summary is useful if the JSON needs extra
context.
