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
- 2026-06-24 decision matrix:
  `refs/conformance/olmkirakira_8bpc_decision.md`
  classifies the current blocker as `blocked-compose-or-final-quantization`.
  Ray-helper stages match Windows within float print precision after the
  BT.709 seed fix, and `FUN_18114fd90` aggregation is grounded at three
  witnesses. The merge-mode-1 internal compose/writeback site is still
  unisolated, so do not reopen luma, boxFilter, ray-helper choreography, or
  global compose scale from PNG residuals.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Merge mode 1 composes with screen RGB and source-alpha passthrough. | Strength=0 single-ray refs; `notes/OLMKiraKira_ASM_FACTS.md`. | reference-confirmed / binary-aligned |
| Zero-length rays are skipped entirely. | `FUN_18114f4a0` guards `length != 0`; single-ray refs. | binary-grounded |
| Channel 2 seed uses BT.709 luma coefficients, not BT.601. | 2026-06-24 runtime-trace reconciliation: input RGB `[230,210,60]` gives old local `0.77992159` with BT.601 but Windows pre-boxFilter plateau `0.79773343`, matching BT.709 `0.7977333`. | runtime-trace reconciled |
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
| Blur Mode 1 | One horizontal `boxFilter` call through `FUN_181280bc0`; branch `0x181150958 -> 0x18115122e`, call at `0x181151290`. | static binary dispatch |
| Blur Mode 2 | Three-pass horizontal `boxFilter` helper path; calls at `0x18115116f`, `0x1811511c2`, `0x181151215`. | static binary dispatch |
| Blur Mode 3 | One call to `FUN_181272ec0`, the recovered GaussianBlur wrapper; branch `0x18115096a -> 0x1811510a9`. The actual-AEX boundary is `_InputArray(CV_32FC1)`, `_OutputArray(CV_32FC1)`, `Size(0,1)`, `sigmaX = length * 0.5`; `0.5` is the binary `double` at `0x18148d670`. | static binary + actual-AEX boundary |
| Blur Mode 4 | Inline recursive/separable accumulation body at `0x181150979..0x181150f3a`; no subordinate filter call. The UI label “Exponential” is semantic metadata, not derived from the body alone. | static binary dispatch/body |
| Merge Mode 1/2 | `param_15==1` selects `FUN_18114fd90`; `==2` selects `FUN_18114ffd0`. | static vtable dispatch |
| Channel | Seed function; current traced `Channel=2` vtable normalize byte returns `1`. | vtable / refs |

## Current Mac Source Gap Audit

This section is about the current Apple Silicon port source, not the grounded
Windows behavior.

- `Brightness Gain`
  - current Mac source reads `params[OLMKIRAKIRA_BRIGHTNESS_GAIN]->u.fs_d.value`
    as a float, which matches returned witness manifests that include real
    values like `9.39999961853027`
  - however, the Windows fresh range capture reports metadata `1..100`, so the
    host-control unit mapping is still unresolved
- `Fade Out`
  - current Mac host range now matches the Windows fresh capture `0..1`
  - but the render path still does not consume a Fade Out value at all
- `Highlight Radius`
  - current Mac source registers the parameter, but the render path does not
    consume it
  - Windows fresh range says `0..500`, while the official manual/source shape
    still suggests `0..1000`
- `Approximated Input`
  - exposed in the Windows UI and current Mac UI, but not consumed in the
    current Mac render path
- `Merge Mode`
  - current Mac source always composes with the merge-mode-1 screen-over path;
    it does not branch on the UI Merge Mode control yet
- `Blur Mode`
  - current Mac source now exposes the Windows four-choice host surface, but
    only Modes 1 and 2 have grounded render dispatch
  - Modes 3 and 4 still deliberately use the Mode 2 three-box scaffold; the
    Mode 3 warp/Gaussian contract is grounded and its portable Gaussian
    primitive is now the remaining implementation boundary
- `Highlight Color` and the five `Use Ramp` toggles
  - current Mac source reads them into `OLMKiraKiraInfo`, but the render path
    does not consume them yet
- `Ramp` / color-ramp custom controls
  - still absent from the current Mac UI surface

## Algorithm IR

