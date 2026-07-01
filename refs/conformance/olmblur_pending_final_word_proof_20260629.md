# OLMBlur Pending Final-Word Proof

- Runtime package context: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/runtime_trace_packages/olm_runtime_trace_olmblur_case0006_helper_prestore_witness_20260630.zip`
- Latest runtime summary: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/runtime_trace_summary_olmblur_repeat_threshold_20260629_235638.json`

## Decision Boundary

Decide whether the remaining OLMBlur residuals come from slightly different pre-store floats/helper ordering at the two sign-mixed non-Legacy witnesses, or from a true last-step writer rule mismatch that would justify changing the non-Legacy 16bpc writer.

## Why The Live Windows Request Still Matters

- The latest imported Windows case_0006 pre-writeback fact is still the older full-comp output-address witness at (498,940). It proves the non-Legacy lane already diverges before the final byte store, but it does not answer the current normalized 16bpc current-word witnesses at (314,14) and (29,71).
- Older imported Windows case_0006 witness: `[498, 940]`
- Current live request witnesses: `[[314, 14], [29, 71]]`
- Practical consequence: Treat the 2026-06-19 Windows trace as proof context only. The live `olmblur_case0006_helper_prestore_witness_20260630` package is still required because only those two current-word witnesses can decide whether the remaining sign-mixed family is already split in helper/pre-store state.

## Why A Global Writer Swap Is Still Forbidden

- The current Mac source uses `nearbyintf(v)` for non-legacy 16bpc store16, while Windows standard 16bpc asm is `+0.5 -> helper -> CVTTSS2SI -> word store`.
- This is a real source-vs-asm contract mismatch at the writer boundary.
- But the current 16bpc residual family is sign-mixed one-word across all non-legacy cases, so the evidence still does not support a blind global `nearbyintf -> floorf(v + 0.5f)` swap without proving pre-writeback/helper state.
- Legacy already matches the add-half family in source, so `case_0007` remains a separate border/seed/all-same investigation rather than proof for the non-legacy store path.

## Witness Families

### olmblur__case_0006

- Family: `nonlegacy_sign_mixed_one_word`
- Meaning: Sign-mixed one-word family; this already argues against a blind global rounding-direction swap.
- Latest Windows runtime note: `{'summary': '2026-06-19 Windows cdb full-comp output-address probe hit the exact witness pixel. The final write site carried esi=498, r12d=940, r13d=780, r15d=0x7c8, pre-writeback RGB bits [43397fff,3da251e1,3da251e1], and destination bytes ff b9 00 00. This narrows case_0006 to the last-float / helper / cvttss2si path rather than a coordinate-remap issue.', 'windows_pre_writeback_rgb_hex': ['0x1.72fffe0000000p+7', '0x1.44a3c20000000p-4', '0x1.44a3c20000000p-4'], 'windows_final_rgba': [185, 0, 0, 255], 'current_mac_cli_pre_writeback_rgb_hex': ['0x1.73p+7', '0x1.44a3c6p-4', '0x1.44a3c6p-4'], 'current_mac_cli_candidate_rgba': [186, 0, 0, 255]}`
- Witness: `{'xy': [314, 14], 'mac_raw': 1100.5, 'mac_stored_word': 1100, 'windows_png': 2201, 'mac_png': 2199, 'inference': 'Windows would need internal word 1101 at this witness.'}`
- Witness: `{'xy': [29, 71], 'mac_raw': 363.5, 'mac_stored_word': 364, 'windows_png': 725, 'mac_png': 727, 'inference': 'Windows would need internal word 363 at this witness.'}`

### olmblur__case_0007

- Family: `legacy_last_pixel_half_step`
- Meaning: Legacy border/all-same structural blocker is retired; only a narrow half-step family remained, and the 16bpc witness is now directly grounded.
- Latest Windows runtime note: `{'summary': '2026-06-19 Windows cdb probes proved that Legacy case_0007 uses the later OLMBlur+0x7FDF writeback family, not the non-legacy OLMBlur+0x4481 family. First hit at +0x7FDF was exactly (0,0) with esi=0, r12d=0, r13d=780, r15d=0 and destination base rbx=...0100. Full-comp output-address data breakpoints then hit (488,941) and (488,942) at the same +0x7FDF family with esi=488, r12d=941/942, r15d=0x7a0 and final stored byte 0xfb/251.', 'windows_writeback_family': 'OLMBlur+0x7FDF', 'windows_first_halfstep_xy': [0, 0], 'windows_pre_writeback_rgb_hex': ['0x0p+0', '0x0p+0', '0x1.8d84660000000p+0'], 'current_mac_cli_pre_writeback_rgb_hex': ['0x1.7e74ccp+0', '0x1.7e74ccp+0', '0x1.7e74ccp+0']}`
- Witness: `{'xy': [345, 672], 'mac_raw_blue': 12544.5, 'mac_stored_word_blue': 12545, 'windows_pre_store_blue': 12544.498046875, 'windows_internal_word_blue': 12544, 'windows_png_blue': 97, 'mac_png_blue': 98, 'inference': 'Resolved as pre-store float delta before truncation, not an open writer-rule question.'}`
- Witness: `{'xy': [488, 941], 'context': 'old 8bpc normalized witness', 'mac_raw_red': 250.499985, 'windows_png_red': 251, 'mac_png_red': 250, 'inference': 'This is already a pure half-step boundary split.'}`

## Actionable Return Criteria

- It records Windows pre-store float(s) at the two listed case_0006 witnesses, not only final PNG bytes.
- It records any helper/clamp value between add-half and final CVTTSS2SI/truncate on the non-Legacy path.
- It can distinguish 'same writer rule but smaller pre-store float' from 'different writer/helper rule'.

## Not Actionable

- It only reports final PNG values or final RGBA16 words.
- It revisits the retired old Legacy (0,0) spill or reopens the already-grounded 16bpc Legacy (345,672) witness instead of answering case_0006.
- It broadens back into generic blur-kernel tuning rather than the narrow writer/helper boundary.

## Recommended Next Windows Probe

- 16bpc non-Legacy case_0006 at (314,14) and (29,71): capture the last helper/upstream value, pre-store float, and final internal word.
- Do not spend this package on the already-grounded 16bpc Legacy (345,672) point unless it is only being used as a debugger control sample.
- Only revisit old normalized 8bpc (488,941) if the same debugger setup can return it almost for free after answering the two case_0006 witnesses.
