# Forecast-First Porting Policy

This note records how to make progress before new Windows PNG/runtime trace
returns arrive.

The goal is to reduce round trips by using official manuals, local UI strings,
Ghidra/objdump, and existing references to form a constrained implementation
hypothesis. This does not lower the correctness bar: final completion is still
`AE exact` only, as defined in `notes/AE_EXACT_CONFORMANCE.md`.

## Why This Exists

Input/output PNGs are necessary but expensive. Waiting for every new PNG before
thinking can stall the port, while tuning only from PNG diffs can overfit the
wrong behavior.

Use forecast-first work for the middle layer:

1. Read product intent and parameter meaning.
2. Predict the feature slices and likely primitive family.
3. Confirm as much as possible from binary evidence.
4. Implement only the parts whose behavior is constrained enough to test.
5. Use future PNG/runtime returns to validate or reject the prediction.

## Evidence Order

Prefer evidence in this order:

1. Windows AEX binary facts: Ghidra decomp, objdump, constants, calls, branches,
   runtime traces.
2. Official OLM manuals and site wording under `refs/upstream_official/`.
3. Local AE/mac source strings, PiPL metadata, match names, parameter disk IDs.
4. Existing Windows Software references and manifests.
5. PNG diffs and probes.

PNG diffs are symptoms. Binary facts explain causes. Official manuals explain
what the user-facing feature is supposed to mean.

## What Forecast Work May Do

Allowed before new Windows returns:

- Build or update binary-grounded IR notes.
- Split a plugin into feature slices.
- Map UI parameters to internal fields and likely code paths.
- Locate constants, tables, helper functions, and library primitive calls.
- Implement narrow branches when the manual and binary both constrain the rule.
- Add diagnostic probes and smoke tests that make the hypothesis falsifiable.
- Improve dashboards, ledgers, and handoff docs to show the current evidence.

Do not claim completion from forecast work.

## What Forecast Work Must Not Do

Do not:

- Promote a slice to `AE exact`.
- Tune arbitrary constants until a PNG diff looks smaller.
- Hide a residual behind tolerance unless it is explicitly marked `guarded`.
- Rewrite a broad plugin path based only on product wording.
- Add Rust parity for an algorithm whose C++/CLI behavior is still unstable.
- Treat official manual language as proof of rounding, loop bounds, or border
  behavior.

If a change improves PNG diff but contradicts known binary evidence, keep it as
an experiment only and do not promote it.

## Feature Slice Workflow

For each plugin or feature slice:

1. Start from `notes/PLUGIN_INTENT_MAP.md`.
2. Create or update an IR note from `notes/BINARY_GROUNDED_IR_TEMPLATE.md`.
3. Record the official intent:
   - what the effect does,
   - which pixels/channels it acts on,
   - which parameters select modes,
   - which modes should become separate test cases.
4. Record binary facts:
   - parameter normalization,
   - constants and tables,
   - branch conditions,
   - loop bounds,
   - sampling order,
   - boundary behavior,
   - writeback and rounding.
5. Mark each rule as one of:
   - `proved`: binary/runtime evidence exists,
   - `manual-backed`: official manual constrains the high-level behavior,
   - `inferred`: likely but not proven,
   - `unknown`: needs trace/PNG/asm work.
6. Implement only `proved` and low-risk `manual-backed` rules by default.
7. Add smoke/probe output that can disprove the inference later.
8. Update `notes/CONFORMANCE_LEDGER.md` with the next required proof.

## When To Request More Windows Evidence

Stop and request Windows evidence when:

- Two or more plausible binary-consistent implementations remain.
- A residual depends on rounding, SIMD/library primitive behavior, or exact
  border sampling.
- PNG improvement requires a constant or branch not seen in the AEX.
- The feature depends on AE host behavior that CLI cannot model.
- The slice is ready for an `AE exact` claim.

Prefer a small diagnostic package over another broad random PNG set. The best
request distinguishes specific hypotheses.

## Current Forecast Targets

These can be advanced without waiting for more returned PNGs:

- `OLMBlur`: use official `alpha > 0` behavior and existing binary constants to
  narrow the repeat/writeback residual; do not replace the current shim until the
  accumulation/order rule is grounded.
- `OLMColorKey`: split core keying from Edge Thin/Edge Blur. Core color-space
  and replace behavior can be documented separately; Edge residual needs
  distance/matte shell proof.
- `OLMToonDilate`: document the propagation/dilation IR from the now exact
  normalized CLI behavior; prepare Mac AE exact validation cases.
- `OLMDistanceGradation`: use the official inside/outside alpha-mask model and
  blur-mode descriptions to audit distance normalization and blur branches.
- `OLMSmoother2`: use the official v1/v2 gamma note to reduce the search space;
  avoid treating v1/v2 as entirely separate algorithms without evidence.
- `OLMDirectionalBlur`: use the official opaque-pixel-group and noise-mode
  wording to guide connected-component/noise-path IR before implementation.
- `OLMRadialBlur`: use the official outer/inner direction definitions,
  repeat-border branch, ellipse transform, and quality parameter to refine the
  Inner IR before further tuning.
- `OLMKiraKira`: use the official channel and blur-mode names to pin the
  pipeline shape; focus binary work on exact OpenCV/filter primitive behavior.

## Naming And Reporting

Use these words carefully:

- `forecast`: a constrained prediction awaiting proof.
- `manual-backed`: supported by official docs, not exactness proof.
- `binary-grounded`: supported by AEX/asm/runtime evidence.
- `CLI exact`: useful intermediate state.
- `AE exact`: only final completion state.

Avoid percentage progress and avoid calling a plugin "done" unless the relevant
feature/bit-depth slice is `AE exact`.
