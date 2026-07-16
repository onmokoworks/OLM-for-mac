# Binary-Grounded IR: OLMDistanceGradation

## Feature

- Plug-in: Distance Gradation
- Feature/path: alpha-mask distance gradation, interpolation, optional blur
- Bit depth: 8bpc, 16bpc, and 32bpc policy are tracked separately. The current
  8bpc Mac binary is known-red; 16bpc has a depth-gated source-mask rule and a
  binary-grounded PF16 field-world boundary; 32bpc still needs
  float-preserving references.
- Reference set: `refs/win_references/20260605_extra/OLMDistanceGradation`
- Current status: `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`
  is the current authority. The OpenCV reciprocal-scale plus PF16
  round-to-nearest-even boundary closes 16bpc `case_0010/0011` and makes the
  canonical extended batch `7/16 AE exact`. The remaining true16 families are
  Layer/no-bg `0012/0013/0014/0016`, max-2 `0024..0027`, and the separate
  `0028` outlier. A fresh depth-correct canonical 8bpc run measures the current
  binary at `0/29` exact. The AE-free CLI is not a Windows-reference verdict.
- 2026-06-22 reference provenance audit confirms all 29 historical candidate
  images match the 20260618 normalized Software references exactly. Those
  artifacts do not record the loaded Mac plug-in path/hash; two retained June
  18 binaries fail a fresh canonical rerun. Treat the `29/29` artifact as
  unbound historical evidence, not current-binary conformance.
- Historical cross-feature canonicalization audit:
  `refs/reports/software_reference_canonicalization_8bpc.md` classifies all
  three unbound candidate groups as `normalized-software-exact`:
  basic 12/12, extended 16/16, and blur 1/1. Legacy drift remains only in the
  older 20260605 extra references.
- Historical 2026-06-24 decision matrix (superseded for current-binary status):
  `refs/reports/olmdistancegradation_decision_matrix_20260624/decision_matrix.md`
  consolidates provenance, canonicalization, and the latest trace comparison.
  It classifies normalized 8bpc as `29/29 exact`, legacy drift as 7 old-ref
  cases, and the current runtime trace as `not-actionable` (`await-windows-trace`).
  Its reference-family split remains useful, but its current `29/29` claim is
  superseded by the 2026-07-11 depth-correct rerun.
- 2026-07-08 depth-gate rule:
  `source_mask_owns_alpha(alpha, pixel_size)` keeps PF_Pixel8 inclusive
  (`alpha > 0`) and uses `alpha > 1.5/255.0` for PF_Pixel16 and deeper. This
  matches the observed Windows 16bpc source-mask staging while preserving the
  8bpc HEAD behavior by construction. Do not use `scripts/run_ae_single_case.py`
  as an 8bpc verdict runner; use the canonical 8bpc batch flow for that.
