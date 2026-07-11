# OLMRadialBlur Zoom Direct-Core Prefill Probe

Date: 2026-07-08

## Verdict

The local Zoom AEX emulator now reaches `FUN_1800056f0` directly, but the next
blocker is the full polar-grid prefill inside that function, not the final
sampler or Mac output writeback.

This is still a local emulator/harness fact, not a Windows semantic proof, and
must not be used to change `mac/OLMRadialBlur`.

## Commands

```bash
python3 -m py_compile tools/emulation/test_zoom_case0009.py
python3 tools/emulation/test_zoom_case0009.py \
  --direct-zoom-core \
  --max-instructions 2000000 \
  --output-json /tmp/zoom_case0009_direct_branch_probe_a0.json \
  --output-md /tmp/zoom_case0009_direct_branch_probe_a0.md
```

Reduced-geometry hookability check:

```bash
python3 tools/emulation/test_zoom_case0009.py \
  --direct-zoom-core \
  --direct-debug-size 32x32 \
  --max-instructions 2000000 \
  --output-json /tmp/zoom_case0009_direct_debug32_q90_final.json \
  --output-md /tmp/zoom_case0009_direct_debug32_q90_final.md
```

Full-size reachability check with synthetic prefill and no-op heavy workers:

```bash
python3 tools/emulation/test_zoom_case0009.py \
  --direct-zoom-core \
  --direct-fast-forward-prefill \
  --direct-detour-prepass \
  --direct-detour-scatter \
  --max-instructions 2000000 \
  --output-json /tmp/zoom_case0009_direct_ff_prefill_detour_both.json \
  --output-md /tmp/zoom_case0009_direct_ff_prefill_detour_both.md
```

Full-size Python prefill candidate check:

```bash
python3 tools/emulation/test_zoom_case0009.py \
  --direct-zoom-core \
  --direct-python-prefill \
  --direct-detour-prepass \
  --direct-detour-scatter \
  --max-instructions 500000 \
  --output-json refs/reports/olmradialblur_zoom_case0009_python_prefill_candidate_20260708.json \
  --output-md refs/reports/olmradialblur_zoom_case0009_python_prefill_candidate_20260708.md
```

Reduced-geometry AEX-vs-Python prefill validation:

```bash
python3 tools/emulation/test_zoom_case0009.py \
  --direct-zoom-core \
  --direct-debug-size 32x32 \
  --direct-stop-after-prefill \
  --max-instructions 2000000 \
  --output-json refs/reports/olmradialblur_zoom_debug32_original_prefill_stop_20260708.json \
  --output-md refs/reports/olmradialblur_zoom_debug32_original_prefill_stop_20260708.md

python3 tools/emulation/test_zoom_case0009.py \
  --direct-zoom-core \
  --direct-debug-size 32x32 \
  --direct-python-prefill \
  --direct-stop-after-prefill \
  --max-instructions 2000000 \
  --output-json refs/reports/olmradialblur_zoom_debug32_python_prefill_stop_20260708.json \
  --output-md refs/reports/olmradialblur_zoom_debug32_python_prefill_stop_20260708.md
```

## Facts

- Direct mode calls `FUN_18000a7e0`, `FUN_18000a810`, then `FUN_1800056f0`.
- The branch hooks prove execution reaches:
  - `0x18000573b` (`thread-count-read`)
  - `0x180005849` (`input-world-read`)
  - `0x1800058b0` (`post-input-world`)
- At `0x1800058b0`, the computed geometry is:
  - `R12 = 1800` angular rows
  - `R15 = 1104` radial columns
  - `work_min_radius_0x18 = 0`
  - `work_max_radius_0x1c = 1103`
- The direct-context fix now sets `param_ctx+0xa0` to a float output plane.
  The probe samples show `param_output_0xa0` is non-zero after the fix.
- `prepass_calls = 0` and `scatter_calls = 0` within the 2,000,000 instruction
  probe because the function is still inside the full `1800 * 1104` polar input
  prefill path before `0x180005ba2`.

Reduced-geometry debug facts:

- `--direct-debug-size 32x32` plus the default debug quality step `90.0` reduces
  the core geometry to:
  - angular rows: `4`
  - radial columns: `49`
  - `min_radius = 1055`
  - `max_radius_plus = 1103`
- In that reduced non-semantic run:
  - `prepass_calls = 1`
  - `scatter_calls = 1`
  - branch hooks reach `0x180005ba2`, `0x180005c1a`, `0x180005c7c`,
    `0x180005c9f`, and `0x180005d99`
  - the run then faults at `0x180009e35` during the final sampler/output phase,
    which is acceptable for this hookability check

Full-size synthetic reachability facts:

- `--direct-fast-forward-prefill` skips only the `0x180005a00..0x180005b98`
  polar input prefill after the real full-size allocations are made.
- The synthetic prefill run keeps the full case geometry:
  - angular rows: `1799`
  - radial columns: `1104`
  - synthetic prefill cells: `1987200`
