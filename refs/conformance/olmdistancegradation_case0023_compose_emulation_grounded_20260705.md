# OLMDistanceGradation case_0023 — compose stage binary-grounded by local emulation (2026-07-05)

## What changed

The Windows debugger route for this witness family failed the xy-binding step
three times (see `olmdistancegradation_case0023_refcon_stack_wordmap_intake_20260705.md`).
Local Unicorn emulation of the CPU `.aex` bypassed that blocker entirely.

`tools/emulation/test_dg_compose.py` drives `FUN_181170480` (the 16bpc iterate
compose+word-store callback) directly, with a hand-built refcon, at the witness
triplet. Report: `tools/emulation/DG_STRATEGY_A_REPORT.md`.

## Result (binary-grounded, no Windows round-trip)

- Leaf sanity (degenerate use_bg branch) PASSED, confirming the harness's stack
  arg5 (output pixel pointer, `[RSP+0xd0]`) placement is correct.
- All three witness pixels reproduce the Windows final RGBA16 **exactly**:
  - `(414,393)` field_x=0.0 → raw (3598,0,30583,32768) → promoted (7195,0,61165,65535) = Windows exact
  - `(415,393)` field_x=1.0 → (32768,0,0,32768) → (65535,0,0,65535) = Windows exact
  - `(416,393)` field_x=1.0 → same = Windows exact

## Facts established

- **In-memory 16-bit word order is A(+0), G(+2), R(+4), B(+6)** (corrects the
  earlier A,R,G,B guess in `DG_M1_NOTES.md`), verified operand-by-operand in the
  degenerate and normal compose branches.
- **Promotion AE-16 → full-16 is `trunc(half_word / 32768 * 65535)`**, not `×2`.
  Naive ×2 gives +1 errors on the non-endpoint pixel (7196 vs 7195). This matches
  AE's `PF_MAX_CHAN16 = 32768` convention. Empirically re-derived from 3 points;
  promotion happens host-side, outside `FUN_181170480`.
- The endpoint selection (Gradation color vs BG color) is fully explained by
  `field_x` (0/1), `Invert=0`'s `1-X` flip, Linear pass-through, and the use_bg
  blend — all inside the compose callback.

## Lane-state implication

**The compose stage is no longer the live lane for case_0023.** The remaining
residual (per `notes/IR_OLMDistanceGradation.md`: 73px = 65px at `inside=1.0` +
8px at the threshold crossing) is NOT a compose-stage bug — given the same
`field_x`, compose already produces the Windows bytes. The divergence is upstream
in **field generation**: `distanceTransform → threshold → normalize` in
`FUN_181174760`, which decides the binary `field_x` (0/1) fed to compose.

## Caveats (do not over-claim)

- The `field_x` values (0.0/1.0) injected into this run were INFERRED from the
  recorded "crosses Inside Threshold=36" fact, not read from a live field buffer.
  Field generation still needs its own emulation grounding pass.
- Promotion formula validated on 3 points only; mid-range/rounding-boundary
  generality unconfirmed.
- 8bpc sibling `FUN_181170870` and Sphere/Power interp modes not exercised
  (case_0023 is Linear/Gradation only).

## Next

Drive `FUN_181174760` (field generation) in emulation for case_0023 to obtain the
Windows ground-truth `field_x` at the 73 residual pixels, then compare against the
Mac port's field values there. That localizes the exact upstream divergence
without a Windows trip. Threshold-family stays provenance/export-first for the Mac
build; this is binary-grounding of the field decision, not PNG-mean retuning.