- 2026-07-11 depth-correct runner and current-binary correction: both AE JSX
  runners now fall back to `reference_manifest.comp.bpc` when
  `project.bits_per_channel` is absent. The canonical 8bpc batch explicitly
  logs `bits_per_channel 8 source=comp.bpc`; the current plug-in is `0/29`
  exact. This supersedes using the unbound 2026-06-19 output as current status.

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
| Upstream field prep helper `FUN_181174760` is structurally `distanceTransform -> threshold(TRUNC) -> distanceTransform -> threshold/normalize`, with a Constant-only fork that changes the second threshold mode from `THRESH_TRUNC` to `THRESH_BINARY` and clamps the effective denominator floor at `1.0`. | `decomp/DistanceGradation.aex.c.txt` around `FUN_181174760`, `FUN_1812b15a0`, and `FUN_1812b6a40`. `FUN_1812b15a0` is a threshold wrapper with the OpenCV mode table (`THRESH_BINARY`, `THRESH_TRUNC`, ...); `FUN_181174760` hardcodes the first call as mode `2`, then switches the second call to mode `0` only when `param_8 == 1`. | binary-grounded / 2026-06-30 helper audit |
| Per-pixel compose path implements Sphere with `sqrt(1 - (1 - X)^2)` and Power with `powf(X, power)`. | `decomp/DistanceGradation.aex.c.txt` around `FUN_181170870` and sibling 16/float compose functions. | binary-grounded |
| 8bpc compose reads the distance field from the green byte of the field pixel and applies invert/interpolation in `FUN_181170870`. | `decomp/DistanceGradation.aex.c.txt` `FUN_181170870`: `_X = field_pixel[green] / 255`, then optional `1 - X`, Sphere/Power, and final RGBA byte cast. | binary-grounded |
| 8bpc compose is an AE iterate callback over a prebuilt field world. | `FUN_181170380` requests `PF Iterate8 Suite` and passes callback `FUN_181170870` with user data `param_4 + 0x2c`; `FUN_181170870` then reads the field world through `param_1[1]`. | binary-grounded |
| 16bpc and float compose use sibling iterate callbacks. | `FUN_181170280` requests `PF iterate16 Suite` and passes `FUN_181170480`; float path stores callback `FUN_181170c90`. | binary-grounded |
| OpenCV `NORM_MINMAX` field normalization uses one float32 reciprocal scale followed by multiplication; it is not per-element division by the maximum. | Actual-AEX fieldgen fixtures plus the OpenCV 4.5.5 sidecar and `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`. | binary-grounded / independently reproduced |
| Hash-pinned direct `FUN_181174760` execution matches the current portable field core at all `187/187` float32 samples for a bounded `param8=0`, raw-threshold `4`, `ds_scale=1` ramp; strict `param8=1`, threshold-zero anchors are `(0,1,1)`. An explicit `ds_scale=0.5` changes the current caller's effective threshold and therefore does not match the raw-threshold helper call. | `refs/conformance/olmdistancegradation_fieldgen_actual_aex_differential_20260716.md`; detour/callback/import/sample guards are recorded in the paired JSON. | binary-grounded helper parity; caller integration unresolved |
| Before `FUN_181170480` consumes the 16bpc field world, OpenCV converts the normalized float field to PF16 with round-to-nearest-even. Focused scaled values `22891.5`, `29500.5`, `4408.5009765625`, `1.5`, `2.5`, `3.5` become `22892`, `29500`, `4409`, `2`, `2`, `4`. | OpenCV 4.5.5 sidecar `CV_16U` conversion, actual-AEX field values, Mac AE `case_0010/0011` exact result, and the focused core regression. | binary-grounded + AE-host-validated |
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
| 2026-06-30 Windows Constant-boundary runtime return upgrades that boundary reading from inference to bounded witness. `case_0020` now has a direct boundary-pair proof: the `951/950` neighbor pair flips exactly at the local `field_x == 1` plateau edge, and the matching `950,417` neighbor shows the correct blue endpoint is already decided before final writeback. `case_0022/0023` stayed `answered_partial`, but their representatives remain explicitly classified as boundary-localized Constant/THRESH_BINARY ownership rather than compose drift. | `refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_boundary_witness.md` and `refs/reports/runtime_trace_summary.md`. | runtime-trace-grounded / answered-partial but actionable |
| 2026-06-30 live Mac AE negative probe rejects a tempting compose-side explanation. Removing the Mac port's extra Constant/no-blur post-compose threshold from `compose_pixel()` leaves the representative outputs unchanged (`case_0020` stays `1px`, `case_0022` stays `192px`, `case_0023` stays `73px`, and control `case_0012` stays broad). Therefore the active residual family still lives upstream in field prep / threshold ownership / plateau formation, not in that extra compose gate. | `refs/conformance/olmdistancegradation_16bpc_constant_no_post_threshold_probe_20260630.md` and `refs/reports/ae_single_case_distancegradation_constant_no_post_20260630/summary.json`. | AE-host-grounded / implementation-rejected |
| 2026-06-30 the surviving `case_0023` residual is now split by raw inside-EDT bucket instead of treated as a generic sparse mismatch. All 73 changed pixels stay inside the source alpha region (`outside EDT = 0.0` for every changed pixel), and they divide into only two endpoint-choice families: `65px` at `inside EDT = 1.0` where Mac stays on the Gradation-color endpoint while Windows uses BG-color, and `8px` at `inside EDT = 36.013885...` (just beyond `Inside Threshold = 36`) where the endpoint choice flips the other way. | `refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.md` and `scripts/analyze_distancegradation_case0023_residual_split.py`. | AE-host-grounded / threshold-ownership split |
| 2026-06-30 live Mac AE point-debug turns those `case_0023` buckets into direct field witnesses. The `inside EDT = 1.0` bad pixels at `(1699,7)` and `(1698,7)` already have `field_x=0` / `d_alpha=1`, while immediate outside-side neighbors flip to `field_x=1` / `d_alpha=0`. The `inside EDT = 36.013885...` witness at `(415,393)` already has `field_x=1`, and its immediate neighbors straddle `field_x=0/1` exactly as `raw_inside` crosses `36`. This upgrades the remaining lane from a PNG-space split to a live AE field-prep ownership witness. | `refs/conformance/olmdistancegradation_16bpc_case0023_pointdebug_20260630.md` and `/tmp/olmdg_case0023_pointdebug_20260630_multi/field_debug.txt`. | AE-host-grounded / live field witness |
| 2026-07-01 consolidated threshold-family audit freezes why `case_0023` stayed a Windows-typed-ownership lane before the later local probes. | `scripts/analyze_distancegradation_case0023_threshold_family.py`, `refs/scripts/smoke_analyze_distancegradation_case0023_threshold_family.py`, and `refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.md`: the active lane is only `73px`, splits into `65px` at `inside=1.0` and `8px` at the `35.014 -> 36.013 -> 37.013` threshold crossing, local field debug already proves the `field_x` flip before compose, and the tempting `trunc_plateau_binary` family is explicitly rejected because it explodes to `182793px`. This is now bounded historical context for the current Mac AE source/output-ownership lane, not a standalone pending threshold-family ask. | reproducible lane audit / superseded by 2026-07-07 closeout evidence |
| 2026-07-01 threshold-family runtime comparator treats the `case_0023` triplet follow-ups as first-class intake lanes. | `scripts/compare_distancegradation_trace.py` and `refs/scripts/smoke_compare_distancegradation_trace.py`: the comparator recognizes the threshold-family follow-up `olmdistancegradation_case0023_threshold_family_followup_20260701`, the tighter compose-hook ask `olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701`, the superseded output-word ask `olmdistancegradation_case0023_output_word_triplet_followup_20260701`, and the later refcon-wordmap ask `olmdistancegradation_case0023_refcon_wordmap_followup_20260702`. It preserves the local threshold-triplet context (`414/415/416,393`) and keeps those returns in the same threshold-ownership lane rather than collapsing them into the older edge-family boundary note. The later 2026-07-07 reference export and Mac shade/compose probes supersede resending these packages as-is. | reproducible intake comparator / archived queue context |
| 2026-07-02 live Mac AE rerun plus latest Windows typed triplet initially suggested a threshold-family provenance split inside `case_0023`; this is now superseded by the 2026-07-07 reference export audit below. | `refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.md`: live Mac AE single-case rerun still differed from the then-packaged expected PNG by `73px`, and the threshold triplet was no longer evidence for a compose/writeback retune. The later `refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.md` proves the current packaged/current Windows files are byte-identical, so this row is historical narrowing evidence only, not a current stale-reference claim. | historical provenance-first / superseded by reference-export audit |
| 2026-07-02 live Mac AE `Use Background Color=0` rerun keeps the residual cardinality at `73px` against the Windows `bg_off` reference, so the case_0023 lane is still upstream of the final bg-on compose blend. | `refs/conformance/olmdistancegradation_case0023_bgoff_current_probe_20260702.md`: current Mac `bg_off` agrees with Windows `bg_off` at `(1698,7)`, `(1700,7)`, `(414,393)`, and `(416,393)`, but still disagrees at `(1699,7)` and `(415,393)`. This is strong negative evidence against a simple final blend explanation: the remaining sparse mismatch survives with background disabled, so the live implementation lane stays in field ownership / threshold staging. At the same time it shows the lane is more localized than a broad branch failure, because adjacent representative points already match. | AE-host-grounded / bg-off negative probe |
| 2026-07-07 local AEX CPU emulation of `FUN_181170480` grounds a case_0023 field-to-color mapping, but not current final PNG exactness. | `scripts/materialize_distancegradation_case0023_compose_witness.py`, `refs/scripts/smoke_materialize_distancegradation_case0023_compose_witness.py`, and `refs/conformance/olmdistancegradation_case0023_compose_witness_20260707.md`: executing the Windows AEX callback locally with injected field values `(414,393)=0`, `(415,393)=1`, `(416,393)=1` reproduces the recorded runtime words under the promotion rule `trunc(half_word / 32768.0 * 65535.0)`. The later reference export audit proves the current Windows PNG has `(415,393)` on the blue side, so this witness must be used as mapping evidence only; it is not current AE exact evidence. | binary-grounded local emulation / mapping only |
| 2026-07-16 PF8 actual-AEX compose/store differential closes the local callback interpretation at three live Mac coordinates. | `refs/conformance/olmdistancegradation_pf8_compose_store_differential_20260716.json`: with hash-pinned `FUN_181170870`, correct PF8 world geometry, and nonzero fixture readback, `(17,0)`, `(780,495)`, and `(987,496)` match the current Mac model through field/source reads, canonicalized pre-U8 floats, truncation, and stored ARGB. The field/source bytes are injected identically in both lanes; `FUN_181174760` field generation and AE-host output are explicitly outside scope. | binary-grounded compose/store / field generation still open |
| 2026-07-07 Mac source-model audit matches the recorded AEX CPU helper samples for case_0023. | `scripts/materialize_distancegradation_case0023_source_model_audit.py`, `refs/scripts/smoke_materialize_distancegradation_case0023_source_model_audit.py`, and `refs/conformance/olmdistancegradation_case0023_source_model_audit_20260707.md`: using the same alpha-derived mask, Constant binary thresholds, OpenCV-detour EDT, and `min(inside+outside,1)` BOTH merge as the Mac port, all 10 recorded AEX helper sample points match, including the live edge witness `(1699,7)` where both report `0.0`. This is sampled evidence, not a full exported-field diff, but it further excludes broad field-helper retuning. | source-model / AEX-helper sampled equivalence |
| 2026-07-07 reference export audit rejects the older packaged-stale explanation for current `case_0023` files. | `scripts/materialize_distancegradation_case0023_reference_export_audit.py`, `refs/scripts/smoke_materialize_distancegradation_case0023_reference_export_audit.py`, and `refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.md`: the packaged 2026-06-25 16bpc Windows Software PNG, the 2026-07-03 current-AEX recapture, and the 2026-07-06 current-AEX recapture are byte-identical (`sha256:4ffcbd0015557e076067969ce364625e9aad12ffb8c96756a97d7dc6d8ad4910`, `nonzero_px=0`, `max_diff=0`). The live Mac bg_on/bg_off candidates still differ by `73px`, so the remaining lane is Mac AE source/output ownership rather than Windows reference export drift. | reference-export-grounded / stale-reference rejected |
| 2026-07-07 case_0023 probe chain is historical closeout context after the 2026-07-08 depth gate. | The Mac-only probe plan, bg_on/bg_off probe, neighborhood probe, and final/source ownership package below are retained because they explain why the depth-gated source-mask rule is valid. They are no longer current next-step guidance; the live DG near-miss lane is now export-quantization-first, with only `(907,222)` still needing a direct PF16 store/export stop if pursued further. | historical closeout context |
| 2026-07-07 Mac-only probe plan narrows the next local step for `case_0023`. | `scripts/prepare_distancegradation_case0023_probe.py`, `refs/scripts/smoke_prepare_distancegradation_case0023_probe.py`, and `refs/conformance/olmdistancegradation_case0023_mac_probe_plan_20260707.md`: run the same case with `Use Background Color=1` and `0`, collecting `OLM_DG_DEBUG_POINTS` for `(1699,7)` plus the `(414/415/416,393)` threshold triplet. If alpha/raw distance/field changes, the seam is source-world or field-boundary provenance; if debug fields match but exported pixels remain red, the seam is 16bpc host source/output packing. | Mac AE source/output probe plan |
| 2026-07-07 Mac-only bg_on/bg_off probe result was pre-closeout evidence for the later depth-gated rule. | `scripts/materialize_distancegradation_case0023_mac_probe_result.py`, `refs/scripts/smoke_materialize_distancegradation_case0023_mac_probe_result.py`, and `refs/conformance/olmdistancegradation_case0023_mac_probe_result_20260707.md`: both Mac AE runs emit identical debug values at all 10 witness points (`alpha`, `d_alpha`, `field_x`, raw distances, per-side helper outputs), and the shade logs capture source RGBA, `x_row/a_row`, compose output floats, and 16bpc stores. Those stores match the Mac PNG after transparent-RGB zeroing, but `win_bg_on_vs_mac_bg_on` and `win_bg_off_vs_mac_bg_off` both remain `73px` nonzero. This moves the lane past `Use Background Color`, sampled field generation, and visible PNG/export packing; the next local step is mismatch-neighborhood shade expansion or same-run raw-output extraction, not broad helper/compose retuning. | Mac AE probe result / shade-compose ownership live |
| 2026-07-07 Mac-only neighborhood probe was pre-closeout evidence that confined the old case_0023 residual to two representative pixels. | `scripts/materialize_distancegradation_case0023_neighborhood_probe_result.py`, `refs/scripts/smoke_materialize_distancegradation_case0023_neighborhood_probe_result.py`, and `refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.md`: the 18-point neighborhoods around `(1699,7)` and `(415,393)` still give full-frame `73px` residuals, `bg_on`/`bg_off` debug fields match, shade sources match the request input PNG under AE `PF_Pixel16` promotion, and shade stores match the Mac PNG. Within the sampled neighborhoods, only `(1699,7)` and `(415,393)` disagree with Windows; all immediate neighbors agree. This makes a broad field-helper, Both-merge, source-input, or compose retune even less plausible and leaves Windows final/source-ownership proof as the remaining boundary. | Mac AE neighborhood probe / Windows ownership proof next |
| 2026-07-07 Windows final/source ownership package was the last DG case_0023 external proof before depth-gate closeout. | `refs/conformance/olmdistancegradation_case0023_final_source_ownership_contract_20260707.md`, `refs/scripts/smoke_package_distancegradation_case0023_final_source_ownership.py`, and `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_final_source_ownership_20260707.zip`: the package asks only for `(1699,7)` and `(415,393)` plus immediate matching controls, and requires source words, ownership mask/alpha, consumed field value, pre-store words, final stored RGBA16, and exported RGBA16. It explicitly forbids broad callback activity, final PNG restatement alone, and resending the old stack/refcon package as-is. | Windows proof package / next external evidence |
| 2026-07-07 case_0023 low-alpha source-mask lane is closed in Mac AE. | `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_final_source_ownership_20260707.md` classifies `(1699,7)` as Windows source/mask ownership and `(415,393)` as export/path split. The Mac port now treats the one-code 8bpc alpha fringe as transparent for source-mask ownership (`alpha <= 1.5/255.0`), and `refs/conformance/olmdistancegradation_case0023_alpha_threshold_mac_ae_result_20260707.md` shows both bg_on and bg_off Mac AE probes match the corresponding Windows Software references exactly (`nonzero_px=0`, `max_diff=0`). | AE exact / binary-grounded closeout for case_0023 |
| 2026-07-08 depth-gated source-mask rule supersedes the global low-alpha rule. | `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md` records the measured rule: PF_Pixel8 keeps the original inclusive source mask (`alpha > 0`), while PF_Pixel16 and deeper use `alpha > 1.5/255.0`. This preserves the 8bpc code path by construction and keeps 16bpc `case_0023` exact. Its original `7/16` extended-batch count is superseded by the 2026-07-09 canonical true16 reverify below. | AE-host-grounded depth rule / case_0023 closeout |
| 2026-07-08 depth-gated `case_0024..0027` max=1 family is export-quantization-first. | `refs/conformance/olmdistancegradation_depthgate_quantization_return_intake_20260708.md` classifies three `case_0026` representatives as matching a lower 16bpc-to-export quantization/export rule, with only `(907,222)` unresolved. This is not evidence for a new field/source/compose retune. | runtime-trace-grounded / narrow residual classification |
| 2026-07-08 depthgate one-pixel endgame request. | `refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md` narrows the remaining max=1 family to the single unresolved `case_0026` pixel `(907,222)`. The required proof is a same-run PF_Pixel16 store/export witness: whether Windows stores B as zero before export or stores a small positive B that export quantizes to zero. | prepared Windows proof contract |
| 2026-07-08 depthgate one-pixel return. | `refs/conformance/olmdistancegradation_depthgate_907_store_export_return_intake_20260708.md` classifies `olmdistancegradation_depthgate_907_store_export_witness_20260708` as `answered_partial`. It preserves carried values for `(907,222)` (`field=0.121742934`, pre-PF16 float `(0.996250153,0,0.00393153122,1)`, carried store `(32645,0,129,65535)`, carried export `(255,0,0,255)`), but did not freshly bind the output-world address or directly observe the same-run PF_Pixel16 store. | still open / same-run store-export proof needed |
| 2026-07-08 Layer-source follow-up returned `failed_partial`. | `refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md` and profile `distancegradation-case0014-layer-source-witness` define `olmdistancegradation_case0014_layer_source_witness_20260708` for the broad 16bpc Layer-source witness. The return is classified in `refs/conformance/olmdistancegradation_case0014_layer_source_return_intake_20260708.md` and `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0014_layer_source_witness_20260708.md`: it confirms the alpha-preserving RGB deficit shape at `(1652,2)` and `(461,6)`, but no fresh live Windows callback stop captured consumed source RGBA16, field/compose inputs, pre-store float, or final stored RGBA16. Do not patch from this return; a retry must bind those values in the same run. | failed_partial / evidence-only |
| 2026-07-08 16bpc Layer/no-bg straight-source RGB rule. | `refs/conformance/olmdistancegradation_layer_source_true16_audit_20260708.md` first exposed that the old Layer/no-bg residual was a true16 `max=16384` / byte-equivalent `64` RGB scaling error, not a one-word rounding issue. The Mac port now keeps the old 8bpc path but uses straight source RGB without final-alpha multiplication for 16bpc and deeper Layer/no-bg. `refs/conformance/olmdistancegradation_layer_straight_patch_20260708.md` shows the first focused rerun: `case_0012 max=251`, `case_0013 max=2`, `case_0014 max=4`, `case_0016 max=2`. | AE-host-grounded implementation improvement / not exact |
| 2026-07-08 16bpc Layer/no-bg low-alpha hidden-color rule. | `refs/conformance/olmdistancegradation_layer_lowalpha_final_20260708.md` narrows the remaining Layer-source family without broadening the 16bpc source rule: `case_0012 max=90`, `case_0013 max=2`, `case_0014 max=4`, `case_0016 max=2`. The broader low-alpha ratio attempt is preserved only as a rejected A/B in `refs/conformance/olmdistancegradation_layer_lowalpha_patch_20260708.md`: it reduced `case_0012` to `max=48` but regressed `case_0013/0014/0016` to `max=47`, so it is not an allowed rule. | AE-host-grounded implementation improvement / not exact |
| 2026-07-08 16bpc Layer/no-bg `3.1/255` low-alpha threshold was tested and rejected. | A live debug point at `case_0012 (1133,13)` shows the current candidate uses `src_a=386/32768`, `src_r=4/32768`, `out_a=0.991803288`, and stores RGB word `340`, while the Windows reference is consistent with a higher low-alpha source ownership rule. However, simply widening the hidden-color threshold to include that alpha band regresses the nearby Layer cases. `refs/conformance/olmdistancegradation_layer_lowalpha_31_threshold_20260708.md` improves `case_0012` to `max=62` but worsens `case_0013/0014/0016` to `max=7/7/7`; adding an `out_a > 0.5` gate still worsens `case_0013/0014` to `max=257`, as shown in `refs/conformance/olmdistancegradation_layer_lowalpha_outa_gate_20260708.md`. Keep the narrower `1.5/255` rule until the zero-RGB low-alpha inheritance and nonzero `alpha=386` case can be separated by proof. | implementation-rejected / AE-host-grounded |
| 2026-07-08 16bpc Layer/no-bg Both-only low-alpha channel-mask rule. | `case_0012` is the only focused Layer-source case with `In/Out=Both`; `case_0013/0014/0016` are Inside cases. For 16bpc+ Layer/no-bg Both, using `src_a * out_a` for nonzero premultiplied channels only in the low-alpha band (`src_a <= 13/255`) reduces the focused family to `case_0012 max=28`, `case_0013 max=2`, `case_0014 max=4`, `case_0016 max=2` in `refs/conformance/olmdistancegradation_layer_both_lowalpha_20260708.md`. A wider `20/255` test is rejected because it worsens `case_0012` to `max=40` (`/tmp/olmdg_both_lowalpha20_case0012/audit.md`). | AE-host-grounded implementation improvement / not exact |
| 2026-07-08 `case_0012` point-debug isolates the remaining max `28` family to one uniform low-alpha store/export-scaling band. | `refs/conformance/olmdistancegradation_case0012_pointdebug_20260708.md` samples ten max-delta points. All share source `[195,195,195,3597]`, `field_x=0.00819672085`, `out_a=0.991803288`, and Mac pre-export store `[1785,1785,1785,32499]`, while the true16 PNG comparison is candidate `[3539,3539,3539,64997]` vs Windows `[3567,3567,3567,64997]`. This rules out distance topology or per-coordinate ownership for this residual. | AE-host-grounded / store-export scaling lane |
| 2026-07-08 dominant-channel Both mask rule closes the broad `case_0012` Layer-source miss. | `refs/conformance/olmdistancegradation_case0012_dominant_channel_closeout_20260708.md` records the accepted rule: in 16bpc+ Layer/no-bg Both, promote only dominant source channels to `src_a` up to `150/255`; non-dominant channels keep straight-source ratio. This reduces `case_0012` from true16 max `28` to `2` and preserves neighboring `case_0013/0014/0016` at `2/4/2`. Full-alpha/all-range and `180/255` broadening probes are rejected because they explode low-luma color components. | AE-host-grounded implementation improvement / residual export-rounding |
| 2026-07-09 dominant-channel all-modes probe was tested and deferred. | `refs/conformance/olmdistancegradation_dominant_channel_all_modes_probe_rejected_20260709.md` shows the tempting all-in/out generalization: it changes `case_0014` from max `4` to max `2`, confirming the large residual is tied to low-alpha dominant-channel source/store handling. However, it still leaves the focused family non-exact and is not binary-grounded. A reverted BOTH-only spot-check also reports `case_0010` and `case_0011` at max `2` under `scripts/run_ae_single_case.py`, so the single-case run cannot be used as the 16bpc exact-count authority here. The source was reverted to the BOTH-only dominant-channel rule and the installed plug-in rebuilt. | implementation-deferred / AE-host-grounded diagnostic |
| 2026-07-09 current integrated 16bpc canonical batch is `5/16`. | `refs/conformance/olmdistancegradation_current_integrated_16bpc_batch_20260709.md` records a canonical `run_ae_validation_batch.py` + `verify_ae_pixel_validation_result.py` run on the current installed/worktree build. Exact cases are `0008/0020/0021/0022/0023`. This remains the current true16 count. | AE-host-grounded current-state correction |
| 2026-07-09 depthgate true16 reverify invalidates the old `7/16` count. | `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md` reruns `scripts/verify_ae_pixel_validation_result.py` against `/tmp/olmdg_16ext_depthgate2` and gets `ok=5 fail=11`. Therefore the old `7/16` figure was not a true16 conformance count, and the suspected current-vs-depthgate provenance delta should not be pursued. | AE-host-grounded measurement correction |
| 2026-07-09 true16 residual family audit. | `refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md` uses `refs/scripts/verify_manifest.py::load_rgba` to classify the current 16bpc residuals. `case_0010/0011` are sparse R/A-only abs-2, `case_0012/0013/0014/0016` are mostly abs-2 Layer/no-bg rounding with `case_0014` carrying the only small abs-4 RGB subfamily, and `case_0024..0028` are broad field/export true16 residuals hidden by byte-view comparison. | AE-host-grounded residual split |
| 2026-07-09 `case_0010/0011` R/A quantization probe. | `refs/conformance/olmdistancegradation_0010_0011_ra_quantization_probe_20260709.md` captures Mac AE field/shade debug at representative positive and negative witnesses. Render Mode=Gradation Color/no-bg stores `R=32768`, while the PNG visible R follows alpha. The Windows-vs-Mac visible `±2` deltas imply `PF_Pixel16` `store_a` differs by one word. Sign flips by point, so this is not a global store-rounding toggle. | AE-host-grounded / next local field-normalization proof |
| 2026-07-09 local field-normalization proof for `case_0010/0011` is insufficient. | `refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md` compares the request-derived masks through both Mac Meijster and the repository OpenCV-compatible EDT. They are bit-identical at the target raw distances, and simple field-pack/store simulations are not safe as a broad fix. The old non-prewarm field/store packages must not be resent unchanged. `refs/conformance/olmdistancegradation_0010_0011_writeback_follow_return_intake_20260709.md` proves the path reaches `DistanceGradation+0x117051c` and `PF!PF_Interleave1to4<float>`, but the contract pixels are still not bound. The live proof boundary is now `refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_contract_20260709.md`: derive output base/rowbytes/pixel-size and exact addresses for `case_0010 (6,40)` and `(901,394)`, then watch those PF16 words through export. | local negative proof / pointer-map writeback witness next |
| 2026-07-09 pointer-map return binds sparse `case_0010` PF16 stores. | `refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md` classifies the return as `partial_success_missing_true16_export`: not full request acceptance, but enough to retire the pointer-map ask. Windows proves the final PF16 output pointer formula `out = base + y * 0x3c00 + x * 8` with pixel size `8`, rowbytes `0x3c00`, `24356` verified hits, and zero formula misses. Same-run hardware watches bind `(6,40)` to final words `0cc4 8000 0000 0000` (`3268`) and `(901,394)` to `2694 8000 0000 0000` (`9876`) at writer sites `DistanceGradation+0x1170814/+0x117081c/+0x1170824/+0x117082b`. Missing true16 TIFF/EXR export means export binding remains optional follow-up, but the one-word split is present by Windows PF16 store time. | runtime-trace-grounded / partial-success |
| 2026-07-09 sparse `case_0010/0011` is not a final-rounding-only bug. | `refs/conformance/olmdistancegradation_0010_0011_pf16_store_classification_20260709.md` compares Mac debug `out_a`/store values with the Windows pointer-map `xmm2_alpha`/store words. At `(901,394)`, truncating the Mac half-boundary value would match Windows, but at `(6,40)` it would keep the wrong lower word. Windows `xmm2_alpha` is already close to the final PF16 word grid before the writer stores. Therefore a global final `clamp16()` rounding swap is forbidden; the live proof is the 16bpc field-world pack/read path consumed before `FUN_181170480` writes. | local classification / runtime-trace-informed |
| 2026-07-09 PF16 field-pack/read alone is still insufficient for sparse `case_0010/0011`. | `refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md` tests the AEX-shaped hypothesis that the Mac port should pack `df.x` into a PF16 field world before the 16bpc callback reads it. The source shape is correct to inspect because `FUN_181170480` reads field words from a PF16 world and multiplies by `1/32768`, while the Mac port currently passes a float array. But a single `floor`, `ceil`, or round-half-up pack of the current Mac float field cannot match all sign-flipped witnesses: `(6,40)` wants floor, `(901,394)` wants ceil, and `(915,392)` wants ceil/round. The live discriminator is now raw-distance / normalization-denominator / OpenCV field-pack boundary. | local arithmetic audit / not an implementation proof |
| 2026-07-09 sparse `case_0010/0011` denominator split is mixed actual-max and threshold. | `refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md` quantifies the field-word deltas. `(6,40)` is outside-field actual-max normalized (`raw=41`, denominator `~45.54119`, UI outside threshold `82` is not the active denominator), while `(901,394)` and `(915,392)` are threshold-limited inside-field witnesses (`63` and `348`). The required movements are half-boundary scale changes, not a single global denominator or final writer rounding rule. The next local proof is the AEX/OpenCV field-prep detail that measures/clamps actual max, applies threshold, and packs the PF16 field world consumed by `FUN_181170480`. | local denominator audit / not an implementation proof |
| 2026-07-01 threshold-family partial return is now frozen as a stable local evidence object instead of only a transient import. | `refs/returns/windows/20260701_214150_distancegradation_case0023_threshold_followup/...return_windows.zip` and `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_threshold_followup_20260701.md`: the return preserves the endpoint flip and the exact blocker (`FUN_181170480` triplet XY not retained), which keeps the lane on helper/compose ownership and justifies the tighter `triplet_xy_compose_hook` follow-up rather than a broad Constant rewrite. | runtime-trace-grounded / failed-partial but decision-useful |
| 2026-07-01 triplet-hook anchor audit freezes the exact local threshold boundary that the archived output-word Windows hook needed to retain. | `scripts/analyze_distancegradation_case0023_triplet_hook_anchor.py`, `refs/scripts/smoke_analyze_distancegradation_case0023_triplet_hook_anchor.py`, and `refs/conformance/olmdistancegradation_case0023_triplet_hook_anchor_audit_20260701.md`: the local triplet is already precise — `(414,393)` below threshold with `field_x=0`, `(415,393)` first above threshold with `field_x=1`, `(416,393)` deeper on the same plateau side, plus vertical context at `(415,392)` and `(415,394)`. This remains useful boundary context, but the live lane has moved to Mac AE source/output ownership after the 2026-07-07 local probes. | reproducible hook-anchor audit / archived queue context |
| 2026-07-01 triplet-hook follow-up return proves the crossing again but still fails to retain XY at the actual helper/compose hook. | `refs/returns/windows/20260701_225800_distancegradation_case0023_triplet_hook_followup/...return_windows.zip`, `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_triplet_hook_followup_20260701.summary.md`, and `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_triplet_hook_followup_20260701.md`: the exact `414/415/416,393` crossing is preserved (`35.014 -> blue`, `36.013/37.013 -> red`) but `xy_retained_at_compose_hook=false` for the triplet, and `field_value_finally_consumed_by_FUN_181170480` remains null. The next Windows ask therefore has to derive XY from output-word address or compose refcon and stop only when the triplet identity is bound at `FUN_181170480`, not just when broad callback activity appears. | runtime-trace-grounded / failed-partial but decision-useful |
| 2026-07-01 the output-word / compose-refcon follow-up was the then-active Windows proof contract; it is now archived/superseded by the local AEX CPU simu, compose witness, and 2026-07-07 reference export audit. | `refs/conformance/olmdistancegradation_case0023_output_word_triplet_followup_contract_20260701.md`, `refs/conformance/olmdistancegradation_case0023_output_word_triplet_return_acceptance_20260701.md`, and `refs/reports/pending_runtime_trace_packages.md`: the request bound the same triplet from the actual output-word address or compose refcon at `FUN_181170480`, but the current lane no longer needs this package resent as-is. This is archived pre-depth-gate proof context; the live DG near-miss lane is now export-quantization-first, with only `(907,222)` still needing a direct PF16 store/export stop if pursued further. | archived queue-grounded proof contract |
| 2026-07-01 source-candidates audit freezes the current implementation decision ladder for the same `case_0023` lane. | `scripts/analyze_distancegradation_case0023_source_candidates.py`, `refs/scripts/smoke_analyze_distancegradation_case0023_source_candidates.py`, and `refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.md`: with the threshold-family split already bounded, the allowed source order is now explicit and source-lined: first `dt_to_normalized(...)` Constant threshold ownership, then `build_distance_field(...)` Both-mode ownership, and only then `compose_pixel(...)` if a later Windows typed witness explicitly contradicts the current field-first reading. | reproducible source-decision audit |
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
- Normalization: compute one float32 reciprocal of the actual maximum after
  truncation (with denominator at least `1.0`), then multiply each value.
