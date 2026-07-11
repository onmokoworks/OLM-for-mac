# Audit Request: OpenCV Detour P1B

Date: 2026-07-07

Please audit Codex's P1B `cvDistTransform` detour work.

P1 was first rejected by subagent audit because the all-foreground / no-zero
source case did not match OpenCV 4.5.5. P1B fixes that sentinel behavior and
adds the missing edge cases to the detour suite.

## Scope

P1 implements a native detour for DistanceGradation's OpenCV C-API entry:

- `FUN_1812b15a0`
- observed call shape: `cvDistTransform(src_8u, dst_32f, 2, 0, 0, 0, 0)`
- intended OpenCV meaning: `DIST_L2 + DIST_MASK_PRECISE`

This is a primitive/detour gate only. It is not a claim that
OLMDistanceGradation `case_0023` is fixed.

## Changed Files To Inspect

- `tools/emulation/opencv_impls.py`
- `tools/emulation/sidecar_oracle.py`
- `tools/emulation/test_opencv_detour.py`
- `tools/emulation/OPENCV_DETOUR_P1_REPORT.md`
- `tools/emulation/OPENCV_DETOUR_P1B_TEST_OUTPUT_20260707.txt`
- `.gitignore`

## Context Files

- `tools/emulation/OPENCV_DETOUR_DESIGN.md`
- `tools/emulation/GOTCHAS.md`
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `decomp/DistanceGradation.aex.c.txt` around `FUN_181174760`

## FACTS Claimed

- FACT: `FUN_181174760` calls `FUN_1812b15a0(local_48[0], local_88[0], 2, 0, 0, 0, 0)`.
- FACT: The detour seam uses IplImage pointers.
- FACT: This op has different src/dst types: `src` is single-channel `uint8`, `dst` is single-channel `float32`.
- FACT: The P1B detour test passes against sidecar OpenCV 4.5.5 for ten mask families, including the previously failing `all_nonzero` case.

## INFERENCES Claimed

- INFERENCE: For current DG frame sizes, the OpenCV-exact detour should match OpenCV precise L2 EDT bit-for-bit because squared distances stay within the float32 exact-integer range and the OpenCV all-foreground sentinel is now explicitly covered.
- INFERENCE: This should speed up DG field-generation emulation, but full witness-runner speedup has not been measured.

## Verification Command

```bash
tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
```

Expected terminal ending:

```text
[PASS] detour dist_transform/single_zero  instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/cross        instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/box          instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/diagonal     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/all_nonzero  instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/all_zero     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_one_zero instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_one_nonzero instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=4
[PASS] detour dist_transform/one_by_n     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16
[PASS] detour dist_transform/n_by_one     instr=3 bypassed=True written=True header_intact=True native_exact=True cv455_exact=True max_abs=0 align_step=16

[GATE C BLOCKED] emulated-equivalence: emulated path faults at RIP=0x181187e41 (OpenCV static-init not scaffolded)
            (expected: exact-reference GATE B is authoritative for threshold; GATE C is the gold gate reserved for float ops / P3)

RESULT: all detour + bridge gates PASS (GATE A+B). GATE C blocked as documented.
```

## Questions For Audit

1. Does the numpy OpenCV-exact EDT implementation faithfully cover P1B, including the all-foreground sentinel?
2. Is sidecar OpenCV 4.5.5 a valid independent oracle for this exact integer/EDT op?
3. Are the ABI assumptions correct for `cvDistTransform` args and return behavior?
4. Are there missing edge cases before this can be used in the DG field-generation witness runner?
