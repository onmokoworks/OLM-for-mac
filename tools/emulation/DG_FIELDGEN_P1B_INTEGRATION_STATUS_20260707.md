# DG Fieldgen P1C Integration Status - 2026-07-07

## Verdict

`FUN_181174760` now completes on a small synthetic DistanceGradation fieldgen
probe under AEX CPU emulation. This is a local runner milestone, not a
case_0023 conformance claim.

## FACTS

- `tools/emulation/test_opencv_detour.py` now validates the OpenCV detours used
  by the current DistanceGradation field-prep probe:
  - `cvThreshold` at `0x1812b6a40`
  - `cvDistTransform` at `0x1812b15a0`
  - limited same-shape `FUN_1812aef70` copy detour at `0x1812aef70`
- P1B `cvDistTransform` matches sidecar OpenCV 4.5.5 for ten masks, including
  the previously failing all-foreground case and padded `float32` destination
  rows. Full output:
  `tools/emulation/OPENCV_DETOUR_P1B_TEST_OUTPUT_20260707.txt`
- P1C `resize_same_shape` is intentionally narrow: it only copies when source
  and destination have identical shape and dtype. It does not claim general
  `cvResize` compatibility.
- The existing local DG emulation runner, `tools/emulation/test_dg_compose.py`,
  drives `FUN_181170480` compose/writeback leaf-style. It injects field words;
  it does not build the upstream field by calling `FUN_181174760`.
- The new local DG fieldgen runner, `tools/emulation/test_dg_fieldgen_p1b.py`,
  directly calls `FUN_181174760` with a small synthetic mask and validated
  detours registered.
- Latest run output:
  `tools/emulation/DG_FIELDGEN_P1C_RUN_OUTPUT_20260707.json`
  - status: `completed`
  - instructions: `11443`
  - callbacks: `cv::resize_same_shape` x2, `cv::dist_transform` x1,
    `cv::threshold` x1
  - reached hooks: `FUN_1812aef70`, `FUN_1812aef70`, `FUN_18117ca50`
  - output range: `0.0..1.0`
- `tools/emulation/DG_FIELD_GEN_REPORT.md` identifies `FUN_181174760` as the
  upstream field-generation path and records the sequence:
  working buffers -> `cvDistTransform` -> convert/resize-like stage ->
  `cvThreshold` -> normalize/write field.

## INFERENCES

- The next local step is to replace the synthetic mask with a case_0023-shaped
  witness mask or a cropped witness mask whose expected field values are
  independently known.
- The remaining risk is not the small-run control flow. It is whether the
  synthetic runner's input staging, downsample dimensions, and threshold
  arguments match the real AE case_0023 path.

## Next Concrete Step

Create a case-bound `test_dg_fieldgen_case0023_probe.py` or extend the runner
behind explicit flags so it can:

1. Build the relevant case_0023 input mask/crop.
2. Pass the actual threshold/interpolation arguments observed for the case.
3. Compare emitted field values at the known threshold-family and edge-family
   witness pixels against the existing Windows/Mac evidence.
4. Keep reporting control-flow callbacks and detour counts so a passing output
   cannot hide an accidentally bypassed binary stage.

## Non-Claims

- This does not prove DistanceGradation `case_0023`.
- This does not replace the current Windows Send First request:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`
- This does not authorize Mac source changes for the 65px family; that lane is
  still `reference-path-split-or-upstream-field-ownership`.
