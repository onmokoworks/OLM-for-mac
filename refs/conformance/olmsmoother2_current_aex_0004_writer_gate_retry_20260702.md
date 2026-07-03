# OLMSmoother2 Current-AEX 0004 Writer-Gate Retry

Date: `2026-07-02`

This retry exists because the broad producer-path diff proved reachability of:

- `+0xc280`
- `+0xcce0`
- `+0x350b`
- `+0x3610`

but produced a hit storm before the witness-local producer values for
`legacy_case_0004_current_aex` were retained.

## Target

- case: `legacy_case_0004_current_aex`
- witness xy: `(1903,519)`
- reference RGBA: `[103,103,103,113]`
- local candidate RGBA: `[0,0,0,0]`

## Required strategy

Do not start with unconditioned broad breakpoints.

1. Use the current-AEX writer anchor to bind the exact output address or exact
   writer-frame xy for `(1903,519)`.
2. Only after that exact writer hit is confirmed, step or one-shot-break into
   the corresponding `+0x350b -> +0x3510` call path for the same frame.
3. From that exact frame, capture the first unresolved producer facts.

## Required facts

- c280 switch index at the exact witness frame
- polygon vertex count before `bb10/b120`
- helper append source xy / rgba / weight, or proof of no append
- cce0 output floats before final u8 packing

## Rejected non-answers

- broad `+0xc280/+0xcce0/+0x350b/+0x3610` hits without witness-local gating
- known writer-anchor bytes/floats only
- generic “hit storm” prose without the exact gated condition attempted
