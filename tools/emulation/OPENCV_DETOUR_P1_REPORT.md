# OpenCV Detour P1/P1C/P2 Report

Date: 2026-07-07

Scope:

- `cvDistTransform` detour for DistanceGradation (`FUN_1812b15a0`) on the
  observed call shape `cvDistTransform(src_8u, dst_32f, 2, 0, 0, 0, 0)`.
- P1C limited same-shape copy detour for `FUN_1812aef70`, used only for the two
  no-resize staging calls in the small DG fieldgen probe.
- P2 limited `cvNormalize` / `NORM_MINMAX` detour for `FUN_18117ca50`, used by
  DistanceGradation fieldgen writeback normalization.

## Verdict

P1 primitive gate: P1B PASS after audit fix.
P1C same-shape copy gate: PASS.
P2 normalize-minmax gate: PASS for the observed no-mask float32 path.

This means the native detour for `DIST_L2 + DIST_MASK_PRECISE`:

- fires under Unicorn through the detour stub,
- writes the destination IplImage without changing the header,
- matches the native OpenCV-exact EDT implementation in this detour,
- and matches sidecar OpenCV 4.5.5 `cv2.distanceTransform(..., DIST_L2, DIST_MASK_PRECISE)` bit-for-bit on the checked masks.

Audit note: the first P1 report was too strong. A subagent audit found that
the initial `inf = w + h` sentinel failed the all-foreground / no-zero-source
case (`3x4` all `255`: native `7.0`, OpenCV 4.5.5 `31622776.0`). P1B replaces
the sentinel with the OpenCV 4.5.5 precise-L2 all-foreground value and adds
that case plus all-zero and 1D/1x1 shape coverage.

This is not yet a claim that DistanceGradation `case_0023` is solved. The first
DG fieldgen probe now registers `threshold`, `dist_transform`, and
`resize_same_shape`, then completes a small synthetic `FUN_181174760` run. The
later P2 update also registers `normalize_minmax`, making the direct fieldgen
probe fast enough for full-frame case_0023 inside/outside witness runs. That is
still a field-helper witness, not whole-plugin AE exact.

## Changed Files

- `tools/emulation/opencv_impls.py`
  - added `CV_DIST_TRANSFORM_ADDR`
  - added `cvdisttransform_l2_precise_native`
  - added `dist_transform` detour registration
  - added limited `CV_NORMALIZE_ADDR` / `cvnormalize_minmax_native`
- `tools/emulation/sidecar_oracle.py`
  - added `distance_transform_l2_precise` operation for sidecar OpenCV 4.5.5
  - added `normalize_minmax` operation for sidecar OpenCV 4.5.5
- `tools/emulation/test_opencv_detour.py`
  - added P1 `cvDistTransform` detour tests
  - added P1C limited same-shape `FUN_1812aef70` copy tests
  - added P2 limited `FUN_18117ca50` normalize tests
- `tools/emulation/test_dg_fieldgen_p1b.py`
  - added a small direct-call `FUN_181174760` fieldgen probe
  - added real-PNG mask/crop/point sampling, mask inversion, and
    `normalize_minmax` registration for full-frame case probes

## FACTS

- FACT: DistanceGradation calls `FUN_1812b15a0(local_48[0], local_88[0], 2, 0, 0, 0, 0)` in `FUN_181174760`.
  Evidence: `decomp/DistanceGradation.aex.c.txt` around `FUN_181174760`.
- FACT: The detour seam passes IplImage pointers.
  Evidence: `tools/emulation/OPENCV_DETOUR_DESIGN.md` rev 2 and existing P0 bridge tests.
- FACT: The source and destination dtypes differ for this op: source is single-channel `uint8`, destination is single-channel `float32`.
  Evidence: decomp call allocates `local_48` as depth `8` and `local_88` as depth `0x20`.
- FACT: The P1B detour test passes against sidecar OpenCV 4.5.5 on ten mask
  families: `single_zero`, `cross`, `box`, `diagonal`, `all_nonzero`,
  `all_zero`, `one_by_one_zero`, `one_by_one_nonzero`, `one_by_n`, and
  `n_by_one`.
