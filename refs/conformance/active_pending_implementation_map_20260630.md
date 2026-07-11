# Active Pending Implementation Map - 2026-07-01

> **Historical correction (2026-07-10):** the OLMBlur `answered` reading in
> section 1 is invalid. No `TARGET_OLMBLUR_CASE0006_*` CDB block was captured,
> and the later numeric `windows_*` fields have no independent Windows runtime
> provenance. Use
> `refs/conformance/olmblur_case0006_unverified_windows_value_audit_20260710.md`
> and the current conformance ledger instead.

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
  - `refs/conformance/olmblur_case0006_reference_provenance_20260701.md`
  - `refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.md`
  - `refs/conformance/olmblur_source_candidates_audit_20260701.md`
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
- The companion Legacy `case_0007` lane is now also split more cleanly than
  before: `refs/conformance/olmblur_case0007_halfstep_family_audit_20260701.md`
  freezes that normalized 16bpc `(345,672)` is already resolved as a Windows
  pre-store float delta, while old normalized 8bpc `(488,941)` is still the
  only same-family witness that would need a new Windows pre-store float if we
  decide to advance that branch.
- A new machine audit now freezes that provenance reading reproducibly:
  `refs/conformance/olmblur_case0006_reference_provenance_audit_20260701.md`
  proves the canonical 2026-06-25 reference and handoff expected file are
  byte-identical, while the two known Mac export artifacts disagree with that
  canonical file in different directions. With no same-run Windows current-AEX
  export artifact in-tree, the lane remains `current-aex-export-missing`, not
  "needs Mac source change".
- That same audit now also freezes the local alias structure so we do not
  accidentally count duplicate export artifacts as new evidence:
  `handoff/.../results/.../case_0006` is byte-identical to the tracked
  `mac_single_export`, and the archived
  `handoff/archive/.../results/.../case_0006` is byte-identical to the tracked
  endian-fix `mac_batch_export`.
- A new source-candidates audit now freezes the implementation order across the
  still-live OLMBlur lanes:
  `refs/conformance/olmblur_source_candidates_audit_20260701.md`
  keeps `case_0006` behind a non-source provenance/export gate, keeps the
  non-Legacy writer boundary ahead of helper accumulation if that gate is ever
  contradicted, and keeps Legacy `case_0007` split by bit depth so the
  resolved 16bpc witness does not reopen the old normalized 8bpc lane by
  accident.

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
- use `refs/conformance/olmblur_case0006_current_aex_export_contract_20260701.md`
  as the exact request/acceptance boundary if a Windows export follow-up is
  scheduled
- the same boundary is now machine-auditable too:
  `refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md`
  stays `awaiting-windows-current-aex-export` until that artifact is imported,
  then classifies it directly as Outcome `A`, `B`, or `C`
- if that exported PNG agrees with Mac rather than the canonical reference,
  reclassify the current `case_0006` residual as a reference-generation split

### Explicit non-goals until the witness arrives

- No broad PNG tuning
- No reopening Legacy `case_0007`
- No global writer swap justified only by `(314,14)`
- No helper-accumulation rewrite from this answered witness

## 2. OLMDistanceGradation `olmdistancegradation_extended__case_0023`

