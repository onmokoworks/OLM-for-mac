# OLM for Mac Public Beta リリースノート — 2026-08-07

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
| OLMColorKey | core、Edge Thin、Edge Blur、replace／color-space；PF8／PF16／PF32限定 | Edge Blurは記録済み4×3、corner／center、single-key、方向、amountに限定 |
| OLMToonDilate | copy／dilate、fractional radius、frontier／tie／corner／eligibility；PF8／PF16／PF32 | padded／partial／empty worldとradius -1〜4を確認。現行PF32 radius 13 AE代表はhost smoke |
| OLMDistanceGradation | Inside／Outside／Both、RGB／Layer、Constant／Linear／Sphere／Power、invert／background／blur；PF8／PF16／PF32限定 | 証明済みaxisとfamilyは全コントロール直積ではない。PF32 SmartRenderは元AEXのnative機能ではない |
| OLMDirectionalBlur | 基本方向ブラー、Noise Type 1／2／3；PF8／PF16／PF32限定 | PF16 Type 3 Layerは16×16、angle 45、front 8、back 0、variation 100、neutral size／fade／tail、独立paddingに限定。Layer欠落・寸法不一致・他tupleはfail-close |
| OLMRadialBlur | Zoom／Rotation／Inner；PF8／PF16／PF32 guard付き | PF8 centered neutral Inner Strength 1〜64は9×7、64×36、640×360で証明。さらにPF16／PF32を64×36 padded、PF16を640×360まで実AEXとbit exact確認し、Strength 3／33／64を含む。未記載offset／ratio／angle／quality／repeat／edge／noise／variationの全組合せへは一般化しない |
| OLMSmoother2 | v1／v2 classifier、key／invert、Gamma None／All／Colors、range／extra、palette；PF8／PF16／PF32限定 | PF8ではv1／v2非均一base経路と、v2のkey／invert＋Gamma Colorsをpadded 3×2でraw exact確認。PF32 case07はraw artifact exactだが、同一runのWindows process／module証明がなく、process-attested AE exactとは呼ばない |
| OLMKiraKira | Mode 1／2／3／4、ramp、compose、warp／blur；PF8／PF16／PF32限定 | Mode 4 Highlightの経験的0.62 gainを除去。記録済み4×1、radius 5、orange、directional 0ではactual AEX 16引数full callerのMakeSeed→3-pass 11×11、aggregation、Merge 1からPF8／PF16／PF32 writerまで全段bit exact。未記載shape／tupleへは一般化しない |
| OLMSmoother v1 | no-key／Color Key、smoothing range；native PF8／PF16 | PF8 canonical 960×540と保持済みkey pathはexact。PF16 walker／subhandler／MainKernel／Executorはactual AEXへ局所・10,000 pixel累積exact。Windows AE EXRの183語差は全点でhost Gamma 2.4境界。AEXにnative PF32 callbackはなく、32bpc projectではAEがclassic integer pluginの前後をhost-convertする |

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
PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10 elapsed=435.03s
captured-output-sha256 f4a7186cfd2d6dc665f6cab35fdcee789564397fb6524c320c115723be2766d6
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
