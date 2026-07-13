# OLMSmoother2 Gamma Colors a9c0 Fix

Date: 2026-07-12

## Verdict

`BINARY_GROUNDED_IMPROVEMENT_NOT_AE_EXACT`

## FACT

- `FUN_18000a9c0` performs the output-transfer conversion only when the low
  32-bit version/config field is zero. Normal v1/v2 values bypass it.
- The Mac port previously converted Gamma Color comparison candidates whenever
  `version != SMOOTHER_V1`, causing v2 mode 3 to miss colors that the AEX matches.
- The local AEX CPU simulator now implements the imported Windows-x64
  `pow(double,double)` ABI. Before that detour, gamma apply was observable but
  pow returned its unchanged XMM input and hid the semantic difference.
- Identical synthetic mode-3 fixture after the fix:
  - AEX cce0: `[0.8971925378, 0.4243943989, 0.4243943989, 0.9980392456]`
  - Mac cce0: `[0.897192419, 0.424394399, 0.424394399, 0.998039246]`
  - comparison: equal at `1e-6`
- Existing Windows-reference CLI A/B:
  - `legacy_case_0004_current_aex`: unchanged, `max=113`, `mean=0.0044534867`.
  - `legacy_case_0012_gamma5_red_blue_current_aex`: `mean=0.0150559414` to
    `0.0092496142`, nonzero pixels `0.186101466%` to `0.121576003%`;
    `max=91` remains at `(91,841)`.
- Mac AE host audit exposed and fixed two independent host defects:
  - `PF_FloatSliderDef.value` was incorrectly passed through `FIX_2_FLOAT`,
    turning Gamma Value `2.1695473` into `3.31046649e-05`.
  - The Xcode project inherited deployment target `26.2` from the SDK and was
    unloadable on macOS 15.7.2; the project now pins macOS `11.0`.
- The Windows-visible parameter surface is restored: Smoothness, Extra Smooth,
  and Smooth Range use `0..100`; Gamma Value uses `1.0..2.4`, default `2.4`.
- Latest confirmed Mac AE 26.3 render after forcing a bundle-mtime rescan:
  `max=115`, `mean=0.1616552132`, nonzero `19,486` pixels (`0.939718%`).
  At the active legacy witness `(91,841)`, Windows is `[0,0,0,0]` and Mac AE
  is `[32,32,32,91]`. This is not AE exact.

## INFERENCE

- The full-image improvement isolated to the Gamma Colors case supports the
  a9c0 version-gate correction. CLI evidence is not Mac AE exact evidence.
- The remaining `(91,841)` residual is still an upstream live class/config or
  producer-selection problem; it is not resolved by this gamma comparison fix.
- Mac AE plugin validation must touch the installed bundle root after copying;
  otherwise AE can reuse an old `Ignore`/plugin registry entry and produce a
  misleading result from a previous binary.

## Commands

```sh
python3 refs/scripts/smoke_smoother2_fullchain_diff.py
bash refs/scripts/build_olmsmoother2_cli.sh
python3 scripts/analyze_smoother2_current_aex_residuals.py \
  --output-dir /tmp/olmsmoother2_gamma_match_fix_20260712 --keep-run-dir
```