- Returned package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701.zip`
- Archived return:
  `refs/returns/windows/20260701_225800_distancegradation_case0023_triplet_hook_followup/olm_runtime_trace_olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701_return_windows.zip`
- Current Mac evidence:
  - `refs/conformance/olmdistancegradation_16bpc_case0023_residual_split_20260630.md`
  - `refs/conformance/olmdistancegradation_16bpc_case0023_pointdebug_20260630.md`
  - `refs/conformance/olmdistancegradation_case0023_probe_refresh_20260701.md`
  - `refs/conformance/olmdistancegradation_16bpc_case0023_plateau_transition_20260701.md`
  - `refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.md`
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
- The local Mac probe surface is now one step richer too. A fresh rerun of that
  single-case request will append per-side helper outputs (`inside_x`,
  `outside_x`, `both_x`), Constant threshold-scaled values, binary ownership
  bits, and `compose_input_x` for each requested point via
  `OLM_DG_DEBUG_DUMP_PATH`; the parser in
  `scripts/analyze_distancegradation_debug_points.py` now preserves those
  fields automatically.
- That richer probe has now been exercised once on host with the rebuilt
  DistanceGradation plug-in:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/field_debug_report_20260702.md`
  and `/private/tmp/olmdg_case0023_probe_20260702/verify/case0023_verify.json`.
  The live `case_0023` triplet stays on the same unresolved lane
  (`max=61165`, `mean=1.0518` in authoritative 16bpc compare), but the new
  helper values tighten the interpretation further: `(414,393)` and
  `(415,392)` stay `inside_x=0/outside_x=0/compose_input_x=0`, while
  `(415,393)`, `(416,393)`, and `(415,394)` are already
  `inside_x=1/outside_x=0/compose_input_x=1`. So the current Mac host build
  confirms that the threshold-family split is already decided in field prep
  before compose, not in final 16bpc packing.
- The older Windows package is now evidence context only: it stayed too
  edge-family-centric. The first threshold-family-only follow-up then returned
  `failed_partial` and proved the endpoint flip, but it still did not retain
  the case-local helper/compose stop with the triplet XY identity attached.
  The live send target first moved to the tighter helper/compose-hook follow-up
  documented in
  `refs/conformance/olmdistancegradation_case0023_triplet_xy_compose_followup_contract_20260701.md`
  and
  `refs/conformance/olmdistancegradation_case0023_triplet_xy_compose_return_acceptance_20260701.md`,
  then to the output-word follow-up:
  `refs/conformance/olmdistancegradation_case0023_output_word_triplet_followup_contract_20260701.md`
  and
  `refs/conformance/olmdistancegradation_case0023_output_word_triplet_return_acceptance_20260701.md`,
  and now to the current refcon/wordmap follow-up:
  `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_followup_contract_20260702.md`
  and
  `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md`.
- Windows runtime evidence already says the lane is still
  Constant/THRESH_BINARY ownership, not generic compose drift.
- The narrowed `case_0023` follow-up now also has a dedicated comparison file,
  so this lane is no longer only described in the global runtime summary.
- The comparison path is now stricter too: `scripts/compare_distancegradation_trace.py`
  directly recognizes both
  `olmdistancegradation_case0023_threshold_family_followup_20260701` and
  `olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701`,
  plus the superseded output-word ask
  `olmdistancegradation_case0023_output_word_triplet_followup_20260701`,
  and carries the local threshold-triplet context into the generated
  comparison, so the return can be judged against the `414/415/416,393`
  crossing immediately instead of being folded back into the older edge-family note.
- A dedicated local triplet-hook anchor audit now freezes the exact boundary
  that the current output-word Windows ask must retain:
  `refs/conformance/olmdistancegradation_case0023_triplet_hook_anchor_audit_20260701.md`.
  It records that the local transition is already pinned at the same-row triplet
  `(414,393) -> (415,393) -> (416,393)` with `field_x 0 -> 1 -> 1`, plus the
  vertical contrast pair `(415,392)` / `(415,394)`. That means the Windows
  debugger lane is no longer "find the threshold crossing"; it is specifically
  "hold this XY identity at the helper/compose hook and type the consumed value".
- The stored threshold-family partial return now also has a stable project-local
  evidence path and direct comparison:
  `refs/returns/windows/20260701_214150_distancegradation_case0023_threshold_followup/20260701_214150__olm_runtime_trace_olmdistancegradation_case0023_threshold_family_followup_20260701_return_windows.zip`
  and
  `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_threshold_followup_20260701.md`.
  Use those instead of the blank generic import index when reviewing what the
  failed-partial return actually proved.
