# OLM Proof Contract Ledger

Updated: 2026-07-01

This note is the thin contract layer between the conformance ledger and a new
Windows runtime-trace request. The goal is to say, before sending a request:

- which lane is active
- which exact witness would advance it
- which implementation moves are still forbidden
- what counts as actionable vs non-actionable on return

Do not use this file to restate whole IR notes. Keep it narrow and operational.

## Active contracts

| Lane | Target witness | Wanted proof | Forbidden action until proof lands | Actionable return must include |
| --- | --- | --- | --- | --- |
| `OLMBlur 16bpc case_0006 provenance` | `case_0006` current-AEX export vs canonical 16bpc ref | Whether the remaining sign-mixed one-word residual is reference/export provenance rather than writer/helper behavior; exact missing artifact is frozen in `refs/conformance/olmblur_case0006_current_aex_export_contract_20260701.md` and classified mechanically by `refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md` | Global 16bpc writer swap, helper surgery, broad rounding retune | Reference provenance facts: exported PNG source, canonical reference source, bit depth, whether the compared files are truly the same render class, and the four representative 16-bit witness points in the export contract |
| `OLMBlur 16bpc case_0007 Legacy` | `case_0007` Legacy witness family | Legacy border/all-same state and remaining 1px family | Reopen non-Legacy math, merge `case_0006` and `case_0007` into one fix | Exact Legacy witness path or equivalent binary/runtime evidence naming the remaining border/all-same rule |
| `OLMRadialBlur Zoom caller-collapse` | `case_0009 (6,0)` | Caller-side polar alpha/sample collapse through `sampler -> +0xf252 -> +0xf250 -> +0xe -> final byte`; see `refs/conformance/olmradialblur_outer_witness_contract_20260701.md` for the accepted chain | Final-byte tuning, validity-plane retune, direct zero-on-invalid promotion | Target case, XY, exact caller chain hit, typed values at each requested stage, and the denominator or equivalent normalization state behind `254` vs local `255`. If the shared package answers only this lane, classify overall return per `refs/conformance/olmradialblur_outer_return_acceptance_20260701.md`. |
| `OLMRadialBlur tiny Rotation source population` | `case_0010 (1614,6)` | Upstream polar RGB / substitute-path / neighboring-row contribution ownership; see `refs/conformance/olmradialblur_tiny_rotation_followup_contract_20260701.md` for the exact typed chain | Validity-alpha fixes, propagated-validity promotion, broad row-coupling promotion | Target case, XY, exact source-population or substitute-path values for the requested top-border witness plus the typed `+0xf252/+0xf250/+0xe` chain. Classify return quality per `refs/conformance/olmradialblur_tiny_rotation_return_acceptance_20260701.md`, not the older shared outer acceptance note. |
| `OLMRadialBlur Inner per-cell` | `rb_inner_only_strength_large`, `rb_inner_quality_1` | Typed `FUN_180001c90` span/row/scatter/writeback facts for one low-span and one strong-quality representative | Global `loop-minus-one`, `circular-wrap`, `table-span-minus-one` promotion | Exact representative family, effective span, row/column, accumulation/denominator or explicit fault classification |
| `OLMDistanceGradation Constant ownership` | `case_0023` `Both + Outside Threshold=0` | Upstream helper-staging / threshold ownership before compose-writeback; active split is now the `inside=1.0/outside=0.0` edge family (`65px`) plus the `35.014 -> 36.013 -> 37.013` threshold family (`8px`) documented in `refs/conformance/olmdistancegradation_case0023_witness_contract_20260701.md` | Outside-side equality tweak, broad Constant rerun, Layer/no-bg unpremultiply retry | Target case, one of those two witness families, exact helper/threshold staging values, or explicit “not isolated” reason. If the current pending package answers only the edge family, classify it per `refs/conformance/olmdistancegradation_case0023_return_acceptance_20260701.md` rather than promoting a full-lane code change. |
| `OLMDistanceGradation case_0023 current-AEX export provenance` | `case_0023` same-run Windows Software export | Whether the packaged expected PNG is stale for part or all of the remaining `73px` residual; exact export contract is frozen in `refs/conformance/olmdistancegradation_case0023_current_aex_export_contract_20260702.md` | Reopen Constant helper/compose tuning from the packaged expected PNG alone | A current Windows Software export plus before-effects/source provenance for the same case, with the edge-family and threshold-family witness pixels preserved in the manifest/PNG output |
| `OLMDistanceGradation Layer/no-bg ownership` | `case_0012/0016` Layer/no-bg family | Source ownership before writeback in `render_mode=Layer && use_bg=0` | Broad unpremultiply toggles outside the proven path | Target case, field/world/source ownership values tied to the narrowed Layer/no-bg path |
| `OLMSmoother2 legacy producer path` | `0004 (1903,519)` and `0012 (91,841)` | Upstream producer selection from final writer anchor back to actual `c280/cce0` or alternate path | Global alpha/index/f270 fallback changes | Successful writer-anchor reconstruction to the producer path, or an exact failed breakpoint/watchpoint reason |
| `OLMKiraKira compose hotspot` | `(934,118)` | Merge-mode-1 compose / pre-writeback / final quantization boundary | Global gain, luma, boxFilter, ray-helper, or fd90 retune | Target hotspot, compose/pre-writeback values, and whether attenuation happens before compose, inside compose, or only at quantization |
| `OLMKiraKira hotspot provenance` | same-run export or witness-placement proof for `(934,118)` | Whether the canonical `131` reference or the traced `144` hotspot class is the final export class for the current lane; exact boundary is now frozen in `refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.md` | BT.709 retune, boxFilter/ray-helper retune, broad compose/final-quantization rewrite from the canonical mismatch alone | Same-run exported PNG source, canonical reference source, whether trace and export are the same render class, hotspot RGBA at `(934,118)`, and any witness-placement or endgame-control note if trace/export differ |

## Return vocabulary

Use one of these when a Windows return is imported:

- `answered`: the exact requested proof landed and can move implementation
- `answered_partial`: some requested structure landed, but the proof boundary is
  still incomplete
- `failed_breakpoint_watchpoint`: the planned stop did not resolve, but the
  failure reason itself is exact and useful
- `trace-too-sparse`: too little typed data to support a code move
- `not isolated`: the right area was hit, but the requested witness was not
  separated from neighboring state
- `non-actionable`: the return may be interesting historically, but should not
  drive the current lane

## Operating rule

Before sending a new request:

1. Add or update the lane row here.
2. Make sure the request asks for one proof boundary, not several.
3. Name at least one forbidden action explicitly.
4. Decide in advance which of the return vocabulary words should apply if the
   exact witness does not land.
