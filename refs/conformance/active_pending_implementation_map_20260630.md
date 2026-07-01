# Active Pending Implementation Map - 2026-07-01

This note converts the live Windows runtime-trace wait, plus the just-answered
OLMBlur witness, into concrete
Mac-side implementation decision points.

It is intentionally narrow: only the currently pending witness lanes and the
freshly-answered OLMBlur boundary are included here.

## 1. OLMBlur `olmblur__case_0006` non-Legacy helper/pre-store witness

- Answered package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_case0006_helper_prestore_witness_20260630.zip`
- Latest comparison:
  `refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_witness.md`
- Current Mac evidence:
  - `refs/conformance/olmblur_case0006_nonlegacy_helper_witness_20260630.md`
  - `refs/conformance/olmblur_case0006_source_audit_20260630.md`
  - `refs/conformance/olmblur_writer_only_hypothesis_20260630.md`
  - `refs/conformance/olmblur_pending_final_word_proof_20260629.md`
  - `refs/reports/runtime_trace_returns/olmblur_case0006_helper_prestore_failed_20260630/summary.md`
  - `refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_failed_20260630/olmblur_case0006_helper_prestore_witness.md`

### Current reading

- The focused Windows return is now `answered`.
- At both active witnesses, Windows and Mac agree on:
  - pre-store float: `1100.5` / `363.5`
  - stored internal word: `1100` / `364`
- That retires both of the old live suspicions for `case_0006`:
  - not a non-Legacy writer-rule mismatch
  - not a helper-local divergence at those two final witnesses
- The remaining exported PNG mismatch is therefore outside the proven internal
  OLMBlur word-store boundary for these points. Treat it as
  reference-generation / export-provenance work until stronger contradictory
  evidence appears.

### Mac code sites that may change once Windows witness arrives

None from this witness alone.

The current answered evidence does not justify touching:

1. Non-Legacy helper accumulation:
   - `blur_1d_horizontal(...)`
   - `blur_1d_vertical(...)`
2. Final 16bpc writer:
   - `round_blur_value(...)`
   - `store16(...)`

all in `mac/OLMBlur/OLMBlur.cpp`.

### Decision gate

If later evidence contradicts the answered witness:

- require a new current-AEX capture that explicitly disagrees on
  pre-store float or stored internal word
- otherwise keep `case_0006` in provenance/export audit, not source surgery

Practical next step for this lane:

- compare any current-AEX Windows exported PNG from the same probe run against
  the canonical 2026-06-25 16bpc reference set
- if that exported PNG agrees with Mac rather than the canonical reference,
  reclassify the current `case_0006` residual as a reference-generation split

### Explicit non-goals until the witness arrives

- No broad PNG tuning
- No reopening Legacy `case_0007`
- No global writer swap justified only by `(314,14)`
- No helper-accumulation rewrite from this answered witness

## 2. OLMDistanceGradation `olmdistancegradation_extended__case_0023`

- Pending package:
  `refs/runtime_trace_packages/olm_runtime_trace_requests_20260630_182750.zip`
- Share copy:
  `/Volumes/onmk/olm_pr/new/olm_runtime_trace_requests_20260630_182750.zip`
- Current Mac evidence:
  - `refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.md`
  - `refs/conformance/olmdistancegradation_16bpc_case0023_pointdebug_20260630.md`
  - `refs/conformance/olmdistancegradation_case0023_probe_refresh_20260701.md`
  - `refs/conformance/olmdistancegradation_16bpc_case0023_plateau_transition_20260701.md`
  - `refs/conformance/olmdistancegradation_case0023_source_audit_20260630.md`
  - `refs/conformance/olmdistancegradation_16bpc_rejected_outside_threshold_eq_probe_20260630.md`
  - `refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_boundary_witness_20260630.md`
  - `refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_case0023_outside0_witness.md`

### Current reading

- Remaining residual is only `73px`, split into two buckets:
  - `65px` at `inside EDT = 1.0`, `outside EDT = 0.0`
  - `8px` at `inside EDT = 36.013885...`, `outside EDT = 0.0`
- Live Mac field debug already proves the residual exists before final 16bpc
  writeback.
- A fresh 2026-07-01 single-case rerun now packages that same proof into a
  reusable request plus machine-readable point report:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/field_debug_report.md`.
- Windows runtime evidence already says the lane is still
  Constant/THRESH_BINARY ownership, not generic compose drift.
- The narrowed `case_0023` follow-up now also has a dedicated comparison file,
  so this lane is no longer only described in the global runtime summary.
- A simple outside-side equality tweak (`>=` or floor-to-1) was tested and
  rejected as too broad or ineffective.