- The newer triplet-hook follow-up is now frozen the same way:
  `refs/returns/windows/20260701_225800_distancegradation_case0023_triplet_hook_followup/olm_runtime_trace_olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701_return_windows.zip`
  and
  `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_triplet_hook_followup_20260701.md`.
  That return preserves the exact `414/415/416,393` crossing again, but
  `xy_retained_at_compose_hook=false` for all three representatives and
  `field_value_finally_consumed_by_FUN_181170480` is still null. So the next
  Windows ask must derive XY from output-word address or compose refcon at the
  actual hook, not re-send this same package.
- The next publishable package for this lane is now:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`
  with contract
  `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_followup_contract_20260702.md`
  and acceptance
  `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md`.
- That output-word follow-up has now also returned and been archived locally:
  `refs/returns/windows/20260702_0012_distancegradation_case0023_output_word_followup/olm_runtime_trace_olmdistancegradation_case0023_output_word_triplet_followup_20260701_return_windows.zip`
  plus
  `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_output_word_triplet_followup_20260701.md`.
  It is still `failed_partial`: the `414/415/416,393` endpoint crossing is
  preserved, but no retained frame binds the triplet from output-word address
  or compose refcon, and the consumed helper / compose value is still null. So
  the next Windows retry must start by dumping refcon layout and recovering
  xy/output-address mapping from `r8/r9/refcon` before setting the data
  breakpoints on the three `RGBA16` word ranges.
- A new machine audit now consolidates the current local proof boundary:
  `refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.md`
  reproduces that the lane is only `73px`, already splits into the `inside=1.0`
  and `35.014 -> 36.013 -> 37.013` buckets, and that the tempting
  `trunc_plateau_binary` family is non-promotable because it blows the frame up
  to `182793px`.
- A second machine audit now freezes the implementation decision ladder too:
  `refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.md`
  now splits the lane by family instead of treating all `73px` as one bug.
  Threshold-family `(414/415/416,393)` is a provenance/export gate first:
  live Mac AE already matches the latest Windows typed triplet at `(415,393)`,
  while the packaged expected PNG stays stale there. Edge-family `(1699,7)`
  remains the live implementation lane, with source suspicion ordered as
  `build_distance_field(...)` first, `dt_to_normalized(...)` second, and
  `compose_pixel(...)` only if a later Windows contradiction says compose input
  is already correct.
- A new live Mac `bg_off` negative probe keeps the remaining implementation
  lane narrow:
  `refs/conformance/olmdistancegradation_case0023_bgoff_current_probe_20260702.md`.
  Current Mac `Use Background Color=0` still differs from the Windows `bg_off`
  reference by `73px`, but the disagreement is now highly localized:
  `(1698,7)`, `(1700,7)`, `(414,393)`, and `(416,393)` already match, while
  `(1699,7)` and `(415,393)` still differ. So the residual is not merely the
  final bg-on blend, but also not a broad branch failure.
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

## 3. OLMRadialBlur tiny Rotation narrow follow-up

- Returned package:
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701.zip`
- Archived return:
  `refs/returns/windows/20260701_225800_radialblur_tiny_rotation_backstep_followup/olm_runtime_trace_radialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701_return_windows.zip`
- Current Mac evidence:
  - `refs/conformance/olmradialblur_outer_caller_collapse_probe_20260630.md`
  - `refs/conformance/olmradialblur_outer_validity_rejection_20260630.md`
  - `refs/conformance/olmradialblur_caller_collapse_plane_diag_20260701.md`
  - `refs/conformance/olmradialblur_outer_propagated_validity_probe_20260701.md`
  - `refs/conformance/olmradialblur_local_witness_dumps_20260630.md`
  - `refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md`
  - `refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md`
  - `refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.md`
  - `refs/conformance/olmradialblur_tiny_rotation_support_envelope_20260701.md`
  - `refs/reports/pending_runtime_trace_packages.md`
  - `notes/IR_OLMRadialBlur.md`

### Current reading

