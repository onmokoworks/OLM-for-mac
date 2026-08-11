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
  Gamma 1.0／2.4、Gamma All／Colors、key極性、3 smoothing tupleを交差した
  9×7 fixtureは54／54 raw exactです。旧PF8 Gamma All 2.4 mixed tupleの5-byte seamは、
  current-AEXの10,000-entry LUTをPF8 decode／outputにも使い、Windowsのscalar
  MULSS→ADDSSをarm64 FMADDへ縮約しないことで閉じました。期待byte補正ではありません。
  Gamma Colors paletteのcount／reorder／duplicateをkey極性と3深度で交差した
  18／18ケースもraw exactです。未列挙palette／key／smoothing直積へは一般化しません。
- OLMKiraKira：Mode 4の方向レイを、回転後geometry 9×7以上、Length 1〜1000へ
  一般化しました。17ケース、51中間stageの比較はすべてmax ULP 0です。
  さらに5代表ケース×PF8／PF16／PF32で、非default色、半透明／HDR、Merge 1／2、
  ramp off／1／2を含むcompose交差を確認し、aggregate 320 bytesとtyped output
  560 bytesがraw exact／max ULP 0でした。Length 1の非identity経路と、
  actualの合成順Vertical→Horizontal→Diagonal→Diagonal2→Highlightも反映しています。
  natural Mode 4の残り4 source caseもsame-runで閉じ、新規12 typed outputは
  raw exact／max ULP 0です。Highlight gradientは15 words中2 wordsに1 ULP seamが
  あるためconstant source限定のままとし、任意gradientへは一般化しません。
- OLMDirectionalBlur：Front／Back Fade 50／100とSharp Tail 50／100の組合せを、
  PF8／PF16／PF32の計24行でraw exact確認しました。
  さらにfront／back各4 covering tupleでFade、Sharp、Noise Variation、
  Noise Type 1／2、Size Variationを交差させた高次24行もraw exactで、
  既存回帰を通過しています。さらにFront＋Back同時の4 tuple×3深度、計12行も
  raw exactです。Type 3、他geometry、未列挙tupleはfail-closeします。
  同じdual-side familyを32×18 geometryでも3深度12／12、rowdriver 32 callsで
  raw exact確認しました。他geometryや未列挙tupleは引き続きfail-closeです。
- OLMBlur：exported EffectMainからSmartPreRender／SmartRenderへ至るactive chainを
  PF8／PF16／PF32の6／6ケースで確認し、出力とrow paddingがexactです。
  これは全深度の記録済みSmart chain証拠であり、classic entrypointの同等性主張ではありません。
- OLMColorKey：半透明入力のEdge Blur Amount 2、Direction 1／2／3、
  Distance Type 1／2／3を、PF8／PF16／PF32の計27行でbyte exact確認しました。
  さらにDirection 0／4、Amount 1／4、Distance Type 2のendpoint 12行も
  temporary planeからrow paddingを含む出力までexactです。
  Direction 0／4、Distance Type 1／3のcovering 12行も追加でexactとなり、
  retained controlを含むmatrixは51／51です。PF32 Amount 4は記録済みshellに限定し、
  未列挙tuple／geometryへは一般化しません。
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
- OLMRadialBlur：Zoom／Rotation、PF8／PF16／PF32、4 covering tupleの
  Size×Edge×Noise計24ケースで、consumed planesとtyped outputがexactです。
  Edge prepassのcomponent factorと、scatterが使うSize×Noise spanは別経路として
  一致を確認しました。Rotation Size Variation 25のdiagnostic source scalarだけは
  各ケース1326／8186 float中に既知の1 ULP差があり、prepass以降とoutputはexactです。
  Inner、未列挙tuple／geometry、Type 3はfail-closeします。
- OLMRadialBlur：Inner Strength 4のSize×Edge×NoiseもZoom／Rotation、
  PF8／PF16／PF32、4 tupleの24ケースでconsumed planes／output exactです。
  PF32 Rotationの4 tupleだけはforward-angle、PF8／PF16はreverse-angleを使います。
  Size Variation 25のdiagnostic source scalarには既知1 ULP差がありますが、
  prepass以降とtyped outputはexactです。未列挙tuple／geometry／Type 3はfail-closeします。
- OLMRadialBlur：非neutral transform×workerの3 tupleをZoom／Rotation、
  PF8／PF16／PF32で交差した18／18ケースがexactです。Aはratio 2／angle 30°＋
  Edge 50、BはQuality 3／Repeat off＋Noise 100 Type 2、Cはoff-center (8,6)＋
  Size 50です。Repeat offでは有効tapだけで正規化し、Rotation noise gateを通し、
  Quality 3のouter spanは3／5を使うactual-AEX機序を反映しています。
  未列挙tuple／geometry／Type 3へは一般化せずfail-closeします。
