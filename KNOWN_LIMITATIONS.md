# OLM for Mac Public Beta — 既知の制限

このベータは、Windows版OLM Toolsの全入力・全geometry・全パラメーター直積に対する
完全互換を保証しません。`Exact`は、証拠に記録されたAEバージョン、レンダー経路、
色深度、入力、geometry、設定値におけるbyte／raw word一致を意味します。

## 共通

- 主な検証環境はAfter Effects 26.3x87、CPU Software、working space None、linear
  blending offです。
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

- OLMColorKey：Edge Blurのexact証拠には、記録済みの小型geometry、multi-key、および
  半透明入力のAmount 2／Direction 1〜3／Distance Type 1〜3が含まれます。
  任意geometry、amount、方向、distance typeの全直積は未証明です。
- OLMDistanceGradation：主要な各モード・補間・背景・反転・blurは個別に検証していますが、
  全コントロールの直積は未証明です。PF16 Blur 2〜5とPF32 Blur 2〜4の記録済みtyped
  matrixはexactです。PF32 Blur 5はactual AEXで観測済みですが、一部1 ULP差が残るため
  BAD_CALLBACK_PARAMでfail-closeし、Exactとは表現しません。元AEXにownerがないPF32
  SmartRender要求も互換性主張の対象外です。
- OLMDirectionalBlur：Noise Type 3 LayerのPF16/PF32は、記録済みtupleを中心とする
  bounded対応です。Front／Back Fade 50／100×Sharp Tail 50／100は3深度でexactですが、
  Layer欠落、寸法不一致、未列挙値や他機能との複合tupleはfail-closeする場合があります。
- OLMRadialBlur：centered neutral InnerはPF8/PF16/PF32で複数geometryを実AEXと
  bit完全一致確認済みです。直接観測済みの最大geometryはPF8/PF16が640×360、PF32が
  64×36です。off-center、非unit ratio、angle、quality、repeat、offset、
  edge fade、noise、variationを含む全組合せは未証明です。Size Variation×Edge Fadeは
  記録済み32×18 fixtureの3深度36行でexactですが、任意geometryや未列挙値へは一般化
  しません。Dual Strength×Noiseの記録済み48ケースは最終出力exactですが、
  Rotation Noise Type 1のsampled source scalarには1〜4 ULP差が残るため、全内部stage
  exactとは表現しません。Windows独自のcustom preview描画と操作も未証明です。
- OLMSmoother2：key、invert、Gamma、range、paletteの主要分岐はbounded exactです。
  全パラメーター直積は未証明です。
- OLMKiraKira：Mode 1〜4の主要経路を実装しています。Mode 4の方向レイは、9×7以上の
  回転後geometryとLength 1〜1000を、実AEXの17ケース・51中間stageで一般化しています。
  5代表compose交差では非default色、半透明／HDR、Merge 1／2、ramp off／1／2を含めて
  raw exactですが、小型shape、ray／色／ramp／Merge Modeの全直積とDrawbot custom UIは
  未証明です。
- OLMSmoother v1：元AEXのnative depthはPF8/PF16です。32bpcプロジェクトではAEが
  classic integer pluginの前後を変換するため、native PF32互換とは表現しません。

より詳細な証拠境界は
[リリース完成表](refs/conformance/olm_release_completion_matrix_20260806.md)を参照してください。