- The remaining outer lanes are now explicitly split, and one half is no
  longer the best live Windows ask:
  - Zoom `case_0009` is a caller-collapse / denominator issue on the final
    alpha path, not a final byte-packing issue. The 2026-07-01 return already
    made this bounded and should now be treated as evidence context.
  - tiny Rotation `case_0010` is still an upstream polar RGB /
    substitute-path issue, not a validity-alpha issue, and is the actual live
    debugger lane.
- The old shared Windows package is therefore no longer the active send target.
  The first tiny-only follow-up also returned `failed_partial`, so the live
  boundary first moved to the tighter inverse-sampler backstep contract:
  `refs/conformance/olmradialblur_tiny_rotation_backstep_followup_contract_20260701.md`
  and `refs/conformance/olmradialblur_tiny_rotation_backstep_return_acceptance_20260701.md`,
  then to the anchor-watch contract:
  `refs/conformance/olmradialblur_tiny_rotation_anchor_watch_followup_contract_20260701.md`
  and `refs/conformance/olmradialblur_tiny_rotation_anchor_watch_return_acceptance_20260701.md`,
  and now to the current pointer/watch contract:
  `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_followup_contract_20260702.md`
  and `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md`.
- Intake is now narrowed on the Mac side too:
  `scripts/compare_radialblur_trace.py` recognizes
  `olmradialblur_tiny_rotation_substitute_path_followup_20260701` and the
  tighter `olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701`
  directly, plus the superseded anchor-watch ask
  `olmradialblur_tiny_rotation_anchor_watch_followup_20260701`,
  classifies typed upstream returns as
  `tiny_rotation:substitute-or-upstream-rgb`, and carries the frozen local lane
  audit (`same_row_structure`, `source_polar_structure`, `row_coupling_probe`)
  into the comparison output so the Windows witness is judged against the live
  substitute-path hypothesis instead of the older shared outer residual story.
- A dedicated local backstep-anchor audit now freezes the exact last stable
  sample point that the current anchor-watch ask starts from:
  `refs/conformance/olmradialblur_tiny_rotation_backstep_anchor_audit_20260701.md`.
  It records that the reliable local inverse-sampler anchor for
  `case_0010 (1614,6)` is `(angle=1603.83948, radius=844.317505)`, with direct
  support only on rows `844/845` and the nearest positive family one row above
  at `row 843 / angles 1601..1602`. That means the Windows debugger lane is no
  longer "find the right final sample"; it is specifically "step backward from
  this anchor until the first upstream inclusion/substitute branch is typed".
- 2026-07-01 tiny-only return outcome:
  the package came back `failed_partial`, but usefully. It reconfirmed the
  final white byte at `(1614,6)`, the same near-black inverse-sampler source
  sample, and the absence of any retained upstream substitute/fallback or
  `+0xf252/+0xf250/+0xe` chain capture. So the next Windows round should hook
  from that reliable inverse-sampler coordinate hit and step backward into
  polar population / substitute-promotion, rather than re-asking for final
  bytes or broad outer-lane logs.
- The newer backstep follow-up is now also archived and compared locally at
  stable paths:
  `refs/returns/windows/20260701_225800_radialblur_tiny_rotation_backstep_followup/olm_runtime_trace_radialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701_return_windows.zip`
  and
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.md`.
  It remains `failed_partial`: the stable `+0x4eb9/+0x4ec8` anchor and same
  near-black sample are preserved, but the first upstream promotion branch is
  still not retained. So the next Windows ask must go narrower than this
  package by attaching stack/pointer context or sampled-cell watchpoints to the
  anchor rather than re-sending this same backstep package.
- The next publishable package for this lane is now:
  `refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip`
  with contract
  `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_followup_contract_20260702.md`
  and acceptance
  `refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md`.
- That anchor-watch follow-up has now also returned and been archived locally:
  `refs/returns/windows/20260702_0012_radialblur_tiny_rotation_anchor_watch_followup/olm_runtime_trace_radialblur_tiny_rotation_anchor_watch_followup_20260701_return_windows.zip`
  plus
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_watch_followup_20260701.md`.
  It is still `failed_partial`: the stable `+0x4eb9/+0x4ec8` anchor and same
  near-black sampled RGBA are preserved, but no retained watchpoint path holds
  the sampled polar cell, neighboring rows, or the first upstream promotion
  branch. So the next Windows retry must dump `rsi/rbp/rsp`-derived polar-grid
  and row pointers at the stable anchor, compute the exact sampled-cell
  address for source xy `[1603.8396,844.3175]`, then set read/write
  watchpoints on that cell and neighboring rows before final inverse sampling.
