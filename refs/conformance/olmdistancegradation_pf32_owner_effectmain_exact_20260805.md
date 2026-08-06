# OLMDistanceGradation PF32 owner to EffectMain exact slice

- Status: `exact`
- Scope: same-shape 17x11 PF32, Inside/Linear/Invert-on/RGB/background-on, threshold 4, no blur.

The hash-pinned actual AEX `FUN_181172a10` completes naturally after probe-local host/suite/Mat-TLS shims. Its output checkout ABI is a PF world pointer returned through the first indirect callback's out argument, with data at `+0x18`, rowbytes at `+0x20`, width at `+0x24`, and height at `+0x28`. A 0xcd output sentinel is completely overwritten.

Retained fixture:

- source PF32 bytes: 2,992
- intermediate field: 187 float32 words, SHA-256 `13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf`
- final PF32 bytes: 2,992, SHA-256 `cda258b2a722a9336224ca9bb3997f0761213a8dac68d24b5fed88d80f18e2a3`

The production harness enters `EffectMain(PF_Cmd_RENDER)`, uses its real PF32 format dispatch, and matches all 2,992 typed bytes exactly. The independent PF32 capture proves that Inside ownership outside pixels clear hidden RGB too; production extends that rule to PF32 without introducing PF8/PF16 field staging.

PF8 and PF16 full-small-frame regressions remain exact. SmartRender checkout plumbing, host resize, blur, and nonzero-source PF32 color arithmetic remain outside this narrow claim. No AEXCompat change was required.
