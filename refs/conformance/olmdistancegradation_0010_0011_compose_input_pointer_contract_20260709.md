# OLMDistanceGradation 0010/0011 compose input pointer witness contract

Date: 2026-07-09

Request id:
`olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709`

## Purpose

The previous return captured `rdx` at `DistanceGradation+0x1170814`, but a
static read of `FUN_181170480` shows that this late `rdx` register is the
source/shade pixel pointer derived from `param_1[0]`, not the distance-field
world pointer. The distance-field pointer is built earlier in the same callback
through `RCX` from `param_1[1]` and is read at `DistanceGradation+0x117057d`.

This request replaces the narrower-but-misnamed `rdx producer` ask. It must bind
both compose inputs in one run:

- `RCX` field-world pixel read at `DistanceGradation+0x117057d`
- `RDX` source/shade pixel read at `DistanceGradation+0x11705f1`

The final writer values at `DistanceGradation+0x1170808..0x1170828` are only
confirmation.

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

## Static anchors

From `disasm/DistanceGradation.aex.asm.txt`:

- `18117054d..181170571`: build `RCX` from `param_1[1]` field world
- `18117057d`: read field green word `[RCX + 0x2]`
- `1811705c8..1811705ed`: build `RDX` from `param_1[0]` source/shade world
- `1811705f1`: read source/shade green word `[RDX + 0x2]`
- `181170808..181170824`: final `CVTTSS2SI` conversions

The retained return's `rdx_src_words` are therefore source/shade words, not the
field-world pack value. Do not use them as direct proof of field packing.

## Required trace

For each primary pixel:

1. Stop before or at `DistanceGradation+0x117057d`.
2. Record `RCX`, field-world rowbytes/dimensions/base if recoverable, and
   words at `RCX + 0/2/4/6`.
3. Record `XMM1` after `CVTDQ2PS/MULSS` and `XMM2` after the invert branch
   (`DistanceGradation+0x11705b3..0x11705c8`).
4. Stop before or at `DistanceGradation+0x11705f1`.
5. Record `RDX`, source/shade rowbytes/dimensions/base if recoverable, and
   words at `RDX + 0/2/4/6`.
6. Reconfirm final writer scalars at `DistanceGradation+0x1170808`,
   `+0x1170814`, `+0x117081c`, and `+0x1170824`.
7. If feasible, data-watch the `RCX` field-world address backwards to the last
   writer/pack-site before callback consumption.

## Acceptance

Satisfactory:

- both primary pixels bind `RCX` field-world words and `RDX` source/shade words
  in the same run;
- the return includes `XMM1/XMM2` field scalar values before/after invert;
- either the field-world producer/pack-site is identified, or the exact consumed
  field words explain whether the residual occurs before field packing, at
  field packing, or later in compose.

Partial:

- one primary pixel is fully typed, or
- both primary pixels bind `RCX` and `RDX` read pointers but the producer watch
  misses with exact address/register/log evidence.

Failure:

- final writer / PF interleave hits only;
- treating late `RDX` source words as field-world proof;
- final PNG/display bytes only;
- package-local recomputation.
