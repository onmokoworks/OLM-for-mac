# Binary-Grounded IR: OLMDistanceGradation

## Feature

- Plug-in: Distance Gradation
- Feature/path: 8bpc alpha-mask distance gradation, interpolation, optional blur
- Bit depth: 8bpc documented here; 16bpc is under active AE validation;
  32bpc still needs references
- Reference set: `refs/win_references/20260605_extra/OLMDistanceGradation`
- Current status: packaged 8bpc Mac AE validation is `AE exact` for the
  basic/extended/blur request sets. The AE-free CLI still has guarded
  residuals, so the shared binary-grounded field-prep/OpenCV spec is not yet
  complete. 16bpc is not AE exact yet; 32bpc remains untested.
- 2026-06-22 reference provenance audit confirms all 29 packaged AE-host
  candidates match the 20260618 normalized Software references exactly. The
  visible residuals against `refs/win_references/20260605_extra` are
  reference-generation differences, not current AE-host failures.
- Cross-feature canonicalization audit:
  `refs/reports/software_reference_canonicalization_8bpc.md` classifies all
  three DistanceGradation groups as `normalized-software-exact`:
  basic 12/12, extended 16/16, and blur 1/1. Legacy drift remains only in the
  older 20260605 extra references.
- 2026-06-24 decision matrix:
  `refs/reports/olmdistancegradation_decision_matrix_20260624/decision_matrix.md`
  consolidates provenance, canonicalization, and the latest trace comparison.
  It classifies normalized 8bpc as `29/29 exact`, legacy drift as 7 old-ref
  cases, and the current runtime trace as `not-actionable` (`await-windows-trace`).
  Preserve normalized AE-exact behavior; do not tune DistanceGradation from
  legacy-only drift or AE-free CLI residuals.
