# OLMDistanceGradation 8bpc Current-Binary Reconstruction Classification

Date: 2026-07-12

## Verdict

`known-red / no defensible 8bpc code fix identified`

The current Mac binary-grounded reconstruction remains `0/29 AE exact` for
the depth-correct 8bpc batch. This pass does not change the production
implementation. The current evidence validates the shared field and compose
primitives, but does not isolate a binary-supported 8bpc field, compose, or
host-write rule that can explain the complete residual family.

The historical `29/29` artifact is explicitly excluded as proof. It has no
loaded Mac plug-in hash; two retained June 18 binaries fail fresh reruns.

## FACT

- The latest ledger override is the authority for this status:
  `notes/CONFORMANCE_LEDGER.md`, 2026-07-11 `OLMDistanceGradation
  OpenCV/PF16 boundary`.
- The referenced boundary report records a depth-correct current-binary AE
  batch of `0/29` exact, using `comp.bpc` fallback in both JSX runners.
- The installed/current result matrix is recorded in
  `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json`.
  Its 8bpc groups are basic `0/12`, extended `0/16`, and blur `0/1`.
- Current 8bpc residuals are not a single rounding edge. Representative
  maxima are `case_0001=2`, `case_0005=6`, `case_0015=64`,
  `case_0008=254`, `case_0012=250`, `case_0023=238`, and
  `case_0029=23`.
- The current source keeps the PF16 OpenCV/PF16 field-world roundtrip
  depth-limited to `PF_Pixel16`; the 8bpc and float paths are intentionally
  unchanged. See `mac/OLMDistanceGradation/OLMDistanceGradation.cpp` lines
  570-582.
- The current source's 8bpc source-mask rule is `alpha > 0`, while the
  deeper-depth rule excludes the 1-code fringe. See
  `mac/OLMDistanceGradation/OLMDistanceGradation.cpp` lines 378-392.
- The standalone DG core distance stage passes all `286` checked values.
  This is a local primitive/fixture result, not AE exactness.
- The local compose emulation passes its leaf and case_0023 triplet checks.
  Its own report states that the injected triplet field values are assumed
  and that 8bpc sibling branches were not verified by that run.
- The direct current AEX field-generation probe completes and reaches the
  expected OpenCV detours: one distance transform, one threshold, one
  normalize, and two resize/convert callbacks.
- The universal Debug plug-in build succeeds for `x86_64` and `arm64`.

## INFERENCE

- The broad, depth-correct 8bpc failure family cannot defensibly be repaired
  by applying the proven PF16 reciprocal-scale/PF16-rounding boundary to
  8bpc. That boundary is directly scoped to PF16 evidence and would be an
  unsupported cross-depth inference.
- The primitive gates show that the current field and compose ports are
  executable and internally consistent for their covered contracts, but the
  8bpc AE residuals leave ownership unresolved among field staging, 8bpc
  compose branches, and host export/writeback.
- PNG-derived pixel tuning, the historical 29/29 artifact, and broad
  8bpc rule changes would therefore be evidence-invalid. The next useful
  step requires a hash-pinned current-AEX 8bpc same-run witness that exposes
  typed field input, compose input/output, and final host stores at a shared
  address/coordinate boundary.

## Commands And Results

All commands were run from the repository root:

```text
clang++ -std=c++17 -O2 -Wall -Wextra -I. core/olmdistancegradation_fieldgen.cpp tools/emulation/test_dg_core_distance_stage.cpp -o /tmp/olmdg_core_distance_stage && /tmp/olmdg_core_distance_stage
DG core distance stage: PASS (286 values)

python3 tools/emulation/test_dg_compose.py
exit 0; local Strategy-A compose leaf and case_0023 triplet checks PASS

python3 tools/emulation/test_dg_fieldgen_p1b.py
exit 0; status=completed; callbacks=dist_transform:1, threshold:1, normalize_minmax:1, resize_same_shape:2

xcodebuild -project mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj -scheme OLMDistanceGradation -configuration Debug -sdk macosx ARCHS='x86_64 arm64' ONLY_ACTIVE_ARCH=NO build
** BUILD SUCCEEDED **
```

The AE comparison result used by this classification is the existing,
hash-recorded JSON report named above; no new PNG oracle or historical
29/29 candidate was used.

## Changed Files

- `refs/conformance/olmdistancegradation_8bpc_current_binary_reconstruction_20260712.md`

No production source, ledger, or unrelated worktree file was changed.