- 16bpc field-world boundary: convert normalized values to PF16 with
  round-to-nearest-even, then read the quantized words back for compose.
- Blur boundary: Reflect101/mirror.

These rules are plausible and guarded, but the remaining residual means exact
Windows OpenCV/helper details are not fully proven.

2026-07-09 case_0010/0011 sparse 16bpc R/A lane:

- Windows pointer-map return is accepted only as partial success because the
  same-run true16 TIFF/EXR export sample is still missing. It nevertheless
  grounds the PF16 output write address formula and final PF16 words for
  `(6,40)` and `(901,394)`.
- `refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md`
  rejects a single field-pack rule over the current Mac float field.
- `refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md`
  splits the witnesses into outside-actual-max and inside-threshold
  half-boundary families.
- `refs/conformance/olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.md`
  narrows the next proof to the AEX/OpenCV field-prep chain before
  `FUN_181170480`, not final writer rounding. The concrete next check is a
  case-bound AEX CPU fieldgen probe with `threshold`, `dist_transform`,
  `resize_same_shape`, and `normalize_minmax` detours registered.
- `refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md`
  executes that probe on the full `1920x1080` inputs. The real-AEX helper
  reproduces current Mac float fields: `case0010_inside` field word float is
  `22891.5` (Windows needs ceil), `case0010_outside` is `29500.5` (Windows
  needs floor), and `case0011_inside` is `4408.50097656` (Windows needs ceil).
  The residual is therefore not a plain EDT/OpenCV helper mismatch and not a
  single PF16 pack/final writer toggle. The next proof belongs at the real
  Windows field-world pack/read boundary.