1. Build seed from input according to Channel and Strength.
2. For each nonzero directional ray:
   - allocate two temporary Mat-like float canvases using AEX temp extent
     formula;
   - center-copy the source seed into the first temp ROI;
   - forward-rotate through OpenCV `warpAffine` semantics;
   - dispatch Blur Mode: one box filter (1), three box filters (2), horizontal
     Gaussian with `Size(0,1)` and `sigmaX = length * 0.5` (3), or the inline
     recursive accumulation body (4);
   - rotate back through OpenCV `warpAffine` semantics;
   - center-copy back to the final ray buffer.

The Mode 3 synthetic actual-AEX witness records 59 nonzero float cells after
the ROI copy and 63 after the forward warp. The corrected 5-degree matrix is
`[cos, sin, tx; -sin, cos, ty]`; OpenCV 4.5.5 reproduces all 63 post-warp
float32 words exactly. An earlier all-zero artifact came from omitted libm
imports in the emulator and is not admissible evidence.

The same corrected harness now runs the embedded Gaussian body to caller
return `0x181151105` and records all 63 CV_32FC1 output words. Those words do
not match pinned OpenCV 4.5.5 or the portable primitive at any position. Since
the harness supplies synthetic TLS and a zero-initialized CPU-dispatch table,
the completed local path is not yet a live-Windows oracle. Validate dispatch
selection or capture the bounded output in a live Windows process before
using those words to change production behavior.
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
- 2026-06-24 Mac-side reconciliation found the upstream source-buffer
  difference: the local CLI was using BT.601 luma for Channel 2 seed. The
  Windows plateau `0.79773343` for RGB `[230,210,60]` equals BT.709 luma
  (`0.2126R + 0.7152G + 0.0722B`), while the old local plateau
  `0.77992159` equals BT.601. `refs/scripts/olmkirakira_cli.py` now uses
  BT.709 in AEX seed mode for channel 2.
- New BT.709 local trace:
  `refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json`.
  New witness plan:
  `refs/reports/olmkirakira_boxfilter_window_plan_20260624_bt709/witness_plan.md`.
  The first-pass witness deltas from the Windows return are explained by this
  luma correction: center `+0.00765902`, ray-length-up `+0.00722808`, and
  ray-length-right `+0.00512671`.
- 2026-07-12 implementation audit found that the C++ CLI and Mac plug-in had
  retained the old BT.601 constants even though the Python witness path and
  this IR were already corrected. Both production C++ paths now use the
  runtime-proven BT.709 coefficients. This closes only Channel 2 seed luma;
  compose/writeback and the remaining blur/merge modes stay unresolved.

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
store behavior are now known. The specific 2026-06-24 upstream source-buffer
delta is explained by BT.709 seed luma, so do not request another trace for
that witness until the updated BT.709 CLI residual is remeasured.

Next Mac-side step: rerun the KiraKira OpenCV/CLI comparisons against the
Software references with the BT.709 seed. If residuals remain, compare from
pass 2 / rotate-back / aggregation with the new BT.709 trace baseline rather
than returning to `boxFilter` window or seed-luma hypotheses.

2026-06-24 BT.709 remeasure completed this Mac-side step against
`kirakira_single_ray_20260606` using the OpenCV 4.5.5 probe environment and
the current `aex-screen-over` Python CLI. The report is stored at
`refs/reports/olmkirakira_remeasure_20260624_bt709_software/reports/diff.json`
and the Software rows are:

| Case | max | mean | Classification |
| --- | ---: | ---: | --- |
| vertical len50 brightness1 strength100 | 14 | 1.6006 | residual remains |
| horizontal len50 brightness1 strength100 | 11 | 1.6365 | residual remains |
| diagonal len50 brightness1 strength100 | 23 | 1.5068 | residual remains |
| diagonal2 len50 brightness1 strength100 | 23 | 1.5212 | residual remains |
| vertical len50 brightness94 strength0 | 1 | 0.0215 | strength-0 near-match |
| horizontal len50 brightness94 strength0 | 0 | 0.0000 | exact for this slice |
| diagonal len50 brightness94 strength0 | 3 | 0.0238 | strength-0 near-match |
| diagonal2 len50 brightness94 strength0 | 3 | 0.0238 | strength-0 near-match |
| diagonal len50 rotation13 | 66 | 1.8809 | residual remains |

