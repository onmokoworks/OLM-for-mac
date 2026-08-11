# OLM for Mac Public Beta リリースノート — 2026-08-11

> 本プロジェクトはOLM DigitalのオリジナルOLMプラグインを基にした非公式の
> 互換移植であり、OLM Digitalによる提携・承認を示すものではありません。
> オリジナルのプラグイン、製品名、商標および原著作物に関する権利は、
> それぞれの権利者に帰属します。リポジトリのLICENSEは収録コードの利用条件であり、
> 本家資産に別途の権利を付与するものではありません。

## 2026-08-11 追加検証

2026-08-10の統合ゲート通過後も、完了判定に寄与する複合分岐の
actual-AEX比較を追加しました。これは全パラメーター直積への一般化ではありません。

- OLMRadialBlur：32×18の記録済みcomponent fixtureで、PF8／PF16／PF32の
  Size Variation×Noise Variation（48行）、Brightness×Size×Noise（96行）、
  Edge Fade×Noise（72行）をexact確認しました。さらにRotationの
  Offset×Noise（48行）、ZoomのEdge×Offset×Noise（48行）、Rotationの
  Edge×Offset×Noise（96行）を閉じました。Noise Variation 0では
  Zoomのself seedを保持するactual-AEXの振る舞いも回帰に反映しています。
- OLMSmoother2：v1／v2、PF8／PF16／PF32、複数geometryと入力patternを含む
  core 96行とfeature 18行の計114行をactual AEXとexact確認しました。
  この過程で、特定の幅での水平／対角scan境界を修正しています。
- OLMKiraKira：Mode 4の方向レイを、回転後geometry 9×7以上、Length 1〜1000へ
  一般化しました。17ケース、51中間stageの比較はすべてmax ULP 0です。
  さらに5代表ケース×PF8／PF16／PF32で、非default色、半透明／HDR、Merge 1／2、
  ramp off／1／2を含むcompose交差を確認し、aggregate 320 bytesとtyped output
  560 bytesがraw exact／max ULP 0でした。Length 1の非identity経路と、
  actualの合成順Vertical→Horizontal→Diagonal→Diagonal2→Highlightも反映しています。
- OLMDirectionalBlur：Front／Back Fade 50／100とSharp Tail 50／100の組合せを、
  PF8／PF16／PF32の計24行でraw exact確認しました。
- OLMColorKey：半透明入力のEdge Blur Amount 2、Direction 1／2／3、
  Distance Type 1／2／3を、PF8／PF16／PF32の計27行でbyte exact確認しました。
- OLMRadialBlur：Size Variation 25／100とEdge Fade 50／100の記録済み複合経路を、
  PF8／PF16／PF32の計36行でexact確認しました。
- OLMRadialBlur：Dual Strength×Noiseの48ケースでは、Zoomは全内部stage exact、
  Rotation Noise Type 2も全内部stage exactです。Rotation Noise Type 1はsampled
  source scalarに既知の1〜4 ULP差がありますが、prepass以降と最終出力はbyte exactです。
  この経路には未列挙tupleを拒否するfail-close controlがあります。
- OLMRadialBlur：Rotationの固定32×18 component fixtureで、PF8／PF16／PF32、
  Outer／Inner、Size Variation 25／100、Offset Mode 2／3（UI 4）の計24ケースを
  actual AEXとexact確認しました。polar、source scalar、accum、max、final、coords、
  outputの各stageが一致します。未列挙値、geometry、Type 3はfail-closeします。
- OLMDistanceGradation：Constant／Linear／Sphere／Power、Background on／offの
  typed blur matrixで、PF16はBlur 2／3／4／5の32行、PF32はBlur 2／3／4の24行を
  byte exact確認しました。PF32 Blur 5はactual AEXの8行を取得済みですが、
  OpenCV 4.5.5 SIMD bilateral経路に一部1 ULPの差が残るためExactへ昇格せず、
  productionではBAD_CALLBACK_PARAMでfail-closeします。

上記の数値は記録済みfixtureの行数です。任意のgeometryや未列挙の
Size／Noise／Edge／Offset／Brightness組合せへの完全互換は主張しません。
OLMRadialBlur Noise Type 3のLayer入力と、未記録の複合tupleは引き続き
証拠境界です。OLMKiraKiraの極小geometry、OLMDirectionalBlurとOLMColorKeyの
未列挙値・未列挙複合tupleも同様であり、上記結果を全設定へ一般化しません。

## リリース候補の状態

