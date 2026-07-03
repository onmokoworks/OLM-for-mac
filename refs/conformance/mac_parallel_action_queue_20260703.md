# Mac Parallel Action Queue - 2026-07-03

This note captures the plugin lanes that can move forward on the Mac side
without waiting for a fresh Windows return. It is intentionally operational:
each lane names the exact next local action, the files to anchor on, and the
class of work that remains forbidden.

## 1. OLMRadialBlur tiny Rotation

- Lane:
  - `case_0010 (1614,6)` upstream ownership / bright-lobe reconstruction
- Why this is locally actionable:
  - the lane is already narrowed away from final byte packing and away from a
    simple validity-alpha theory
  - the live Windows ask is still pending, but local observation can keep the
    exact witness neighborhood and source/polar ownership boundaries stable
- Current anchors:
  - [notes/IR_OLMRadialBlur.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/IR_OLMRadialBlur.md)
  - [refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_patch_audit_20260630.md)
  - [refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_bright_lobe_search_20260630.md)
  - [refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.json)
  - [handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701](/Users/onmk/Documents/Projects/Personal/OLM%20as/handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0010_probe_20260701)
- Next allowed local action:
  - re-read the local witness neighborhood around the bright lobe and keep the
    source/polar/scatter ownership hypothesis narrow
- 2026-07-03 local refresh:
  - current source で same-row / source-polar / row-coupling / support-envelope /
    lane-audit / source-candidates を再生成し直しても、
    `neighboring-row contribution ownership or substitute/fallback branch`
    という stop line は変わらなかった
- Forbidden:
  - final byte tuning
  - promoting propagated validity alpha as a global fix
  - mixing `20260604` and `20260605` references by case number alone

## 2. OLMDistanceGradation case_0023

- Lane:
  - 16bpc Constant `Both + Outside Threshold=0`
  - threshold-family provenance split vs edge-family ownership split
- Why this is locally actionable:
  - the threshold triplet already has a strong provenance warning
  - the remaining live implementation suspicion is upstream ownership on the
    edge-family side, not a broad writeback question
- Current anchors:
  - [notes/IR_OLMDistanceGradation.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/IR_OLMDistanceGradation.md)
  - [refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.md)
  - [refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.md)
  - [refs/conformance/olmdistancegradation_case0023_threshold_return_acceptance_20260701.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmdistancegradation_case0023_threshold_return_acceptance_20260701.md)
  - [refs/reference_requests/olmdistancegradation_case0023_current_aex_recapture_20260702.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olmdistancegradation_case0023_current_aex_recapture_20260702.json)
- Witnesses that must stay separated:
  - threshold-family triplet:
    - `(414,393)`, `(415,393)`, `(416,393)`
  - edge-family witnesses:
    - `(1698,7)`, `(1699,7)`, `(1700,7)`
- Next allowed local action:
  - keep reports and candidate classification split into threshold-family
    provenance vs edge-family ownership
- 2026-07-03 local refresh:
  - source-candidates / threshold-family audit を current reports で再生成し、
    threshold-family が implementation bug lane ではなく provenance lane だと再確認した
- Forbidden:
  - broad PNG tuning
  - treating the packaged expected PNG as authoritative current Windows output
    for the threshold triplet

## 3. OLMColorKey 32bpc

- Lane:
  - bit-depth expansion only
- Current anchors:
  - [notes/BIT_DEPTH_REFERENCE_STRATEGY.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/BIT_DEPTH_REFERENCE_STRATEGY.md)
  - [refs/reference_requests/olm_bitdepth_32bpc_colorkey_probe_20260703.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_colorkey_probe_20260703.json)
  - [refs/reports/parallel_lane_report.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/parallel_lane_report.md)
- Next allowed local action:
  - keep status and intake/reporting ready so the Windows float-output return
    can be compared immediately
- 2026-07-03 share state:
  - `refs/reports/parallel_lane_report.md` は更新済みで、
    `olm_reference_request_32bpc_colorkey_probe_20260703.zip` は
    `/Volumes/onmk/olm_pr/new` に出ている
- Forbidden:
  - any 32bpc exact claim before the returned reference is imported and
    compared

## 4. OLMToonDilate 16bpc

- Lane:
  - bit-depth expansion only
- Current anchors:
  - [notes/BIT_DEPTH_REFERENCE_STRATEGY.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/notes/BIT_DEPTH_REFERENCE_STRATEGY.md)
  - [refs/reference_requests/olm_bitdepth_16bpc_toondilate_exact_20260703.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_16bpc_toondilate_exact_20260703.json)
  - [refs/reports/parallel_lane_report.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/parallel_lane_report.md)
- Next allowed local action:
  - keep request lifecycle / comparison entry points current so the return can
    be turned into a same-day compare
- Forbidden:
  - reopening the 8bpc two-pass dilation algorithm without new evidence

## 5. OLMKiraKira

- Lane:
  - provenance and host-context separation only
- Current anchors:
  - [refs/conformance/olmkirakira_live_hotspot_probe_20260703.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmkirakira_live_hotspot_probe_20260703.md)
  - [refs/conformance/olmkirakira_witness_path_split_20260703.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/olmkirakira_witness_path_split_20260703.md)
  - [handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260703_r3](/Users/onmk/Documents/Projects/Personal/OLM%20as/handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260703_r3)
- Next allowed local action:
  - keep 8bpc witness and 16bpc live-host lanes separated
- Forbidden:
  - hotspot-based retuning of compose/gain/luma/final quantization

## Windows-pending but Mac-stable queue

- Runtime queue report:
  - [refs/reports/pending_runtime_trace_packages.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/pending_runtime_trace_packages.md)
- Live share folder:
  - `/Volumes/onmk/olm_pr/new`
- Current first-send request:
  - [refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/runtime_trace_packages/olm_runtime_trace_radialblur_tiny_rotation_anchor_context_watch_followup_20260702.zip)

## Practical takeaway

When Windows is busy, the best Mac-only parallel work right now is:

1. keep `OLMRadialBlur tiny Rotation` tightly classified and avoid reopening
   final-byte theories
2. keep `OLMDistanceGradation case_0023` split into threshold-family provenance
   vs edge-family ownership
3. keep `OLMColorKey 32bpc` and `OLMToonDilate 16bpc` in ready-to-intake state
4. keep `OLMKiraKira` in provenance/host-context separation, not retuning
