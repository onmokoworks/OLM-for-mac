# Binary-Grounded IR: OLMKiraKira

## Feature

- Plug-in: OLM Kira Kira
- Feature/path: 8bpc Software-render glow ray generation and merge mode 1
- Bit depth: 8bpc documented here; 16/32bpc untested
- Reference sets:
  - `refs/win_references/20260604_olm/OLMKiraKira`
  - `refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira`
  - `refs/win_references/olm_reference_return_windows_recapture_20260615/OLMKiraKira`
- Current status: `binary-grounded / guarded`, not `AE exact`

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Merge mode 1 composes with screen RGB and source-alpha passthrough. | Strength=0 single-ray refs; `notes/OLMKiraKira_ASM_FACTS.md`. | reference-confirmed / binary-aligned |
| Zero-length rays are skipped entirely. | `FUN_18114f4a0` guards `length != 0`; single-ray refs. | binary-grounded |
| Directional ray helper scalar is not used by merge-mode-1 aggregator output. | `FUN_18114f4a0` / `FUN_18114fd90` argument audit and single-ray refs. | binary-grounded |
| Temp extents use truncation after `+4.0f`, then clamp to at least source size + 4. | `FUN_18114f4a0`, `.rdata DAT_18148b830 = 4.0f`. | binary-grounded |
| Ray helper uses centered ROI/copy, forward `warpAffine`, three horizontal `boxFilter` passes, rotate-back, and final centered copy. | `FUN_181150790`, `FUN_181156cd0`, `FUN_18115cfb0`, `FUN_181297ac0`. | binary-grounded |
| `boxFilter` args are `ksize=(length,1)`, `anchor=(-1,-1)`, `normalize=true`, `borderType=4` (`BORDER_REFLECT_101`), float output. | `FUN_181280bc0` call audit and negative probes. | binary-grounded |
| First `boxFilter` pass dispatches to OpenCV 4.5.5 AVX2 branch `FUN_1812e39d0` on the traced Windows machine. | `refs/reports/runtime_trace_summary.md`, `kirakira_opencv455_primitive_fact_20260618`. | runtime-trace |
| `warpAffine` calls pass `INTER_LINEAR`, no `WARP_INVERSE_MAP`, `BORDER_CONSTANT`, zero border value. | `FUN_181297ac0` wrapper call audit. | binary-grounded |

## Parameters

| UI / manifest name | Internal meaning | Evidence |
| --- | --- | --- |
| Brightness / Gain | `FUN_18114fd90` ray-to-alpha multiplier before clamp; Strength=0 maps through the half-gain path at `127/255`. | binary + brightness anchors |
| Strength | Seed exponent / ray enable strength, not the final brightness multiplier. | single-ray refs |
| Vertical/Horizontal/Diagonal lengths | Per-ray raw length; zero skips ray, nonzero feeds `boxFilter` width. | binary + single-ray refs |
| Glow Rotation | Adds to diagonal/axis ray angles and temp-canvas rotation. | helper audit |
| Blur Mode 2 | Three-pass horizontal `boxFilter` helper path. | `FUN_181150790` |
| Channel | Seed function; current traced `Channel=2` vtable normalize byte returns `1`. | vtable / refs |

## Algorithm IR

1. Build seed from input according to Channel and Strength.
2. For each nonzero directional ray:
   - allocate two temporary Mat-like float canvases using AEX temp extent
     formula;
   - center-copy the source seed into the first temp ROI;
   - forward-rotate through OpenCV `warpAffine` semantics;
   - apply Blur Mode 2 as three horizontal normalized box filters;
   - rotate back through OpenCV `warpAffine` semantics;
   - center-copy back to the final ray buffer.
3. Aggregate five ray buffers with `FUN_18114fd90` shape:
   - skip `ray <= 0.001`;
   - `alpha = clamp(ray * brightness)`;
   - add premultiplied layer RGB;
   - update output alpha with union formula;
   - normalize RGB by final alpha.
4. Compose merge mode 1:
   - `out_rgb = 1 - (1 - src_rgb) * (1 - glow_rgb * glow_a)`;
   - `out_a = src_a`.

## Current Measurements

- Legacy C++ smoke on `20260604_olm` remains expected-red:
  `case_0001 max=21 mean=0.8291`, `case_0002 max=24 mean=1.1609`,
  `case_0003 max=233 mean=53.8132`. This smoke still exercises older
  `aex-premul`/legacy references and is a regression measurement scaffold, not
  a completion gate.
- 2026-06-19 C++ probe refresh:
  - `box-anchor opencv` remains the best tested anchor; `floor-left` worsens
    `case_0002`, and `origin` / `end` are strongly negative.
  - `rotate-filter bilinear` remains the least bad tested interpolation mode.
    Bicubic, nearest, and fixed-table variants do not explain the residual.
  - Local OpenCV Python screen-over probe could not run because the available
    Python interpreters do not currently have `cv2` installed.