Mac統合候補は、全10プラグインの固定fixture回帰、インストール済みUniversal
bundleのarchitecture／署名／identity検査、および現行Mac AEでの代表ロード・
レンダーを通過しています。

同一契約によるWindows AE 7行は取得・受領検証済みです。ColorKeep 3深度、
OLMKiraKira Mode 4 PF32内部経路、OLMSmoother v1 PF16内部経路のbounded比較も
完了しています。host入出力変換を含むraw EXRの包括一致へは昇格しません。

現在のhost証拠は、原則として次の条件を前提とします。

- After Effects `26.3x87`
- CPU `SOFTWARE`レンダー
- working space：None
- linear blending：off
- 各証拠に記録された入力解釈、source hash、geometry、bit-depth、パラメーター

この文書での`Exact`は、該当レコード内のbyte一致、またはraw FLOAT32 word一致です。
あらゆる画像や全コントロールの直積に対する主張ではありません。

配布候補はUniversal／ad-hoc署名を検証しています。Developer ID署名とAppleの
notarizationは未実施であり、ダウンロード先のGatekeeperに拒否される可能性があります。

## 対応範囲と重要な境界

| プラグイン | リリース候補の主要モード／native depth | 重要な証拠境界 |
| --- | --- | --- |
| OLMBlur | Legacy／NonLegacy、repeat、bias；PF8／PF16／PF32 | 複数のpadded typed fixtureでdimension-generic workerを確認。現行PF32 host smokeはロード／レンダー証拠であり、Windows exact出力の新規主張ではない |
| ColorKeep | enabled／disabled、tolerance、1〜100色；PF8／PF16／PF32 | Windows/Macのkeep mask、alpha、保持／棄却関係は3深度exact。raw EXRはeffect-off時点の全RGBにhost色変換差があるためcross-host exactへ昇格しない |
| OLMColorKey | core、Edge Thin、Edge Blur、replace／color-space；PF8／PF16／PF32限定 | Edge Blurは記録済み4×3 familyと32×18 multi-keyに加え、半透明入力のAmount 2、Direction 1／2／3、Distance Type 1／2／3を3深度27行でbyte exact。未列挙amount／direction／distance／geometryの直積へは一般化しない |
| OLMToonDilate | copy／dilate、fractional radius、frontier／tie／corner／eligibility；PF8／PF16／PF32 | padded／partial／empty worldとradius -1〜4を確認。実効radiusは`ceil(radius × downsample_x.num / den)`。legacy `PF_Cmd_RENDER`は実AEX同様3深度でno-op、描画はSmartRender経路。現行PF32 radius 13 AE代表はhost smoke |
| OLMDistanceGradation | Inside／Outside／Both、RGB／Layer、Constant／Linear／Sphere／Power、invert／background／blur；PF8／PF16／PF32限定 | typed blur matrixはPF16のBlur 2〜5を32行、PF32のBlur 2〜4を24行exact。PF32 Blur 5は一部1 ULP差のためfail-closeし、Exactとしない。証明済みaxisとfamilyは全コントロール直積ではない |
| OLMDirectionalBlur | 基本方向ブラー、Noise Type 1／2／3；PF8／PF16／PF32限定 | PF16 Type 3 Layerは16×16の限定tuple。Front／Back Fade 50／100×Sharp Tail 50／100は3深度24行でraw exact。未列挙値やNoise／Sizeとの複合tupleへは一般化しない |
| OLMRadialBlur | Zoom／Rotation／Inner；PF8／PF16／PF32 guard付き | PF8 centered neutral Inner Strength 1〜64を含む複数geometryに加え、32×18の記録済みfixtureで複合分岐を確認。Rotation Size×Offsetは3深度24ケース全stage exact。Dual Strength×NoiseのRotation Type 1 source scalarには1〜4 ULP差が残る。Noise Type 3 Layer、未記載geometry／tupleへは一般化しない |
| OLMSmoother2 | v1／v2 classifier、key／invert、Gamma None／All／Colors、range／extra、palette；PF8／PF16／PF32限定 | 1×1から32×18までの複数geometryと入力patternを含む114行のclassifier matrixがexact。公開機能間の全直積や、記録されていないswitch family全体の証明ではない |
| OLMKiraKira | Mode 1／2／3／4、ramp、compose、warp／blur；PF8／PF16／PF32限定 | Mode 3 Gaussianは記録済みfixtureだけを許可。Mode 4方向レイと5代表compose交差はraw exact／max ULP 0。Length 1、非default色、半透明／HDR、Merge 1／2、ramp off／1／2を含むが、極小geometryや全直積は未証明 |
| OLMSmoother v1 | no-key／Color Key、smoothing range；native PF8／PF16 | PF8 canonical 960×540と保持済みkey pathはexact。PF16 Color Keyはexported `PF_Cmd_RENDER`からtemporary world、mask／main passまで5×3 padded fixtureでraw exact。AEXにnative PF32 callbackはなく、32bpc projectではAEがclassic integer pluginの前後をhost-convertする |