- That failed-partial return is now also archived and compared locally at
  stable paths:
  `refs/returns/windows/20260701_214150_radialblur_tiny_rotation_substitute_followup/20260701_214150__olm_runtime_trace_radialblur_tiny_rotation_substitute_path_followup_20260701_return_windows.zip`
  and
  `refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_substitute_followup_20260701.md`.
  Read that comparison for the preserved white-byte / near-black-sampler facts
  instead of the empty generic import index.
- Local probes have already rejected the obvious shortcuts:
  - direct binary-validity substitution
  - zero-RGB-on-invalid substitution
  - propagated-validity-alpha substitution
- A same-day source-candidates audit now freezes the allowed source order for
  the bounded Zoom half too:
  `refs/conformance/olmradialblur_zoom_source_candidates_audit_20260701.md`
  keeps the next implementation suspicion order at
  `RenderZoom8 polar population / preserved-validity capture` first,
  `alpha accumulation / denominator state` second, and final inverse-sample /
  writeback only if a later Windows typed witness explicitly contradicts the
  current caller-collapse reading.
- The current Mac source still uses one blurred polar alpha plane in the outer
  inverse-sampling path, so it does not yet model the AEX caller-side
  `+0xf252 -> +0xf250 -> +0xe.alpha` split that the Windows follow-up now asks
  for directly.
- Mac AE now also has a narrow local witness surface for this lane:
  `refs/conformance/olmradialblur_mac_debug_hook_20260701.md`. The plug-in can
  dump `sample_rgba`, `sample_u8`, `validity_alpha`, `brightness_gain`,
  pre-normalized `accum_rgba`, pre-gain `normalized_rgba`, and four-cell
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
- A same-row source audit now turns that into a source-structure fact rather
  than just a visual hunch:
  `refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.md`.
  For the active case, the current Mac branch uses `row_length=3` and only
  same-radius-row angular taps for each blurred witness cell. The live witness
  rows therefore rule out one more class of Mac-side fixes: the missing bright
  lobe cannot come from those exact direct same-row source cells plus a later
  writeback tweak.
- A new machine audit now consolidates that local boundary:
  `refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.md`
  freezes that propagated-validity remains inert, the direct same-row source
  cells at `(1614,6)` are all black, the dominant local positive source-polar
  family sits one row above at row `843`, and the tested row-coupled
  surrogates still keep the bright-lobe count at `0` versus Windows `17`.
- A support-envelope follow-up then makes the branch limit more concrete:
  `refs/conformance/olmradialblur_tiny_rotation_support_envelope_20260701.md`
  shows that some nearby outputs can directly see that row-843 bright family,
  but the active witness `(1614,6)` cannot because its bilinear support stays
  on rows `844/845`. So the row-843 cluster is a real local clue, but not one
  the current same-row branch can directly write into the witness.
- A same-day source-candidates audit now freezes the allowed source order too:
  `refs/conformance/olmradialblur_tiny_rotation_source_candidates_audit_20260701.md`
  keeps the next implementation suspicion order at
  `RenderRotation8 polar population / preserved-validity capture` first,
  `scatter/substitute-path ownership` second, and final inverse-sample/writeback
  only if a later Windows typed witness explicitly contradicts the current
  upstream reading.
