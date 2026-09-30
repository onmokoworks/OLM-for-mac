# Windows互換性の復元・解析計画

作成日: 2026-10-01（日本時間）

## 目的と完成の意味

同じWindows版の入力、設定、機能を持つ代替実装を作り、出力をビット単位で一致させる。
Public Betaの合格や見た目の一致で、この目標を置き換えない。
解析では元の処理を説明・再実装できるところまで復元する。変数名やコメントを含む
元ソースの原文復元は、コンパイル後の情報から一意に確定できないため完了条件にしない。

最初の対象はWindows 2025版AEX、CPU Software経路、既存の8/16/32 bpc契約とする。
これは初期作業範囲であり、GPU・他AE版の除外をユーザーが恒久承認したという意味ではない。
比較対象のAEX hash、AE版、architecture、色管理、素材解釈、downsample、座標、
parameterの単位・popup対応、Classic/Smartを毎回記録する。
Windows自身が非対応の経路は移植側の機能欠落と混同しない。

「全入力で完全互換」と「記録したケースでexact」は別の主張。
有限のテスト成功だけで全入力の一致を宣言しない。一般化には分岐、型、演算順、
境界処理、依存関数の復元根拠を併記し、未証明範囲を残す。

## 差分の分類と終了条件

| 分類 | 次に確かめること | その解析を閉じる条件 |
|---|---|---|
| 未解明の処理 | 同一入力の中間値を比較して最初の不一致を特定 | 該当分岐・データ構造・演算順を復元し、反例を含めてexact回帰。未調査分岐は別項目に残す |
| 移植実装の差 | 実AEXの値とMac側の対応箇所を直接比較 | 原因に対応する一般処理を修正し、public経路と既存回帰がexact。座標別の期待値補正は禁止 |
| Windows依存先の差 | UCRT/OpenCV/IPP等の実装・版・ABIを同定 | 必要な入力域で同じ関数意味を復元し、実AEXの呼出しから出力まで一致。固定native tableはそのセルの証拠に留める |
| ホスト・設定の差 | parameter builder、world、色管理、callback、書戻しを比較 | 同じ条件のnative AEで入力worldと出力worldを比較して一致。PNG保存成功だけでは閉じない |
| 比較器・参照の問題 | host代替関数、GPU/CPU、premultiply、codec、hash bindingを監査 | 比較経路を修正し再測定。誤参照へMac出力を寄せない |
| 未検証 | 既存処理を変更せず、狙った分岐に到達する入力を作る | 到達を確認して比較結果を取得。不一致が出れば上の分類へ移す |
| 古い記録 | 現行sourceと当時の証拠を照合 | 履歴を保持して現行参照を追記。過去のPASSを現行へ自動昇格しない |

原因が判明しても再現できていない項目は「原因判明・未解決」。外部証拠待ちも
「未解決」であり、数値差を許容して完了にはしない。

## 現状の初期棚卸し

下表は次の検証を選ぶ索引で、全入力exactの判定表ではない。
現行一般対応はBETA_SUPPORT.md、個別証拠はrefs/conformance/を参照する。
古いKNOWN_LIMITATIONS.mdやledgerの記述だけで残件を確定しない。

| 対象 | 判明している境界 | 次の検証と終了条件 |
|---|---|---|
| ColorKeep | count 5/100の末尾色に3深度anchor。全count/全paletteとClassicの契約は未完 | count 1/4/5/99/100、重複・透明色・不一致、public checkoutを比較。scalar/unrolled/tailの分岐とparameter対応を復元してexact |
| OLMBlur | repeat/legacy等の固定exactと一般laneが存在。Classic PF32は非対応として記載 | Windows側のClassic能力を先に確認。fractional Smoothness、Repeat、Biasのbuilder→worker→writerの最初の差を特定し一般処理で閉じる |
| OLMColorKey | Thin公開216設定に加え、Around/Manhattan/Blur4＋Thinの2592設定を公開AEX Smart→Mac Classic/Smartでexact確認。Thin±4000は距離capを復元し公開制限を解消。旧workerの255 contextと未実装sinfを隔離 | 他のBlur amount/distance/directionを公開ownerで再検証し旧stub依存分岐を復元。全color/threshold/HDR、native AEとROI/downsampleを閉じる |
| OLMDirectionalBlur | 非整数角度162ケースに加え、Windows公開builderの固定小数getter47件を復元。一般経路の等分行範囲へ戻して37×29の33画素差を解消。135候補中111件は本番dispatcherでもexact、24件は深度16/32の機能拒否 | 一般Size/Sharp/Noise/Fade等180候補はexactだが全件公開拒否。−720/−32768 Offsetの候補は未定義メモリ参照。元AEXの下限処理・allocation境界を確認し、追加workspace/Noise/Fadeの予算と公開admission・Smart契約を復元。Fade/Noise Layer、全設定・素材、native AE/UCRTを閉じる |
| OLMDistanceGradation | PF32 Powerのnative-UCRT 8固定セルは解決済み。一般Power/Bilateralへは未一般化 | 63組のpowf表を一般実装と混同しない。未登録引数でnative依存関数との差を測り、field/blur/writerと分離して復元 |
| OLMKiraKira | Mode3 Length代表4値×Rotation2値×3深度の24 retainedセルがexact。他source/geometry/依存関数へは未一般化 | まず異なるsourceと奇数geometryでpublic ownerを比較。相違がなければ長さ境界・他ray/modeの欠落へ進み、helper差とhost代替差を区別 |
| OLMRadialBlur | 固定component anchorsはexact。一般topologyの右端処理等は未証明 | 画像端に接する連結成分、穴、離れた島の同一typed入力で比較。component/field/sampler/writerの最初の差を閉じる |
| OLMSmoother | PF16実用geometryにClassic/Smart exact anchor。PF32非対応 | Windowsの深度・owner契約を確認後、透明/半透明とTolerance境界を比較。未対応のWindows仕様を不要に追加しない |
| OLMSmoother2 | 114 retainedケースを現行sourceで再生して一致。未到達65種は4×3の自然入力で到達し、両version×3深度の390ケースがローカルAEXと一致。保持した到達witnessは256種になった。奇数strideの型アクセスで見つけたUBはbyte copyで修正 | 分類番号の網羅を全演算・全設定の復元と混同しない。色・透明度・パラメータでscan/weightの状態を変え、最初の差を復元する。public owner/native AEとLUT構築の境界も残る |
| OLMToonDilate | corner-seedの3深度anchor。HD radius 2.01/5の過去campaignは未実行 | 小型でfractional radius/画像端/haloを比較して意味を復元後、HD性能とnative ROIを確認。遅さ・未実行を数値不一致と混同しない |