- 2026-06-29 `case_0026` runtime return answered the main branch question:
  Windows 16bpc Software already has the row-0 scalar ramp in the field before
  `FUN_181170480` compose. The compose callback is not creating the ramp from a
  saturated field. The next useful Mac-side check is rerendering this case with
  the current installed Mac plug-in, because the older 2026-06-26 candidate may
  be stale relative to the current source/model.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Generates gradation inside/outside an alpha-channel mask. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMDistanceGradation__OLMDistanceGradation__doc__DistanceGradationUserManualEN.txt`. | manual-backed |
| Local description says distance transform. | `mac/OLMDistanceGradation/OLMDistanceGradation_Strings.cpp`. | manual/local-backed |
| Current mac port implements exact Euclidean distance transform equivalent to OpenCV `distanceTransform(DIST_L2, DIST_MASK_PRECISE)`. | Comments and code in `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`. | implementation-grounded |
| Distance field is thresholded then normalized by actual max, not always by threshold. | Current mac implementation comments and CLI behavior. | implementation-grounded / guarded |
| Gaussian blur uses OpenCV-style separable kernel with `BORDER_REFLECT_101` and default sigma formula. | Current mac implementation comments and Python CLI. | implementation-grounded |
| Constant+Blur first thresholds the normalized field to a binary full-distance field and uses doubled radius. | Current mac/Python implementation and guarded `case_0029` result. | guarded / inferred |
| Windows AEX embeds OpenCV 4.5.5. | `decomp/DistanceGradation.aex.c.txt` contains OpenCV 4.5.5 build strings and source paths. | binary-grounded |
| Per-pixel compose path implements Sphere with `sqrt(1 - (1 - X)^2)` and Power with `powf(X, power)`. | `decomp/DistanceGradation.aex.c.txt` around `FUN_181170870` and sibling 16/float compose functions. | binary-grounded |
| 8bpc compose reads the distance field from the green byte of the field pixel and applies invert/interpolation in `FUN_181170870`. | `decomp/DistanceGradation.aex.c.txt` `FUN_181170870`: `_X = field_pixel[green] / 255`, then optional `1 - X`, Sphere/Power, and final RGBA byte cast. | binary-grounded |
| 8bpc compose is an AE iterate callback over a prebuilt field world. | `FUN_181170380` requests `PF Iterate8 Suite` and passes callback `FUN_181170870` with user data `param_4 + 0x2c`; `FUN_181170870` then reads the field world through `param_1[1]`. | binary-grounded |
| 16bpc and float compose use sibling iterate callbacks. | `FUN_181170280` requests `PF iterate16 Suite` and passes `FUN_181170480`; float path stores callback `FUN_181170c90`. | binary-grounded |
| 16bpc compose scales by `32768.0`, reads pixels with `1/32768`, and appears to write via `CVTTSS2SI`. This is a binary fact, but it is not yet adopted as the Mac output rule. | `FUN_181170480` uses `DAT_181504a80 = 1/32768`, `DAT_181504ac4 = 32768`, then `CVTTSS2SI` before storing 16-bit ARGB words. A 2026-06-26 Mac AE experiment that globally switched the port to truncation kept the exact count flat and worsened several 16bpc residuals, so the current port keeps round-to-nearest while source/field packing is unresolved. | binary-grounded / implementation-rejected-for-now |
| 16bpc compose's color-selection shape matches the current Mac implementation: `render_mode==1` selects Gradation Color, `render_mode==2` selects source-layer RGB, and `use_bg!=0` mixes `BG*(1-X) + inner*X` while `use_bg==0` keeps `inner` RGB and uses `alpha = d_alpha * X`. | `FUN_181170480` around `181170720..1811707f4`. | binary-grounded |
| OpenCV border names including `BORDER_REFLECT_101` are present in the AEX. | `decomp/DistanceGradation.aex.c.txt` contains `cv::copyMakeBorder` and border-name table strings. | binary-grounded for availability, not final blur branch proof |
| 16bpc Inside mode with an all-opaque input mask and no zero-distance source should compose to final `X=0` regardless of `Invert`. | 2026-06-26 Mac AE 16bpc validation: `olmdistancegradation_basic__case_0002` changed from full red/opaque to exact when the pre-invert field is forced to `0` for `Invert=ON` and `1` for `Invert=OFF`; previously exact all-opaque Inside cases stayed exact. | measured Windows-reference-backed / needs static trace |
| 2026-06-26 local Mac AE rerun reproduces three unresolved 16bpc residual families: threshold/ramp mismatch (`case_0010..0016`), BG-like vs Grad-like binary decisions under `Render Mode=1` + background color (`case_0020..0023`), and RGB-zeroed/alpha-preserved output (`case_0027/0028`). | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_204952_rerun/...`, `refs/conformance/bitdepth_16bpc_mac_ae_rerun_20260626_204952.md`, and `refs/conformance/olmdistancegradation_16bpc_focus_cases_20260626.md`. | AE-validation diagnostic |
| 2026-06-26 Mac AE host debug confirms the 16bpc packaged parameters for `olmdistancegradation_extended__case_0027` are applied exactly inside After Effects; the residual is not a bad request/JSX path. | `scripts/ae_debug_distancegradation_case.jsx` output `handoff/ae_pixel_validation_20260618/OLMDistanceGradation_case_debug.json`. | AE-host-grounded |
| 2026-06-26 Mac AE probe on `case_0027` rules out request drift and provides an observable field witness: native 16-bit decoding of `layer_no_bg` shows the compose/background branches are active, but the observed `X` remains much closer to `1.0` than the current distance model predicts at key pixels. | `refs/conformance/olmdistancegradation_16bpc_case0027_mac_ae_probe_20260626.md`, `refs/conformance/olmdistancegradation_16bpc_case0027_probe_x_20260626.md`, and probe PNGs in `handoff/ae_pixel_validation_20260618/probes/distancegradation_case0027_variants/`. | AE-host-grounded |
| 2026-06-26 field probes suggested `case_0020..0023` might only diverge once `Use Background Color=1` participates, but a 2026-06-27 Windows bg-compose return invalidates that simplification: Windows `bg_off` still keeps the grad-color opaque witness for `case_0020..0022`, and `case_0023 bg_off` still does not match the prior Mac `no_bg` probe over the full frame. `case_0027/0028` remain active Mac-side field mismatches even in the `no_bg` probe. | `refs/conformance/olmdistancegradation_16bpc_field_cases_probe_20260626.md`, `refs/conformance/olmdistancegradation_16bpc_bg_compose_variants_return_20260627.md`, and probe PNGs in `handoff/ae_pixel_validation_20260618/probes/distancegradation_field_cases/`. | AE-host-grounded + Windows-reference-grounded |
| 2026-06-28 Mac-side analysis of the largest current 16bpc residual (`extended case_0026`) classifies it as `candidate_x_saturated_to_gradation_color_while_reference_ramps`: on changed pixels the Mac candidate has inferred compose `X≈1.0`, while Windows Software spans `X≈0.0..1.0`; row `y=0,x=3..14` shows Windows ramping from `X≈0.812` to `0.001` while Mac stays at `1.0`. | `refs/conformance/olmdistancegradation_16bpc_case0026_analysis_20260628.md` and latest candidate/report under `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/`. | AE-validation diagnostic |
| 2026-06-29 Windows runtime trace for `extended case_0026` shows the row-0 scalar ramp already exists before the 16bpc compose callback. Observed field green words at `x=0..14` are `8000,8000,8000,7627,6c4f,6276,589e,4ec5,44ec,3b14,313b,2762,1d8a,13b1,09d9`, which correspond to pre-compose `X` values `1,1,1,0.923065,0.846161,0.769226,0.692322,0.615387,0.538452,0.461548,0.384613,0.307678,0.230774,0.153839,0.076935`. `compose_interpolation_creates_ramp_from_saturated_field=false`; `field_already_ramps_before_compose=true`. | `refs/reports/runtime_trace_comparisons/olmdistancegradation_16bpc_case0026_x_witness_20260629.md` and `refs/reports/runtime_trace_summary.md`. | runtime-trace-grounded / answered-partial |
| 2026-06-29 Mac-side source-model check reproduces the same compact row0 field for `case_0026` from the current DistanceGradation source model, but the current Mac AE rerender still saturates to the Gradation Color endpoint where Windows ramps (`max_diff=61157`, `mean_diff=11754.422780309607`). The first AE automation attempts exposed two separate host facts: `scripts/diagnose_ae_host_block.py` can classify modal/accessibility blockers, and `scripts/run_ae_single_case.py` can set JSX env vars reliably before calling the single-case renderer. | `refs/conformance/olmdistancegradation_16bpc_case0026_current_mac_ae_rerun_20260629.md`, `refs/conformance/olmdistancegradation_16bpc_case0026_current_mac_ae_rerun_20260629.json`, and smoke `python3 refs/scripts/smoke_diagnose_ae_host_block.py`. | AE-host-grounded / implementation mismatch |
| 2026-06-29 Mac AE no-background probe for `case_0026` now completes after switching the single-case JSX parser away from AE 26.3 `JSON.parse`. Disabling `Use Background Color` does not recover the Windows ramp: the probe still stays at or near the Gradation Color endpoint on the row-0 witness, with `max_diff=61155` against the Windows bg-on Software reference. | `refs/conformance/olmdistancegradation_16bpc_case0026_no_bg_probe_20260629.md` and `refs/reports/ae_single_case_olmdistancegradation_case0026_no_bg_20260629_1408/`. | AE-host-grounded / field-prep mismatch |
| 2026-06-29 gated Mac plug-in debug dump proves `case_0026` field prep itself already has the Windows row-0 ramp, but `Power` was read as `3.96332907e-05` instead of `2.59740734` because the port applied `FIX_2_FLOAT` to a `PF_ADD_FLOAT_SLIDERX` value. Removing that conversion recovers the row-0 ramp within `0..4` channel units and reduces `case_0026` from full saturation to `max_diff=11480`, `mean_diff=2.925372`. | `refs/conformance/olmdistancegradation_16bpc_power_param_fix_20260629.md`, `refs/reports/ae_single_case_olmdistancegradation_case0026_debugdump_20260629_1420/field_debug.txt`, and `refs/reports/ae_single_case_olmdistancegradation_case0026_powerfix_20260629_1422/field_debug.txt`. | AE-host-grounded / implementation fix |
| 2026-06-29 post-Power-fix 16bpc extended failures are classified into residual families rather than one mixed failure bucket: 4 Constant/background sparse full-color, 4 Layer/no-bg source-or-alpha ownership, 2 Power/layer source-or-premultiply, 2 Sphere boundary quantization, 1 Power/RGB boundary quantization, 1 sparse boundary quantization, and 1 Both/no-bg zero-threshold edge case. | `refs/conformance/olmdistancegradation_16bpc_powerfix_residual_families_20260629.md` and `scripts/analyze_distancegradation_powerfix_residuals.py`. | AE-host-grounded / residual triage |
| 2026-06-29 representative witness audit makes `case_0020` the smallest next proof: all changed pixels are opaque, the first bad point differs only by endpoint selection (`Windows [7195,0,61165,65535]`, Mac `[65535,0,0,65535]`), and a one-pixel neighbor already matches. `case_0012` remains useful for Layer/no-bg source ownership because alpha matches at the max witness while RGB stays source-low on Mac. | `refs/conformance/olmdistancegradation_16bpc_representative_witnesses_20260629.md` and `scripts/analyze_distancegradation_representative_witnesses.py`. | AE-host-grounded / next-proof narrowing |
| 2026-06-29 `case_0020` point dump proves the representative Constant/background residual is decided before final 16bpc writeback: at `(951,417)` Mac field prep outputs `field_x=1` and the Mac candidate chooses the red endpoint, while `(950,417)` has `field_x=0.999095619` and already matches the Windows blue endpoint. The next suspect is field normalization / local full-distance plateau ownership, not color writeback. | `refs/conformance/olmdistancegradation_16bpc_case0020_field_witness_20260629.md` and `refs/reports/ae_single_case_olmdistancegradation_case0020_pointdebug_20260629_1445/field_debug.txt`. | AE-host-grounded / field witness |
| 2026-06-29 implementing the Constant-specific `THRESH_BINARY` path from `FUN_181174760` fixes the plateau-class error without moving non-Constant families: `case_0020` changes from `1001` pixels to `1`, `case_0021` from `1002` to `1`, `case_0022` from `9347` to `192`, and `case_0023` from `1388` to `73`. The extended 16bpc batch remains `1/16` exact, so this is a grounded improvement, not completion. | `refs/conformance/olmdistancegradation_16bpc_constant_binary_fix_20260629.md` and `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_constant_binary_20260629_1454/reports/ae_pixel_16bpc_extended_constant_binary.json`. | binary-grounded / AE-host-validated implementation fix |
| 2026-06-29 post-fix Constant residuals are all boundary-class: every remaining changed pixel in `case_0020..0023` lies within 1px of the active inside/outside threshold in the source alpha EDT (`case_0020=1/1`, `case_0021=1/1`, `case_0022=192/192`, `case_0023=73/73`). Treat these as OpenCV/AEX distanceTransform threshold ownership, not compose/writeback drift. | `refs/conformance/olmdistancegradation_16bpc_constant_remaining_boundary_20260629.md` and `scripts/analyze_distancegradation_constant_remaining_boundary.py`. | AE-host-grounded / boundary-localized |
| 2026-06-29 direct Layer/no-bg source unpremultiply was tested and rejected. On `case_0012`, it increased coverage from the restored Constant-binary state (`max=16250`, `mean=53.4510`, `nonzero_px=25421`) to a broader failure (`max=16476`, `mean=332.8368`, `nonzero_px=285406`). AE also kept the previously loaded plug-in image until restart, so reinstall validation must restart AE before trusting a revert. | `refs/conformance/olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.md`, `refs/reports/ae_single_case_olmdistancegradation_case0012_layer_unpremul_20260629_1510/`, and `refs/reports/ae_single_case_olmdistancegradation_case0012_reverted_after_ae_restart_20260629_1515/`. | implementation-rejected / AE-host-grounded |
| 2026-06-29 new Windows partial runtime return narrows the Layer/no-bg ownership rule cleanly: Windows is consistent with `straight_source_rgb * output_alpha` and inconsistent with carrying premultiplied source RGB directly. A new narrow Mac patch applies that rule only on `render_mode=Layer`, `use_bg=0`, `src_a>0`. After rebuilding and reinstalling the plug-in, the main `case_0012` witnesses improve from the old factor-of-two miss to `-1/-2` RGB at `(462,7)`, `(72,8)`, `(106,19)`, though the case is still not globally exact (`max=65`, `mean=1.3003`). | `refs/reports/runtime_trace_comparisons/olmdistancegradation_field_prep_latest.md`, `olm_runtime_trace_distancegradation_layer_no_bg_source_ownership_20260629_windows_partial_return.zip`, and `refs/conformance/olmdistancegradation_16bpc_layer_source_fix_case0012_20260629.md`. | runtime-trace-grounded + AE-host-grounded / implementation-improved |
| 2026-06-29 representative live Mac AE reruns confirm the new narrow Layer/no-bg source patch is active beyond the single witness case. `case_0016` now reruns at `max=38`, `mean=0.10384`, `nonzero_px=13353`, while Constant representatives stay localized (`case_0020=1px`, `case_0022=192px`). The remaining 16bpc families are therefore still split cleanly into Layer/no-bg residual cleanup and Constant boundary ownership. | `refs/conformance/olmdistancegradation_16bpc_representative_rerun_after_layer_source_fix_20260629.md` and `refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/`. | AE-host-grounded / representative rerun |
| 2026-06-29 machine-generated current-baseline audit freezes the actual post-fix RGBA16 witness values and corrects an optimistic quick-view reading: the main `case_0012` witness points really do improve to small RGB deltas (`-266/-354`) while alpha stays exact, but the authoritative whole-frame compare is still broad (`max=16476`, `mean=332.8368`, `nonzero_px=285406`). Treat the earlier `max=65` note as non-authoritative PNG-space shorthand, and use the new baseline file for any interpretation of the pending Windows Layer/no-bg runtime trace. | `refs/conformance/olmdistancegradation_16bpc_layer_source_current_baseline_20260629.md` and `scripts/analyze_distancegradation_layer_source_current_baseline.py`. | AE-host-grounded / baseline freeze + evidence correction |
| 2026-06-29 a new AE batch wrapper stabilizes targeted Mac-side reruns by injecting request ids through environment variables instead of relying on stale `REQUEST_IDS.txt` state. When the full extended 16bpc DistanceGradation request is rerun and verified through the authoritative 16-bit verifier, the global status remains `1/16 exact`; the earlier tiny `max=65`-style spot numbers were 8-bit viewer-space witnesses, not conformance-grade 16bpc evidence. | `scripts/run_ae_validation_batch.py`, `refs/conformance/olmdistancegradation_16bpc_batch_wrapper_rerun_20260629.md`, and `refs/reports/ae_batch_distancegradation_extended_rerun_20260629/verify/reports/ae_pixel_16bpc_extended_exact.json`. | AE-host-grounded / authoritative rerun |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `In/ Out` | Selects inside, outside, or both regions. | enum: Inside, Outside, Both. | official manual + implementation |
| `Inside Threshold` | Maximum inside distance before normalization. | `max(1, threshold * ds_scale)`; threshold `0` becomes `1`. | implementation |
| `Outside Threshold` | Maximum outside distance before normalization. | `max(1, threshold * ds_scale)`; threshold `0` becomes `1`. | implementation |
| `Render Mode` | RGB color ramp or source layer color. | enum: RGB, Layer. | official manual + implementation |
| `Use Background Color` | Selects color+opaque-background ramp vs alpha gradation. | Boolean. | official manual + implementation |
| `Gradation Color` | Primary gradation color. | RGBA float color. | implementation |
| `BG Color` | Background color when background mode is enabled. | RGBA float color. | implementation |
| `Invert` | Inverts alpha/color ramp meaning. | Current implementation flips `X` when off before interpolation. | implementation |
| `Interpolation Mode` | Constant, Linear, Sphere, Power. | enum. | official manual + implementation |
| `Power` | Exponent for Power interpolation. | `pow(X, power)`. | implementation |
| `Blur Mode` | No Blur, Blur No Scale, Blur. | enum. | official manual + implementation |
| `Blur Size` | Gaussian blur radius base. | No Scale uses size as-is; Blur scales by `ds`. Constant+Blur doubles radius. | guarded / implementation |