- A broader local outside-side plateau rewrite (`trunc_plateau_binary`) was
  also re-audited against the live `73px` candidate and is now explicitly
  rejected as an implementation candidate: it broadens the frame to
  `182793px`, so keep it only as hypothesis evidence, not as a patch shape.

### Mac code sites that may change once Windows witness arrives

1. Constant helper staging / threshold ownership:
   - `dt_to_normalized(...)`
   - `build_distance_field(...)`
   - file: `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
2. Only if Windows explicitly contradicts current assumption:
   - `compose_pixel(...)`
   - same file

### Decision gate

If Windows returns the missing typed witness around `FUN_181170480` /
case-local ownership:

- If the decisive value is already wrong before compose:
  - keep changes inside `dt_to_normalized()` / `build_distance_field()`
  - focus on plateau membership, `Both` ownership, and the
    `Outside Threshold=0` special lane
- If compose input matches but output endpoint is still different:
  - only then reopen `compose_pixel()`
- If Windows can only observe the decisive rule one stage earlier/later:
  - update the request contract, not the PNG-fit code

### Explicit non-goals until the witness arrives

- No generic 16bpc writeback changes
- No broad color-mix tuning
- No reopening already-rejected simple equality probes as if they were fixes
- No forgetting that the case is now cheaply re-runnable on Mac AE; use the
  dedicated single-case probe before doing broad batch reruns for this lane.

## 3. OLMRadialBlur Zoom / tiny Rotation caller-collapse follow-up

- Pending package:
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_caller_collapse_followup_20260701.zip`
- Share copy:
  `/Volumes/onmk/olm_pr/new/olm_runtime_trace_radialblur_caller_collapse_followup_20260701.zip`
- Current Mac evidence:
  - `refs/conformance/olmradialblur_outer_caller_collapse_probe_20260630.md`
  - `refs/conformance/olmradialblur_outer_validity_rejection_20260630.md`
  - `refs/conformance/olmradialblur_caller_collapse_plane_diag_20260701.md`
  - `refs/conformance/olmradialblur_outer_propagated_validity_probe_20260701.md`
  - `refs/conformance/olmradialblur_local_witness_dumps_20260630.md`
  - `refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md`
  - `refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md`
  - `refs/reports/pending_runtime_trace_packages.md`
  - `notes/IR_OLMRadialBlur.md`

### Current reading

- The remaining outer lanes are now explicitly split:
  - Zoom `case_0009` is a caller-collapse / denominator issue on the final
    alpha path, not a final byte-packing issue.
  - tiny Rotation `case_0010` is an upstream polar RGB / substitute-path issue,
    not a validity-alpha issue.
- Local probes have already rejected the obvious shortcuts:
  - direct binary-validity substitution
  - zero-RGB-on-invalid substitution
  - propagated-validity-alpha substitution
- The current Mac source still uses one blurred polar alpha plane in the outer
  inverse-sampling path, so it does not yet model the AEX caller-side
  `+0xf252 -> +0xf250 -> +0xe.alpha` split that the Windows follow-up now asks
  for directly.
- Mac AE now also has a narrow local witness surface for this lane:
  `refs/conformance/olmradialblur_mac_debug_hook_20260701.md`. The plug-in can
  dump `sample_rgba`, `sample_u8`, `validity_alpha`, and four-cell
  `cell_valid` / `cell_alpha` for exact output XYs via
  `OLMRADIALBLUR_DEBUG_DUMP_PATH` and `OLMRADIALBLUR_DEBUG_POINTS`. Use that
  before any broad rerun if the next patch needs local Mac-AE confirmation.
- A same-day host rerun now proved one more operational boundary:
  single-case AE requests for RadialBlur must carry `project.bits_per_channel=8`
  or host falls back to copy-input behavior, which only reflects the current
  unimplemented 16/32bpc path. With explicit 8bpc, live AE output re-enters the
  expected guarded lanes and the new debug hook becomes useful:
  `refs/conformance/olmradialblur_mac_ae_single_case_probe_20260701.md`.
- The same host lane now has one more guardrail in tooling: AE single-case runs
  are serialized by `scripts/run_ae_single_case.py` because parallel wrappers
  can race on shared `$.setenv(...)` state inside one AE process. This removes
  the earlier mixed/missing RadialBlur debug-log artifact and makes the narrow
  host witness surface trustworthy again.
