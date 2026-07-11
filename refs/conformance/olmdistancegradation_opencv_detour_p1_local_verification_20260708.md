# OLMDistanceGradation OpenCV Detour P1 Local Verification — 2026-07-08

Scope: local verification of the `cvDistTransform` detour for
`FUN_1812b15a0` under `tools/emulation/`, bounded to the observed
`cvDistTransform(src_8u, dst_32f, DIST_L2, DIST_MASK_PRECISE, 0, 0, 0)` call
shape.

## FACT

- `tools/emulation/opencv_impls.py` installs a dedicated `dist_transform`
  detour at `0x1812b15a0` for `DistanceGradation`.
- The handler contract is `src` single-channel `uint8`, `dst` same shape
  `float32`; it does not reuse the `cvThreshold` same-dtype guard.
- `tools/emulation/.venv-cv455/bin/python` is present locally, so the sidecar
  OpenCV 4.5.5 oracle is available.
- Command run on 2026-07-08:

  ```bash
  tools/emulation/.venv/bin/python tools/emulation/test_opencv_detour.py
  ```

- Result from that run:
  - all threshold cases passed GATE A+B;
  - all ten `dist_transform/*` masks passed with `native_exact=True`,
    `cv455_exact=True`, `max_abs=0`;
  - the explicit `dist_transform/contract` regression passed, proving the
    accepted contract is `src uint8 -> dst float32` and that a `uint8` dst is
    rejected with `cvDistTransform dst mismatch`;
  - GATE C remained blocked at `RIP=0x181187e41` because OpenCV static-init is
    still not scaffolded in emulation.

## INFERENCE

- Because the local detour output matched both the sidecar OpenCV 4.5.5 oracle
  and the Meijster-style implementation family already used by the mac port,
  the current P1 detour is fit for local fieldgen acceleration on the observed
  DG path.
- The remaining DG conformance gaps are downstream of this exact EDT primitive,
  not evidence that the `FUN_1812b15a0` detour itself is wrong.