## Kernel / Loop Shape

1. Convert source alpha to a binary mask: `alpha > 0`.
2. Build `d_alpha` as the binary nonzero-alpha mask.
3. Compute `ds = (ds_x + ds_y) * 0.5`, with fallback `1.0`.
4. Build normalized distance field `X`:
   - Inside: distance in mask.
     - If the inside mask has no zero-distance source (all pixels are inside),
       prepare a degenerate field that composes to final `X=0`: pre-invert
       `X=1` when `Invert` is off, pre-invert `X=0` when `Invert` is on.
   - Outside: distance in inverted mask.
   - Both: max of inside and outside normalized fields.
5. If Constant interpolation plus blur is active, convert `X` to
   `X >= 1.0 ? 1.0 : 0.0`.
6. If blur is active, apply separable Gaussian blur to `X`.
7. Compose each pixel:
   - if `Invert` is off, replace `X` with `1 - X`;
   - apply interpolation transform;
   - derive output alpha from In/Out mode;
   - choose RGB from Gradation Color or source layer;
   - write premultiplied-looking PNG output according to background mode.
8. In the current Mac port, convert 16bpc float channels with round-to-nearest
   after multiplying by `32768.0`. The Windows callback's apparent
   `CVTTSS2SI` writeback remains a tracked binary fact, but a direct global
   truncation change did not improve conformance and is not the active rule.