Conclusion: BT.709 fixes the traced pass-1 source-window explanation but does
not make the final PNGs exact. The remaining useful Mac-side work is
stage-local: compare the BT.709 trace baseline from pass 2 through rotate-back
and final aggregation. Do not reopen first-pass window selection, border mode,
or luma coefficients unless a new trace contradicts this measurement.

The same BT.709 trace was compared against the 2026-06-21 deep Windows stage
trace in
`refs/reports/runtime_trace_comparisons/olmkirakira_deep_stage_values_20260624_bt709.md`.
All captured ray-helper stages now match within float print precision:
box pass 1, pass 2, pass 3, rotate-back, and final center-copy are all within
`1e-5` (`~3e-8..1.2e-7` observed deltas). This moves the remaining single-ray
PNG residual out of ray generation for the captured vertical witness and into
aggregation, screen-over compose, or final quantization/export behavior.
The focused Windows follow-up package is
`refs/runtime_trace_packages/olm_runtime_trace_kirakira_aggregation_compose_bt709_20260624.zip`
(Finder/send copy:
`handoffs/windows_batch/olm_runtime_trace_kirakira_aggregation_compose_bt709_20260624.zip`).

Mac-side residual hotspot extraction from the same BT.709 Software remeasure
now gives concrete trace targets:

| Target | Case | XY | Windows RGBA | Local BT.709 RGBA | Candidate - Windows |
| --- | --- | ---: | --- | --- | --- |
| Primary | vertical len50 brightness1 strength100 | `(934,118)` | `[131,131,131,255]` | `[145,145,145,255]` | `[14,14,14,0]` |
| Optional largest observed | diagonal len50 rotation13 | `(1098,202)` | `[112,112,112,255]` | `[46,46,46,255]` | `[-66,-66,-66,0]` |

The active package asks Windows to trace aggregation, screen-over compose, and
final byte/writeback values at the primary vertical hotspot first. The
rotation13 hotspot is useful only if the debugger setup can cheaply switch to
that case; it should not delay the primary vertical-case answer.

2026-06-24 Windows return for
`kirakira_aggregation_compose_bt709_20260624` is imported and compared in
`refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md`.
It directly grounds `FUN_18114fd90` for the center/up/right witnesses:

| Point | Ray input alpha | fd90 glow RGBA | PNG-facing output |
| --- | ---: | --- | --- |
| center `(960,540)` | `0.71891218` | `[1,1,1,0.71891218]` | `[124,124,124,255]` |
| up `(960,490)` | `0.76832885` | `[1,1,1,0.76832885]` | `[240,229,144,255]` |
| right `(1010,540)` | `0.71564364` | `[1,1,1,0.71564364]` | `[123,123,123,255]` |

The internal merge-mode-1 compose float/writeback site was not isolated, so the
current `aex-screen-over` compose remains a near-match model rather than a
binary-grounded rule. The PNG-facing bytes nevertheless let us invert the
screen equation for the traced points. Using
`out = 1 - (1 - src) * (1 - effective_glow_alpha)`, the implied compose
scale relative to the fd90 glow alpha is:

| Point | fd90 alpha | implied effective alpha | implied scale |
| --- | ---: | ---: | ---: |
| center `(960,540)` | `0.71891218` | `0.41777778` | `0.58112491` |
| up `(960,490)` | `0.76832885` | `~0.41766382` | `~0.54360033` (`0.52061041..0.56065737` by RGB channel) |
| right `(1010,540)` | `0.71564364` | `0.41333333` | `0.57756865` |

This points at a compose/writeback-side attenuation or color-dependent detail
after fd90, not at luma, boxFilter, ray-helper choreography, or fd90 itself. A
Mac-side gain probe rejected the tempting simple fix: `--gain-scale 0.60`
improves some strength-100 max values but worsens total Software mean versus
the current `0.62` (`8.7974` vs `8.2150` over the 9 Software single-ray rows),
while direct `--scale-override 1.0` badly worsens all strength-0 anchors. Do
not change the production/default KiraKira compose scale from this return
alone.

A C++ cross-check on the same 9 Software single-ray rows with
`--warp-mode aex-two-temp-mapremap-f32` confirms that point-wise implied scale
does not promote to a global gain change:

