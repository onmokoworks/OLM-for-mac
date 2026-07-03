# Smoother2 / DirectionalBlur Runtime Retry Contract

Date: `2026-07-02`

This note exists because the latest Windows returns for:

- `olmsmoother2_current_aex_producer_path_diff_20260702`
- `olmdirectionalblur_witness_logging_prep_20260702`

were both `failed_partial`, but in the same specific way:

- the return restated already-known retained evidence
- no new producer-stage or per-pixel witness trace was captured

That means the next retry must be judged primarily by whether it contains a
new debugger/runtime capture, not by whether a return JSON exists.

2026-07-02 late retry update:

- `OLMSmoother2` did produce a fresh CDB pass. `+0xc280`, `+0xcce0`, `+0x350b`,
  and `+0x3610` are all reachable in the current AE run.
- `OLMDirectionalBlur` also produced a fresh CDB pass. The module does load,
  and broad `+0x2000` hits are reachable in a valid Software render.
- So the old “maybe it did not even run” uncertainty is gone.
- The current blocker for both lanes is now narrower: broad breakpoints fire
  too often, creating hit storms before the requested witness-local condition
  can be held.

## 1. OLMSmoother2 current-AEX producer-path diff

Current bad outcome:

- a fresh run did happen, and `+0xc280`, `+0xcce0`, `+0x350b`, `+0x3610` were
  all reachable
- but the run stayed broad and hit-stormed before witness-local producer facts
  were retained
- no new c280 / cce0 / cardinal6 / e170 / f270 / e3a0 producer evidence was captured

Minimum useful retry:

1. a fresh debugger pass anchored from the writer frame
2. witness gating must happen before the broad hit storm expands
3. at least one new producer-stage fact for one active lane:
   - `0004`: c280 switch index, polygon count, helper append fact, or cce0 fallback fact
   - `0012`: cardinal6 descriptor/key, e170 bits/code, f270/e3a0 append-no-append fact
4. if the exact callsite still cannot be held:
   - the exact failed breakpoint/watchpoint condition
   - the closest writer-anchored frame that still preserves producer inputs

Rejected as non-answer:

- known final writer bytes only
- known writer-anchor floats only
- prose saying producer stage was not isolated without a fresh failed condition
- another broad `+0xc280/+0xcce0/+0x350b/+0x3610` rerun without witness-local gating

## 2. OLMDirectionalBlur witness logging prep

Current bad outcome:

- a fresh run did happen, and the module does load
- broad `+0x2000` hits are reachable in a valid Software render
- but no witness-local denominator / `alpha_or_valid` / pre-writeback record was captured
- none of the required typed witness fields were captured

Minimum useful retry:

1. prove the module loads and the intended breakpoint/watchpoint can actually bind
2. move off broad `+0x2000` entry-style hits and onto a narrower witness-local stage
3. at least one lane returns a same-record witness with:
   - denominator
   - `alpha_or_valid` or equivalent validity value
   - pre-writeback RGBA
4. plus lane-specific evidence:
   - angle-0: helper-local touched destination x range for `(494,169)` and `(579,169)`
   - diagonal: rotate sampler source coordinates/order and border-validity decision

Rejected as non-answer:

- final bytes only
- broad PNG restatement
- retained contract/prose rewritten into JSON
- “module not loaded” without exact bind/load failure details
- another broad `+0x2000` hit storm without witness-local typed fields

## Operational rule

For these two lanes, a new return is useful only if it contains either:

- fresh typed witness values
- or a fresh exact failed breakpoint/watchpoint or module-load condition

Anything else should be treated as retry failure, not partial analytical progress.