- OLMDistanceGradation：Constant／Linear／Sphere／Power、Background on／offの
  typed blur matrixで、PF16はBlur 2／3／4／5の32行、PF32はBlur 2／3／4の24行を
  byte exact確認しました。PF32 Blur 5は、固定17×11の厳格predicateでConstant×
  Background off／onの2行をOpenCV 4.5.5の一般式によりraw exact確認しました。
  Linear／Sphere／Power×Backgroundの残り6行は37 wordに1〜2 ULPの残差があり、
  機序未解明のためBAD_CALLBACK_PARAMでfail-closeします。期待word補正は採用していません。
  この結果、typed matrix全体は58行exact、6行fail-closeです。
  Linear Mode 5の追加観測では、距離pre-plane 187／187 wordsがexactで、
  cvSmooth wrapperのentry／return間の変化は0／187でした。残差はopaque出力33 wordsに
  絞られましたが、x86 OpenCV reduction／compose機序は未解明です。58 exact／6
  fail-closeを維持し、期待word補正もproduction変更も行っていません。

AEXCompat側では汎用pointee-memory dereference watchを別リポジトリの
`37bdeae9`（`codex/issue851-smart-primary-checkout`）へ記録しました。
新規focused testsとbuildはpassしていますが、既存suiteには3 failが残ります。
この基盤更新自体をOLMのExact証拠とは数えません。

上記の数値は記録済みfixtureの行数です。任意のgeometryや未列挙の
Size／Noise／Edge／Offset／Brightness組合せへの完全互換は主張しません。
OLMRadialBlur Noise Type 3のLayer入力と、未記録の複合tupleは引き続き
証拠境界です。OLMKiraKiraの極小geometry、OLMDirectionalBlurとOLMColorKeyの
未列挙値・未列挙複合tupleも同様であり、上記結果を全設定へ一般化しません。
OLMKiraKira Mode 4の自然生成5×3 full-frameは、同一actual-AEX full-caller実行の
vtable seed 15 words、Horizontal slot 1／Length 5／Rotation 0°、aggregate入口ray
15 wordsからPF8／PF16／PF32 typed outputまでraw exactです。production変更は不要でした。
これはhostlessの1 source caseで、Windows AE pixelや任意sourceへは一般化しません。

## リリース候補の状態

Mac統合候補は、全10プラグインの固定fixture回帰、インストール済みUniversal
bundleのarchitecture／署名／identity検査、および現行Mac AEでの代表ロード・
レンダーを通過しています。

最新の最小host smokeはAfter Effects 26.3x87、macOS 15.7.2 arm64、
Software renderer（raw 1816）で実行し、全10プラグインがloaded／applied／
render_succeededでした。各プラグインについて64×64 PNGを1枚保存し、以前の
9/10 smokeで未達だったOLMDirectionalBlurも今回は成功しています。これはhostの
ロード・適用・レンダー成立を示すsmokeであり、Windows pixel exact、主要パラメーター
一致、または保存PNGのconformanceを一般化する証拠ではありません。

同一契約によるWindows AE 7行は取得・受領検証済みです。ColorKeep 3深度、
OLMKiraKira Mode 4 PF32内部経路、OLMSmoother v1 PF16内部経路のbounded比較も
完了しています。host入出力変換を含むraw EXRの包括一致へは昇格しません。

## 2026-08-12 public entry／installed boundary

- ColorKeep：installed public covering 6セルがraw exactです。
- OLMSmoother2：public EffectMain SmartPreRender→SmartRenderの6セルが3深度で
  actual-AEX coreとexactです。PF8／PF16の同条件classic Renderもraw-identicalですが、
  PF32 classicには分岐がなくfail-closeします。
- OLMToonDilate：installed EffectMain Smart chainの4 semantic family×3深度、
  12／12がraw exactです。これはAE-free installed-binary境界です。
- OLMDirectionalBlur：32×18 dual-side Type 2と16×16 padded Type 3 Layerの
  public Smart chainが3深度6／6 exactです。21個の非input parameterとworld lifecycleを
  確認し、Type 3 Layer欠落時は出力を変更せずfail-closeします。別sourceへ一般化しません。
- OLMColorKey：exported Smart ownerとproduction EffectMainのpublic Edge Blur
  covering 6 tuple×3深度、18／18がraw exactです。
- OLMRadialBlur：Outer 4＋Inner 2／4とSize 25／100をZoom／Rotation・3深度で
  交差した24／24が内部planeからtyped outputまでexactです。
- OLMKiraKira：Mode 1 public 3-depth経路は5×3半透明source、Horizontal Length 7、
  Rotation 0でPF8／PF16／PF32のactive bytes、input不変、row paddingまでraw exactです。
  nondefault RotationはAEXCompatのANGLE edit未対応のためfail-closeし、Mode 2／3の
  public ownerは未完です。

