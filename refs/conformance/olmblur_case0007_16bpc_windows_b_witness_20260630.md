# OLMBlur case_0007 16bpc Windows B Witness

- Date: `2026-06-30`
- Source zip:
  `/Volumes/onmk/olm_pr/new/olmblur_case0007_16bpc_345_672_b_witness_windows_20260630.zip`
- Target witness: `olmblur__case_0007`, `x=345`, `y=672`, blue channel

## Captured Windows Fact

- Runtime path: `FUN_180005f20`
- Writer branch: `16bpc rounded scalar loop, eax == 0x10 branch`
- `cvttss2si` site RVA: `0x6d1e`
- store site RVA: `0x6d22`
- break-after-store RVA: `0x6d26`
- Register coordinates at write:
  - `esi_x = 345`
  - `r12d_y = 672`
  - `r13d_width = 1920`
- Source float raw word for blue: `0x464401fe`
- Decoded Windows blue pre-store float: `12544.498046875`
- Final `cvttss2si` / stored word: `12544` (`0x3100`)

## Interpretation

- This directly resolves the surviving 16bpc Legacy half-step witness at
  `(345,672)` as a pre-store-float difference, not as a local writer-rule
  mystery.
- Current Mac-side witness at the same point is exactly `12544.5`, which under
  the current Legacy `floor(x + 0.5)` path becomes `12545`.
- Windows is slightly below the half-step (`12544.498046875`) and then
  truncates to `12544` through `cvttss2si`.
- So this witness no longer supports a blind writer rewrite. It supports the
  narrower reading already suggested by the local baseline: Windows and Mac are
  landing on different pre-store floats at this pixel.

## What This Closes

- The 16bpc Legacy witness `olmblur__case_0007 (345,672)` is no longer an
  open "writer rule or not?" question.
- The remaining OLMBlur final-word uncertainty is now concentrated in:
  - non-Legacy 16bpc `case_0006` sign-mixed witnesses `(314,14)` and `(29,71)`
  - old normalized 8bpc Legacy witness `(488,941)`

## Raw Return Summary

- `WITNESS_RESULT.json` reports:
  - `source_float_triplet_big_endian_decode.b = 12544.498046875`
  - `final_word.decimal = 12544`
  - interpretation:
    `Blue pre-store float 12544.498046875 is converted by cvttss2si to 12544 (0x3100), then stored to the 16bpc output B word at x=345,y=672.`