| gain-scale | max diff | mean sum | exact |
| ---: | ---: | ---: | ---: |
| `0.58` | `67` | `9.802595` | `2/9` |
| `0.60` | `66` | `8.041545` | `2/9` |
| `0.62` | `66` | `7.081053` | `2/9` |

This keeps `0.62` as the best measured global scale among those three C++
probes and leaves the next target as compose/writeback structure, not scalar
retuning.

The 2026-06-29 pending compose-proof contract now ties that conclusion to the
latest bundled Windows runtime summary:
`refs/conformance/olmkirakira_pending_compose_proof_20260629.md`.
That contract explicitly freezes the primary residual-hotspot ask at
`kk_vertical_len50_brightness1_strength100 (934,118)` with Windows
`[131,131,131,255]` vs current Mac BT.709 `[145,145,145,255]`, plus the
optional `rotation13 (1098,202)` hotspot. It also records that the latest
bundle still leaves `merge_mode_1_compose.composed_rgba_float` and
`pre_writeback_rgba_float` unisolated, so the next useful Windows return must
capture that internal compose/quantization boundary instead of re-opening
BT.709 luma, boxFilter pass-1, ray-helper choreography, or global gain.

2026-06-30 live Mac AE compose-boundary witness:

- A new env-gated Mac plug-in dump now captures source RGBA, normalized glow
  RGBA, post-opacity glow alpha, pre-writeback composed RGBA, and final plugin
  `u8` at selected pixels.
- Running the real AE plug-in on
  `kk_vertical_len50_brightness1_strength100` shows the primary residual
  hotspot `(934,118)` already diverges at the compose boundary:
  Mac `out_u8=(144,144,144,255)` exactly matches the saved PNG candidate, while
  the Windows reference stays `[131,131,131,255]`.
- The same holds for the control witnesses `(960,540)`, `(960,490)`, and
  `(1010,540)`: the Mac compose-boundary bytes agree with the Mac saved PNGs.
- This does not yet distinguish "Windows fd90 glow differs at the hotspot"
  from "Windows merge-mode compose attenuates differently", but it does reject
  a pure final-export explanation for the Mac side. See
  `refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.md`.
- The same witness also sharpens the next Windows decision boundary
  numerically. At hotspot `(934,118)`, source gray is `30/255`; Windows final
  `[131,131,131]` implies effective screen alpha `0.44888888...`, while the
  current Mac plug-in logs `glow_alpha_after_opacity=0.507505655` and
  `out_u8=[144,144,144]` at the compose boundary. So the unresolved lane is
  now: "Windows hotspot alpha path is about `0.0586` lower than the current
  Mac direct-use compose path." The next useful Windows witness must say
  whether that drop already exists at fd90/post-opacity glow alpha, inside
  merge-mode-1 compose, or only in the last pre-writeback float/writeback
  helper.

2026-06-24 decision matrix:

- `scripts/analyze_kirakira_decision_matrix.py` combines the BT.709 remeasure,
  deep stage comparison, pass-1 microprobe, and aggregation/compose return.
- Latest report:
  `refs/conformance/olmkirakira_8bpc_decision.md`.
- Machine decision: `blocked-compose-or-final-quantization`.
- BT.709 Software set: 9 cases, 1 exact, max-diff max `66`, mean sum
  `8.215029`.
- Group split:
  - `strength100_single_ray`: 4 cases, max `23`, mean sum `6.265140`.
  - `strength0_anchor`: 4 cases, max `3`, mean sum `0.069035`, 1 exact.
  - `rotation13`: 1 case, max `66`, mean `1.880854`.
- New compose-scale inversion in the decision matrix shows the traced
  center/right samples imply roughly `0.58x` fd90 alpha at final screen
  compose, while the colored up sample is channel-dependent (`0.52..0.56x`).
  Treat this as the next Mac-side compose model audit target, not as permission
  to retune a global gain.
- Ray helper: `grounded-within-float-print-precision`, max captured stage
  delta about `1.23e-7`.
- Aggregation: `fd90-grounded-compose-unisolated`. Center/up/right
  `FUN_18114fd90` glow RGBA is grounded, but internal merge-mode-1
  compose/writeback is still missing.