全10本に共通して、custom UIのEVENT/UPDATE、動的ラベル・preview・操作、
ROI/downsample・色管理・素材解釈も機能互換の残件に含む。数値kernelの完了で代用しない。

## 実行順序

1. 現行sourceと証拠のbindingを監査し、既存回帰を実行する。テスト失敗は数値差と
   証拠・環境の問題に分類する。過去の一括PASSをそのまま現行PASSにしない。
2. OLMColorKeyのpublic Thin+Blurを最初の解析対象とする。機能欠落とparameterの
   証拠欠落が明確なので、元の処理の復元が互換性へ直接つながる。
3. OLMSmoother2の現行分類再生と未到達分岐を調べる。近似が残るというコメントと
   実際のcounterexampleを区別し、実証された最初の差だけを修正する。
4. DirectionalBlur Dual、RadialBlur topology、KiraKira一般入力を順に比較する。
   同時に全経路のentrypointを掘り直さず、差のある最初の境界までに絞る。
5. UCRT/OpenCV等の依存先復元と欠落モード、全10本のpublic UI/host経路を閉じる。
6. 源流AEXとsource・build・installed bundleをbindしたnative両ホスト比較を行う。
   同じtyped入力worldから同じ出力worldになることを確認後、最終ファイルの差を調べる。

## 最初の作業: ColorKeyの合法Thin+Blur設定

実AEX parameter builderからThin Distance Typeのpublic 1..3の内部表現を確認する。
旧probeのゼロ初期化recordは使い回して合法設定の証拠にしない。
13×11のring/slope/islandを出発点に、distance typeの差が見える非飽和amountを選ぶ。
Thin=0、Blur=0の単独controlsを含め、Thin正負、Type 1/2/3、Replace off/onを
まずPF8で比較する。必要な分岐が観測できたらPF16/PF32と異なるgeometryへ拡張する。
比較はmatch mask→Thin matte→Blur field→Replace RGB→writerの順。

終了条件: 合法parameterが実AEX builderとMac public経路で同じ意味になり、
最初の不一致を原因に対応する一般処理で解消し、独立反例と既存exact回帰が通る。
内部Type 0の固定exactやテスト用adapterだけの一致では閉じない。
到達できない場合はbuilder/ABIの不足として記録し、数値本体を推測で変更しない。

## 一項目ごとに残す記録と解析の切替条件

記録: ID、分類、AEX/source/参照hash、host条件、最小入力、public設定と内部値、
実行command、最初の不一致位置・float bits、原因仮説、反証実験、修正箇所、
回帰結果、復元できた一般規則、残る範囲、次の一手、終了条件。
実行結果・disasmの事実と、そこからの推論を分ける。

二つの異なる仮説を反証しても新しい境界値が取れなければ、同じentrypoint追跡を
繰り返さず、最小入力・中間値採取・静的解析・native証拠のどれへ切り替えるか記録する。
この切替は解析手法の終了条件であり、互換性の完了や差分許容ではない。

元ソース相当の復元記録には、関数の役割、分岐と呼出し関係、データ配置、整数幅・
float精度、演算順、走査順、境界規則、依存先を含める。コードだけを残さない。

## この計画作成時の実行結果

- baseline: reports/compatibility_analysis_baseline_20261001.json。
- 新規generic gate: reports/olm_generic_beta_gate_20260930.json。
  52 PASS / 1 FAIL / 0 SKIP。FAILは性能reportのinvocation executable prefix binding。
  この結果は新しい画素不一致を示さず、性能証拠の再検証が未完である。
- 旧generic gateの依存hashは1箇所が現行と異なる（AE smoke runner）。
- KiraKira Mode3のoffline verifierは現行checkoutで成功。24既存セルの証拠検証であり、
  新しいWindows実行やnative AE比較を行ったという意味ではない。
- 計画作成時はSmoother2の191分類reportと現行sourceがhash不一致だった。
  その後114ケースを再生し、未到達65分類の390 AEX witnessを追加した。
  安全な型アクセスへ修正後もO2/ASan/UBSanで一致。過去captureのsource hashは
  書き換えず、新しい再生のbindingを別のvalidation reportへ記録した。

この文書は解析の実行計画。既存release gate、個別exact証拠、ledgerの禁止事項を
変更しない。実装変更と再検証は進捗記録に追記する。installed/native hostは別に確認する。
