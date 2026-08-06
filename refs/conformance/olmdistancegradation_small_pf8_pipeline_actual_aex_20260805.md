# OLMDistanceGradation small PF8 pipeline

- Status: `exact`
- Geometry: `17x11`, 187 pixels / 748 PF8 channel bytes.
- Pipeline: actual-AEX `FUN_181174760` fieldgen, nearest-even PF8 staging, actual-AEX `FUN_181170870` compose/store.
- Parameters: Inside, Linear, Invert on, RGB mode, background on, threshold 4, no blur.

An independent hash-bound Unicorn fixture was captured for PF8; the PF16 result was not generalized. Initial production comparison found two independently evidenced differences: PF8 field values require nearest-even byte staging before compose, and pixels outside the Inside ownership mask clear hidden RGB along with alpha. Both rules were added only after this PF8 capture.

After the changes, production `RenderBits<PF_Pixel8>` matches all 187 pixels and 748 bytes exactly. The PF16 full-small-frame and typed layout regressions also pass.

Excluded: host resize, blur, AE checkout/export, other parameters and canonical full frames. No AEXCompat change was required.
