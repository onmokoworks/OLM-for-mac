# OLMBlur Source-Candidates Audit

- Source: `mac/OLMBlur/OLMBlur.cpp`
- case_0006 status: `current-aex-export-missing`
- case_0007 status: `16bpc-resolved-8bpc-still-open-prestore-family`

## Non-Source Gates

- `case_0006_nonlegacy_16bpc`
  - Required before source patch: Same-run Windows current-AEX export or witness that contradicts the current provenance/export reading.
  - Why: No same-run Windows current-AEX exported PNG is present, so the lane remains a provenance/export question rather than a reopened implementation bug.
- `case_0007_legacy_8bpc_old_normalized`
  - Required before source patch: Windows pre-store float/helper boundary at `(488,941)`.
  - Why: The surviving Legacy case_0007 family is no longer one undifferentiated residual. The normalized 16bpc witness at `(345,672)` is already closed as a pre-store float delta: Mac lands at exactly `12544.5`, while Windows runtime witness says `12544.498046875 -> 12544`. The old normalized 8bpc witness at `(488,941)` remains below the half-step on the Mac side (`250.499985`) and is not solved by either local writer rule, so that companion witness still needs a Windows pre-store float rather than a blind writer rewrite.

## Source Candidates

| Rank | Site | Function | Line | Why live | Allowed change shape |
| --- | --- | --- | ---: | --- | --- |
| 1 | `store16_nonlegacy_writer_boundary` | `round_blur_value / store16` | `451` | This is only the first source reopen point if a future same-run Windows export or witness explicitly contradicts the current case_0006 provenance reading and says helper/pre-store match while final stored words differ. | non-Legacy 16bpc writer-only contradiction only |
| 2 | `nonlegacy_helper_accumulation` | `blur_1d_horizontal / blur_1d_vertical` | `113` | Reopen the non-Legacy helpers only if a future Windows witness disproves the current provenance freeze and shows the decisive mismatch already exists before the 16bpc writer boundary. | case_0006 helper-local contradiction only; no broad kernel retune |
| 3 | `legacy_carry_prev_horizontal_vertical` | `legacy_blur_1d_horizontal / legacy_blur_1d_vertical` | `254` | The old normalized 8bpc case_0007 witness is still open, but only as a separate pre-store-float lane. The normalized 16bpc witness is already resolved as a Windows-side pre-store float delta. | old normalized 8bpc witness only; keep 16bpc Legacy witness closed |

## Decision Ladder

1. If no same-run Windows current-AEX export/witness contradicts case_0006 provenance -> Do not patch OLMBlur source for case_0006; keep the lane in provenance/export classification.
2. If Windows shows case_0006 helper/pre-store already match but final stored words differ -> Reopen only the non-Legacy 16bpc writer boundary (`round_blur_value` / `store16`).
3. If Windows shows case_0006 mismatch already exists before final store -> Only then reopen non-Legacy helper accumulation in `blur_1d_horizontal` / `blur_1d_vertical`.
4. If case_0007 advances again -> Keep Legacy split by bit depth: 16bpc remains closed, only the old normalized 8bpc witness may reopen carry-prev/helper logic.

## Forbidden Actions

- Do not promote a blind global `nearbyint -> floor05` writer swap from the current OLMBlur evidence.
- Do not mix case_0006 provenance/export uncertainty with the resolved 16bpc Legacy case_0007 witness.
- Do not reopen the retired Legacy `(0,0)` blocker or broad kernel tuning from these lanes.

