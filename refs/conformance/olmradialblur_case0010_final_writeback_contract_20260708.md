# OLMRadialBlur case_0010 Final Writeback Contract - 2026-07-08

This is a future Windows runtime request. Do not send it while the active
DistanceGradation depth-gate package is still in the shared `new` queue.

## Purpose

Classify the remaining tiny Rotation `case_0010 (1614,6)` split as either:

1. a CPU-side rule not captured by the current local AEX emulation,
2. a final output-buffer/writeback/export path split,
3. or stale/reference-provenance drift in the legacy PNG.

This request follows:

- `refs/conformance/olmradialblur_static_witness_plan_20260708.md`
- `refs/conformance/olmradialblur_static_witness_20260708.md`
- `notes/IR_OLMRadialBlur.md`
- `notes/OLMRadialBlur_ASM_FACTS.md`

## Current Local Facts

- Local CPU AEX emulation reaches the Rotation path for `case_0010`.
- The direct final inverse sample for output pixel `(1614,6)` samples `+0xe` at
  `(1603.839558785, 844.317504883)`.
- Local direct `+0xe` sampler result is approximately
  `(-0.004081939, -0.004081939, -0.004081939, 1.0)`, which clamps to
  `(0,0,0,255)`.
- Local output-world bytes from the existing M4 artifact are RGBA `(0,0,0,0)`.
- The legacy Windows PNG reference remains white at the same pixel.
- Existing local artifacts preserve the four-cell neighborhood but lack
  `+0xf252` for the `1604` column and do not contain a Windows final-writeback
  dump.

## Required Primary Witness

Case: `case_0010` / tiny Rotation

Pixel: `(1614,6)`

Capture in one same-run Windows Software render:

- module base and exact AEX path/version,
- final inverse sampler input coordinate for `(1614,6)`,
- the four contributing polar cells around `(x=1603.839558785, y=844.317504883)`,
- for each contributing cell:
  - `+0xf250.rgba`,
  - `+0xf252`,
  - collapsed `+0xe.rgba`,
- direct inverse-sampler result from `+0xe`,
- output buffer RGBA immediately after the inverse sampler/writeback path for
  `(1614,6)`,
- exported RGBA8/PNG byte from the same run,
- any alternate final-output path if the exported byte does not match the
  observed output buffer.

## Control Witnesses

If cheap, include nearby controls from the known bright-lobe neighborhood:

- `(1612,4)`
- `(1613,5)`
- `(1614,6)`
- `(1612,6)`

The controls are secondary. Do not broaden the trace if the primary pixel can
be captured cleanly.

## Acceptance

`answered`:

- The return classifies whether Windows final output at `(1614,6)` comes from
  the same collapsed `+0xe` path as local CPU AEX emulation, another final
  output path, or a stale/reference path.
- It includes typed `+0xf250`, `+0xf252`, `+0xe`, output-buffer, and exported
  byte facts for the primary pixel.

`answered_partial`:

- The return captures the collapsed `+0xe` and final output buffer for the
  primary pixel but cannot observe export, or it captures a precise failure
  reason with the nearest retained frame.

`failed`:

- Only final PNG bytes are returned.
- The old broad caller-collapse / anchor-context request is rerun as-is.
- The return reopens low-alpha fringe, final RGB clamp, span-minus-one, or wrap
  toggles without a typed final-writeback contradiction.

## Forbidden

- Do not tune Mac code from this request until the final path is classified.
- Do not re-run broad PNG matrices.
- Do not use old parent-folder names as provenance. Key by manifest/request and
  same-run output.
