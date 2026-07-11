# OLMDistanceGradation 0010/0011 Field/Store Prewarm Witness Contract

Date: 2026-07-09

## Purpose

This is the retry contract for
`olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709`.

The earlier `olmdistancegradation_0010_0011_field_store_witness_20260709`
returns are `failed_partial`. The first live CDB retry did not reach the module
load stop. The later 2026-07-09 19:47 return, classified in
`refs/conformance/olmdistancegradation_0010_0011_field_store_return2_intake_20260709.md`,
does improve the tactic: `DistanceGradation.aex` module-load stop is reliable,
the live callback/store path remains `DistanceGradation+0x1170480`, and frozen
hardware-entry stepping reaches `DistanceGradation+0x117051c`. It still does
not capture same-run source/field/pre-store/PF16/export values for the requested
pixels.

This retry changes the tactic. First stabilize and prove module load for the
exact request/case path, then bind the narrow pixel witnesses in the same AE
session. Do not start with only the final coordinate-gated hooks. If this
contract is revised, prefer a narrower continuation from hardware-entry freeze
past `DistanceGradation+0x117051c` into PF interleave/writeback.

## Required Execution Shape

1. Use the exact 16bpc Software request:
   `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/`.
2. Prewarm/load phase:
   - run a load-only or prewarm render for `olmdistancegradation_extended__case_0010`;
   - prove `DistanceGradation.aex` module load with a retained module base;
   - if module load still fails, return the exact AE/CDB command, timeout,
     process state, and log tail. That is the primary result.
3. Witness phase, same AE session after module load:
   - bind the final compose/writeback path for the primary `case_0010` pixels
     `(6,40)` and `(901,394)`;
   - keep `case_0011 (915,392)` optional.

## Values To Capture

For each captured target pixel, return typed same-run Windows AEX values:

- source RGBA16 consumed by the effect callback;
- inside/outside raw distance before normalization;
- normalized field value consumed by compose;
- field-world stored word/value if an intermediate field world exists;
- final compose `out_a` and RGBA floats immediately before PF_Pixel16
  conversion;
- PF_Pixel16 stored RGBA words immediately after writeback;
- exported true16 TIFF/EXR sample if observable from the same render.

PNG/display bytes alone are not enough.

## Acceptance Rule

Satisfactory:

- module load is proven in the exact case path; and
- both primary `case_0010` pixels return field, pre-store float, PF16 store
  word, and exported true16 sample in the same run.

Partial:

- module load is proven and one primary pixel is fully typed; or
- module load is proven and the precise downstream hook/watchpoint failure is
  returned with enough address context for the next retry.
- module load is proven but only entry/compose-path addresses are retained; this
  is useful diagnostic evidence, not implementation proof.

Failed:

- module load is not reached and the return does not include a precise startup
  / load failure signature;
- the answer restates local/implied store words or package-local recomputation;
- only PNG/display bytes, broad hit counts, or residual directions are returned.

Avoid resident breakpoints at `DistanceGradation+0x1170509` for this render
shape unless a new guard strategy is provided; both software and hardware
variants failed before store samples in the 2026-07-09 19:47 return.

## Why This Is Narrow

Local Mac evidence already shows the EDT implementations agree at the target
fields. The unresolved family is a sign-flipping one-word PF_Pixel16 alpha-store
split exposed as R/A `max=2`, so a global rounding or field topology change is
forbidden until this same-run Windows witness classifies the split as field,
PF16 conversion, or export behavior.
