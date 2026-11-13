# Numerical provenance

The port uses `olm-math` for x86 float-to-int conversion and its `Mode` type.
The shared crate has no `logf` entry point. Implementing it there is outside
Job N-uvmap's ownership, so `src/numerics.rs` is a local extension awaiting
migration into `olm-math`; it never calls platform libm.

`src/numerics.rs` was translated from the loaded Windows UCRT logf SSE and FMA
bodies at RVAs `0xa9b80` and `0xa9d40`. Its provider is
`C:/Windows/System32/ucrtbase.dll`, version 10.0.26100.9711, SHA-256
`dedb7611e1abc1ff3852dcac3d4c93a048d729e25b061973b9969f22698f14ca`.
`src/log_tables.rs` stores the 129 raw f32 words from each of the reciprocal,
lead and tail tables at RVAs `0x10a440`, `0x109000` and `0x109210` respectively.
Explicit `mul_add` is used only at instructions observed in the FMA body.

The native render reference uses the FMA path on this capture machine; the
deterministic kernel therefore uses `Mode::Fma` on every target. Mipmap count
preserves the original double log(2) divisor, raw bits `0x3fe62e42fefa39ef`,
and the original float/double conversions. Trilinear LOD uses the original
float logf ratio. Do not replace these with log2 or reassociated arithmetic.

`validate_numerics.py` compares return bits from the production DLL with native
`logf`, explicitly selecting both UCRT FMA modes. Seed 20261113 samples 50,000
positive finite bit patterns across the f32 exponent range plus nine boundary
values per mode. Both modes pass 50,009/50,009 exactly. This test does not
qualify errno, FP exception flags, all NaN payloads, every rounding mode, or
arbitrary HDR/negative/NaN image rendering.

This is an OLM-internal translation and constant extraction. As with the
repository's `ucrtmath/ms/` and combined math artifacts, it must not be
published as a standalone math library. No original AEX or UCRT DLL is included.
