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
| First `boxFilter` pass dispatches to OpenCV 4.5.5 AVX2 branch `FUN_1812e39d0` on the traced Windows machine; the feature gate is `0xb` / `CV_CPU_AVX2`. | `refs/reports/runtime_trace_summary_hardpaths_20260621_041022.md`, `kirakira_opencv455_primitive_fact_20260618`. | runtime-trace |
| `warpAffine` calls pass `INTER_LINEAR`, no `WARP_INVERSE_MAP`, `BORDER_CONSTANT`, zero border value. | `FUN_181297ac0` wrapper call audit. | binary-grounded |
| The 2026-06-20 wrapper trace confirmed two `warpAffine` wrapper hits, three `boxFilter` wrapper hits, dsize/temp `1924x1924`, length `50`, and `boxFilter` ksize `(50,1)`. | `refs/reports/runtime_trace_summary_kirakira_stage_values_20260620.md`. | runtime-trace |
| 2026-06-21 deep trace captured concrete witness floats after each box pass, rotate-back, and final copy for the vertical len=50 Software case. Windows is already brighter than the local OpenCV baseline after box pass 1, so the next focus is forward-warp or boxFilter input, not final compose. | `refs/reports/kirakira_deep_stage_values_20260621/runtime_trace_comparisons/olmkirakira_deep_stage_values.md`. | runtime-trace partial |

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
- 2026-06-19 local OpenCV probe refresh after creating a temporary OpenCV
  4.5.5 probe environment with `opencv-python-headless==4.5.5.64` and
  `numpy==1.26.4`
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
- 2026-06-20 overnight recheck recreated the temporary OpenCV 4.5.5 probe and
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
- 2026-06-20 Windows wrapper trace return is useful but too sparse for an
  implementation change:
  - `ray_length=50` and temp/dsize `1924x1924` match the local OpenCV baseline.
  - `warpAffine` wrappers hit twice, `boxFilter` wrappers hit three times, and
    each box pass reaches the AVX2 branch.
  - Forward/back matrices, ROI/copy rectangles, per-stage witness floats,
    aggregation, and merge-mode compose values were not isolated.
  - The normalized comparison now reports `trace-too-sparse`, not
    `warp-matrix-or-center`.
- 2026-06-21 deep trace return is `answered_partial` but useful:
  - input and rendered PNGs are byte-identical to the existing
    `kirakira_single_ray_20260606` Software reference;
  - function-entry and forward-warp breakpoints did not fire, so matrices,
    center-copy, and forward-warp witness values are still missing;
  - concrete stage floats were captured after box pass 1/2/3, rotate-back, and
    final copy. Against the local OpenCV 4.5.5 baseline, Windows is higher from
    the first box pass:
    `center +0.00765908`, `ray_length_up +0.00722814`,
    `ray_length_right +0.00512678`;
  - after pass 3 the deltas are still consistent:
    `center +0.00867754`, `ray_length_up +0.00858700`,
    `ray_length_right +0.00840882`;
  - after rotate-back/final-copy, `ray_length_up` diverges further
    (`+0.01375264`), but the first proven divergence is already before that.
  - normalized comparison focus:
    `forward-warp-or-boxfilter-input`.
- 2026-06-21 focused forward-warp / box-input trace return is `answered`:
  - forward `warpAffine` is now concrete for the vertical len=50 Software case:
    dsize/temp `1924x1924`, copy origin `[2,422]`, source ROI
    `[2,422,1920,1080]`, matrix
    `[~0, 1, ~0, -1, ~0, 1924]`;
  - this matches the local OpenCV baseline's forward matrix and temp geometry
    within floating print precision, so the broad forward-warp choreography is
    no longer the leading suspect;
  - first `boxFilter` pass arguments are concrete:
    `ksize=[50,1]`, `anchor=[-1,-1]`, `normalize=true`, `border_type=4`,
    branch `FUN_1812e39d0 / AVX2`;
  - forward-warp output / pass-1 input witnesses match local at the traced
    points (`before_box_1 == after_forward_warp == 0.11764707`);
  - the remaining first concrete mismatch is split between one center-copy
    witness and first box output: `ray_length_up after_center_copy`
    Windows `0.79773343` vs local `0.77992159`, while center/right
    center-copy match; after box pass 1 Windows remains higher
    (`center +0.00765908`, `up +0.00722814`, `right +0.00512678`).
  - normalized comparison focus is now `center-copy-or-boxfilter-input`, with
    a stronger suspicion on exact OpenCV AVX2 `boxFilter` / Mat alias behavior
    or the local witness baseline around the center-copy sample.
