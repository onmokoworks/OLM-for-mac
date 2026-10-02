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
| OLMColorKey | Thin公開216設定に加え、Around/Manhattan/Blur4＋Thinの2592設定を公開AEX Smart→Mac Classic/Smartでexact確認。Thin±4000は距離capを復元し公開制限を解消。旧workerの255 contextと未実装sinfを隔離 | Aroundを全合法Blur量0–4000・Type1/2/3へ一般化し、1列のThin/Blur距離workspace再利用とfloat slider materializationを復元。公開AEXの13530条件を現行Classic/Smartへ再生。Inside/Outsideも元のdouble sin曲線とmatched matte→writer→Keep-off subtractionを復元し、公開全合法Blur量・Type1/2/3・Thin組合せを一般化。11232条件の独立設定・geometry・toggle・極小float witnessを保持。SSE invalid phaseの負NaNと整数CVTTSS2SIも再現。typed PF16高値/PF32 HDR・signed RGB/alpha・負ゼロは1760条件のmatched matte/writerを復元し公開cmdでexact。RGB palette count1/2/4/5/24/25・末尾/重複/per-color/Replace216条件もexact。Lab76/94成分別はin-place offset、Lab76の成分別epsilon倍率、scalarの別々のFLOAT32積と加算、Lab94成分別の加算→倍率を復元し本番へ一般化。独立色順序432＋隣接FLOAT32境界162＋従来測定396条件を両cmd/sanitizerでexact再生し従来108差分を解消。新しい1×1/1列/1行/17×11のThin/Blur合成144条件も公開AEX exact。固定workerのLab94 scalar36条件はatan2f未実装で失敗する。外部source/workerを保持した一時コピーへhost f32 atan2を追加し、従来396行で出力を校正。scalar/DOUBLE境界1224行を両cmd/sanitizerでexact再生し、DOUBLE→FLOAT32丸めの102差分を本番修正。独立color/HDR/palette576条件でRGB scalar距離、HSVの逆数乗算、PF8 source正規化、整数Premultipliedの中間非量子化、HSV unordered分岐を復元し16差分を解消。本番両cmd/sanitizer2304再生と元AEX再取得576条件は全exact（528固定worker、48 controlled Lab94）。PF32 alpha_hdr/combinedはHDRとsigned alphaの混在を含む。さらにRGB/HSV/YUV/YCrCbの144族で隣接FLOAT32境界とDOUBLE値1728条件を測定し、YUV/YCrCbのFLOAT32許容幅で192差分を解消。有限最大PF32入力512条件のunordered判定64差分と、通常UI範囲外の第3threshold診断24差分も復元。本番2348行9392再生と280差分の元AEX再取得は両cmd exact。実Windows UCRTでのatan2fとnative AEは未検証。全color/threshold/HDR、native AEとROI/downsampleを閉じる |
| OLMDirectionalBlur | 固定小数getter47と行範囲を復元。一般機能180件のClassic/Smart出力一致に加え、PF32のHDR・signed RGB/alpha・float境界120件も両公開cmdでAEX raw exact。PF32は有限値を受け付ける。PF16一般機能は32768超のsource/Layer144とLayerなし・生成Noise72条件のraw uint16 exactを根拠にSDR制限を解除し、深度別Layer値から散布予算を求める。neutralも3 geometry・4高値profile＋SDR・Front/Back/Dual・Gain 0/1/2.25・retained Backの150条件を根拠にSDR検査を解除。公開cmdの600再生がAEX exact。追加予算とatomic/ROIを適用 | 独立Layerの値3は同寸法・原点0の120条件を一般公開経路へ復元しClassic/Smart exact。native/Macの有効choices2・labels3は保持し、値1/2は選択Layerを使わない。HDR/signed Layer180条件はCVTTSS2SIの範囲外整数変換を復元しexact。異寸法Layer288とNone Layer54は元AEXのfield未生成／Noise無効規則を復元し両公開cmdでexact。非zero原点Layerと通常UI/保存stateの到達性は残る。任意float・非有限値、downsample、旧個別owner契約、全設定、native AE/UCRT/installedを閉じる。元AEX負Offsetの範囲外読取りは未閉鎖境界。PF32 Layerは絶対premultiplied channel積から散布上限を見積もり、720×480のSDR/HDR/signed Layer3条件で旧full-row拒否を解消。PF16も1/32768で正規化した積上限を使い、最大uint16 Layerによる約4倍の散布を予算へ反映。実AEで非SDR PF16入力が生じるかは未確認。独立typed source/Layer・17×11/61×47・Front31/Back47/Dual31+47の216条件は公開Smart対Mac Classic/Smartで全exact。固定workerのmanifestは原点fieldを拒否するため、非zero原点は公開数値検証の未達として保持。依然残る保守的予算と大画像/強設定の拒否を全互換達成とは扱わない |
| OLMDistanceGradation | PF32 Powerのnative-UCRT 8固定セルは解決済み。一般Power/Bilateralへは未一般化 | 63組のpowf表を一般実装と混同しない。未登録引数でnative依存関数との差を測り、field/blur/writerと分離して復元 |
| OLMKiraKira | Mode3 Length代表4値×Rotation2値×3深度の24 retainedセルがexact。他source/geometry/依存関数へは未一般化 | まず異なるsourceと奇数geometryでpublic ownerを比較。相違がなければ長さ境界・他ray/modeの欠落へ進み、helper差とhost代替差を区別 |
| OLMRadialBlur | AD→FLOAT32、Zoom PF8/PF32 writer・正負alpha・ゼロseed・最大alpha、Rotation Gaussian/final/neutral/両Edge、領域run境界と両fade接続を復元。Sizeの合法有限0–100、Noiseとの係数積、独立したFade用Size係数を共通経路へ接続。元のFLOAT32正規化→DOUBLE比較によるSize enabledも復元。Noiseの有限0–100とゼロ時Type2も既存profileへ接続。 Quality有限1–50・Type1/2のSeed整数1–1000とThickness有限1–100も共通経路へ接続。元の逆数乗算による格子サイズに加え、QualityのFLOAT32逆数/radianとRotationの制御値換算、ZoomのStrength表選択を復元。 Gainの有限0–10を共通経路へ接続。RotationのNoise座標も元のFLOAT32逆数乗算へ復元。 両Strengthの整数0–2000を共通経路へ接続。ZoomのStrength表を元のvector＋scalar-tail B680へ戻し、Rotationの3000打切りを係数乗算前へ復元。両Strength・両Offset・両Fadeが全0の元入力コピーも復元。 全0・Noise Type1/2のコピーはBlur処理の制限から分離し、PF16全raw値とPF32 HDR/非有限/NaN payloadをbyte単位で保持。中心・Border・Ratio/Angle・Quality/Gain/Size/NoiseのBlur専用制限とSmartのBlur予算を通さない。正の同寸法full-frame、独立payloadと有効byte strideは確認する。現行694条件は全exact・差分0・拒否0 | 整数Size1–100、小数とSize/Noise/Fade/Seed/楕円の独立560条件は全exact（旧542拒否）。微小Size・閾値のFLOAT32/DOUBLE隣接値とNoise/両Fadeの720条件も全exact（中間候補381差分を解消）。Noise整数1–100・小数・極小値と両Fade/Sizeの952条件も全exact（旧932拒否）。従来独立1855を保持し候補14004公開再生が一致。元Noise正規化とSize/Noise合成の16 map、各面4080語も一致。 Seed/Thickness独立1532条件も全exact（旧1531拒否）。既存独立2807を保持し、厳密/通常コンパイル設定の30198本番公開再生が一致。初期化済み格子20条件/2080語も一致し、直接除算の寸法差16条件を分離。 Quality整数/小数/隣接値・Noise/Size/両Fade/Offset/楕円/旧profileの2262条件も全exact。従来5033条件を保持し3 build/両cmdの43770本番公開再生が一致。元builder/constructorとZoom/Rotation制御値60条件も照合。 Gain整数0–10・小数/隣接値/極小値/負ゼロとNoise/Size/両Fade/Offset/楕円の1140条件も全raw exact。従来7295条件を保持し3 build/両cmdの50610本番再生が一致。Gainの元getter64条件、Noiseサンプラーleaf1936条件も一致。最初の32出力差分とleaf249語の差分を元の逆数乗算で解消。 Strength境界・内側/両側・Quality/Noise/Size/Fade/小画像と全0コピーの1128条件も全raw exact。従来8435条件を保持し3 build/両cmdの57378本番再生が一致。全Strength1–2000表の2001000語、元設定80条件、自然2画像の全所有面も一致。過去に80語差のあったStrength290の同一入力・同一設定は保存native-UCRT出力hashに本番6経路で一致した。新しいWindows実行や一般UCRTの復元を主張しない。 全0コピーの独立82条件（HD/UHD・幅4097・高値/全uint8/uint16・float exponent/NaN bit/複合controls）を元公開AEXと照合し、従来9563条件と合わせ3 build/両cmdで57870本番再生が一致。odd byte stride492再生と不正world84検査も通過。参照hostの寸法/arenaだけ広げた別buildは元AEX/ABI/Math/copy callbackを保持し、native Windows/AEの証明とは扱わない。元enabled block20/SDK40回とdisabled自然factor20 map・700語/SDK120回を照合。自然Zoom3＋複合2画像のfield2567099語は一致。別の自然1画像は既知のlength19/index17 controlled expf差に由来するnormalized27語が未解決。本番scalar policyは保持。任意入力/複合設定、他のNoise/Layer/Brightness/Strength/Offset交差、scalar fade3語・native ISA/RCPPS/UCRT、allocator末尾、Rotation追加半径行、native両AE/UI/保存/ROI/downsampleと全10本は未完 |
| OLMSmoother | PF16実用geometryにClassic/Smart exact anchor。PF32非対応 | Windowsの深度・owner契約を確認後、透明/半透明とTolerance境界を比較。未対応のWindows仕様を不要に追加しない |
| OLMSmoother2 | 114 retainedケースを現行sourceで再生して一致。未到達65種は4×3の自然入力で到達し、両version×3深度の390ケースがローカルAEXと一致。保持した到達witnessは256種になった。奇数strideの型アクセスで見つけたUBはbyte copyで修正。色・半透明の3200条件と7×9/17×19の独立pattern144条件も内部classifier/workerの出力・実dispatchが一致。Smoothness=0の384条件はclass由来の理論indexと実行数を区別して閉鎖。公開AEX resident Smartで1×1/1行/1列を含む252条件を取得し、Macのbeta-only最小16×16制限による216拒否を確認。正の寸法を共通処理へ渡す規則に変更し、252条件を公開Mac経路のO2/ASan/UBSanでexact再生。公開Key/Invert/Gamma1260条件でGamma Colors count 0の252拒否を復元。typed高値432条件ではPF16 writerの32768打切り86差分を、元のMULSS/ADDSS→CVTTSS2SI RAX→AX保存へ復元。1692条件3384再生と元AEXの本番再取得が全exact。HDR＋Gamma合成840条件は一致。PF32色判定境界1440条件でv2 Gamma Colorsだけ16差分を確認し、公開a9c0のinverse LUT分岐へ復元。2280条件4560再生と元AEXの再取得が全exact | 分類番号の網羅を全演算・全設定の復元と混同しない。公開ownerのKey/Gamma組合せは独立15 stateであり、全直積ではない。HDRとGammaの合成、任意float・scan長・境界を拡張する。内部v2 captured LUTと公開builder/host参照を分け、native Windows UCRT/AEとLUT構築の境界も閉じる |
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
