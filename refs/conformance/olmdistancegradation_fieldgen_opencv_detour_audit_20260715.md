# DistanceGradation Fieldgen OpenCV Detour Audit - 2026-07-15

## Scope and disposition

This audit covers the owned DG fieldgen integration surface:

- `tools/emulation/opencv_impls.py`
- `tools/emulation/cv_bridge.py`
- `tools/emulation/test_opencv_detour.py`
- `tools/emulation/test_dg_fieldgen_p1b.py`
- `tools/emulation/export_dg_fieldgen_fixture.py`
- `tools/emulation/replay_dg_fieldgen_fixture.cpp`

No source adapter was added. The current-AEX witness path is executable with the
existing binary-grounded contracts, so there is no concrete missing adapter to
implement. No PNG, `mac/OLMDistanceGradation`, or
`notes/CONFORMANCE_LEDGER.md` file was changed.

## FACT

- P1 detours `FUN_1812b6a40` (threshold) and `FUN_1812b15a0` (precise L2
  distance transform) are registered explicitly for `DistanceGradation`.
- P1C detour `FUN_1812aef70` is intentionally limited to same-shape,
  same-dtype copies. The DG fieldgen path invokes that staging seam twice in
  the tested witness.
- P2 detour `FUN_18117ca50` is limited to single-channel float32,
  `NORM_MINMAX`, no-mask normalization. The DG fieldgen path invokes it once
  in the tested witness.
- `cv_bridge.py` decodes and writes the binary-grounded x64 `IplImage` layout,
  including padded `widthStep`, and reads stack arguments at the established
  detour ABI location.
- The direct current-AEX fieldgen runner completes and records these callbacks:
  `cv::dist_transform` x1, `cv::resize_same_shape` x2,
  `cv::threshold` x1, and `cv::normalize_minmax` x1.
- The OpenCV detour suite passes all bridge, threshold, P1, P1C, and P2 gates.
  The informational emulated-equivalence gate remains blocked at
  `0x181187e41` because OpenCV static initialization is not scaffolded.
- The DG CPU fixture smoke passes AEX export, manifest verification,
  deterministic replay, and portable replay. For the full-frame case-0023
  inside and outside passes, each field is `8,294,400` bytes and matches the
  AEX fixture exactly; the compose triplet is `0,32768,32768`.
- The local current-AEX binary under test is
  `plugins_2025/DistanceGradation.aex`. These are local Unicorn/AEX and
  portable-core results, not a Windows AE Software versus Mac AE comparison.

## INFERENCE

- The existing P1/P1C/P2 integration is sufficient to execute the current-AEX
  DG fieldgen witness and the full-frame case-0023 fixture workflow. Adding a
  broader resize adapter would exceed the observed same-shape contract and
  would not improve the requested compatibility proof.
- The strongest newly proven local boundary is the complete fieldgen-to-compose
  fixture path for full-frame case-0023, with byte-exact AEX-to-portable replay
  on both inside/outside fields and the bound compose words.
- This evidence does not establish `max_diff=0` for Windows AE Software versus
  Mac AE. That boundary still requires paired Windows AE Software and Mac AE
  artifacts from the same render contract.

## Exact verification commands and output summary

All commands were run from the repository root on 2026-07-15.

```bash
tools/emulation/.venv/bin/python -m py_compile \
  tools/emulation/opencv_impls.py tools/emulation/cv_bridge.py \
  tools/emulation/test_opencv_detour.py tools/emulation/test_dg_fieldgen_p1b.py \
  tools/emulation/export_dg_fieldgen_fixture.py
```

Output: no output; exit `0`.

```bash
tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
```

Output summary: bridge round-trip PASS; threshold cases PASS; P1 distance
transform cases PASS for ten mask families plus contract rejection cases; P1C
same-shape copy cases PASS; P2 normalize cases PASS for ramp, binary, constant
zero, and constant nonzero; `RESULT: all detour + bridge gates PASS (GATE A+B)`;
exit `0`. GATE C reported BLOCKED at `0x181187e41` as documented.

```bash
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py \
  --points '8,5;7,5;9,5'
```

Output summary: `status=completed`, `instructions=6921`, output range `0.0..1.0`,
and all four detour callbacks present.

```bash
tools/emulation/.venv/bin/python refs/scripts/smoke_dg_cpu_fixture.py
```

Output summary: synthetic fieldgen `748` bytes and compose `24` bytes match AEX
exactly; DG core distance stage PASS for `286` values; exit `0`.

```bash
tools/emulation/.venv/bin/python refs/scripts/smoke_dg_case0023_cpu_fixture.py
```

Output summary: full-frame inside/outside AEX fields each match portable core
exactly for `8,294,400` bytes; fieldgen triplet binds to compose words
`0,32768,32768`; exit `0`.

The additional cropped current-AEX probes also completed with all four detour
callbacks. The threshold crop produced samples `0,1,1,0,1` at
`(414,393),(415,393),(416,393),(415,392),(415,394)`. The edge crop completed
with output range `0.0..0.0`; neither result is promoted to Windows/Mac
conformance.
