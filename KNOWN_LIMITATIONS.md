# OLM for Mac Public Beta — 既知の制限

このベータは、Windows版OLM Toolsの全入力・全geometry・全パラメーター直積に対する
完全互換を保証しません。`Exact`は、証拠に記録されたAEバージョン、レンダー経路、
色深度、入力、geometry、設定値におけるbyte／raw word一致を意味します。

## 共通

- 主な検証環境はAfter Effects 26.3x87、CPU Software、working space None、linear
  blending offです。
- macOS 15.7.2 arm64の最新最小host smokeでは全10プラグインのロード、適用、
  64×64 PNGレンダーが成功しています。この結果はhost smokeであり、Windowsとの
  pixel exactや主要パラメーター設定の一致を証明するものではありません。
- AEの素材import、premultiply／unpremultiply、色管理、codec、EXR出力はWindowsと
  macOSで異なる場合があります。同じプラグイン演算でも最終ファイルが一致しないことが
  あります。
- GPUレンダー、異なるAEバージョン、第三者ホストは互換性主張の対象外です。
- 現在のbundleはUniversal／ad-hoc署名を確認していますが、Developer ID署名とApple
  notarizationは未実施です。ダウンロード先のMacでGatekeeperに拒否される可能性があります。
- 未証明の設定では、安全のためエラーを返す、処理を拒否する、または限定経路へ入る場合が
  あります。
- 公開パラメーターの順序・型・名前・初期値・範囲はactual AEXの30定義と比較しています。
  一方、Windows版と同じcustom preview描画、クリック操作、動的ラベルのEVENT／UPDATE
  経路は未移植・未証明です。現行Mac版は、それらのcustom UI capabilityをAEへ広告しません。

## プラグイン別

- OLMBlur：exported EffectMainからSmart chainへ至る記録済み6ケースは全深度でactive、
  出力とpaddingがexactです。classic entrypointや未列挙tupleの同等性は主張しません。
- OLMColorKey：Edge Blurのexact証拠には、記録済みの小型geometry、multi-key、および
  半透明入力のAmount 2／Direction 1〜3／Distance Type 1〜3が含まれます。
  半透明endpointのDirection 0／4、Amount 1／4、Distance Type 2も12行exactです。
  Direction 0／4、Distance Type 1／3のcoveringを含むmatrixは51／51 exactですが、
  PF32 Amount 4は記録済みshell限定です。任意geometry、amount、方向、distance typeの
  全直積は未証明です。64×36の記録済み4 tupleは12／12 exactで、PF32 Type 3の
  float distance multiply→double sin→float plane構築順を含みますが、任意geometryへは
  一般化しません。
- OLMDistanceGradation：主要な各モード・補間・背景・反転・blurは個別に検証していますが、
  全コントロールの直積は未証明です。PF16 Blur 2〜5とPF32 Blur 2〜4の記録済みtyped
  matrixはexactです。PF32 Blur 5のConstant×Background off／onは固定17×11の厳格
  predicateでraw exactです。Linear／Sphere／Power×Backgroundの6行は37 wordに
  1〜2 ULP差が残るためBAD_CALLBACK_PARAMでfail-closeし、期待word補正も行いません。
  Linearのpre-planeは187／187 exact、cvSmooth entry／return差は0ですが、
  exported PF32の残差はOpenCV 4.5.5 IPP bilateral producer fieldで既に発生します。
  opaque出力33 wordsの数値機序が未解明なため、58 exact／6 fail-closeを維持します。
  元AEXにownerがないPF32 SmartRender要求も互換性主張の対象外です。
- OLMDirectionalBlur：Noise Type 3 LayerのPF16/PF32は、記録済みtupleを中心とする
  bounded対応です。Front／Back Fade 50／100×Sharp Tail 50／100は3深度でexactですが、
  Noise Type 1／2、Size Variationを含む高次covering 24行もraw exactです。
  Front＋Back同時の記録済み12行もraw exactです。Type 3、他geometry、未列挙tuple、
  Layer欠落／寸法不一致はfail-closeする場合があります。32×18の対応familyも
  3深度12／12 exactですが、これを任意geometryへ一般化しません。
