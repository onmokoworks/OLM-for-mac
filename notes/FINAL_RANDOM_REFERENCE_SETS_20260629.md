# Final Random Windows Reference Sets (2026-06-29)

2026-06-29 に返却された「最終確認用のランダム参照」は 2 系統ある。

## 1. Holdout 本命

- source zip:
  - `/Volumes/onmk/olm_pr/old/olm_final_random_per_plugin_10cases_20260629_windows_reference_return.zip`
- imported root:
  - [refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olm_final_random_per_plugin_10cases_20260629_windows_reference_return)
- Windows AE: `26.2x49`
- render path: `SOFTWARE`
- shape:
  - 9 plug-ins
  - each 10 random cases
  - total 90 cases
  - inputs:
    - `random_final_grid_1920x1080.png`
    - `random_final_alpha_1920x1080.png`
- important property:
  - parameter write failures are reported as `0`

これは最終段の confidence / holdout suite として使う。一次仕様の確定は、
従来どおり狭い reference request と runtime trace を優先する。

## 2. Smoke 補助セット

- source zip:
  - `/Volumes/onmk/olm_pr/old/olm_final_random_smoke_20260629_windows_reference_return.zip`
- imported root:
  - [refs/win_references/olm_final_random_smoke_20260629_windows_reference_return](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olm_final_random_smoke_20260629_windows_reference_return)
- Windows AE: `26.2x49`
- render path: `SOFTWARE`
- shape:
  - 5 requests
  - total 10 cases
  - inputs:
    - `random_final_grid_1920x1080.png`
    - `random_final_alpha_1920x1080.png`

重要:

- この smoke では、元の乱数値の一部が Windows AE scripting range を超えて
  `setValue` に失敗している。
- したがって、元 request JSON ではなく、返却された
  `reference_manifest.json` に記録された actual/effective 値を正とする。

既知の write-failure case:

- `final_random_colorkey_001`
- `final_random_colorkey_002`
- `final_random_kirakira_001`
- `final_random_kirakira_002`
- `final_random_radialblur_002`
- `final_random_smoother2_002`

## 運用ルール

1. まず narrow proof / runtime trace / IR で仕様を詰める。
2. その後に 90-case holdout を回して confidence check を行う。
3. smoke は補助的に使うが、上記 6 case は request 値そのものを信用しない。