- `refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_return_intake_20260709.md`
  classifies the field-world pack/read return as
  `partial_success_fieldread_boundary_not_pack`. It does not bind the upstream
  pack site, but it captures the final-writer read-side candidate in `rdx`.
  In the retained run, `(6,40)` has all-zero `rdx_src_words`, `(901,394)` has
  alternating `8000 8000 0000 0000`, and `rdx = rdi - 0xfe0000` at
  `DistanceGradation+0x1170814`. Static asm corrects the register meaning:
  this late `rdx` is the source/shade pointer from `param_1[0]`; field-world is
  read earlier through `RCX` from `param_1[1]` at `DistanceGradation+0x117057d`.
  The next proof is therefore
  `refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md`:
  bind `RCX` field-world words, `RDX` source/shade words, and final writer
  scalars in the same run.
- `refs/conformance/olmdistancegradation_0010_0011_rdx_producer_return_intake_20260710.md`
  classifies the superseded `rdx producer` return as
  `partial_watch_miss_prepopulated_rdx`: both derived `rdx` addresses were
  already populated by the first captured `DistanceGradation+0x1170480`
  callback, and no data-write watch hit occurred. This is negative evidence
  against a callback-level producer watch and reinforces the corrected
  compose-input request above.
- `refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_return_intake_20260710.md`
  classifies the compose-input return as
  `partial_compose_inputs_bound_not_exact_xy`. It confirms `RCX` is the
  field-world read at `DistanceGradation+0x117057d` and `RDX` is the
  source/shade read at `DistanceGradation+0x11705f1`, while the final-writer
  `RDX` at `+0x1170814` remains source/shade. However, the strict
  `r9=x && rbp=y` gate missed both `(6,40)` and `(901,394)`, so `rbp` is not a
  valid y discriminator here. The next proof is
  `refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md`:
  derive field/source/output base + rowbytes + pixel-size address formulas and
  gate the compose reads by exact addresses.

