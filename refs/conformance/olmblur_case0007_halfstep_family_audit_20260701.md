# OLMBlur case_0007 Half-Step Family Audit

- Family: `legacy_last_pixel_half_step`
- Decision: `16bpc-resolved-8bpc-still-open-prestore-family`
- Reason: The surviving Legacy case_0007 family is no longer one undifferentiated residual. The normalized 16bpc witness at `(345,672)` is already closed as a pre-store float delta: Mac lands at exactly `12544.5`, while Windows runtime witness says `12544.498046875 -> 12544`. The old normalized 8bpc witness at `(488,941)` remains below the half-step on the Mac side (`250.499985`) and is not solved by either local writer rule, so that companion witness still needs a Windows pre-store float rather than a blind writer rewrite.
- Forbidden action: Do not reopen the retired Legacy `(0,0)` blocker, do not treat case_0007 as proof for a global writer-rule swap, and do not mix the resolved 16bpc witness with the still-open 8bpc witness.
- Next allowed action: Keep case_0007 split by bit depth: preserve the 16bpc witness as resolved, and only ask Windows for the old normalized 8bpc pre-store float/helper boundary at `(488,941)` if this family needs to move further.

## 16bpc Witness

- XY: `(345, 672)`
- Mac reference RGBA: `[1247, 0, 25087, 65535]`
- Mac candidate RGBA: `[1247, 0, 25089, 65535]`
- Mac raw/store note: `['624.429565', '1.26167242e-05', '12544.5']` -> stored `['624', '0', '12545']`
- Windows pre-store float: `12544.498046875`
- Windows final word: `{'decimal': 12544, 'hex': '0x3100'}`
- Status: `resolved-as-pre-store-float-delta`

## 8bpc Old Normalized Witness Pair

- Low witness XY: `(488, 941)`
- Low witness reference/candidate: `[251, 0, 0, 255]` / `[250, 0, 0, 255]`
- Low witness trace: `OLMBLUR_TRACE x=488 y=941 rgb=(250.499985,0.00161030458,0.00161030458) rgb_hex=(0x1.f4fffep+7,0x1.a621b6p-10,0x1.a621b6p-10) floor05=(250,0,0) nearby=(250,0,0) legacy=1 repeat=10`
- High control XY: `(488, 942)`
- High control reference/candidate: `[251, 0, 0, 255]` / `[251, 0, 0, 255]`
- High control trace: `OLMBLUR_TRACE x=488 y=942 rgb=(250.500015,0.00162608409,0.00162608409) rgb_hex=(0x1.f50002p+7,0x1.aa44a8p-10,0x1.aa44a8p-10) floor05=(251,0,0) nearby=(251,0,0) legacy=1 repeat=10`
- Status: `still-needs-windows-pre-store-float`

## Reading

- The 16bpc Legacy witness is already resolved as a pre-store float delta before truncation, not a writer-rule mystery.
- The 8bpc old normalized witness is a companion half-step family, but it is still open because the Mac-side raw value is already below 250.5 and no Windows pre-store float is recorded in-tree yet.
- So `case_0007` should stay split by bit depth in future decisions.

