# OLMBlur Closeout Gate Audit

- Plug-in: `OLMBlur`
- Closeout status: `provenance-first-case0006-and-split-case0007`
- Decision: `do-not-reopen-source-without-two-specific-external-proofs`
- Reason: The non-Legacy 16bpc lane `case_0006` is still a provenance/export gate because no same-run Windows current-AEX export is imported, while Legacy `case_0007` is no longer one unresolved family: its 16bpc witness is already closed as a Windows-side pre-store float delta and only the old normalized 8bpc half-step witness remains open.
- Next allowed action: Preserve current source behavior. Advance only by importing a same-run Windows current-AEX export for `case_0006`, or by capturing the old normalized 8bpc Windows pre-store float/helper boundary at `(488,941)` for `case_0007`.

## Lanes

### case_0006_nonlegacy_16bpc

- Status: `awaiting-windows-current-aex-export`
- Reason: No same-run Windows current-AEX export has been imported yet, so the contract remains a provenance gate rather than a source-change signal.
- Next step: Import the Windows current-AEX export PNG from the same run class as the witness capture and rerun this audit.
- Required external evidence:
  - exported PNG file
  - AE version
  - project renderer metadata
  - bit depth metadata
  - parameter/property snapshot for the same slice
  - statement whether the PNG came from the same current-AEX build/path and same render class as the witness run
- Key points:
  - `{'xy': [314, 14], 'reason': 'lane-defining witness A', 'canonical_ref': [2201, 2201, 2201, 65535], 'mac_single_export': [2199, 2199, 2199, 65535], 'mac_batch_export': [2201, 2201, 2201, 65535]}`
  - `{'xy': [29, 71], 'reason': 'lane-defining witness B', 'canonical_ref': [725, 725, 725, 65535], 'mac_single_export': [727, 727, 727, 65535], 'mac_batch_export': [727, 727, 727, 65535]}`

### case_0007_legacy_16bpc

- Status: `resolved-as-pre-store-float-delta`
- Reason: Windows pre-store float is already grounded at `12544.498046875 -> 12544`, so this lane is closed as a pre-store float delta rather than an open writer-rule mystery.
- Next step: Keep this lane closed unless contradictory same-run witness evidence appears.
- Key points:
  - `{'xy': [345, 672], 'windows_pre_store': 12544.498046875, 'windows_final_word': {'decimal': 12544, 'hex': '0x3100'}}`

### case_0007_legacy_8bpc_old_normalized

- Status: `still-needs-windows-pre-store-float`
- Reason: The remaining old normalized 8bpc witness stays just below the half-step on the Mac side and has no in-tree Windows pre-store float, so it cannot justify a writer or helper rewrite yet.
- Next step: Keep case_0007 split by bit depth: preserve the 16bpc witness as resolved, and only ask Windows for the old normalized 8bpc pre-store float/helper boundary at `(488,941)` if this family needs to move further.
- Key points:
  - `{'xy': [488, 941], 'reference_rgba': [251, 0, 0, 255], 'candidate_rgba': [250, 0, 0, 255], 'trace': 'OLMBLUR_TRACE x=488 y=941 rgb=(250.499985,0.00161030458,0.00161030458) rgb_hex=(0x1.f4fffep+7,0x1.a621b6p-10,0x1.a621b6p-10) floor05=(250,0,0) nearby=(250,0,0) legacy=1 repeat=10'}`

## Source Reopen Order

1. If no same-run Windows current-AEX export/witness contradicts case_0006 provenance -> Do not patch OLMBlur source for case_0006; keep the lane in provenance/export classification.
2. If Windows shows case_0006 helper/pre-store already match but final stored words differ -> Reopen only the non-Legacy 16bpc writer boundary (`round_blur_value` / `store16`).
3. If Windows shows case_0006 mismatch already exists before final store -> Only then reopen non-Legacy helper accumulation in `blur_1d_horizontal` / `blur_1d_vertical`.
4. If case_0007 advances again -> Keep Legacy split by bit depth: 16bpc remains closed, only the old normalized 8bpc witness may reopen carry-prev/helper logic.

## Forbidden Actions

- Do not promote a blind global `nearbyint -> floor05` writer swap from the current OLMBlur evidence.
- Do not mix case_0006 provenance/export uncertainty with the resolved 16bpc Legacy case_0007 witness.
- Do not reopen the retired Legacy `(0,0)` blocker or broad kernel tuning from these lanes.
- Do not collapse the unresolved OLMBlur work back into one generic 16bpc writer problem.
- Do not spend the next Windows round on the already-closed 16bpc Legacy witness unless it is only a debugger control sample.

## Supporting Evidence

- case_0006 provenance status: `current-aex-export-missing`
- case_0006 point pattern: `{'counts': {'mac_single_matches_canonical': 1, 'mac_batch_matches_canonical': 2, 'mac_single_matches_mac_batch': 1, 'all_split': 0}, 'witness_pattern': {'29,71': ['mac_single_matches_mac_batch'], '314,14': ['mac_batch_matches_canonical']}, 'reading': 'No single export artifact dominates all sampled points: batch and single-case exports each match canonical at some points and disagree at others, while the original witness pair also splits by point.'}`
- case_0007 decision status: `16bpc-resolved-8bpc-still-open-prestore-family`
- source-candidates status: `{'case0006_status': 'current-aex-export-missing', 'case0007_status': '16bpc-resolved-8bpc-still-open-prestore-family', 'case0006_recommended_action': 'Keep OLMBlur case_0006 frozen on the Mac side and request only the precise same-run Windows current-AEX export artifact if this lane must advance.', 'case0007_next_allowed_action': 'Keep case_0007 split by bit depth: preserve the 16bpc witness as resolved, and only ask Windows for the old normalized 8bpc pre-store float/helper boundary at `(488,941)` if this family needs to move further.'}`