## Interpolation

- Linear: pass `X` through.
- Constant without blur: current port uses `X > 0 ? 1 : 0`, but this is now
  understood as a field-prep behavior, not a `FUN_181170870` compose behavior.
- The remaining Constant 16bpc failures now sit on threshold ownership and
  plateau membership, not generic writeback. The safe next rule checks are
  bounded ones: `<` vs `<=`, which side owns equality, and whether the
  `field_x == 1` plateau is formed before or after the Constant-specific
  binary path.
- A 2026-06-30 decomp pass materially strengthens that reading: the upstream
  helper `FUN_181174760` hardcodes the first threshold as `THRESH_TRUNC`,
  then switches the later threshold/normalize wrapper from mode `2` to
  mode `0` only for the Constant path. So the unresolved question is not
  whether Constant is "binary somewhere" but which pixels land exactly on the
  ownership boundary before that Constant-only binary fork.
- A same-day bounded model probe rejects the narrowest local explanation too:
  nudging the Constant/no-blur comparison from `dist > t` to `dist > t + eps`
  in the simplified AE-free model does not improve any of the focused
  `case_0020..0023` whole-frame comparisons. See
  `refs/conformance/olmdistancegradation_16bpc_constant_threshold_bias_20260630.md`.
  Treat the remaining lane as more structural than a one-line threshold-bias
  tweak.
