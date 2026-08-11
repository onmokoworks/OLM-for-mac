# OLMSmoother v1 retained case01 PF8 owner and host boundary

The retained Windows Software PF8 case01 exposed two independent boundaries.
The final unexplained production arithmetic was owned by the natural
`MainInterpKernel8` call at center `(288,539)`, direction `1`. Its negative
even Y delta entered a decompiler-style sign correction containing signed
overflow. Replacing that PF8 expression with the equivalent defined signed
remainder (`% 2`) makes the four affected raw ARGB pixels byte-exact against a
direct call to the pinned Windows AEX (`6206f601...35fe82`).

The scalar curve evaluators and `AlphaBlend8` also preserve each Windows
`SUBSS`/`MULSS`/`ADDSS`/`DIVSS` binary32 rounding point, preventing arm64 FMA
contraction from changing integer truncation at sparse pixels.

The later actual-AEX-backed PF8 `ColorCompare8` correction invalidated the old
claim that the entire retained PNG residual is explained by one host model.
With current production, 101 decoded pixels differ: the former model reproduces
98 alpha-254 pixels, while three opaque pixels remain unexplained. Those three
pixels cannot be attributed to a premultiply/unpremultiply conversion.

The June 29 retained manifest records AE 26.2x49, Software rendering, effect
and parameter readback, and the decoded PNG files. It does **not** bind the
loaded AEX SHA-256, input alpha interpretation, output premultiply conversion,
or project working-space state. The PNG files contain no embedded metadata that
closes those gaps. Consequently this fixture is retained as an unresolved AE
PNG observation, not an exact plug-in or host-adapter gate. No production
workaround is admitted.

The executable regression is fail-closed in two independent lanes: the four
isolated owner pixels must remain actual-AEX exact, while the host boundary must
remain explicitly non-exact until stronger capture provenance exists. It also
pins the current 101/98/3 observation so further drift cannot pass unnoticed.

Evidence and executable regression:

- `refs/conformance/olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.json`
- `tools/emulation/test_olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.py`

Canonical PF8 case0001, retained Color-Key case05, and the newer exported-AEX
colored fractional-alpha family provide the arithmetic evidence. PF16, native
PF32, and AE-host/export claims are not expanded by this retained fixture.