## AE host境界

AE import、premultiplication、color management、exportの差は、プラグイン演算とは
別のhost境界です。両hostが同じ入力worldを渡していない場合、最終ファイル差だけで
プラグイン演算差とは判定しません。

ColorKeepでは通常importによる16bpc clamp／色変換、Smoother v1ではalpha 254の
premultiply→unpremultiply境界を実際に分離しています。

## 受領済みWindows AE境界 — 7行

使用するパッケージ：

`refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`

| プラグイン | ケース | depth |
| --- | --- | --- |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF8 |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF16 |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF32 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF8 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF16 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF32 |
| OLMSmoother v1 | `case_0001` | PF16 |

各行でdisabled／effect-onのuncompressed scanline FLOAT32 OpenEXRと、
`BATCH_CONTRACT.json`指定のprocess／module attestationが必要です。PNG previewは
返却物として使用しません。今回の返却はこの条件で7行すべて受理されました。
ただし、受理はWindows観測の成立を意味し、Win/Mac pixel equalityの成立は
プラグイン別の同一条件比較が完了した行だけに限定します。

パッケージSHA-256：

```text
6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652
```

返却物：

`refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip`

返却物SHA-256：

```text
e582b0f368deb6dfbb34de2675e382d2222372705da043151d90dc895f7d7a0a
```

受領記録は
[`olm_windows_ae_release_boundary_minimal_intake_20260806.json`](olm_windows_ae_release_boundary_minimal_intake_20260806.json)
を参照してください。

プラグイン別の同一契約解析：

- ColorKeep：[`colorkeep_windows_mac_ae_boundary_20260806.md`](colorkeep_windows_mac_ae_boundary_20260806.md)
- OLMKiraKira：[`olmkirakira_mode4_windows_boundary_closure_20260806.md`](olmkirakira_mode4_windows_boundary_closure_20260806.md)
- OLMKiraKira hostless exact境界：[`olmkirakira_mode4_highlight_hostless_actual_aex_20260807.md`](olmkirakira_mode4_highlight_hostless_actual_aex_20260807.md)
- OLMSmoother v1：[`olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.md`](olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.md)
- OLMSmoother v1 host Gamma境界：[`olmsmoother_v1_pf16_crosshost_gamma_boundary_20260806.md`](olmsmoother_v1_pf16_crosshost_gamma_boundary_20260806.md)

## 最終Mac検証結果

```text
PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=510.90s
captured-output-sha256 3f4cb7381ee21f6ba11ca982a3183e8e63b471d3a19bb1c27e754853ddf209aa
Mac AE representatives 10 proven / 0 pending / 0 invalid
Universal installed bundles 10 / 10
Parameter UI registration 10 / 10（exact 7、bounded 3）
列挙済みdynamic UI callback 5 / 5
release_gate_pass
```

再実行：

```sh
python3 scripts/run_olm_release_gate_20260806.py
python3 -m unittest \
  tests.test_olm_release_documentation_20260806 \
  tests.test_windows_ae_release_boundary_minimal_20260806
shasum -a 256 refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip
```

Windows返却物の再検証：

```sh
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py \
  RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
```

プラグイン別の詳細証拠とfail-close条件は
[`olm_release_completion_matrix_20260806.md`](olm_release_completion_matrix_20260806.md)、
インストール済みbinary hashは
[`olm_release_gate_status_20260806.json`](olm_release_gate_status_20260806.json)を参照してください。

## English summary

The bounded Mac candidate passes all ten fixed-fixture lanes, ten installed
Universal/signature/identity checks, and ten current-Mac-AE representative
load/render witnesses. Exactness claims remain limited to the declared host,
depths, fixtures, geometries and parameter boundaries. Seven same-contract
Windows AE calibration rows are accepted and bounded per-plugin comparisons
are complete. Host color/export transforms remain separate, so no blanket
cross-host exported-pixel equality is claimed.
