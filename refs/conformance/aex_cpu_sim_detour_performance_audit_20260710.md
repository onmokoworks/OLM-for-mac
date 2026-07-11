# DistanceGradation AEX CPU Simulation / Detour Performance Audit

Date: 2026-07-10

## Scope

This is a read-only benchmark of the existing
`tools/emulation/test_dg_fieldgen_p1b.py` runner and its registered OpenCV
detours for `DistanceGradation.aex` `FUN_181174760`. No source, dependency, or
detour implementation was changed.

The measurements are local AEX-emulation measurements, not AE-host render
measurements.

## Commands and measurements

Interpreter: `tools/emulation/.venv/bin/python`

| Run | Input | Wall time | User/sys | AEX instructions | Detour callbacks |
| --- | --- | ---: | ---: | ---: | --- |
| Synthetic smoke | 17x11 synthetic mask, threshold 3 | 0.26 s | 0.16/0.03 s | 6,921 | `dist_transform` x1, `threshold` x1, `resize_same_shape` x2, `normalize_minmax` x1 |
| Threshold crop | 96x96 crop at `(380,350)`, threshold 36 | 0.34 s | 0.23/0.05 s | 6,921 | same profile |
| Full frame inside | 1920x1080 alpha mask, threshold 36 | 7.08 s | 6.85/0.09 s | 6,921 | same profile |
| Full frame outside | 1920x1080 inverted alpha mask, threshold 0 | 7.18 s | 6.95/0.12 s | 6,921 | same profile |

Repeated full-frame inside runs with the same command measured:

| Repeat | Wall time | User/sys | AEX instructions |
| ---: | ---: | ---: | ---: |
| 1 | 7.36 s | 6.94/0.14 s | 6,921 |
| 2 | 7.08 s | 6.89/0.10 s | 6,921 |
| 3 | 7.22 s | 6.90/0.11 s | 6,921 |

Repeated full-frame inside mean: **7.22 s wall**, **6.91 s user**. The
emulated instruction count and callback profile were invariant across the
three repeats. The callback log also contained the expected host-suite
activity: `SPBasic.AcquireSuite`/`ReleaseSuite` x16 each and
`PFHandle.new`/`lock`/`unlock`/`dispose` x8 each.

Representative command:

```bash
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py \
  --mask-png refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png \
  --mask-channel alpha --points '1699,7;415,393' --threshold 36 --param8 1
```

The shell wall times above were collected with `/usr/bin/time -p`. The runner
itself reports the AEX instruction count and callback counts in JSON.

## Baseline attempt and boundary

There is no supported selectable non-detoured mode in the existing DG runner.
The bounded existing GATE C attempt was run through:

```bash
tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
```

It completed the detour test suite and reported:

```text
[GATE C BLOCKED] emulated-equivalence: emulated path faults at RIP=0x181187e41 (OpenCV static-init not scaffolded)
RESULT: all detour + bridge gates PASS (GATE A+B). GATE C blocked as documented.
```

That command took 26.50 s wall time, but it is a detour validation suite, not
a comparable DG fieldgen baseline. Its non-detoured path faults before a
useful OpenCV comparison, so no baseline instruction count or baseline wall
time exists for the same `FUN_181174760` workload.

## Conclusion

- **Speedup proven: No.** The detoured path is measured and repeatable, but no
  supported non-detoured DG baseline completed. Therefore a speedup ratio,
  percentage, or claim of lower end-to-end cost would be unsupported.
- **GATE C remains blocked.** The existing gold emulated-equivalence gate still
  stops at OpenCV static initialization (`RIP=0x181187e41`).
- **What the detour establishes:** the observed DG fieldgen call sequence can
  complete under AEX CPU emulation; the registered detours fire with stable
  counts; and the existing detour tests pass their GATE A+B checks, including
  the sidecar OpenCV 4.5.5 comparisons documented in
  `refs/conformance/opencv_detour_current_gate_20260708.md`.
- **What it cannot establish:** native-vs-detoured performance, AE-host
  performance, whole-plugin conformance, or GATE C emulated equivalence. The
  7.22 s full-frame figure is a detoured local-emulator wall-time datum only.
