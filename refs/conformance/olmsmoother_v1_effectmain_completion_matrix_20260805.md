# OLMSmoother v1 EffectMain completion matrix

The canonical classic PF8 render is now exact. The portable renderer produces
the same 960x540 `case_0001` PNG as the pinned Windows AEX for Use Color Key=0
and Do Smooth Range=6. Both files have SHA-256
`b2c4cf128d89712b6565745a2d451b6ead1a47ad2efa5a4f4c92a402e95e3156`;
pixel, channel-byte, maximum, and mean differences are all zero.

The fix was at the generated EdgeWalker/SubHandler memory seam. Windows helper
code uses both the compact world offsets and the native PF world offsets
`+0x18/+0x20/+0x24/+0x28`. The portable memory adapter now bridges both layouts
to the native Mac `PF_EffectWorld`, so long edge walks no longer terminate at
the first pixel.

The result is covered below the frame boundary as well. Across all 1,898
nonuniform 3x3 centers in the case, 7,592 actual Classifier8 calls yield the
same 368 natural MainInterpKernel8 calls in the actual and portable paths.
Those calls produce 687 Executor8 calls. The actual-AEX, independent CFG
interpreter, and portable boundary captures match with normalized SHA-256
`26cd0b0fd1883c0ec6852c2e50cb1dfbc334166671192fdde4138d2c557f3ae9`;
actual and portable Executor replay both hash to
`8a2728344e9cceec81b2ffd2b4b4425421a0d7e0228c571b48383b922315db34`.

The public setup and UI no-op boundaries remain exact. Smart Render is not
advertised by the v1 flags. PF16 typed-session work remains explicitly owned by
the separate AEXCompat Apple Silicon task, and an AE-host load/render claim is
still withheld until the newly built universal bundle is observed in-host.
The full-frame exact result is canonical-case evidence, not yet an assertion
that every PF8 parameter combination has been covered.