- OLMRadialBlur：centered neutral InnerはPF8/PF16/PF32で複数geometryを実AEXと
  bit完全一致確認済みです。直接観測済みの最大geometryはPF8/PF16が640×360、PF32が
  64×36です。off-center、非unit ratio、angle、quality、repeat、offset、
  edge fade、noise、variationを含む全組合せは未証明です。Size Variation×Edge Fadeは
  記録済み32×18 fixtureの3深度36行でexactですが、任意geometryや未列挙値へは一般化
  しません。Rotation Size Variation×Offset Mode 2／3は同fixtureの3深度24ケースで
  全stage exactですが、未列挙値、geometry、Type 3はfail-closeします。
  Dual Strength×Noiseの記録済み48ケースは最終出力exactですが、
  Rotation Noise Type 1のsampled source scalarには1〜4 ULP差が残るため、全内部stage
  exactとは表現しません。Size×Edge×Noiseの記録済み24ケースもconsumed planes／
  outputはexactですが、Rotation Size Variation 25のdiagnostic source scalarに
  既知1 ULP差があります。Inner、未列挙tuple／geometry、Type 3はfail-closeします。
  ratio 2／angle 30°＋Edge、Quality 3／Repeat off＋Noise Type 2、off-center＋Sizeの
  3 tupleはZoom／Rotation・3深度の18／18でexactです。これはRepeat-off有効tap正規化、
  Rotation noise gate、Quality 3 outer span 3／5を閉じるbounded証拠であり、
  任意transform／worker直積へは一般化しません。
  Inner Strength 4のSize×Edge×Noiseも記録済み24ケースでconsumed planes／output
  exactです。PF32 Rotationの4 tupleだけforward-angle、PF8／PF16はreverse-angleで、
  SV25 diagnostic source scalarには既知1 ULP差があります。prepass以降はexactですが、
  未列挙tuple／geometry／Type 3へは一般化しません。
  Windows独自のcustom preview描画と操作も未証明です。
- OLMSmoother2：key、invert、Gamma、range、paletteの主要分岐はbounded exactです。
  Gamma／key／smoothing交差は54／54 exactです。旧PF8 Gamma All 2.4 seamは
  current-AEX LUT契約と非縮約scalar積和で閉じましたが、全パラメーター直積と
  AE host実行は未証明です。palette count／reorder／duplicate交差18／18もexactですが、
  未列挙palette直積へは一般化しません。
- OLMKiraKira：Mode 1〜4の主要経路を実装しています。Mode 4の方向レイは、9×7以上の
  回転後geometryとLength 1〜1000を、実AEXの17ケース・51中間stageで一般化しています。
  5代表compose交差では非default色、半透明／HDR、Merge 1／2、ramp off／1／2を含めて
  raw exactですが、小型shape、ray／色／ramp／Merge Modeの全直積とDrawbot custom UIは
  未証明です。自然生成5×3 full-frameは同一実行のseed／ray／aggregateからtyped
  outputまでexactですが、hostlessの1 source caseであり、Windows AE pixelや
  geometry-generalへは昇格しません。追加4 source／12 typed outputはmax ULP 0ですが、
  Highlight gradientは2／15 wordsに1 ULP seamがありconstant source限定です。
  Mode 1 public ownerはRotation 0の記録済み5×3 fixtureで3深度raw exactです。
  nondefault RotationはANGLE edit未対応でfail-closeし、Mode 2／3 public ownerは未完です。
- OLMSmoother v1：元AEXのnative depthはPF8/PF16です。32bpcプロジェクトではAEが
  classic integer pluginの前後を変換するため、native PF32互換とは表現しません。

より詳細な証拠境界は
[リリース完成表](refs/conformance/olm_release_completion_matrix_20260806.md)を参照してください。