## Distance / Boundary

Current port model:

- Distance primitive: exact Euclidean distance transform equivalent to OpenCV
  `DIST_L2`, precise mask.
- Threshold: truncate distances to threshold before normalization.
- Normalization: divide by actual maximum after truncation, with denominator at
  least `1.0`.
- Blur boundary: Reflect101/mirror.

These rules are plausible and guarded, but the remaining residual means exact
Windows OpenCV/helper details are not fully proven.

## Interpolation

- Linear: pass `X` through.
- Constant without blur: current port uses `X > 0 ? 1 : 0`, but this is now
  understood as a field-prep behavior, not a `FUN_181170870` compose behavior.
- Constant with blur: binary field is prepared before blur; no post-blur
  threshold is applied.
- Sphere: `sqrt(max(1 - (1 - X)^2, 0))`.
- Power: `pow(X, Power)`.

`FUN_181170870` and its 16/float sibling compose functions in the Windows AEX
confirm the Sphere and Power math shape. They also show the default invert
behavior: when the invert byte is zero, the distance value used for composition
is `1 - X`.

2026-06-19 negative probe:

- Removing the current non-blur Constant binarization to match only the visible
  `FUN_181170870` compose body badly worsened Constant+Background cases:
  `case_0020 mean 0.0561 -> 6.9951`, `case_0021 0.0562 -> 23.8661`,
  `case_0022 0.5240 -> 21.6286`, and `case_0023 0.0778 -> 4.5740`.
