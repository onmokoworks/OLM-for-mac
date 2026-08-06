# OLMDistanceGradation PF32 controlled-source boundary

- Status: `exact` for the bounded EffectMain PF32 case.
- Geometry/parameters: same 17x11 PF32 owner probe, no resize or blur.

An independent actual-AEX owner fixture now retains a nonzero source (`A=1, RGB=.25/.5/.75` except the five-pixel zero-alpha cross), its 187-word field, and all 2,992 final output bytes.

- field SHA-256: `8ac06eb6a3a4329f511a3496e33b13c51ec01c6fb03624f238e545c7536e30ca`
- output SHA-256: `c014b5d14d68e4ec6ce49592029067f6415bce31366a7f66694ecb9eb57c8540`
- owner completed naturally and overwrote the full output sentinel.

The initial mismatch had two causes. The first 1,710-byte diagnostic used invalid/default checkout values for slots 5/6. A subsequent 848-byte diagnostic bound RGB/background but still supplied slot 9 as `1` (Constant) while the production fixture requested Linear (`2`). The final capture fail-closes checkout slots 5/6/9 as `1/1/2`; its field SHA is identical to the independent non-Constant `FUN_181174760` fixture.

Owner IplImage captures show the final PF32 branch merges the scalar field into all four channels. At discriminator pixels `0,90,91,93,96`, the final compose inputs and outputs verify `A=R=G=B=d_alpha*X`; this is distinct from PF8/PF16 color callbacks and uses no integer staging. Production applies this rule only to the proven PF32 Inside+RGB+background branch.

The production `EffectMain(PF_Cmd_RENDER)` harness now compares both zero-source and controlled nonzero-source fixtures in one compile: each is exact at 2,992/2,992 bytes. PF8 and PF16 full-small-frame regressions also remain exact. SmartRender, resize, and blur remain excluded.
