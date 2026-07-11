# OLMDirectionalBlur Angle-0 Single-Shot Witness Contract - 2026-07-08

Do not send this while another runtime package is active. This supersedes the
broad `olmdirectionalblur_angle0_helper_gate_retry_20260702` retry shape, which
returned `answered_partial` after proving module/stage reachability but missing
per-pixel typed witness values because of a hit storm.

## Request

- Request id: `olmdirectionalblur_angle0_single_shot_witness_20260708`
- Effect: `OLM DirectionalBlur`
- Case: `directionalblur_context_scale_20260606` /
  `db_existing_case_0001_software_pair`
- Lane: angle-0 only, `angle0-rowdriver-valid-alpha`
- Witness pixels: `(494,169)` and `(579,169)` in the same run

## Required Capture

Use conditional or single-shot witness gating. Do not let broad helper entry
breakpoints free-run.

Capture the two required pixels as two independent records, not as one
case-level record. `(494,169)` and `(579,169)` may diverge in source coverage,
buffer mapping, and downstream validity. If a return collapses them into one
shared value set, classify it as `answered_partial` at best.

For each required witness pixel, capture:

- normalized consumed parameters
- output-to-A/B coordinate mapping and the A/B buffer identity; if AE routes
  this angle-0 case
  through a rotated-buffer path, record that path explicitly as the fallback
  mapping instead
- helper-local source `x/y`
- helper-local source `x` range or an explicit alternate-path explanation for
  the right endpoint `(579,169)`
- actual touched destination `x` range on row `169`
- rowdriver/group membership
- denominator value
- `alpha_or_valid` or equivalent validity side-channel
- accumulation numerator RGBA
- pre-writeback RGBA float/hex
- final stored RGBA bytes

## Acceptance

`answered`:

- both `(494,169)` and `(579,169)` have typed same-run witness records covering
  helper-local coverage, denominator, validity/alpha, accumulation/prewriteback,
  and final stored bytes.

`answered_partial`:

- one witness pixel is complete, or both pixels have a retained source/range
  record but one downstream value is missing.
- this remains pending for queue purposes; it is evidence, not closeout.

`failed_partial`:

- module/stage reachability is proven again but per-pixel witness values are
  still missing.
- the return includes only case-level values where `(494,169)` and `(579,169)`
  cannot be separated.
- the return says the target did not hit but omits which
  breakpoint/condition/watchpoint failed, whether the failure happened before
  or after module load, or how many qualifying hits were seen.

`failed`:

- final bytes only, broad hit counts, module-load-only, surrogate cases, or
  PNG-level restatement.

## Forbidden

- Do not include diagonal witnesses in this request.
- Do not change Mac implementation from this request unless it returns typed
  witness values.
- Do not classify broad breakpoint reachability as proof of rowdriver/group
  membership.
