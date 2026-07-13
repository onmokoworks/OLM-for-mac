# OLMDistanceGradation OpenCV Detour P1 Report - 2026-07-12

Scope: `tools/emulation/` P1 harness only. The plugin binary is unchanged.
The detour target is DistanceGradation `FUN_1812b15a0`, observed as:

`cvDistTransform(src_8u, dst_32f, DIST_L2, DIST_MASK_PRECISE, 0, 0, 0)`

## FACT

- The native implementation is the numpy two-pass exact EDT in
  `tools/emulation/opencv_impls.py`.
- The independent oracle is the local sidecar `cv2 4.5.5` with `numpy 1.26.4`.
- The P1-only harness covers the existing geometric/degenerate cases, five
  deterministic random masks, padded `widthStep`, and the `src uint8 -> dst
  float32` contract.
- The contract gate explicitly rejects non-P1 `distance_type`, `mask_size`,
  non-null `mask`, non-null `labels`, non-zero `labelType`, and a non-float32
  destination.
- Verification command:

  ```bash
  tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py --p1-only
  ```

- Verification result: 16/16 P1 rows passed. Every comparison reported
  `native_exact=True`, `cv455_exact=True`, and `max_abs=0`; all six unsupported
  contract branches were rejected.

## INFERENCE

- The current P1 implementation is suitable for the observed DG fieldgen
  detour shape as a local acceleration harness.
- This does not establish full DistanceGradation conformance, Windows CPU
  equivalence for unrelated SIMD operations, or correctness for other
  `cvDistTransform` modes.
- The all-foreground sentinel is covered by the sidecar oracle, but the
  implementation remains bounded to the OpenCV 4.5.5 precise-L2 behavior and
  should be revalidated if the linked OpenCV version changes.

## Full command output

```text
AEX: /Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/DistanceGradation.aex
cvDistTransform @ 0x1812b15a0
[PASS] detour dist_transform/single_zero      instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/cross            instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/box              instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/diagonal         instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/all_nonzero      instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/all_zero         instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_one_zero  instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_one_nonzero instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_n         instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/n_by_one         instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/random_4101 shape=(2, 2) instr=3 header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/random_4102 shape=(5, 7) instr=3 header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/random_4103 shape=(31, 29) instr=3 header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/random_4104 shape=(3, 64) instr=3 header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/random_4105 shape=(64, 3) instr=3 header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/contract       good_path=True rejected=bad_dst,dist_type,mask_size,mask,labels,label_type/6
RESULT: P1 native EDT + cv455 oracle PASS
```
