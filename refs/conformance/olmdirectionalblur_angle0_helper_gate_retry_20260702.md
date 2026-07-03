# OLMDirectionalBlur Angle-0 Helper-Gate Retry

Date: `2026-07-02`

This retry exists because the fresh Windows pass proved:

- `OLMDirectionalBlur` does load
- a broad `+0x2000` entry-style breakpoint is reachable

but that breakpoint is too early and too noisy to preserve the witness-local
fields for the angle-0 lane.

## Target

- request set: `directionalblur_context_scale_20260606`
- case: `db_existing_case_0001_software_pair`
- witness lane: `angle0-rowdriver-valid-alpha`
- primary witness: `(494,169)`
- endpoint witness: `(579,169)`

## Required strategy

Do not use a surrogate case and do not stop at broad `+0x2000` hits.

1. Use the real DirectionalBlur reference/request case above.
2. Use `+0x2000` only to confirm module load if needed.
3. Move to a narrower rowdriver/front-helper stage so the same pass can retain
   helper-local destination coverage on row `y=169`.

## Required facts

- normalized parameters actually consumed
- A/B mapping or equivalent output-to-buffer xy mapping
- denominator value at `(494,169)` and `(579,169)`
- `alpha_or_valid` or equivalent validity side-channel value
- helper-local source x/y
- actual touched destination x range on row `y=169`
- rowdriver/group membership for `(494,169)` and `(579,169)`
- pre-writeback RGBA
- final stored RGBA bytes

## Rejected non-answers

- broad `+0x2000` hit storm alone
- final PNG or final byte restatement alone
- a surrogate load case that does not run the real requested angle-0 witness