- Interpretation: the binary-visible compose function is not the whole
  Constant story. Constant-mode binarization likely happens upstream during
  field construction/packing, before `FUN_181170870` reads the field pixel.
  Do not remove the current Constant binarization without a runtime trace of
  that upstream stage.

## Binary Notes

- The AEX is statically linked with OpenCV 4.5.5; the decomp contains OpenCV
  source paths such as `C:\Users\devbuild\Documents\4.5.5\sources\...`.
- `FUN_181170380`/`FUN_181170280` prove the visible compose stage runs after a
  separate field-prep stage. The 8bpc wrapper passes `param_4 + 0x2c` to
  `FUN_181170870`, and the callback reads the distance value from the green
  byte of the field world. Therefore Constant interpolation and blur ownership
  must be proven upstream of compose.
- The presence of `cv::copyMakeBorder` and border-name strings proves OpenCV
  border helpers are available in the binary, but it does not by itself prove
  the exact DistanceGradation blur branch. Treat the current Reflect101 blur as
  an implementation-grounded hypothesis until a call/trace pins the arguments.
- The compose functions are stronger evidence than the blur/distance helpers:
  they directly show `powf`, `sqrt`, invert, render-mode color selection, and
  output scaling.
- Because the 16bpc compose body already matches the current Mac render-mode
  and background-mix shape, the rerun families `case_0020..0023` and
  `case_0027/0028` now point upstream to `_X` field prep / saturation rather
  than to a simple channel-order or render-mode enum mismatch.
- 2026-06-26 host debug tightened the diagnosis for `case_0027/0028`: After
  Effects is definitely applying `Render Mode=2`, `Use Background Color=1`,
  `Invert=1`, `Interpolation Mode=4`, and the expected colors/power.
- A same-day four-variant Mac AE probe on `case_0027`, decoded as native
  16-bit PNG, corrected the earlier 8-bit-read misinterpretation. The
  background and no-background branches do differ materially; the problem is
  not a missing compose branch.
- The durable finding from that probe is upstream: `layer_no_bg` exposes the
  observed field `X` through alpha, and those observed values stay much closer
  to `1.0` than the current `max(inside,outside)` model predicts at the key
  witness pixels. So `case_0027/0028` now point to field prep / normalization /
  threshold ownership rather than to render-mode enum or background-branch
  wiring.
