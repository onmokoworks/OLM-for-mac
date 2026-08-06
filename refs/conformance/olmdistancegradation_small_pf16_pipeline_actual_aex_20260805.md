# OLMDistanceGradation small PF16 pipeline

- Status: `exact`
- Geometry: `17x11`, 187 pixels / 748 PF16 channel words.
- Pipeline: actual-AEX `FUN_181174760` non-Constant field generation, nearest-even PF16 field staging, then actual-AEX `FUN_181170480` compose/store.
- Parameters: Inside, Linear, Invert on, RGB mode, background on, thresholds 4, no blur.
- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.

The new Unicorn fixture retains the PF16 source, float field, staged PF16 field words, and complete PF16 output. The production harness runs `RenderBits<PF_Pixel16>` on the same source and parameters. Result: all 187 pixels and 748 channel words are exact.

The comparison exposed one bounded production mismatch: the AEX clears RGB as well as alpha for pixels outside the PF16 Inside ownership mask, while the Mac branch retained hidden background RGB beneath zero alpha. Production now clears RGB only for the proven `PF16 + Inside + use_bg + d_alpha==0` branch.

Focused command:

```text
python3 tools/emulation/test_olmdistancegradation_small_pf16_pipeline_production_20260805.py
```

Fieldgen branch tests, case0023 PF16 compose triplet, and the existing PF16 boundary regression pass after the change.

Excluded from this claim: host resize, blur, AE checkout/export, other modes/depths/parameters, and full canonical frame equality. No AEXCompat change was required.