- 2026-06-22 local OpenCV baseline now records the exact 50-sample horizontal
  input window for each traced `boxFilter` witness and pass:
  - baseline dir:
    `refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac`;
  - window plan:
    `refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.md`;
  - smoke:
    `refs/scripts/smoke_olmkirakira_trace_box_windows.py` checks that each
    recorded window mean matches the local OpenCV `boxFilter` output sample.
  For the vertical len=50 case, OpenCV default `anchor=(-1,-1)` resolves to
  `anchor_x=25`; the three pass-1 witness windows are `x=937..986` for
  `center` and `ray_length_up`, and `x=987..1036` for `ray_length_right`.
  These windows should be the next Windows trace target before changing the
  Mac/C++ implementation.
- Packaged Windows request:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_boxfilter_pass1_microprobe_20260622_012255.zip`.
  This package includes the 2026-06-22 local window plan and a return template
  that asks for the resolved source x range, 50 contributing samples or an
  equivalent sum/min/max/hash, raw normalized sum, stored pass-1 float, and
  src/dst Mat headers.
- 2026-06-24 combined runtime return answers that microprobe. Windows captured
  the pass-1 source windows and after-pass outputs for the three witnesses.
  The resolved x ranges match the local 50-sample plan, the same source and
  destination Mats were used, and the source-window mean delta equals the
  after-pass output delta for all witnesses. This rules out the pass-1
  contributing-window selection, `BORDER_REFLECT_101` resolution, AVX2
  accumulator/store, and wrong Mat stage for this trace. The remaining cause
  is upstream source-buffer content that is already brighter before
  `boxFilter`.
- Current comparison:
  `refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe_20260624.md`.
  Classification: `boxfilter-pass1-upstream-source-buffer-content`.

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

The next useful evidence is not another broad PNG set. The forward-warp
geometry, first `boxFilter` arguments, pass-1 contributing windows, and pass-1
store behavior are now known. The remaining target is earlier than
`boxFilter`: trace or statically ground the source-buffer fill / center-copy
stage that makes the pass-1 source window brighter on Windows.

Start with the narrow `ray_length_up after_center_copy` discrepancy and prove
whether the Windows value comes from the same Mat/address stage as the local
baseline. Do not tune `boxFilter` size, border, or accumulator rules from the
current residual.

The project-local 2026-06-22 window plan gives the exact local rows and
50-sample arrays for that narrow trace:
`refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.json`.

Only after that should the C++/Mac implementation change.

2026-06-20 Windows overnight return:

- Bundle: `handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`
- KiraKira trace package:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_stage_values_20260620_overnight.zip`
- Request id: `kirakira_fun_181150790_stage_values_20260620`
- Imported comparison:
  `refs/reports/runtime_trace_comparisons/kirakira_stage_values_20260620/olmkirakira_stage_values.md`
- Conclusion: no local C++/Mac implementation change is justified from this
  return alone. It confirms the wrapper choreography but does not reveal the
  first numeric divergence.

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
- Use this JSON as the Mac/OpenCV-side baseline for the next deeper Windows
  `FUN_181150790` trace; do not promote a PNG-only tweak unless the stage
  values identify the first numeric divergence.
- Current project-local baseline:
  `refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json`.
  Recreate it with `OLM_PROBE_PYTHON` pointing at an OpenCV 4.5.5 probe Python,
  then run `python3 refs/scripts/write_olmkirakira_trace_baseline.py --out-dir
  refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac`.
- 2026-06-20 read-only audit conclusion after return: the first wrapper pass
  was too shallow to separate first divergence. The next trace should target
  concrete storage/sample values rather than wrapper entry alone.
- 2026-06-21 Mac-side recheck while Smoother2 is paused:
  - `smoke_olmkirakira_cpp_cli.py` remains expected-red on the old three-case
    scaffold: `case_0001 max=21 mean=0.8291`, `case_0002 max=24 mean=1.1609`,
    `case_0003 max=233 mean=53.8132`.
  - The OpenCV 4.5.5 probe Python passes
    `smoke_olmkirakira_opencv_screenover_probe_cli.py` on the guarded
    single-ray set; representative residuals remain `max=13/13/23/23/66`,
    and Strength=0 anchors remain `max=0..3`.
  - The OpenCV two-temp and alias-ROI probes both remain expected-red but
    sharply better than native C++ for old `case_0003`:
    `case_0001 max=21 mean=0.8239`, `case_0002 max=24 mean=1.1568`,
    `case_0003 max=26 mean=1.0477`. Alias-ROI remains byte-equivalent to
    ordinary two-temp.
  Interpretation: do not tune the native C++ scaffold from PNGs. The strongest
  Mac-side evidence is still the OpenCV 4.5.5 trace baseline; the missing fact
  is the first Windows-vs-Mac stage divergence inside `FUN_181150790`.