- A follow-up six-case `no_bg` field probe initially suggested a split:
  - `case_0020..0023`: the local Mac `no_bg` witness matched the current
    constant model at the focused pixels.
  - `case_0027/0028`: observed `X` from the `no_bg` alpha still stayed higher
    than the current model (`1.0` vs `0.812/0.968` at the lead witness).
- 2026-06-27 Windows bg-compose variants then tightened that result: the prior
  `case_0020..0023` simplification was too optimistic. Windows `bg_off`
  witnesses for `case_0020..0022` stay grad-color opaque (`[7195,0,61165,65535]`)
  rather than matching the Mac `no_bg` probe, and `case_0023 bg_off` flips
  transparent at the witness but still differs from the earlier Mac `no_bg`
  frame over 1388 pixels. So `case_0020..0023` are again upstream of just the
  background-compose branch and should not be tuned as a pure `use_bg=1`
  problem.
- 2026-06-26 experimental 16bpc mask-threshold patch (`alpha > 254/255`
  instead of `alpha > 0`) is rejected. It improved the `case_0023` witness and
  made the `no_bg` probe line up with that local flip, but the full-frame
  result still worsened (`mean ≈ 225.9` on a focused rerender) and it did not
  resolve `case_0020/0021/0022/0027/0028`. The working tree and installed
  MediaCore plug-in were restored to the pre-experiment build after measuring
  this.
- 2026-06-20 dense/live runtime returns are not sufficient to settle field
  prep. The dense summary carries placeholders such as `not isolated`,
  `inferred`, `likely`, and `runtime arg still untraced`; the live follow-up
  loaded the module and armed breakpoints, but no requested breakpoint hit
  before AE exited/crashed. The comparison helper now treats those strings as
  non-evidence, so both existing returns classify as `trace-too-sparse`.
- 2026-06-22 provenance follow-up
  (`refs/reports/olmdistancegradation_reference_provenance_20260622_025045/audit.md`)
  promotes the reference-generation split into a machine-readable
  classification: `normalized-software-exact-with-legacy-drift`. All 29
  audited AE-host candidates match the normalized Software refs exactly;
  legacy-only drift remains 1 basic case and 6 extended cases. Do not tune
  field/compose code from those legacy-only differences.
- 2026-06-24 decision matrix records the same stop/go rule in JSON/Markdown:
  normalized 8bpc exactness is the active release evidence; field-prep/OpenCV
  runtime proof is only needed if we choose to close AE-free CLI residuals or
  a current normalized Software residual reappears.
- 2026-06-26 we prepared a narrow Windows AE follow-up request for the
  unresolved 16bpc Constant/background family:
  `refs/reference_requests/olmdistancegradation_16bpc_bg_compose_variants_20260626.json`
  plus packaged handoff zip
  `refs/reference_request_packages/olmdistancegradation_16bpc_bg_compose_variants_20260626.zip`.
  It asks only for `case_0020..0023` original bg-on controls and matching
  `Use Background Color=0` variants so we can decide whether Windows differs in
  field prep or only in the bg-on compose branch.
- 2026-06-26 static decomp audit tightened the plugin-specific field-prep IR:
  `FUN_1811749a0` is not a soft-alpha path. It does `cvSplit` of the first
  channel (AE `PF_Pixel*` channel 0, i.e. alpha), converts by a depth-specific
  scale constant, then calls OpenCV `threshold(..., thresh=0, maxval=1,
  THRESH_BINARY)`. So the live AEX mask really is binary `alpha > 0`, and the
  rejected `alpha > 254/255` experiment was not secretly matching the binary.
- The same audit shows `FUN_181174760` is the plugin-specific
  `distanceTransform -> threshold -> normalize` helper. For non-Constant
  interpolation it uses `THRESH_TRUNC`; for Constant interpolation it switches
  to `THRESH_BINARY` before normalization. The helper also receives explicit
  render-context scaled dimensions from the caller: the hidden register args at
  the callsite carry scaled height `local_70c`, scaled width `local_708`, and
  pixel depth `local_714`. So any remaining
  `case_0027/0028` gap is more likely to live in this exact OpenCV prep path
  (or its temp-size handling) than in the later compose callback.
- 2026-06-26 follow-up decomp audit identifies the `Both`-mode outside seed
  prep more concretely than the older shorthand. `FUN_181174ad0` does not build
  a distance field; it copies the current 8-bit binary mask, converts it to the
  working depth, and then runs `cvSub(const_one, copied_mask, dst)`. In other
  words, the outside branch fed into the second `FUN_181174760` call is the
  strict binary complement `1 - mask`, not a soft-alpha variant and not a
  post-distance transform artifact.
- This same audit also weakens one old assumption in the local port comments:
  `FUN_181174760` itself receives the raw threshold integer plus the scaled temp
  size; it does not visibly multiply the threshold by an averaged `ds` inside
  the helper body. That does not yet prove the Mac `threshold * ds` rule is
  wrong, because the threshold could be pre-scaled earlier in the caller path,
  but it does mean the scaling rule is still implementation-grounded rather
  than binary-grounded and should not be promoted as settled fact.
