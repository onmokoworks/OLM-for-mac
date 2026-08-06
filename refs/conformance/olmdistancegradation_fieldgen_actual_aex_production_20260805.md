# OLMDistanceGradation production fieldgen actual-AEX slice

- Status: `exact`
- Scope: Mac production `dt_to_normalized` numerical output versus a retained actual-AEX `FUN_181174760` CPU fixture.
- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.

Two hash-bound `17x11` synthetic cross-mask fixtures are covered:

- raw threshold `3`, `param8=1` (Constant interpolation);
- raw threshold `4`, `param8=0` (non-Constant truncation/ramp path), newly captured directly from the hash-pinned AEX through Unicorn.

The focused harness includes the production DistanceGradation source and calls the same `dt_to_normalized` leaf used by `build_distance_field`; it does not use a reimplemented Python field model.

For each parameter branch, all `187/187` float32 words match the retained actual-AEX field exactly (`374/374` combined). Seven spatial anchors per branch are also printed and checked as raw float32 words.

Focused command:

```text
python3 tools/emulation/test_olmdistancegradation_fieldgen_actual_aex_production_20260805.py
```

The downstream case0023 PF16 production compose/store triplet and same-shape typed regression also pass after this test.

This closes production numerical slices of both `distanceTransform -> Constant threshold -> normalize` and `distanceTransform -> truncating threshold -> normalize` for the same-shape cross mask. It does not prove the case0023 host mask, other mask geometries or thresholds, resize, blur, PF16 field staging, full-frame output, or AE exactness. No AEXCompat change was required.