- A second same-day probe gives the first weak positive signal for the stronger
  helper-shape hypothesis. Plausible two-stage Constant variants modeled after
  `distanceTransform -> threshold(TRUNC) -> distanceTransform -> threshold/...`
  do not help `case_0020/0021`, split `case_0022` (slightly better nonzero
  count but much worse mean), but materially improve `case_0023` under a
  simple `trunc_plateau_binary` shape (`nonzero 203213 -> 182793`,
  `mean 295.305436 -> 20.041926`). See
  `refs/conformance/olmdistancegradation_16bpc_constant_two_stage_variants_20260630.md`.
  This is not implementation-ready proof, but it does make the remaining
  Constant lane look more like helper staging / plateau formation than like a
  scalar threshold compare bug.
- A follow-up correlation audit narrows where that signal lives. Among the
  focused Constant/background cases, `case_0023` is the only one where the same
  two-stage family wins on both nonzero count and mean, and it is also the
  only one with `In/Out=Both` plus `Outside Threshold=0`. `case_0022`
  (`Outside Threshold=11`) shows only a partial signal. See
  `refs/conformance/olmdistancegradation_16bpc_constant_case_correlations_20260630.md`.
  This makes `Both + Outside Threshold=0` the clearest local correlate for the
  unresolved helper-staging behavior.
