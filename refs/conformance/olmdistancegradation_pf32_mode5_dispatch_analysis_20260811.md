# OLMDistanceGradation PF32 Blur Mode 5 dispatch analysis

Final supersession (2026-08-12): the natural trace below was used to reproduce
the IPP scalar arithmetic exactly: direct `expf(-0.5f*q)`, L/T/R/B sequential
accumulation, late `expf(-0.5f)` spatial multiplication, and explicit
noncontracting float products. Constant, Linear and Sphere Mode 5 cells are
public raw exact; the Power pair fails closed pending native Windows UCRT `powf`.
The fixed PF16/PF32 admission is 56 exact plus 8 PF32 Power rejects.
The historical investigation below remains as the grounded counterfactual and
localization record. See
`olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.{json,md}` and
`olmdistancegradation_pf32_mode5_universal_codegen_20260812.{json,md}`.

Historical follow-up (2026-08-12): the requested resident public-owner capture
now exists. A natural AEXCompat Smart sequence reaches public command `0x18`
and records the pre-field as
`6023adbb0e42b6b1269594e72c2f58f5caf3ce8ece80b68da2f06f384aea623c`,
the post-IPP field as
`7aaab7918d72d64fc2c426c7a52748409294bcab8c473bb5a55cbd4d19e037a6`,
and the final raw output as
`50934ac830542ca73fee4a11b924b746a0ae93f97f34b0d2868170bc371dd387`.
This superseded the final paragraph's proposed next probe but did not by itself
close the numeric conclusion. See
`olmdistancegradation_public_smart_owner_contract_20260812.{json,md}`.

The retained exported-owner matrix contains eight PF32 Mode 5 cells:
Constant/Linear/Sphere/Power × Background off/on on the fixed 17×11
transparent-island fixture.

The Constant pair is now raw-byte exact. Production reproduces the relevant
OpenCV 4.5.5 `CV_32FC1` bilateral semantics from input values: a 4096-bin
exponential LUT, radius-one cross neighbors, replicated borders, four-lane
fused interpolation/accumulation, and the partial-lane pairwise reduction.
Admission additionally checks the complete fixture alpha mask, geometry,
colors, thresholds, power, blur size, downsample scale, owner, and render mode.

At this historical checkpoint the other six cells remained fail-closed.
Reconstructing their consumed blurred
scalar from the exported output shows that an OpenCV 4.5.5 Apple-Silicon
sidecar agrees on 150 of 187 float words. Of the remaining 37 words, 35 differ
by one ULP and two differ by two ULP. This residual propagates through Sphere,
Power, and background composition, so an epsilon comparison cannot establish
raw equality.

The following hypotheses were rejected:

- treating zero-sigma bilateral filtering as identity;
- scalar OpenCV LUT interpolation with fused or unfused accumulation;
- all 24 permutations of the top/left/right/bottom neighbor traversal;
- fused, split-multiply/add, and pairwise four-lane reductions;
- using the Apple-Silicon OpenCV 4.5.5 output directly.

Across the tested general operation-order families, the best result still left
33 of 187 words unequal. A fixture-coordinate ULP correction can make the six
outputs match, but it is an expected-value oracle rather than derived worker
semantics and is intentionally excluded from production.

The natural public trace localized the residual. The later exact closure named
at the top derived the required scalar order without coordinate correction and
supersedes this checkpoint's `PF_Err_BAD_CALLBACK_PARAM` conclusion.