2026-06-21 deep witness plan:

- Generated local OpenCV baseline witness plan:
  `refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.md`
  and
  `refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/witness_plan.json`.
- The plan fixes three ray-helper witness points for the vertical len=50 case:
  center `(source 960,540 / temp 962,962)`, ray-length-up
  `(source 960,490 / temp 962,912)`, and ray-length-right
  `(source 1010,540 / temp 1012,962)`.
- Required Windows evidence is now stage-by-stage values at those exact
  coordinates after center-copy, forward warp, each of the three boxFilter
  passes, rotate-back, final copy, and then aggregation/merge compose samples.
- Prepared runtime trace profile:
  `kirakira-stage-values-deep` / request id
  `kirakira_fun_181150790_deep_stage_values_20260621`.
- This should classify the first divergence as one of:
  center-copy, forward-warp, box-filter-pass-1/2/3, rotate-back, final-copy,
  aggregation, or compose. Wrapper hit counts alone remain insufficient.

2026-06-21 deep trace return:

- Returned zip stored at
  `refs/returns/windows/20260621_1929_kirakira_deep_stage_values/olm_runtime_trace_kirakira_deep_stage_values_20260621_021018_return_windows.zip`.
- Imported partial summary:
  `refs/reports/kirakira_deep_stage_values_20260621/runtime_trace_summary_kirakira_deep_stage_values_20260621.md`.
- Comparison:
  `refs/reports/kirakira_deep_stage_values_20260621/runtime_trace_comparisons/olmkirakira_deep_stage_values.md`.
- Regression guard:
  `refs/scripts/smoke_compare_kirakira_stage_trace.py` covers both the
  original sparse stage request and this deep-stage request id, including
  deep-stage delta computation and `forward-warp-or-boxfilter-input` focus
  selection.
- `scripts/compare_kirakira_stage_trace.py` now also emits a
  `first_divergence` field and Markdown section. For the 2026-06-21 deep
  return, the first concrete Windows-vs-local delta is
  `after_box_1 / center`, Windows higher by `+0.00765908`.
- The same request id is marked superseded in
  `refs/reports/runtime_trace_superseded.json` because the useful partial has
  already narrowed the next focus; re-sending the same package is low-value.
- Next proof should capture the missing center-copy / forward-warp witness
  values or microprobe the exact Windows AVX2 boxFilter input/first pass. Do not
  change final aggregation or compose from this trace.
- Focused follow-up package generated:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_forward_warp_box_input_20260621_212028.zip`.
  Request id: `kirakira_forward_warp_box_input_20260621`. This supersedes
  re-sending the broad deep-stage request by asking only for the missing
  after-center-copy, after-forward-warp, before-box-pass-1, and after-box-pass-1
  typed float values at the three fixed witnesses.

2026-06-22 boxFilter pass-1 microprobe:

- The forward-warp / box-input trace proved the wrapper-level geometry and
  first pass arguments match locally, so the remaining question is inside or
  immediately around OpenCV 4.5.5 AVX2 `FUN_1812e39d0`.
- Local window plan:
  `refs/reports/olmkirakira_boxfilter_window_plan_20260622/witness_plan.md`.
- Packaged focused request:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_boxfilter_pass1_microprobe_20260622_012255.zip`.
  Request id: `kirakira_boxfilter_pass1_microprobe_20260622`.
- `scripts/compare_kirakira_stage_trace.py` now understands this request and
  classifies focused returns as:
  - `boxfilter-pass1-different-window-or-border-reflect`
  - `boxfilter-pass1-accumulator-precision-or-store`
  - `boxfilter-pass1-boxfilter-pass1-window-matches`
  - `boxfilter-pass1-window-values-without-store`
  - `boxfilter-pass1-store-values-without-window`
  - `boxfilter-pass1-trace-structure-present-values-missing`
- The same comparison JSON/Markdown now emits `recommended_next_evidence`.
  Treat that as the stop/go note for the next Mac-side implementation step:
  sparse returns must not drive tuning; concrete window/store/Mat evidence can.
- After importing a Windows return, run:

```
python3 scripts/compare_kirakira_stage_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary.json \
  --local-trace-json refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json \
  --output-json refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe.json \
  --output-md refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe.md
```

Implementation stop line: do not change KiraKira aggregation, final compose, or
ray geometry from this path. The next code change should follow the pass-1
microprobe classification: contributing window/border rule, accumulator/store
precision, or Mat/address stage.