- A latest isolated `case_0010` host rerun with `cell_rgb` dumping narrows the
  active Rotation hypothesis one step more. At the max witness `(1614,6)`, all
  four contributing final polar cells are already dark or negative even though
  `validity_alpha_u8=255`. So the next Mac-side movement should target
  upstream Rotation polar RGB population / prepass-scatter structure rather
  than another final inverse-sample validity tweak.
- An immediate follow-up with `src_cell_rgba` narrows it again: those same four
  direct source polar cells are all `RGBA=(0,0,0,1)`. So the remaining issue
  is not suppression of already-bright witness source cells; it is which nearby
  Rotation contributions or grid placements should have populated the bright
  lobe before final inverse sampling.
- A bounded CLI offset sweep now rejects the simplest "global grid is just a
  little shifted" version of that theory. Quarter/half-step angular offsets
  and quarter/half-pixel radial offsets all worsen `case_0010`; the current
  zero-offset grid remains best. Treat the remaining branch as contribution
  ownership / neighbor geometry, not a single uniform angular/radial offset.
- A same-day local support audit now makes that branch concrete. The current
  no-inner implementation forms the witness from same-row backward support
  `ai, ai-1, ai-2`, and on the witness rows that support mixes one mildly
  positive row (`843`) with two rows whose third tap is already negative
  (`844/845`). A pure forward same-row pass is zero at the witness too. So the
  next implementation lane should stop assuming "plain 1D same-row blur with a
  different tiny offset/direction" and instead target AEX-specific outer
  contribution ownership.
- A nearby source-polar scan now identifies the live local bright family:
  positive source cells cluster at `row 843 / ai 1601..1602`, while the direct
  source cells for witness rows `844/845` are zero or negative. The current
  model can brighten row `843` a little, but it cannot carry that brightness
  into the rows that dominate the final witness bilinear mix. The next narrow
  implementation lane should therefore test a row-coupled outer population
  model rather than more same-row blur variants.
- A bounded CLI `prev-row-add` probe now supports that lane directionally.
  Even a tiny previous-row coupling (`scale=0.01`) starts injecting red values
  into the missing witness patch while keeping the residual relatively near the
  current baseline; larger scales over-brighten the broader image and worsen
  mean sharply. So "cross-row outer population exists" looks more plausible,
  but the AEX ownership is more selective than a uniform previous-row add.
- A tighter version of that probe is better still: `prev-row-tail-positive`
  (only `k>0` previous-row taps with positive source luma) beats both uniform
  `prev-row-add` and generic `prev-row-tail-add`. At `scale=0.01` it reaches
  `mean=0.01424` while preserving the same local patch lift, which is the best
  cross-row diagnostic so far. That keeps the next implementation lane on
  "small positive-only tail coupling", not on broad row mixing.
- An even narrower follow-up is better again: `prev2-row-tail-positive`
  (`ri-2`, positive-only, `k>0`) beats both `prev-row-tail-positive` and the
  `ri-1 + ri-2` ladder blend. Best local result so far is
  `prev2-row-tail-positive scale=0.005` at `mean=0.01256`. So the live lane is
  now "sparse positive tail coupling from farther-up rows", not generic
  neighboring-row averaging.

### Mac code sites that may change once Windows witness arrives

1. Outer Zoom caller-collapse / inverse sample path:
   - `RenderZoom8(...)`
   - especially the polar accumulation and final `sample(...)` / `alpha`
     reconstruction block
   - file: `mac/OLMRadialBlur/OLMRadialBlur.cpp`
2. Outer Rotation caller-collapse or substitute-path population:
   - `RenderRotation8(...)`
   - especially the blurred polar plane construction and final inverse-sample
     block
   - same file

### Decision gate

If Windows returns the requested typed outer values:

- If Zoom disagrees at `+0xf252` / `+0xf250` before final inverse sampling:
  - keep the patch inside outer polar accumulation / caller-collapse state
  - do not reopen final byte packing
- If Zoom matches through `+0xe.alpha` but diverges only at the final sample:
  - patch only the final inverse-sample denominator / alpha formation
- If tiny Rotation already differs before the final sample:
  - keep the patch in the polar RGB population / substitute path
  - do not retune validity alpha
- If tiny Rotation only diverges at the final sample despite matching upstream:
  - reopen the final inverse-sample branch for Rotation only

### Explicit non-goals until the witness arrives

- No AE visual matching
- No global validity-alpha tuning
- No final byte-pack tweaks for Zoom
- No treating tiny Rotation as a simple validity gate problem

## 4. OLMKiraKira hotspot compose/writeback witness

