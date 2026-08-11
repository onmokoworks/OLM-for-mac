# OLMDistanceGradation PF32 Blur Mode 5 dispatch analysis

The retained exported-owner matrix contains eight PF32 Mode 5 cells:
Constant/Linear/Sphere/Power × Background off/on on the fixed 17×11
transparent-island fixture.

The Constant pair is now raw-byte exact. Production reproduces the relevant
OpenCV 4.5.5 `CV_32FC1` bilateral semantics from input values: a 4096-bin
exponential LUT, radius-one cross neighbors, replicated borders, four-lane
fused interpolation/accumulation, and the partial-lane pairwise reduction.
Admission additionally checks the complete fixture alpha mask, geometry,
colors, thresholds, power, blur size, downsample scale, owner, and render mode.

The other six cells remain fail-closed. Reconstructing their consumed blurred
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

The next admissible probe is an internal post-`cvSmooth` plane capture from the
same resident exported-owner worker that produced the retained raw outputs,
including its CPU-dispatch identity. Until that boundary is available,
Linear/Sphere/Power Mode 5 remain `PF_Err_BAD_CALLBACK_PARAM`.
