# Windows Runtime Retry Execution Note - 2026-07-02

This note exists because the current hard-lane runtime packages are no longer
failing from vague target selection. They are failing because the retained log
does not actually preserve the requested register/pointer windows at the stop.

## Current rule

Do not treat "package executed" as success.

For the two current hard lanes, the return is only actionable if the retained
log itself contains the named registers/pointers/watchpoint context. A final
PNG, a stable breakpoint hit, or a repeated anchor value is not enough.

## 1. OLMRadialBlur

Package:

- `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`

What was still missing in the latest return:

- `rsi` qword window at the stable anchor
- `rbp` qword window at the stable anchor
- `rsp` qword window at the stable anchor
- polar-grid / row-base metadata pointers
- computed sampled-cell address for source xy `[1603.8396,844.3175]`
- held watchpoints on that cell or adjacent row cells

What the next retained log must contain:

1. the stable anchor at `OLMRadialBlur+0x4eb9/+0x4ec8`
2. the raw `rsi/rbp/rsp` qword windows at that anchor
3. enough row/grid metadata to compute the sampled-cell address
4. either:
   - the concrete sampled-cell / adjacent-row watchpoint hit
   - or the exact failure reason for why that watchpoint could not be held

If the retained log only repeats:

- source xy `[1603.8396,844.3175]`
- near-black sampled RGBA
- final white output

then the retry is not decision-advancing.

## 2. OLMDistanceGradation

Package:

- `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`

What was still missing in the latest return:

- `r8` at `FUN_181170480`
- `r9` at `FUN_181170480`
- `[rsp+0x28]` at `FUN_181170480`
- surrounding qwords/dwords needed to infer width / stride / current output pointer
- recovered triplet output-word mapping for `(414,393)`, `(415,393)`, `(416,393)`
- held watchpoint on one of the triplet `RGBA16` output word ranges

What the next retained log must contain:

1. `FUN_181170480` stop with `r8`, `r9`, `[rsp+0x28]`
2. nearby qwords/dwords sufficient to infer width, stride, and current output pointer
3. recovered mapping for at least one triplet pixel
4. either:
   - a bound watchpoint on the triplet output-word range with consumed helper/compose values
   - or the exact failure reason for why the mapping/watchpoint could not be held

If the retained log only repeats:

- the 35.014 -> 36.013 -> 37.013 crossing
- final endpoint colors
- a generic "refcon not isolated" note

then the retry is not decision-advancing.

## Operational consequence

If Windows-side tooling cannot retain these register/pointer windows reliably,
the next improvement must happen in the execution method, not in Mac-side image
tuning and not by merely renaming the request package.
