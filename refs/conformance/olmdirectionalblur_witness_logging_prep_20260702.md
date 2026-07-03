# OLMDirectionalBlur Witness Logging Prep

- Date: `2026-07-02`
- Decision: `ready-for-next-witness-level-ab-denominator-validity-logging`
- Structural base: `rotated-aex-full-choreo`
- Runtime package: `refs/runtime_trace_packages/olm_runtime_trace_requests_20260630_004241.zip`
- Current runtime status: `answered_partial`
- Current runtime summary: The current package contains the exact Software reference renders for the two targeted cases and one prior live-attempt log, but no successful Windows per-pixel runtime trace. The prior live attempt failed before `OLMDirectionalBlur` resolved as a loaded module, so no rowdriver/rotate-path stage values were captured.

## Source Anchors

- `rotate_helper_line`: `493`
- `rowdriver_line`: `1509`
- `rowdriver_front_helper_call_line`: `1578`
- `rowdriver_back_helper_call_line`: `1589`
- `rotate_into_b_call_line`: `1935`
- `copy_b_back_into_a_line`: `1943`
- `rowdriver_dispatch_line`: `2018`
- `rotate_back_output_call_line`: `2063`
- `cli_full_choreo_line`: `1395`
- `cli_exact_rowdriver_line`: `1401`
- `cli_rowdriver_prepass_line`: `1445`
- `cli_front_strength_line`: `1441`

## Shared Logging Principles

- Stay on the AEX-shaped full choreography base while logging; direct and rotated-front-strength remain measurement baselines only.
- Capture typed values for A/B mapping, denominator, alpha_or_valid, numerator, pre-writeback, and final bytes in the same witness record.
- Treat angle-0 and diagonal as separate lanes even if one pass can log both.

## angle0-rowdriver-valid-alpha

- Classification: `angle0-rgb-only-rowdriver-or-valid-alpha`
- Primary witness: `[494, 169] ref=[164, 0, 0, 255] cand=[0, 0, 0, 255]`
- Scan-order max witness: `[465, 169] ref=[164, 0, 0, 255] cand=[0, 0, 0, 255]`
- Endpoint constraint: {'rightmost_visible_strip_x': 579, 'required_min_source_x_for_same_row_front_helper': 580, 'same_row_segment_contains_that_source_x': False, 'implication': 'If the angle-0 endpoint pixel is produced by the documented front helper on the same row, the contributing source x must be strictly greater than the endpoint destination x because front writes only to the left. The current local strip row ends at x=579, so a same-row source inside that visible strip cannot explain the endpoint by itself.'}
- Required next proof: A helper-local source-to-destination range witness on the strip row, especially the right endpoint (579,169) plus companion witness (494,169), including actual touched destination x range, rowdriver/group membership, validity side-channel, accumulation, pre-writeback RGBA, and final bytes.
- Helper-local static facts:
  - front helper call uses param_3 = 1
  - effective span is int(param_9 * param_11) with left-edge clipping
  - writes start at offset = 1
  - loop continues while offset < param_9
  - front helper writes only to destination columns strictly left of the current source x

Witness focus:

- Primary interior witness stays (494,169), but the return should include the right-edge endpoint (579,169) in the same pass.
- The point of this lane is to decide whether the missing red strip is a rowdriver/group-membership miss or a valid-alpha side-channel miss.
- A useful answer must expose touched destination coverage, not only final bytes.

Required fields:

- witness case id and output xy
- normalized effect parameters actually consumed by the call
- A/B image pointers plus output-to-A/B buffer xy mapping
- denominator plane pointer/value at the witness
- alpha_or_valid side-channel pointer/value at the witness
- accumulation numerator RGBA before normalization
- pre-writeback RGBA float/hex after normalization
- final stored RGBA bytes
- helper-local source x/y and actual touched destination x range on row y=169
- rowdriver/group membership for both (494,169) and endpoint (579,169)
- effective span inputs/outputs for the front helper

Treat as answered when:

- The same return covers both (494,169) and (579,169) with typed rowdriver/group and alpha_or_valid values.
- The helper-local source-to-destination coverage proves whether the right endpoint is inside or outside the front-helper write range.
- Numerator, denominator, pre-writeback, and final bytes are all present at the witness.

Treat as not answered when:

- Only final PNG bytes or broad means are returned.
- The run confirms the witness coordinates but omits helper-local touched destination range.
- The run logs rowdriver-ish prose without typed values for denominator, alpha_or_valid, and pre-writeback RGBA.

## diagonal-rotate-validity

- Classification: `diagonal-rgb-alpha-rotate-validity`
- Primary witness: `[507, 367] ref=[1, 0, 0, 255] cand=[252, 0, 0, 255]`
- Companion witnesses: `[423, 187] ref=[254, 0, 0, 255] cand=[4, 0, 0, 255]`, `[507, 367] ref=[1, 0, 0, 255] cand=[252, 0, 0, 255]`, `[519, 363] ref=[0, 0, 0, 255] cand=[250, 0, 0, 255]`
- Required next proof: Typed rotate sampler source coordinates/order, border or validity decision, group-size or opacity gate, accumulation denominator, pre-writeback RGBA, and final bytes at the diagonal witnesses.

Witness focus:

- Primary diagonal witness stays (507,367); keep a signed-red companion such as (423,187) in the same answer when possible.
- The point of this lane is to separate rotate sampler order/border-validity from later normalization/writeback.
- A useful answer must expose the sampled source coordinates/order and the validity decision feeding the witness.

Required fields:

- witness case id and output xy
- normalized effect parameters actually consumed by the call
- A/B image pointers plus output-to-A/B buffer xy mapping
- denominator plane pointer/value at the witness
- alpha_or_valid side-channel pointer/value at the witness
- accumulation numerator RGBA before normalization
- pre-writeback RGBA float/hex after normalization
- final stored RGBA bytes
- rotate sampler source coordinates and sample order
- border or validity decision for the sampled source set
- group-size or opacity gate feeding the diagonal witness

Treat as answered when:

- The return includes typed rotate source coordinates/order plus border-validity or equivalent substitute-path facts.
- The return includes group-size/opacity gate, denominator, pre-writeback, and final bytes at the diagonal witness.
- The same answer keeps diagonal evidence separate from the angle-0 strip theory.

Treat as not answered when:

- Only the final diagonal byte is logged.
- Sampler order is described qualitatively but no typed source coordinates or border-validity values are returned.
- The answer collapses diagonal behavior into the angle-0 rowdriver theory.

## Parent Follow-up

- Use this prep artifact to shape the next Windows witness request or local logging harness fields.
- When a new return lands, feed it through compare_directionalblur_trace.py and check it against the per-lane answerable/not-answered rules here.
- Do not start source edits until at least one lane returns typed denominator + validity/alpha_or_valid + pre-writeback evidence.