- `FUN_181182b20` is `cvAdd`, so the AEX `In/Out=Both` path combines inside and
  outside fields by addition after separate prep, not by `max(...)`. For the
  current `case_0027` witness set this does not by itself explain the
  high-`X` residual because the sampled inside/outside supports are disjoint
  there, but it is the binary-grounded rule we should carry forward instead of
  the old `max(inside, outside)` shorthand.
  Do not patch the Mac plug-in to `inside + outside` blindly yet; first rerun
  the existing exact/guarded cases against a local prototype because several
  Constant witnesses that are already explained by the no-bg probe may be
  relying on the current shorthand in degenerate regions.
- 2026-06-26 follow-up analysis on the stored Mac AE probes confirms that this
  new `cvAdd` fact does not immediately unblock `case_0027/0028`. At the lead
  witnesses, the binary-grounded add model and the old max shorthand produce
  the same values because the inside/outside supports are still disjoint there,
  while the observed `no_bg` alpha remains much closer to `1.0`. See
  `refs/conformance/olmdistancegradation_16bpc_case0027_probe_x_20260626.md`
  and `refs/conformance/olmdistancegradation_16bpc_field_cases_probe_20260626.md`.
- 2026-06-27 local variant check further narrows `case_0027/0028`: at the lead
  witnesses, switching between actual-max vs threshold-denominator normalization,
  scaled vs raw thresholds, and `max` vs `add` Both-combine leaves the modeled
  `X` unchanged (`case_0027: 0.812285`, `case_0028: 0.968477`) while the
  observed `no_bg` probe still reports `1.0`. So these two cases are not
  explained by the current `threshold * ds` ownership question alone; the next
  plausible culprit remains a narrower upstream field-prep/temp-size/OpenCV
  branch in or around `FUN_181174760`.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| basic 12-case AE package | 8bpc | `AE exact` | 2026-06-19 AE pixel return: 12/12 `max_diff=0`; decision matrix preserves normalized exact behavior | 16/32bpc references; binary-ground field prep only if closing CLI residuals |
| extended non-blur 16-case AE package | 8bpc | `AE exact` | 2026-06-19 AE pixel return: 16/16 `max_diff=0`; decision matrix preserves normalized exact behavior | 16/32bpc references; binary-ground Constant/render-mode only if closing CLI residuals |
| blur `case_0029` AE package | 8bpc | `AE exact` | 2026-06-19 AE pixel return: `max_diff=0`; normalized and legacy refs both exact | 16/32bpc references; trace OpenCV blur only if closing CLI residuals |
| basic all-opaque Inside `case_0001..0006` | 16bpc | partial AE exact | 2026-06-26 Mac AE: Inside/no-source rule keeps `case_0001/0003/0004/0005/0006` exact and promotes `case_0002` to exact. Basic slice is now 8/12; DistanceGradation total is 9/29 | Static/runtime proof for the no-source branch; continue with non-all-opaque 16bpc residuals |
| basic remaining `case_0015/0017/0018/0019` | 16bpc | not exact / compose-path diagnostic | 2026-06-26 local rerun reproduces the same four failures. `case_0015/0017` are `Render Mode=2` + `Use Background Color=0`; `case_0018/0019` are `Render Mode=1` + `Use Background Color=1` with colored ramps/backgrounds | Ground 16bpc render-mode/background compose path before changing distance field math |
| extended BG-vs-Grad binary `case_0020..0023` | 16bpc | not exact / field-prep-plus-compose diagnostic | 2026-06-26 local rerun focus witnesses are BG-like on one side and Grad-like on the other while alpha remains exact. A same-day Mac `no_bg` probe looked consistent with the local Constant model at the witness pixels, but the 2026-06-27 Windows bg-on/bg-off return invalidates the narrower “only `Use Background Color=1`” reading: Windows `bg_off` for `case_0020..0022` still stays grad-color opaque at the witness, and `case_0023 bg_off` still differs from the prior Mac `no_bg` probe over the whole frame. See `refs/conformance/olmdistancegradation_16bpc_focus_cases_20260626.md`, `refs/conformance/olmdistancegradation_16bpc_constant_variants_20260626.md`, `refs/conformance/olmdistancegradation_16bpc_field_cases_probe_20260626.md`, and `refs/conformance/olmdistancegradation_16bpc_bg_compose_variants_return_20260627.md`. | Re-ground 16bpc Constant field prep and compose together; do not treat these as a pure bg-compose tweak |
| extended Power/background ramp `case_0026` | 16bpc | not exact / Power param bug fixed, residual remains | 2026-06-29 Windows runtime trace proves the row-0 ramp exists before `FUN_181170480`; the compact witness is not a compose-created ramp. Mac debug dump then proved the port's field also ramps, but `Power` was collapsed by an erroneous `FIX_2_FLOAT` conversion. After fixing `Power`, row0 matches within `0..4`, while the full case remains `max_diff=11480` with sparse boundary/source residuals. | Classify remaining high-delta pixels by field quantization/source ownership and compose/writeback; do not revert the Power fix. |
| extended RGB-zeroed `case_0027/0028` | 16bpc | not exact / field-prep diagnostic | 2026-06-26 local rerun shows the current packaged case still fails against the Windows Software reference. Host debug rules out request drift, and the follow-up Mac AE probes show the compose/background branches are active; the live mismatch is that the `no_bg` probe still exposes an observed field much closer to `1.0` than the current model predicts. See `refs/conformance/olmdistancegradation_16bpc_focus_cases_20260626.md`, `refs/conformance/olmdistancegradation_16bpc_case0027_mac_ae_probe_20260626.md`, `refs/conformance/olmdistancegradation_16bpc_case0027_probe_x_20260626.md`, and `refs/conformance/olmdistancegradation_16bpc_field_cases_probe_20260626.md`. | Ground the 16bpc field-prep / normalization path in code/asm before changing compose logic |
| AE-free basic 12-case smoke | 8bpc | guarded | 2026-06-19 rerun passes current guard: worst `case_0007/0009 max=7 mean=0.0909`; residual remains | binary-ground distance normalization and compare against normalized Software refs |
| AE-free extended non-blur 16-case smoke | 8bpc | guarded | 2026-06-19 rerun passes current loose guard, but with large non-exact residuals: `case_0008 max=254`, `case_0011 max=254`, `case_0012 max=251`, `case_0020..0023 max=238` | binary-ground interpolation, Constant field-prep, and render-mode branch details before tuning |
| AE-free blur `case_0029` | 8bpc | guarded | 2026-06-19 rerun: `max=23 mean=0.2827`; tiny non-grounded improvement from Constant+Blur binary-field handling | trace/OpenCV 4.5.5 `distanceTransform` / `GaussianBlur` behavior |
| Constant field-prep witnesses `case_0020/0022/0029` | 8bpc | blocked on runtime proof | current Constant binarization is much closer than compose-pass-through, but not exact | Windows runtime trace package `distancegradation-field-prep` |

