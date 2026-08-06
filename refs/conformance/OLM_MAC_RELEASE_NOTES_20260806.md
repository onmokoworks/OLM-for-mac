# OLM Mac 限定リリースノート — 2026-08-06

## リリース候補の状態

Mac統合候補は、全10プラグインの固定fixture回帰、インストール済みUniversal
bundleのarchitecture／署名／identity検査、および現行Mac AEでの代表ロード・
レンダーを通過しています。

同一契約による最終cross-host校正は、後述するWindows AE 7行だけが保留です。

現在のhost証拠は、原則として次の条件を前提とします。

- After Effects `26.3x87`
- CPU `SOFTWARE`レンダー
- working space：None
- linear blending：off
- 各証拠に記録された入力解釈、source hash、geometry、bit-depth、パラメーター

この文書での`Exact`は、該当レコード内のbyte一致、またはraw FLOAT32 word一致です。
あらゆる画像や全コントロールの直積に対する主張ではありません。

## 対応範囲と重要な境界

| プラグイン | リリース候補の主要モード／native depth | 重要な証拠境界 |
| --- | --- | --- |
| OLMBlur | Legacy／NonLegacy、repeat、bias；PF8／PF16／PF32 | 複数のpadded typed fixtureでdimension-generic workerを確認。現行PF32 host smokeはロード／レンダー証拠であり、Windows exact出力の新規主張ではない |
| ColorKeep | enabled／disabled、tolerance、1〜100色；PF8／PF16／PF32 | duplicate／特殊floatを含むdirect worldはexact。PF8 host exportとPF16 inter-effect discriminatorだけでは、保留中の同一契約Windows 3行を代替しない |
| OLMColorKey | core、Edge Thin、Edge Blur、replace／color-space；PF8／PF16／PF32限定 | Edge Blurは記録済み4×3、corner／center、single-key、方向、amountに限定 |
| OLMToonDilate | copy／dilate、fractional radius、frontier／tie／corner／eligibility；PF8／PF16／PF32 | padded／partial／empty worldとradius -1〜4を確認。現行PF32 radius 13 AE代表はhost smoke |
| OLMDistanceGradation | Inside／Outside／Both、RGB／Layer、Constant／Linear／Sphere／Power、invert／background／blur；PF8／PF16／PF32限定 | 証明済みaxisとfamilyは全コントロール直積ではない。PF32 SmartRenderは元AEXのnative機能ではない |
| OLMDirectionalBlur | 基本方向ブラー、Noise Type 1／2／3；PF8／PF16／PF32限定 | PF16 Type 3 Layerは16×16、angle 45、front 8、back 0、variation 100、neutral size／fade／tail、独立paddingに限定。Layer欠落・寸法不一致・他tupleはfail-close |
| OLMRadialBlur | Zoom／Rotation／Inner；PF8／PF16／PF32 guard付き | PF8 centered neutral Inner Strength 1〜64は9×7、64×36、640×360で証明。PF16／PF32 Innerは9×7 guardを維持。未記載offset／ratio／angle／quality／repeat／edge／noise／variationはfail-close |
| OLMSmoother2 | v1／v2 classifier、key／invert、Gamma None／All／Colors、range／extra、palette；PF8／PF16／PF32限定 | PF32 case07はraw artifact exactだが、同一runのWindows process／module証明がなく、process-attested AE exactとは呼ばない |
| OLMKiraKira | Mode 1／2／3／4、ramp、compose、warp／blur；PF8／PF16／PF32限定 | Mode 3／4は記録済みshape、length、tupleに限定。natural Mode 4と現行PF32 Mac AE出力は保持済みartifactへexact |
| OLMSmoother v1 | no-key／Color Key、smoothing range；native PF8／PF16 | PF8 canonical 960×540と保持済みkey pathはexact。PF16 cross-host parityは1行保留。AEXにnative PF32 callbackはなく、32bpc projectではAEがclassic integer pluginの前後をhost-convertする |

## AE host境界

AE import、premultiplication、color management、exportの差は、プラグイン演算とは
別のhost境界です。両hostが同じ入力worldを渡していない場合、最終ファイル差だけで
プラグイン演算差とは判定しません。

ColorKeepでは通常importによる16bpc clamp／色変換、Smoother v1ではalpha 254の
premultiply→unpremultiply境界を実際に分離しています。

## 保留中のWindows AE境界 — 7行のみ

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
返却物として使用しません。証拠再利用対象の残り7プラグインは再レンダーしません。

パッケージSHA-256：

```text
6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652
```

## 最終Mac検証結果

```text
PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=423.84s
captured-output-sha256 bf5970bbcaf47fed933b8602841ec20ce2e0db1a3f2be7d411fefa8b363e19fd
Mac AE representatives 10 proven / 0 pending / 0 invalid
Universal installed bundles 10 / 10
Parameter UI registration 10 / 10（exact 7、bounded 3）
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

Windows返却後：

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
Windows AE calibration rows remain pending.
