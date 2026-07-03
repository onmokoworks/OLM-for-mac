# OLMRadialBlur Tiny Rotation Intake Audit - 2026-07-03

Status: `intake-boundary-consistent`

This is a no-edit audit of the active `tiny Rotation` Windows return boundary.

Checked against:

- [anchor-context follow-up contract](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_followup_contract_20260702.md)
- [anchor-context return acceptance](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md)
- [scripts/compare_radialblur_trace.py](/Users/onmk/Documents/Projects/Personal/OLM%20as/scripts/compare_radialblur_trace.py)
- [latest backstep comparison](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.md)

## Result

The current intake path is aligned:

- the contract asks for the first retained upstream promotion branch from the
  stable `+0x4eb9/+0x4ec8` anchor
- the return acceptance explicitly rejects anchor-only confirmation as
  `answered`
- `scripts/compare_radialblur_trace.py` classifies the live lane as
  `tiny_rotation:substitute-or-upstream-rgb` when upstream branch/value facts
  are still missing but the inverse-sampler anchor is retained
- the latest imported Windows result is still correctly read as
  `failed_partial`, not actionable implementation proof

## Durable intake rule

The next Windows return for:

- `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`

should be promoted to `answered` only if it includes:

- stable anchor preservation
- concrete sampled-cell / adjacent-row address reconstruction
- the first retained upstream promotion branch
- typed values for substitute/source-population ownership or equivalent
  `+0xf252`, `+0xf250`, `+0xe` path evidence

It should remain `failed_partial` if it only reconfirms:

- the same near-black inverse-sampler sample
- the same final white byte
- the same anchor without the decisive upstream branch/value

## Practical consequence

No additional local RadialBlur source tuning is justified from the current
Windows lane alone.

The intake side is ready; the next meaningful progress on this lane still
depends on the narrower Windows watch/context return itself.
