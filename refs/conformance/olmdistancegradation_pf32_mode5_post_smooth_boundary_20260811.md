# OLMDistanceGradation PF32 Mode5 post-smooth boundary

Status: **PARTIAL_SUCCESS_IPP_FIELD_PRODUCER_NUMERIC_REDUCTION_OPEN**.

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

No expected-word or expected-index correction is admitted. Linear, Sphere, and
Power Mode5, background off/on, remain fail-closed until the exact x86
OpenCV/IPP numeric mechanism is reproduced. The bounded matrix remains 58 exact
and 6 fail-closed.

The focused pointee-memory trace capability needed for this investigation is
separately committed and pushed in AEXCompat as `37bdeae9` on
`codex/issue851-smart-primary-checkout`; it is not mixed into the OLM repository.