- FACT: The P1C `resize_same_shape` detour passes three same-shape copy tests:
  `uint8 (11,17) interp=0`, `float32 (11,17) interp=1`, and
  `uint8 (7,9,3) interp=0`.
- FACT: `tools/emulation/test_dg_fieldgen_p1b.py` completes a small synthetic
  `FUN_181174760` run and records `cv::resize_same_shape` x2,
  `cv::dist_transform` x1, `cv::threshold` x1, and after P2
  `cv::normalize_minmax` x1.
- FACT: `FUN_18117ca50` receives `alpha=0`, `beta=bitdepth max`,
  `norm_type=0x20`, `mask=0` in the `FUN_181174760` fieldgen path.
  Evidence: `disasm/DistanceGradation.aex.asm.txt` around `18117490b..181174942`.
- FACT: the P2 normalize detour matches sidecar OpenCV 4.5.5 exactly on four
  cases: `ramp`, `binary`, `constant_zero`, and `constant_nonzero`.
- FACT: the full-frame `case_0023` AEX CPU fieldgen probe completes both inside
  and outside passes. At `(1699,7)`, inside field is `0.0`, outside field is
  `0.0`, and sampled Both-add-saturate field is `0.0`. Evidence:
  `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`.

## INFERENCES

- INFERENCE: For observed DG frames with at least one zero-source pixel, the
  Meijster-style EDT and OpenCV precise L2 EDT should agree bit-for-bit because
  squared distances stay below the float32 exact-integer bound described in
  `OPENCV_DETOUR_DESIGN.md`. For all-foreground input, the detour intentionally
  follows OpenCV 4.5.5 sentinel behavior rather than the Mac port's former
  image-size sentinel.
- INFERENCE: This detour should make DG field-generation emulation materially faster, but that speedup is not yet measured in the full DG witness runner.
- INFERENCE: P1C is sufficient for the observed same-shape staging calls in the
  synthetic DG probe. It is not a general resize implementation and must not be
  used for downsample/upscale lanes without separate validation.
- INFERENCE: The full-frame `case_0023` fieldgen witness strengthens the
  reference-path split classification for the 65px edge family: the Windows CPU
  AEX helper itself produces the Mac-side field value at `(1699,7)`, while the
  older/reference PNG expects the opposite endpoint after compose.

## Verification Command

```bash
tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
```

## Verification Output

Full current P1C output is archived in:

`tools/emulation/OPENCV_DETOUR_P2_NORMALIZE_TEST_OUTPUT_20260707.txt`

Earlier P1C output is archived in:

`tools/emulation/OPENCV_DETOUR_P1C_TEST_OUTPUT_20260707.txt`

Earlier P1B output is archived in:

`tools/emulation/OPENCV_DETOUR_P1B_TEST_OUTPUT_20260707.txt`

```text
[PASS] detour dist_transform/single_zero  instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/cross        instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/box          instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/diagonal     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0
[PASS] detour dist_transform/all_nonzero  instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/all_zero     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_one_zero instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_one_nonzero instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_n     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/n_by_one     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16

[PASS] detour resize_same_shape/uint8/(11, 17)     instr=3 bypassed=True copy_exact=True header_intact=True interp=0
[PASS] detour resize_same_shape/float32/(11, 17)   instr=3 bypassed=True copy_exact=True header_intact=True interp=1
[PASS] detour resize_same_shape/uint8/(7, 9, 3)    instr=3 bypassed=True copy_exact=True header_intact=True interp=0

[PASS] detour normalize_minmax/ramp             instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 beta=32768
[PASS] detour normalize_minmax/binary           instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 beta=32768
[PASS] detour normalize_minmax/constant_zero    instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 beta=32768
[PASS] detour normalize_minmax/constant_nonzero instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 beta=255

[GATE C BLOCKED] emulated-equivalence: emulated path faults at RIP=0x181187e41 (OpenCV static-init not scaffolded)
            (expected: exact-reference GATE B is authoritative for threshold; GATE C is the gold gate reserved for float ops / P3)

RESULT: all detour + bridge gates PASS (GATE A+B). GATE C blocked as documented.
```