- A bounded CLI offset sweep now rejects the simplest "global grid is just a
  little shifted" version of that theory. Quarter/half-step angular offsets
  and quarter/half-pixel radial offsets all worsen `case_0010`; the current
  zero-offset grid remains best. Treat the remaining branch as contribution
  ownership / neighbor geometry, not a single uniform angular/radial offset.

### Practical next Windows ask

- Target only `case_0010 (1614,6)`.
- Do not spend the next round rediscovering the final white byte or the same
  near-black closest inverse-sampler return.
- The next successful return must isolate either:
  - the substitute/fallback branch that promotes the bright lobe, or
  - the exact neighboring/source-population path that should have filled that
    lobe before final inverse sampling.
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

- Answered package:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_hotspot_compose_writeback_witness_20260701.zip`
- Return summary:
  `refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.md`
- Consolidated audit:
  `refs/conformance/olmkirakira_hotspot_lane_audit_20260701.md`
- Provenance split audit:
  `refs/conformance/olmkirakira_reference_provenance_audit_20260701.md`
- Source-candidates audit:
  `refs/conformance/olmkirakira_source_candidates_audit_20260701.md`
- Current Mac evidence:
  - `refs/conformance/olmkirakira_pending_compose_proof_20260629.md` (historical pre-hotspot contract)
  - `refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.md`
  - `refs/conformance/olmkirakira_hotspot_local_compose_diagnostic_20260701.md`
  - `refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md`
  - `notes/IR_OLMKiraKira.md`

### Current reading

- The broad upstream lanes are already grounded enough to leave alone:
  - BT.709 luma seed
  - ray-helper staging
  - `FUN_18114fd90` glow normalization / opacity path
- The old reading was: the hotspot at `(934,118)` was narrower than a global
  gain/compose retune and needed an internal witness. Keep that only as
  historical context now.
- The 2026-07-01 return answered that witness one step further than before:
  at `(934,118)`, the traced Windows hotspot now agrees with the current Mac
  witness for glow-after-opacity, composed float, pre-writeback float, and the
  sampled RGBA8 value `144`.
- That means the hotspot is no longer an acceptable compose/quantization tuning
  lane from this evidence alone, because the canonical Windows reference PNG
  still says `131`.
- The new provenance audit freezes one more practical boundary:
  the archived BT.709 candidate PNG still says `145`, while the current traced
  hotspot and current Mac compose-boundary witness both say `144`. So this is
  not one monolithic "compose output is wrong" lane.
- A matching contract audit now fixes what later evidence is allowed to prove:
  `refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.md`
  keeps this lane at `awaiting-same-run-export-or-witness-placement-proof`
  until a current-AEX export or explicit witness-placement/endgame-control
  artifact lands, then classifies it directly against the three known hotspot
  classes (`131`, `144`, `145`) before any source movement.
- A new source-candidates audit now freezes the implementation order too:
  `refs/conformance/olmkirakira_source_candidates_audit_20260701.md`
  makes the non-source gate explicit first, keeps `RenderTyped(...)` screen
  compose as the first in-source reopen point only if a same-run export
  contradiction appears, keeps `AddColoredUnion(...)` second-order only, and
  splits highlight/ramp UI coverage into a separate schema/endgame lane.
- So the live lane has shifted from "find the compose math bug" to
  "validate reference/export provenance or witness placement, and leave broad
  KiraKira algorithm changes parked."

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

### Mac code sites that may change only if a later provenance check reopens the lane

1. Hotspot-local merge/compose path:
   - `Render8(...)` final compose block where `out.r/g/b` are built from
     `src` and `glow`
   - same file: `mac/OLMKiraKira/OLMKiraKira.cpp`
2. Only if Windows shows a final mismatch after matching compose float:
   - the final quantization / clamp boundary immediately before byte store
   - same file

### Decision gate

The return now lands in the fourth branch:

- `glow_rgba_float` matches the Mac witness
- `composed_rgba_float` matches the Mac witness
- `pre_writeback_rgba_float` matches the Mac witness
- sampled `final_writeback_or_png_rgba` also matches the Mac witness at `144`
- while the canonical Windows reference PNG remains `131`

So the correct next move is the one that was previously only hypothetical:

- reclassify this residual as reference/export or witness-placement drift
- do not reopen merge-mode-1 compose or final quantization from this witness

### Explicit non-goals after the witness

- No broad luma retuning
- No boxFilter / warp / ray-helper changes
- No global compose-scale changes
- No hotspot fix inferred from PNG-only tuning

## 5. OLMDirectionalBlur source-candidates freeze

- Current Mac evidence:
  - `refs/conformance/olmdirectionalblur_pending_witness_proof_20260629.md`
  - `refs/conformance/olmdirectionalblur_angle0_endpoint_constraint_20260630.md`
  - `refs/conformance/olmdirectionalblur_hook_anchor_audit_20260701.md`
  - `refs/conformance/olmdirectionalblur_source_candidates_audit_20260701.md`
  - `refs/reports/olmdirectionalblur_scatter_ownership_20260629.md`
  - `refs/reports/olmdirectionalblur_algorithm_presets_20260629.md`
  - `notes/IR_OLMDirectionalBlur.md`

### Current reading

- This is not a live send-target lane right now; it is a Mac-side freeze of
  what should stop consuming time.
- `rotated-aex-full-choreo` stays the structural base because it preserves the
  confirmed A/B choreography and is the right place to land later witness-led
  patches.
- The new 2026-07-01 audit now freezes four families as non-promotable global
  fixes:
  - `rowdriver_prepass_and_alpha_fade_gather`
  - `source_driven_scatter`
  - the combined `exact-rowdriver` bundle
  - measurement scaffolds `direct` / `rotated-front-strength`
- Operationally, DirectionalBlur is now reduced to two surviving proof lanes
  only:
  - `angle0-rowdriver-valid-alpha`
  - `diagonal-rotate-validity`
- A dedicated hook-anchor audit now freezes those two live families in one
  stable note:
  `refs/conformance/olmdirectionalblur_hook_anchor_audit_20260701.md`.
  It pins angle-0 to `(494,169)` and the strip endpoint `(579,169)` plus the
  helper-local leftward-only endpoint constraint, and pins the diagonal lane to
  `(507,367)` with signed-red companion witnesses. So the next acceptable
  Windows return is no longer "DirectionalBlur runtime values somewhere"; it is
  one that proves one of those two bounded hook families with typed values.
- So if we touch DirectionalBlur again before new typed witness values arrive,
  it should be to improve evidence packaging or witness interpretation, not to
  retune broad PNG-facing behavior.

### Decision gate

- If a future Windows return proves one lane upstream of final writeback:
  - patch only that lane on top of `rotated-aex-full-choreo`
- If a return still lacks typed module-local values:
  - keep DirectionalBlur parked and do not reopen prepass/scatter/direct tuning

### Explicit non-goals until typed witnesses land

- No direct/front-strength promotion
- No broad scatter ownership retune
- No prepass/global rowdriver rewrite from PNG means
- No mixing the angle-0 and diagonal families into one generic explanation

## Operational bottom line

The remaining live Windows wait is not "more PNGs".

They are the narrowest remaining proofs for:

1. whether DistanceGradation `case_0023` is a stricter Constant helper staging
   rule or an unexpected compose-side branch
2. whether RadialBlur Zoom differs in caller-collapse state or only in the
   final inverse-sample denominator, and whether tiny Rotation loses a bright
   contribution before or during the final sample
3. whether KiraKira's remaining discrepancy is now in reference/export
   provenance or witness placement rather than in the traced hotspot math

Meanwhile, OLMBlur `case_0006` has crossed from "needs runtime witness" into
"needs provenance/export explanation". Mac-side work there should stay on
comparison quality and reference auditing rather than broad implementation
churn.
