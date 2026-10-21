# OLMDistanceGradation PF32 Mode5 post-smooth boundary

Status: **HISTORICAL_PARTIAL_SUCCESS_SUPERSEDED_BY_EXACT_IPP_ORDER_CLOSURE**.

2026-08-12 final supersession: direct `expf`, L/T/R/B sequential accumulation,
late spatial multiplication and explicit noncontracting float products
reproduce the captured IPP field exactly. Fixed17x11 PF32 Mode 5 non-Power is 6/6
public raw exact; its Power pair fails closed pending native UCRT evidence, and
the combined PF16/PF32 admission is 56 exact plus 8 Power rejects. The old portable
37-word/max-2-ULP result remains a counterfactual; no expected-word or
coordinate correction was admitted. See
`olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.{json,md}`.

2026-08-12 clarification: this historical document first separated the classic
identity wrapper from the exported PF32 IPP path. A later natural public Smart
trace proves the actual owner chain as command `0x18` → `FUN_181173d20` →
`FUN_181172a10` → iterateFloat/`FUN_181170c90` and captures the post-IPP
field hash
`7aaab7918d72d64fc2c426c7a52748409294bcab8c473bb5a55cbd4d19e037a6`.
That trace superseded any architecture-wide inference that PF32 Smart lacks an
actual owner; by itself it did not close the numeric residual. See
`olmdistancegradation_public_smart_owner_contract_20260812.{json,md}`.

The checked-in Windows AEX was executed through the existing PF32 whole-owner
probe with the exported 17x11 alpha fixture, Linear interpolation, background
off, Blur Mode 5, and Blur Size 1. The source and destination `IplImage` planes
at `FUN_1812864d0` entry/return contain 187 `float32` words (748 bytes).

- actual-AEX pre-`cvSmooth` SHA-256: `6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c`
- actual-AEX post-`cvSmooth` SHA-256: `6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c`
- changed words across that wrapper boundary: `0 / 187`
- the Mac `build_distance_field` pre-plane is byte-identical to the same hash

The direct whole-owner wrapper capture above belongs to the classic owner path.
A subsequent exported-render instruction census showed that the typed PF32 path
does not use that identity wrapper result as its final field world. It enters the
OpenCV 4.5.5 bilateral dispatcher at RVA `0x12ca750`, constructs the IPP
bilateral invoker whose virtual body is RVA `0x12c9430`, and calls the IPP
backend wrapper at RVA `0x1399760`. The alternative OpenCV implementation at
RVA `0x12cb510` is not reached by this fixture.

The final PF32 compose callback at RVA `0x1170c90` was also disassembled. For
opaque/no-background pixels its alpha path loads the field-world red value and
stores `source_alpha * field_red`; source alpha is exactly `1.0f` in the
residual set. Thus the first mismatch is already present in the IPP-produced
field world, before final compose. Comparing the actual exported alpha words
against the current portable bilateral candidate on the 124 opaque pixels
leaves 33 numeric residuals: 29
are one ULP lower in the AEX result, two are two ULP lower, and the two horizontal
endpoints are one ULP higher. Transparent pixels are cleared by compose and are
not part of this numeric class.

No expected-word or expected-index correction was admitted. Linear, Sphere,
and Power Mode5, background off/on, remained fail-closed at this historical
checkpoint; the exact mechanism and supersession are recorded above.

The focused pointee-memory trace capability needed for this investigation is
separately committed and pushed in AEXCompat as `37bdeae9` on
`codex/issue851-smart-primary-checkout`; it is not mixed into the OLM repository.