- With only prefill fast-forwarded, the runner reaches `FUN_18000b150`; within
  the 2M-instruction cap it does not finish that heavy worker.
- With `FUN_18000b150` no-op detoured too, the runner reaches
  `FUN_18000a9d0`.
- With both `FUN_18000b150` and `FUN_18000a9d0` no-op detoured, the runner
  reaches the final-plane branch at `0x180005c9f`.
- The full-size detoured run has no emulation fault inside the cap and records:
  - `prepass_calls = 1`
  - `scatter_calls = 1`
  - `prepass_detour_calls = 1`
  - `scatter_detour_calls = 1`
  - final branch hook `0x180005c9f = 1`

Full-size Python prefill candidate facts:

- `--direct-python-prefill` replaces the hot `0x180005a00..0x180005b98`
  loop with a Python implementation grounded in `FUN_1800056f0`,
  `FUN_18000a6a0`, and `FUN_18000a270`.
- The candidate run keeps full `case_0009` geometry:
  - angular rows: `1800`
  - radial columns: `1104`
  - cells: `1987200`
- The source planes used by the Python prefill are the same direct-context
  planes passed through `param_2`:
  - RGBA source `param_2[0x13]` / byte offset `0x98`
  - scalar source `param_2[0x12]` / byte offset `0x90`
  - optional scalar source `param_2[0x11]` / byte offset `0x88`
- In the final-plane sample for output `(6,0)`, one of the four source cells is
  already `alpha = 0.9999999403953552`.
- Bilinear sampling of those four cells gives:
  - float sample: `[0.0, 0.0, 0.0, 0.9999999924232991]`
  - trunc u8: `[0, 0, 0, 254]`
  - round u8: `[0, 0, 0, 255]`
- The run output was:
  - `classification=direct-python-prefill-detoured-candidate`
  - `local_sample=[0.0, 0.0, 0.0, 0.9999999924232991] trunc=[0, 0, 0, 254]`
  - `output_world_rgba=[0, 0, 0, 0]`

Reduced-geometry validation facts:

- `refs/conformance/olmradialblur_zoom_python_prefill_validation_20260708.md`
  compares the original AEX prefill stop against the Python prefill stop at
  the same `32x32/q90` pre-worker boundary.
- Compared groups: `param_1[7]` final polar RGBA, `param_1[0x843]`
  denominator, and `param_1[0x842]` accumulation cells for the four cells used
  by the final sample.
- Result: `max_abs_diff = 0.0`.
- This validates the Python prefill formula against the original AEX prefill
  for the reduced direct-core geometry.

Worker detour matrix facts:

- `refs/conformance/olmradialblur_zoom_python_prefill_worker_detour_matrix_20260708.md`
  compares three full-size Python-prefill runs:
  - both `FUN_18000b150` and `FUN_18000a9d0` detoured
  - `FUN_18000b150` live / `FUN_18000a9d0` detoured
  - `FUN_18000b150` detoured / `FUN_18000a9d0` live
- In all three modes, output `(6,0)` final-plane sampling remains
  `[0.0, 0.0, 0.0, 0.9999999924232991] -> trunc [0,0,0,254]`.
- The observed target four-cell `accum_0x842.alpha` and `denom_0x843` values
  remain zero in these runs.

## Interpretation

Previous local evidence said the emulator could not reach the Zoom entry from
`FUN_180007520` within the instruction cap. The direct-core harness improves
that: entry is now reached and the Zoom geometry is computed. The remaining
local full-size bottleneck is the huge in-function prefill loop before
`FUN_18000b150` and `FUN_18000a9d0`.

The reduced-geometry check proves the direct harness is structurally capable of
reaching the Zoom prepass/scatter/final-plane branches. The full-size synthetic
prefill/no-op-worker check proves the same downstream dispatch is reachable at
real `case_0009` geometry. Neither proves `case_0009` semantics because the
input polar plane and worker effects are synthetic or detoured.

The Python prefill candidate is now stronger than the synthetic reachability
check and has a reduced-geometry validation against the original AEX prefill.
It shows the `254` alpha can arise from decomp-grounded polar prefill plus
final-plane bilinear/truncate alone. The single-worker detour matrix did not
move the target sample away from that value. This remains a local AEX-emulation
candidate, not an AE exact or Windows semantic proof.

Useful next local actions are therefore harness actions, not Mac algorithm
tuning:

1. Validate the Python prefill against an original reduced-geometry AEX prefill
   run, or against a Windows trace that captures the same four final-plane
   cells.
2. Use detours sparingly to isolate whether the
   `254/255` split appears in `FUN_18000b150`, `FUN_18000a9d0`, or the
   final-plane normalization/output sampler.
3. Keep full-size `case_0009` semantic claims on Windows/runtime evidence or
   on a later emulator run with real prefill/worker state.

## Forbidden From This Evidence

- Do not tune RadialBlur visually.
- Do not change Mac source from this local harness witness.
- Do not claim Zoom `case_0009` exactness from the current all-zero final plane.