- Action: do not retune luma coefficients, boxFilter windows, ray-helper
  geometry, or global compose scale. Next Mac-side work should audit compose
  models that improve strength-100 residuals without breaking strength-0
  anchors. If Windows is needed later, request a compose-site/pre-writeback
  witness at the BT.709 residual hotspot only.

2026-06-25 compose model audit:

- Report:
  `refs/reports/olmkirakira_compose_model_audit_20260625/compose_model_audit.md`.
- Machine decision: `preserve-current-compose-model`.
- Six compose candidates were checked against the 9 BT.709 Software rows:
  current gain `0.62`, gain `0.60`, inverse-trace-inspired gains
  `0.5811` and `0.5436`, direct `scale_override=1.0`, and premultiplied
  compose.
- Current `aex-screen-over` gain `0.62` is best by total mean and best by max:
  `1/9` exact, max `66`, mean sum `8.215029`.
- `0.60` keeps the same max but worsens total mean to `8.797406`.
  `0.5811` / `0.5436` worsen the aggregate and max. `scale_override=1.0`
  breaks strength-0 anchors (`0/9`, max `113`). Premultiplied compose is also
  rejected (`0/9`, mean sum `26.803340`).
- Conclusion: do not change the default compose scale or promote premultiplied
  compose from PNG residuals. This is now historical compose-target evidence;
  after the 2026-07-01 hotspot witness, the live lane is no longer direct
  compose/pre-writeback isolation but same-run export provenance,
  witness-placement validation, or endgame control coverage.

2026-07-01 hotspot witness closure:

- Report:
  `refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.md`.
- Consolidated audit:
  `refs/conformance/olmkirakira_hotspot_lane_audit_20260701.md`.
- Provenance split audit:
  `refs/conformance/olmkirakira_reference_provenance_audit_20260701.md`.
- Source-candidates audit:
  `refs/conformance/olmkirakira_source_candidates_audit_20260701.md`.
- At the primary hotspot `(934,118)`, the answered Windows trace now reports:
  - `glow_after_opacity_rgba_float = [1,1,1,0.507505655]`
  - `composed_rgba_float = [0.565446166..., 0.565446166..., 0.565446166..., 1]`
  - `pre_writeback_rgba_float = [0.565446166..., 0.565446166..., 0.565446166..., 1]`
  - `final_writeback_or_png_rgba = [144,144,144,255]`
- Those values agree with the current Mac compose-boundary witness rather than
  with the canonical Windows reference PNG `[131,131,131,255]`.
- The provenance split is now frozen more explicitly too:
  - canonical Windows reference PNG hotspot: `[131,131,131,255]`
  - current Mac compose-boundary witness hotspot: `[144,144,144,255]`
  - answered Windows traced hotspot: `[144,144,144,255]`
  - archived BT.709 candidate PNG hotspot: `[145,145,145,255]`
- That three-way split is recorded in
  `refs/conformance/olmkirakira_reference_provenance_audit_20260701.md`, so
  this lane should stay out of compose/gain retuning unless stronger contrary
  evidence appears.
- A matching machine-readable export contract now fixes what later evidence is
  allowed to mean:
  `scripts/analyze_olmkirakira_hotspot_export_contract.py`,
  `refs/scripts/smoke_analyze_olmkirakira_hotspot_export_contract.py`, and
  `refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.md`
  keep the lane at `awaiting-same-run-export-or-witness-placement-proof` until
  a current-AEX export or explicit witness-placement/endgame-control artifact
  lands. When it does, classify it first as:
  - export matches traced hotspot `144`
  - export matches canonical reference `131`
  - export matches archived BT.709 candidate `145`
  - or none of the above
  before touching source.
- A new source-order freeze now makes that operationally explicit:
  `refs/conformance/olmkirakira_source_candidates_audit_20260701.md`
  keeps a non-source gate ahead of any Mac patch, reopens `RenderTyped(...)`
  screen compose only if a same-run export/reference contradiction appears,
  keeps `AddColoredUnion(...)` second-order only, and splits highlight/ramp
  coverage into a separate schema/endgame lane rather than a hotspot math fix.
- So the remaining KiraKira hotspot is no longer permission to retune
  merge-mode-1 compose, hotspot-local attenuation, or final quantization from
  this witness alone. The live lane shifts to:
  - reference/export provenance,
  - witness-placement drift, or
  - still-missing endgame control coverage outside this hotspot trace.

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