これらは記録済みfixtureのpublic-entry／installed境界であり、Windows AE pixel exactや
未列挙入力・geometry・パラメーター直積へは昇格しません。

OLMDistanceGradation PF32 Mode 5の未解決6セルでは、残差の初出がfinal composeではなく
OpenCV 4.5.5のIPP bilateral producer fieldであることを確定しました。classic ownerの
187-word identity wrapperとは別に、exported PF32はIPP invoker／backendを通り、
opaque/no-background composeはそのfield redをそのままalphaへ使います。matrixは
58／64 exactのまま、期待word補正なしで残り6セルをfail-closeします。
AEXCompat側の関連checkpointは別repoの`6561b11b`です。

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
| OLMBlur | Legacy／NonLegacy、repeat、bias；PF8／PF16／PF32 | exported EffectMain→Smart chainは3深度6／6 active、出力／padding exact。記録済みSmart経路の証拠であり、classic entrypointや任意tupleへは一般化しない |
| ColorKeep | enabled／disabled、tolerance、1〜100色；PF8／PF16／PF32 | Windows/Macのkeep mask、alpha、保持／棄却関係は3深度exact。raw EXRはeffect-off時点の全RGBにhost色変換差があるためcross-host exactへ昇格しない |
| OLMColorKey | core、Edge Thin、Edge Blur、replace／color-space；PF8／PF16／PF32限定 | 半透明32×18 two-key fixtureは追加covering 12行を含む51／51 exact。PF32 Amount 4は記録済みshell限定で、未列挙amount／direction／distance／geometryへは一般化しない |
| OLMToonDilate | copy／dilate、fractional radius、frontier／tie／corner／eligibility；PF8／PF16／PF32 | padded／partial／empty worldとradius -1〜4を確認。実効radiusは`ceil(radius × downsample_x.num / den)`。legacy `PF_Cmd_RENDER`は実AEX同様3深度でno-op、描画はSmartRender経路。現行PF32 radius 13 AE代表はhost smoke |
| OLMDistanceGradation | Inside／Outside／Both、RGB／Layer、Constant／Linear／Sphere／Power、invert／background／blur；PF8／PF16／PF32限定 | typed blur matrixは58 exact／6 fail-close。Mode 5 Linearはpre-plane 187／187 exact・cvSmooth差0だがopaque出力33 wordsが残る。期待補正なしで拒否を維持し、任意geometryや全直積へ一般化しない |
| OLMDirectionalBlur | 基本方向ブラー、Noise Type 1／2／3；PF8／PF16／PF32限定 | PF16 Type 3 Layerは16×16の限定tuple。Front＋Back同時familyは16×16と32×18の記録済み各12行がraw exact。32×18ではrowdriver 32 callsを確認。他geometry、未列挙tupleへは一般化しない |
| OLMRadialBlur | Zoom／Rotation／Inner；PF8／PF16／PF32 guard付き | PF8 centered neutral Inner Strength 1〜64に加え、Inner 4 Size×Edge×Noiseは3深度24ケースのconsumed／output exact。PF32 Rotation限定forward-angle、PF8／16 reverse-angle。SV25 diagnostic scalarのみ1 ULP。未列挙tuple／geometry／Type 3へは一般化しない |
| OLMSmoother2 | v1／v2 classifier、key／invert、Gamma None／All／Colors、range／extra、palette；PF8／PF16／PF32限定 | Gamma／key／smoothing 54／54とpalette交差18／18がraw exact。旧PF8 seamはLUT契約と非縮約scalar積和で解消したが、任意直積やAE hostへは一般化しない |
| OLMKiraKira | Mode 1／2／3／4、ramp、compose、warp／blur；PF8／PF16／PF32限定 | natural Mode 4の追加4 source／12 typed outputはraw exact・max ULP 0。Highlight gradientは2／15 wordsに1 ULP seamがありconstant source限定。Windows AE pixel、任意source／gradient、全直積は未証明 |
| OLMSmoother v1 | no-key／Color Key、smoothing range；native PF8／PF16 | PF8 canonical 960×540と保持済みkey pathはexact。PF16 Color Keyはexported `PF_Cmd_RENDER`からtemporary world、mask／main passまで5×3 padded fixtureでraw exact。AEXにnative PF32 callbackはなく、32bpc projectではAEがclassic integer pluginの前後をhost-convertする |

残課題として、OLMDistanceGradation PF32 Mode 5はIPP field数値境界で64セル中
58 exact／6 fail-close、
OLMSmoother v1 PF32はnative laneではなくAE host conversion、Layer Noise Type 3の
汎用検証は未完です。Type 3のmacOS側fixture実行基盤はAEXCompat #1162の対象です。

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