## Reference Provenance

`scripts/analyze_distancegradation_reference_provenance.py` compares the
2026-06-19 AE-host candidates against both the older 20260605 extra reference
set and the 20260618 normalized Software references.

Latest report:
`refs/reports/olmdistancegradation_reference_provenance_20260622_005446/audit.md`.

Cross-feature summary:
`refs/reports/software_reference_canonicalization_8bpc.md`.

| Group | Cases | Nonzero vs 20260605 extra | Nonzero vs 20260618 normalized |
| --- | ---: | ---: | ---: |
| basic | 12 | 1 | 0 |
| extended | 16 | 6 | 0 |
| blur | 1 | 0 | 0 |

Legacy-reference drift cases:

- `basic/case_0017`: old-ref `max=2 mean=0.001613257`, normalized exact.
- `extended/case_0012`: old-ref `max=251 mean=0.622667221`, normalized exact.
- `extended/case_0013`: old-ref `max=62 mean=0.201817371`, normalized exact.
- `extended/case_0014`: old-ref `max=63 mean=0.204961058`, normalized exact.
- `extended/case_0016`: old-ref `max=64 mean=0.207432123`, normalized exact.
- `extended/case_0027`: old-ref `max=6 mean=0.001718147`, normalized exact.
- `extended/case_0028`: old-ref `max=142 mean=0.093512852`, normalized exact.

Interpretation: use normalized Software refs as the current 8bpc AE-host
evidence. Do not tune the Mac plug-in or CLI to the older 20260605 PNGs unless
the reference-generation decision is explicitly reversed.

## Validation Packages

- Runtime trace request:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip`.
  The 2026-06-20 returns did not answer this request with concrete values.
  A future trace must emit typed numeric Windows values for the target pixels:
  pre/post Constant field, OpenCV `distanceTransform` / `GaussianBlur`
  arguments, field-world rowbytes/dimensions, and `FUN_181170870` field green
  byte / `X` / final RGBA. Use that before changing Distance/Constant/Blur
  semantics.
- Mac AE exact check, basic normalized Software refs:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip`.
- Mac AE exact check, extended normalized Software refs:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip`.
- Mac AE exact check, blur normalized Software refs:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip`.

The AE exact packages intentionally use zero thresholds. The 2026-06-19 returns
verified the packaged 8bpc slices with `max_diff=0`; this is completion for
those slices only, not for the still-untested 16/32bpc paths or the AE-free CLI
model.

## Open Questions

- Whether Windows AEX uses OpenCV `distanceTransform` directly or equivalent
  helper with subtle border/minmax differences.
- Exact threshold/minmax behavior on masks where threshold is not reached.
- Exact Gaussian blur kernel, anchor, radius, and border mode for every Blur
  Mode.
- Exact location and scope of Constant-mode field binarization before
  `FUN_181170870`.
- Whether PNG export premultiplication is masking AE-world straight/premul
  differences.
- 16bpc and 32bpc output rules.
- Exact 16bpc render-mode/background-color source selection for the rerun
  palette-swap family (`case_0020..0023`).
- Why some 16bpc source-layer cases preserve alpha but zero RGB
  (`case_0027/0028`).