- 2026-06-19 local OpenCV probe refresh after creating
  `/tmp/olm_cv455_probe_venv` with
  `opencv-python-headless==4.5.5.64` and `numpy==1.26.4`
  via `refs/scripts/setup_olmkirakira_opencv455_probe_env.sh`:
  - `smoke_olmkirakira_opencv_screenover_probe_cli.py` runs and keeps the
    single-ray Software set in the existing guarded residual band
    (`max=13/23/66`, strength-0 anchors `max=0..3`).
  - `smoke_olmkirakira_opencv_two_temp_probe_cli.py` and
    `smoke_olmkirakira_opencv_two_temp_alias_probe_cli.py` are still
    expected-red on the older three-case set, but using real OpenCV primitives
    reduces the difficult `case_0003` from the C++ scaffold's `max=233` to
    `max=26 mean=1.0477`. The alias-ROI variant is byte-identical to the
    ordinary OpenCV two-temp probe for these cases.
  - The same numbers were observed with the earlier local OpenCV 4.10.0 wheel.
    Therefore the remaining KiraKira gap is unlikely to be explained by a
  broad 4.5.5-vs-newer OpenCV version difference alone. It is more likely in
  exact Windows AVX2 branch behavior, `warpAffine` Mat/ROI placement, or
  final ray aggregation details.
- 2026-06-20 overnight recheck recreated `/tmp/olm_cv455_probe_venv` and
  reconfirmed the same shape:
  - `smoke_olmkirakira_opencv_screenover_probe_cli.py` passes its guarded
    bound with single-ray Software residuals `max=13/23/66` and Strength=0
    anchors `max=0..3`.
  - `smoke_olmkirakira_opencv_two_temp_probe_cli.py` still gives old three-case
    residuals `case_0001 max=21 mean=0.8239`, `case_0002 max=24 mean=1.1568`,
    `case_0003 max=26 mean=1.0477`.
  - `smoke_olmkirakira_opencv_two_temp_alias_probe_cli.py` is byte-equivalent
    to ordinary two-temp for those three cases, so ROI aliasing remains
    rejected as an explanation.
- OpenCV remap/warpAffine micro diagnostics in the C++ CLI pass:
  `diag_remap_bilinear_f32`, `diag_warpaffine_map_f32`, and
  `diag_warpaffine_remap_f32` all report `OK`.

## Rejected / Low-Value Next Moves

- Do not tune box size, anchor, normalize flag, border mode, or accumulator
  precision from PNG residuals; the argument set is already binary-grounded
  and negative probes are broad.
- Do not promote bicubic, nearest, simple half-pixel center shifts, direct
  rotate-back, final one-pixel ROI shifts, or naive same-Mat aliasing without
  new runtime evidence.
- Do not treat the older `20260604_olm` expected-red smoke as a Mac AE exact
  gate.

## Next Required Proof

The next useful evidence is not another broad PNG set. Use one of:

- an exact AVX2 `FUN_1812e39d0` microprobe for the traced `boxFilter` branch
  if a local x86/Windows-capable environment is available; or
- a Windows runtime trace of `FUN_181150790` on a single-ray case that records
  both `warpAffine` calls' Mat headers, `dsize`, matrix values, ROI rectangles,
  selected `boxFilter` function, and a few witness float values after each
  helper stage.

Only after that should the C++/Mac implementation change.

Current Windows overnight request:

- Bundle: `handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`
- KiraKira trace package:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_stage_values_20260620_overnight.zip`
- Request id: `kirakira_fun_181150790_stage_values_20260620`

Local comparison helper:

- `refs/scripts/olmkirakira_cli.py` now accepts `--trace-json` for
  `--ray-mode opencv-two-temp` and `opencv-two-temp-alias-roi`.
- The trace dump records temp sizes, rotation centers, forward/back matrices,
  center-copy origin, three representative sample points, explicit
  source/tmp1/tmp2/ray coordinate spaces, and values after center-copy,
  forward warp, each box pass, rotate-back, and final center-copy.
- The same dump now appends an `aggregation_and_compose` record with source,
  glow, float output, and quantized output samples. Compare the returned
  Windows `FUN_181150790` stage values first, then this final record; that
  separates ray-helper mismatch from `FUN_18114fd90` aggregation or
  merge-mode-1 compose mismatch.
- Use this JSON as the Mac/OpenCV-side baseline when the Windows
  `FUN_181150790` trace returns; do not promote a PNG-only tweak if the stage
  values point to a later aggregation/compose difference.
- Current project-local baseline:
  `refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json`.
  Recreate it with
  `OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python python3 refs/scripts/write_olmkirakira_trace_baseline.py --out-dir refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac`.
- 2026-06-20 read-only audit conclusion: the overnight trace request is
  sufficient to separate first divergence at forward `warpAffine`, box pass,
  rotate-back/final copy, or `FUN_18114fd90` aggregation/merge compose. Do not
  change local implementation before this trace returns.
