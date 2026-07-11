# Audit Request: DG Fieldgen P1C

Date: 2026-07-07

Please audit Codex's P1C DistanceGradation AEX CPU emulation work.

## Scope

This milestone adds a narrow `resize_same_shape` detour and a small synthetic
direct-call probe for `FUN_181174760`.

This is not a claim that `OLMDistanceGradation case_0023` is solved.

## Changed Files To Inspect

- `tools/emulation/opencv_impls.py`
- `tools/emulation/test_opencv_detour.py`
- `tools/emulation/test_dg_fieldgen_p1b.py`
- `tools/emulation/OPENCV_DETOUR_DESIGN.md`
- `tools/emulation/OPENCV_DETOUR_P1_REPORT.md`
- `tools/emulation/DG_FIELDGEN_P1B_INTEGRATION_STATUS_20260707.md`
- `tools/emulation/OPENCV_DETOUR_P1C_TEST_OUTPUT_20260707.txt`
- `tools/emulation/DG_FIELDGEN_P1C_RUN_OUTPUT_20260707.json`

## FACTS Claimed

- FACT: `resize_same_shape` detours `FUN_1812aef70` only when source and
  destination have identical shape and dtype.
- FACT: `test_opencv_detour.py` passes three same-shape copy cases:
  `uint8 (11,17) interp=0`, `float32 (11,17) interp=1`, and
  `uint8 (7,9,3) interp=0`.
- FACT: `test_dg_fieldgen_p1b.py` directly calls `FUN_181174760` with a small
  synthetic mask and completes.
- FACT: The completed run records:
  - `cv::resize_same_shape`: 2
  - `cv::dist_transform`: 1
  - `cv::threshold`: 1
  - reached hooks: `FUN_1812aef70`, `FUN_1812aef70`, `FUN_18117ca50`

## INFERENCES Claimed

- INFERENCE: The local AEX CPU emulation harness can now drive the binary
  DistanceGradation field-generation path through the validated primitive
  detours on a small synthetic mask.
- INFERENCE: The next useful local step is a case-bound fieldgen probe using a
  case_0023 mask/crop and independently known witness coordinates.
- INFERENCE: P1C must not be promoted to general `cvResize`; downsample/upscale
  or interpolation behavior requires a separate gate.

## Verification Commands

```bash
tools/emulation/.venv/bin/python -m py_compile \
  tools/emulation/opencv_impls.py \
  tools/emulation/sidecar_oracle.py \
  tools/emulation/test_opencv_detour.py \
  tools/emulation/test_dg_fieldgen_p1b.py

tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py
```

## Expected Evidence

`test_opencv_detour.py` should end with:

```text
[PASS] detour resize_same_shape/uint8/(11, 17)     instr=3 bypassed=True copy_exact=True header_intact=True interp=0
[PASS] detour resize_same_shape/float32/(11, 17)   instr=3 bypassed=True copy_exact=True header_intact=True interp=1
[PASS] detour resize_same_shape/uint8/(7, 9, 3)    instr=3 bypassed=True copy_exact=True header_intact=True interp=0
RESULT: all detour + bridge gates PASS (GATE A+B). GATE C blocked as documented.
```

`test_dg_fieldgen_p1b.py` should report:

```json
{
  "status": "completed",
  "function": "0x181174760",
  "instructions": 11443,
  "callback_counts": {
    "cv::resize_same_shape": 2,
    "cv::dist_transform": 1,
    "cv::threshold": 1
  }
}
```

## Questions For Audit

1. Is the P1C same-shape copy detour appropriately scoped and guarded?
2. Does the DG fieldgen probe actually exercise `FUN_181174760` rather than
   bypassing the plugin logic?
3. Are the non-claims strong enough to prevent accidental case_0023 promotion?
4. What is the safest next case-bound probe shape?