- Pending package:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_hotspot_compose_writeback_witness_20260701.zip`
- Share copy:
  `/Volumes/onmk/olm_pr/new/olm_runtime_trace_kirakira_hotspot_compose_writeback_witness_20260701.zip`
- Current Mac evidence:
  - `refs/conformance/olmkirakira_pending_compose_proof_20260629.md`
  - `refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.md`
  - `refs/conformance/olmkirakira_hotspot_local_compose_diagnostic_20260701.md`
  - `refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md`
  - `notes/IR_OLMKiraKira.md`

### Current reading

- The broad upstream lanes are already grounded enough to leave alone:
  - BT.709 luma seed
  - ray-helper staging
  - `FUN_18114fd90` glow normalization / opacity path
- The remaining hotspot at `(934,118)` already mismatches at the Mac
  compose-boundary value, and the gap is too large to explain by the already
  grounded grayscale control attenuation alone.
- So the live blocker is now narrower than a global gain/compose retune: it is
  a hotspot-local attenuation, merge-mode branch, or final quantization step
  between post-`fd90` glow and final writeback.

### Mac-only local diagnostics already available

- The current Mac plug-in can already dump point-local
  `src / glow_norm / glow_alpha_after_opacity / out_prequantized / out_u8`
  for arbitrary coordinates via `OLMKIRAKIRA_DEBUG_DUMP_PATH` and
  `OLMKIRAKIRA_DEBUG_POINTS`.
- The dump can now be summarized mechanically with:
  `python3 scripts/analyze_kirakira_compose_debug_neighborhood.py --debug-log /path/to/kirakira_debug.log --center 934,118 --radius 1 --windows-target-u8 131 --output-json /tmp/kirakira_neighborhood.json --output-md /tmp/kirakira_neighborhood.md`
- That makes two bounded local probes worthwhile while Windows is pending:
  1. re-dump `(934,118)` plus control points `(960,540)` and `(1010,540)`
  2. dump a `3x3` or `5x5` hotspot neighborhood to see whether the attenuation
     shape is branch-like or smooth
- Those local probes do not replace the Windows witness, but they are safe
  because they stay at the already-accepted compose boundary rather than
  reopening BT.709 / box / ray-helper lanes.
- A live 2026-07-01 `3x3` probe is now captured in
  `refs/conformance/olmkirakira_hotspot_neighborhood_probe_20260701.md`:
  `x=933` is consistently lower while `x=934..935` stays on a near-plateau for
  all three sampled rows. That makes the local shape look branch-like / region-
  like rather than like a smooth center-out attenuation or a pure final-byte
  rounding issue.
- A same-day `5x5` follow-up strengthens that further:
  the local shape now looks like three lanes, not one hotspot point:
  low `x=932`, transition `x=933`, and a broad plateau at `x>=934`.
  That means the next Windows witness should be read as
  "does Windows share this lane split but attenuate the plateau differently, or
  does it diverge before this split is formed?"

### Mac code sites that may change once Windows witness arrives

1. Hotspot-local merge/compose path:
   - `Render8(...)` final compose block where `out.r/g/b` are built from
     `src` and `glow`
   - same file: `mac/OLMKiraKira/OLMKiraKira.cpp`
2. Only if Windows shows a final mismatch after matching compose float:
   - the final quantization / clamp boundary immediately before byte store
   - same file

### Decision gate

If Windows returns the requested hotspot-local values:

- If `glow_rgba_float` already differs from the Mac witness:
  - reopen the post-`fd90` hotspot-local attenuation branch
  - do not retune global BT.709 or box/ray stages
- If `glow_rgba_float` matches but `composed_rgba_float` differs:
  - patch only the merge-mode-1 compose branch
- If compose float matches but final u8 differs:
  - patch only the final quantization/clamp boundary
- If all returned hotspot-local values match:
  - reclassify the residual as reference/export or witness-placement drift

### Explicit non-goals until the witness arrives

- No broad luma retuning
- No boxFilter / warp / ray-helper changes
- No global compose-scale changes
- No hotspot fix inferred from PNG-only tuning

## Operational bottom line

The remaining live Windows wait is not "more PNGs".

They are the narrowest remaining proofs for:

1. whether DistanceGradation `case_0023` is a stricter Constant helper staging
   rule or an unexpected compose-side branch
2. whether RadialBlur Zoom differs in caller-collapse state or only in the
   final inverse-sample denominator, and whether tiny Rotation loses a bright
   contribution before or during the final sample
3. whether KiraKira's hotspot residual is a merge-mode / attenuation branch or
   only a final quantization mismatch

Meanwhile, OLMBlur `case_0006` has crossed from "needs runtime witness" into
"needs provenance/export explanation". Mac-side work there should stay on
comparison quality and reference auditing rather than broad implementation
churn.