- A same-day targeted follow-up strengthens that correlation further. When the
  Mac-side diagnostic changes only the outside-side Constant helper in
  `In/Out=Both` cases, `case_0022` stays completely flat under every tested
  variant, while `case_0023` again improves materially under the plateau-style
  family (`nonzero 203213 -> 182793`, `mean 295.305436 -> 1.095836`). See
  `refs/conformance/olmdistancegradation_16bpc_constant_both_outside0_variants_20260630.md`.
  This is still not implementation-ready proof, but it is now a narrow,
  reproducible signal that the unresolved lane is specifically tied to the
  outside-side helper staging when `Both + Outside Threshold=0` is active.
- A live Mac AE implementation probe on 2026-06-30 rejects the simplest
  outside-side equality interpretation. Making the outside-side Constant helper
  use `dist >= t` for `Both + Outside Threshold=0` flips the tracked witness
  points to the Windows endpoint, but it broadens the whole-frame residual
  catastrophically (`case_0023 nonzero_px=182728`, `mean_diff=10.244082...`).
  A narrower retry that also floors the effective threshold to `1.0` produces
  no observable improvement over the current baseline (`case_0023` stays
  `73px`, `case_0022` stays `192px`). See
  `refs/conformance/olmdistancegradation_16bpc_rejected_outside_threshold_eq_probe_20260630.md`.
  Treat the remaining lane as stricter helper staging / threshold ownership,
  not as a one-line equality bug in the outside-side helper.
