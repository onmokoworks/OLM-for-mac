# OLMRadialBlur reconstructed Zoom collapse witness (2026-07-17)

- Status: `pass`
- Classification: `bounded-actual-aex-collapse-proven`
- Scope: pinned Mac Unicorn execution with a reconstructed 32x1 case_0009 row; no AE-exact or Windows-equivalence claim.
- Target: `FUN_1800056F0+0x5c9f`, exact post-loop exit `0x180005d96`; sampler `FUN_180009D80`.
- Fixture: source row `540`, primary x=`7`, controls x=`8,24`.

- x=7: +0xf252=[1.0]; +0xf250=[1.0, 1.0, 1.0, 1.0]; +0xe=[1.0, 1.0, 1.0, 1.0].
- x=8: +0xf252=[1.0]; +0xf250=[1.0, 1.0, 1.0, 1.0]; +0xe=[1.0, 1.0, 1.0, 1.0].
- x=24: +0xf252=[1.0]; +0xf250=[0.0, 0.0, 0.0, 1.0]; +0xe=[0.0, 0.0, 0.0, 1.0].

The collapse bytes are written by the actual AEX block; the independent oracle and x=7 D80 comparison are in JSON.
