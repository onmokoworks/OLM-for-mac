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

After those production fixes, 98 decoded PNG pixels still differ from the
retained Windows AE file. Every one has production alpha `254`, and every one
is reproduced exactly by rounding the RGB premultiply followed by truncating
the unpremultiply. This is recorded only as a Windows AE PNG host-boundary
model; it is not claimed as plug-in arithmetic and is not emulated inside the
plug-in.

Evidence and executable regression:

- `refs/conformance/olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.json`
- `tools/emulation/test_olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.py`

The full Smoother v1 fixed-fixture lane passes 17 tests. Canonical PF8 case0001
and retained Color-Key case05 remain exact. PF16 and native PF32 claims are not
expanded by this result.
