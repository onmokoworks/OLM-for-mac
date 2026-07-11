# OpenCV Detour P0B Fix Report

## Overview
This report details the implementation of an independent sidecar oracle (GATE B) for the OpenCV detour layer, specifically targeting `cvThreshold` (`FUN_1812b6a40` in DistanceGradation), and the subsequent semantic fixes to `cvthreshold_native` to precisely match OpenCV 4.5.5 behavior.

## Changes Made
1. **Sidecar Oracle Creation**: Created `.venv-cv455` (Python 3.12, `numpy<2`, `opencv-python-headless==4.5.5.64`). Developed `sidecar_oracle.py` to evaluate OpenCV 4.5.5's exact outputs for `cvThreshold` out-of-process.
2. **Oracle Integration in Tests**: Modified `tools/emulation/test_opencv_detour.py`'s GATE B test to invoke `sidecar_oracle.py` via `subprocess`, comparing the emulated outputs bit-for-bit against actual `cv2.threshold` responses rather than relying on the internal `cvthreshold_native`.
3. **Semantic Fixes in `cvthreshold_native`**:
   - Implemented exact out-of-bounds `ithresh` special paths for integer types (`uint8`, `int16`, `uint16`) as described in `thresh.cpp` lines 1577-1596.
   - Refactored `float32`/`float64` logic to accurately reflect NaN handling (`src > thresh` for `BINARY`/`TOZERO`, `src <= thresh` for `BINARY_INV`/`TOZERO_INV`).
   - Fixed `XMM0` return values (integer floor returns vs raw double returns).
4. **Size/Depth Guard**: Inserted explicit `ValueError` guards in `_make_cvthreshold_handler` to fail loudly if `src` and `dst` shapes/dtypes differ.

## Regression Test Log
Prior to updating `cvthreshold_native`, the test suite failed predictably when evaluating `uint8` limits, confirming that the new oracle reliably detects semantic divergences.

```text
[FAIL] detour float32/BINARY       thr=0.3 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=False
...
[PASS] detour uint8/BINARY         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
...
OverflowError: Python integer 300 out of bounds for uint8
```

## Verification
Following the fixes in `opencv_impls.py`, the extended test suite (which includes `NaN` tests and `ithresh` bounding extremes) passes. Full execution log: see "Execution log" section below.

Independent cross-check (reviewer, 2026-07-07): a separate 80-case boundary
suite (all 5 THRESH types x uint8/uint16/int16/float32, incl. maxval=300/-1
saturation and NaN x _INV cases not present in this test file) was compared
against the same sidecar cv2 4.5.5: **pre-fix 44/80 divergences (30 crashes),
post-fix 80/80 bit-exact including return values** (FACT, executed logs).

## Known Limitations
- The sidecar oracle is an `arm64` build of OpenCV 4.5.5. Integer paths are
  LUT/compare-exact vs Windows x64 unconditionally. Float compare/select paths
  are IEEE-deterministic and match — with **one identified concrete exception**:
  - **32F THRESH_TRUNC with NaN in src** (FACT, thresh.cpp 4.5.5 lines 63-67 and
    845-875): the SIMD body uses `v_min(v0, thresh4)`. On Windows x64 SSE,
    `minps(src, thresh)` returns the **second operand (thresh)** when src is
    NaN, while the scalar row-tail (`std::min`) passes NaN through — so Windows
    output is position-dependent. NumPy and the arm64 (NEON) oracle both pass
    NaN through everywhere, so GATE B PASS on the TRUNC+NaN case does NOT
    represent Windows. Not reachable in DistanceGradation practice (threshold
    inputs are distance-transform outputs, no NaN), but any future caller with
    possible NaN + TRUNC must resolve this against a Windows capture first.

## Execution log (FACT — `.venv/bin/python tools/emulation/test_opencv_detour.py`, 2026-07-07, post-fix)

```text
AEX: /Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/DistanceGradation.aex
cvThreshold @ 0x1812b6a40

[PASS] bridge round-trip: bridge round-trip ok (uint8/uint16/float32 + 3ch)
[PASS] detour float32/BINARY       thr=0.3 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/BINARY_INV   thr=0.3 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TRUNC        thr=0.3 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TOZERO       thr=0.3 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TOZERO_INV   thr=0.3 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TRUNC          thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY         thr=300 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY         thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/BINARY        thr=70000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/BINARY        thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/BINARY         thr=-40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/BINARY         thr=40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/BINARY         thr=-5.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/BINARY NaN   thr=0.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/BINARY       thr=0.1 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY_INV     thr=300 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY_INV     thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/BINARY_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/BINARY_INV    thr=70000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/BINARY_INV    thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/BINARY_INV     thr=-40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/BINARY_INV     thr=40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/BINARY_INV     thr=-5.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/BINARY_INV NaN thr=0.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/BINARY_INV   thr=0.1 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TRUNC          thr=300 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TRUNC          thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TRUNC          thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TRUNC          thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TRUNC          thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/TRUNC         thr=70000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/TRUNC         thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TRUNC          thr=-40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TRUNC          thr=40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TRUNC          thr=-5.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TRUNC NaN    thr=0.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TRUNC        thr=0.1 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO         thr=300 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO         thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO         thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/TOZERO        thr=70000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/TOZERO        thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TOZERO         thr=-40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TOZERO         thr=40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TOZERO         thr=-5.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TOZERO NaN   thr=0.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TOZERO       thr=0.1 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO_INV     thr=300 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO_INV     thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint8/TOZERO_INV     thr=100 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/TOZERO_INV    thr=70000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour uint16/TOZERO_INV    thr=-10 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TOZERO_INV     thr=-40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TOZERO_INV     thr=40000 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour int16/TOZERO_INV     thr=-5.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TOZERO_INV NaN thr=0.5 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True
[PASS] detour float32/TOZERO_INV   thr=0.1 instr=3 bypassed=True written=True header_intact=True bit_exact=True ret_exact=True

[GATE C BLOCKED] emulated-equivalence: emulated path faults at RIP=0x181187e41 (OpenCV static-init not scaffolded)
            (expected: exact-reference GATE B is authoritative for threshold; GATE C is the gold gate reserved for float ops / P3)

RESULT: all detour + bridge gates PASS (GATE A+B). GATE C blocked as documented.
```
