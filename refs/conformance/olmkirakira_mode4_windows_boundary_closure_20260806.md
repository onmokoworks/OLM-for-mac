# OLMKiraKira Mode 4 Windows 境界の閉鎖（2026-08-06）

対象は Windows 返却行 `kk_mapped_bm4_mm1_hi_r5_orange_opaque` のみである。設定は Blur Mode 4、Merge mode 1、Highlight Radius 5、Highlight Color orange、全ray length 0、PF8/PF16/PF32。

## 判明した欠落と修正

- 旧Mac実装は Mode 4 を Highlight の分岐へ入れていなかった。実AEX `FUN_18114f4a0` では Mode 4 Highlight は Mode 2 と同じ等方box filterを3回通る。
- 旧Mac実装の Merge mode 1 はscreen合成だった。実AEX `FUN_18114ddc0` は、glow/sourceのopacity適用alphaを個別にclampし、そのalphaでstraight RGBを加重平均し、alpha和を出力する。
- この2点をproductionへ移植し、PF8/PF16/PF32共通のtyped経路へ接続した。

## Mac AE 26.3x87での確認

修正版installed binaryは SHA-256 `84293bd782e9d536ecae0a9e92f2a6890a17d99f7a706dbc53a84366681b50bf`、`x86_64 arm64`、strict codesign検証済み。Software renderer raw 1816、None working space、linear blending offで同じ返却行を実行した。

| depth | no-effect SHA-256 | effect-on SHA-256 | 同一hostで変化した A/B/G/R word数 |
|---|---|---|---|
| PF8 | `f2c2e2a083ef0ef0b9167073741ae230bd9ec4a0164eb5712c7c3fa090329a5a` | `2899e05a7ef60ea496a2b23b058303846fad19b1e6d64ccd151c5e6341615d29` | `0 / 2073600 / 2071692 / 2073600` |
| PF16 | `e5faedc6db3f21483951da00954aea3393cd3d56f1acbc7537e5e0a0612c8095` | `8f5cb3063012ab9359e0c6ee23356bd51ccf1eae494e138b4d8468c148aa9f6d` | `0 / 2073600 / 2073600 / 2073600` |
| PF32 | `fdde660450bfae1916cb540c7b7fe3f848121d1d17d04b4ad030f86507f4ed2d` | `d28c261aa0f382b6b5985514212ed47f200c4f3d8f3f7ef2ef463d145029f872` | `0 / 2073600 / 2073600 / 2073600` |

旧installed binaryではPF32のeffect-onとno-effectが同一SHAだった。修正版では3深度すべてでRGBが変化し、alphaは全word不変であるため、Mode 4 Highlightの欠落は解消した。

## exact claimの境界

同じPNGをeffect無効で出した時点から、WindowsとMacのRGBは各深度とも `6,220,800` wordすべて異なり、alphaだけ一致する。例としてPF32の同一点はMac `0.9725341797`、Windows `0.9353449345` である。プラグインより前のAE入力解釈／色変換が一致していないため、この返却物からMac/Windowsのeffect-on raw FLOAT32 exactは主張しない。

この証拠が閉じるのは、実AEXの2つの局所分岐、productionへの接続、Mac AEでのPF8/PF16/PF32の非identity動作、Universal buildである。全色管理設定や全Mode 4入力のcross-host exactは範囲外である。

補足: AE側の `mainSource.preserveRGB` と `colorProfileName` はこのホストのExtendScriptでは `undefined` だった。結果encoderが `undefined` を扱えずscript error modalを出したため、runnerは `undefined` をJSON `null`として記録するよう修正した。EXR生成、単一AE PID、ロード済みplugin path、設定前後のparameter readbackはモーダル発生前に確認済みである。
