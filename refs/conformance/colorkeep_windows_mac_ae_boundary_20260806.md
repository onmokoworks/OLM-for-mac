# ColorKeep Windows/Mac AE 境界観測（2026-08-06）

## 結論

`colorkeep_opaque_cells_red_darkgray` を AE 26.3x87、Software、作業色空間
None、linear blending off、frame 24、PF8/PF16/PF32 で再取得した。

Windows AEX と Mac plugin の最終 EXR は raw pixel exact ではない。一方で、
ColorKeep が担う選択・保持・棄却の関係は3深度すべて完全一致した。

- Windows/Mac の effect-off は全 `2,073,600` pixelでalpha exact。
- 両hostとも同じ `307,500` pixelを保持し、残り`1,766,100` pixelを棄却した。
- keep maskのWindows/Mac差は0 pixel。
- 保持pixelは各host内でeffect-off RGBAをbit exactに維持した。
- 棄却pixelは各host内でRGBAすべて`+0.0f`になった。
- effect-onのWindows/Mac差`922,500`値は、保持pixelの3 RGB値
  (`307,500 × 3`)に限られ、同じpixelのeffect-off RGB差と完全に一致した。
- keep mask、alpha、保持／棄却関係で説明できないeffect-on差は0値。

従って、このケースで観測したraw差はColorKeep処理が新たに作った差ではなく、
effect-offの時点ですでに存在するWindows/Mac AE hostの素材入力／色変換／FLOAT32
書き出し経路差を、保持pixelがそのまま受け継いだものと分類する。

## raw差分

| depth | effect-off mismatch values | effect-on mismatch values | effect-on unexplained values |
|---|---:|---:|---:|
| PF8 | 6,220,800 | 922,500 | 0 |
| PF16 | 6,220,800 | 922,500 | 0 |
| PF32 | 6,220,800 | 922,500 | 0 |

effect-offの`6,220,800`は全pixelのRGB 3値 (`2,073,600 × 3`) であり、
alpha差は0である。これはプラグイン無効状態なので、プラグインのworker差には
帰属できない。

## 証拠とclaim boundary

- Windows返却ZIPは同梱verifierで7/7 accepted。
- ColorKeep 3行はそれぞれfresh Mac AE processで実行した。
- 各processで現行Universal `ColorKeep.plugin` の実パスを`vmmap`確認した。
- SHA-256: `4974d9f00c5b6a8eaf8ff1fb1cffb1a97d2f36a34af5ae01c759128351d83a2b`
- parameter readbackは描画前後で一致。
- source、Preserve-RGB template、行契約、Windows AEX、Mac pluginをhash bindした。

この証拠が閉じるのは、上記1ケース・3深度におけるColorKeepの同一host
effect-offからの選択／保持／棄却関係である。Windows/Macの最終EXR raw exactや、
別素材・別色設定・別AE versionへの一般化はしない。raw cross-host exactを要求する
場合は、まずプラグイン無効状態で一致する素材解釈／出力色管理契約を別途確立する
必要がある。

機械可読証拠は
`refs/conformance/colorkeep_windows_mac_ae_boundary_20260806.json`、再実行runnerは
`scripts/intake_colorkeep_windows_boundary_20260806.py`。