- A 2026-06-30 live Mac AE probe also rules out a simpler compose-side theory:
  removing the extra post-compose Constant/no-blur threshold in the current Mac
  port does not move the tracked 16bpc witness family at all. Keep the current
  compose code for now and continue investigating upstream Constant field prep.
- The new `case_0023` residual split sharpens where that upstream work should
  land. The surviving `73px` are not arbitrary sparse noise: they all remain
  inside the source alpha region, and they separate cleanly into an
  immediate-boundary bucket (`inside EDT = 1.0`) and a just-beyond-threshold
  bucket (`inside EDT = 36.013885...` with configured `Inside Threshold = 36`).
  That makes the remaining lane look even less like final packing and more
  like exact plateau/threshold ownership in the Constant helper family. See
  `refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.md`.
- A live Mac AE point-debug now grounds that same reading in the current
  plug-in output itself. The tracked `inside EDT = 1.0` witness already lands
  on `field_x=0` while adjacent outside-side pixels flip to `field_x=1`, and
  the `inside EDT = 36.013885...` witness at `(415,393)` sits on the `field_x=1`
  side while immediate neighbors with `raw_inside < 36` stay at `field_x=0`.
  This keeps the active suspect upstream in Constant helper plateau/threshold
  ownership rather than final compose/writeback. See
  `refs/conformance/olmdistancegradation_16bpc_case0023_pointdebug_20260630.md`.
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
| basic 12-case AE package | 8bpc | `known-red` current binary | 2026-07-11 depth-correct canonical rerun: `0/12` exact, worst max `64`. Historical `12/12` candidates have no loaded plug-in hash. | Reconstruct field/compose rules from binary evidence; do not use the unbound historical output as an implementation oracle. |
| extended non-blur 16-case AE package | 8bpc | `known-red` current binary | 2026-07-11 depth-correct canonical rerun: `0/16` exact, worst max `254`. Historical `16/16` candidates have no loaded plug-in hash. | Split by field/compose family before source changes; preserve the grounded 16bpc boundary independently. |
| blur `case_0029` AE package | 8bpc | `known-red` current binary | 2026-07-11 depth-correct canonical rerun: `max=23`, not exact. | Ground OpenCV Gaussian/field boundary before tuning. |
| basic all-opaque Inside `case_0001..0006` | 16bpc | partial AE exact | 2026-06-26 Mac AE: Inside/no-source rule keeps `case_0001/0003/0004/0005/0006` exact and promotes `case_0002` to exact. Basic slice is now 8/12; DistanceGradation total is 9/29 | Static/runtime proof for the no-source branch; continue with non-all-opaque 16bpc residuals |
| basic remaining `case_0015/0017/0018/0019` | 16bpc | not exact / compose-path diagnostic | 2026-06-26 local rerun reproduces the same four failures. `case_0015/0017` are `Render Mode=2` + `Use Background Color=0`; `case_0018/0019` are `Render Mode=1` + `Use Background Color=1` with colored ramps/backgrounds | Ground 16bpc render-mode/background compose path before changing distance field math |
| current exact slice `case_0008/0010/0011/0020/0021/0022/0023` | 16bpc | `AE exact` | 2026-07-11 canonical batch on the OpenCV/PF16-boundary build: `7/16` extended cases exact. `case_0010/0011` are newly exact; the previous five remain exact. See `refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.md`. | Preserve reciprocal-multiply normalization, PF16 nearest-even field roundtrip, Power/Constant fixes, and the depth-gated source mask. |
| depthgate true16 reverify | 16bpc | measurement correction | The old `/tmp/olmdg_16ext_depthgate2` artifacts verify at `5/16` with the canonical 16bpc verifier. `case_0010/0011/0024..0028` were not true16 exact there either. See `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`. | Do not chase a current-vs-depthgate provenance delta unless a new canonical verifier result contradicts this. |
| sparse R/A quantization `case_0010/0011` | 16bpc | `AE exact` | Closed 2026-07-11 by reproducing OpenCV reciprocal-multiply normalization and PF16 round-to-nearest-even field-world conversion. Both canonical outputs have `max_diff=0`. | Preserve the binary-grounded boundary; cancel the superseded broad exact-address retry for this family. |
| Layer/no-bg source family `case_0012/0013/0014/0016` | 16bpc | not exact / narrowed export-rounding family | 2026-07-08 Layer/no-bg straight-source RGB plus focused low-alpha hidden-color/Both dominant-channel patches reduce the family to true16 residuals: `case_0012 nonzero=2948 max=2`, `case_0013 nonzero=9006 max=2`, `case_0014 nonzero=9630 max=4`, `case_0016 nonzero=5373 max=2`. The 2026-07-09 audit `refs/conformance/olmdistancegradation_16bpc_export_rounding_residual_audit_20260709.md` confirms every nonzero delta in the four focused cases is even-valued; `case_0014` is the only focused case with RGB abs delta `4` and has retained target examples. The all-modes dominant-channel probe reduced `case_0014` to max `2` but is deferred/not-adopted because it is PNG/AE-host diagnostic evidence only and still non-exact; see `refs/conformance/olmdistancegradation_dominant_channel_all_modes_probe_rejected_20260709.md`. | Do not return to broad straight-vs-premultiplied tuning, broad low-alpha ratio rules, or all-mode dominant-channel promotion without binary proof or canonical batch validation. Next proof is a store/export-boundary witness for one representative `case_0012` +/-2 pixel and one `case_0014` -4 RGB pixel, or a Mac AE debug export proving whether the PF16 store already contains the Windows word. |
| `case_0024..0027` true16 residual family | 16bpc | not exact / max-2 field-export family | The PF16-boundary build reduces all four cases to `max=2`, but they remain broad and non-exact. | Classify sign/channel distribution before requesting a typed store/export witness; no global rounding toggle. |
| `case_0028` true16 residual | 16bpc | not exact / separate outlier | PF16-boundary build remains `max=3080`, `nonzero_pixels=461476`. | Keep separate from the max-2 family and ground its parameter-specific field/compose branch. |
| smaller residuals `case_0016` plus `case_0028` | 16bpc | not exact / separate small families | Current integrated canonical batch: `case_0016 nonzero=5373 max=2`; `case_0028 nonzero=457177 max=3080`. | Classify after `0010/0011` and the Layer/no-bg residual unless a parameter correlation ties them together. |
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
