# 互換性復元: 2026-10-01

Goal: `docs/COMPATIBILITY_ANALYSIS_PLAN_JA.md` に沿い、同じ機能・設定・入力から
Windows版とビット単位で同じ出力を得る。現時点でGoalは未達成。

## CK-COMPOSITION-001: 合法Thin Distance Type

分類: parameter証拠の欠落を一部解消。typed workerとMac coreの実差分を検出。

実行:

```sh
python3 tools/emulation/probe_olmcolorkey_legal_composition_20261001.py --popup-only
python3 tools/emulation/probe_olmcolorkey_legal_composition_20261001.py --all-depths
```

事実:

- actual AEX `FUN_18000e050` をguest実行。disk ID `0x0e`をlookupし、checkoutで
  public popup 1/2/3を取得すると、実guestのcopy/checkin経路は同じ内部値1/2/3を返す。
  これは実materializer全体の実行証拠ではない。
- `FUN_18000a3d0`のdecomp/disasmは同readerをdisk ID `0x0e`とrecord `+0x2c`で呼ぶ。
  workerも同offsetの1/2/3で距離生成先を分岐する。
- 13×11のopaque ring/slope/island、2 key、padding8。Thin -1/0/+1、Blur0/4、
  Thin Type1/2/3、Replace off/on、PF8/PF16/PF32の108ケースを測定。
- **56/108 exact、52/108 mismatch**。PF8のみでは16/36 exact。
  数値差はレポートにそのまま保存し、probeの正常終了をexact完了とは扱わない。
- `none`/`blur4`の36 controlsは全てexact。Thin単独ですでに差がある。
  Replace off/on双方で差を再現しており、Replaceだけを原因とする説明は不足。
- PF8/PF16の+1 ThinはType1/2/3すべて不一致。PF32 +1のType1/3は一致するが
  Type2は不一致。負ThinはType2/3が全深度で不一致。
- 各実行はnative worker dispatch/checkout/正常return/paddingを確認した。
  元helperの「1画素だけがkey」「Thinなし」のfixture専用assertionはこの入力には
  適用せず、代わりに一般の実行gateと直接出力比較を使う。

証拠: `reports/colorkey_legal_composition_20261001.json`。
AEX/source/probe/直接依存helperのhashを記録。

境界: actual AEX typed workerとMac `RenderWorldDirect`の比較。
AEX full parameter materializerは宣言recordで置換。Mac public admissionもbypass。
exported EffectMain owner、native AE、installed binaryのexactを主張しない。
合法popupの差分が解消するまで、productionのThin+Blur拒否を維持する。

推論:

- 最初に調べる箇所はThinの距離planeと閾値判定。現在のMac実装はColor Keep時に
  整数depthの距離scaleを1へ切り替え、Type2には+2の閾値補正を付ける。
  元の内部Type0/saturated fixtureからの一般化が合法popupで成立するか疑わしい。
- これは原因候補。補正を削除すれば完全互換になるとはまだ証明していない。

次の実験: guest距離plane→Thin matte→Blur fieldを採取し、同じMac中間値と比較。
整数depthの255 metric、Type2の境界、PF32の合成を別々に反証する。
終了条件: 原因に対応する一般処理を復元し、別geometry/境界値の反例と既存回帰がexact、
その後合法parameter builderを通るpublic Classic/Smartで一致を確認する。

## CK-COMPOSITION-002: 閾値境界による反証と境界planeの復元

事実:

- 一時sourceで整数depthの正Thin scaleを255にすると108セル中80 exact。
  Color Keep/Type2の+2補正を外すと84 exact。負Thinをchessboardへ固定する仮説は
  この108セルでは108 exactだが、それだけでは一般アルゴリズムを復元したことにならない。
- 独立にThin 0/±1/±4/±255/±256、Blur0/4、Type1/2/3、全深度の162セルを測定。
  ±255/256はvisible UI範囲外だが、PARAMS_SETUPの合法slider範囲±4000内。
  現行coreは74 exact。chessboard仮説は138 exactで、負Thin -4/-255の整数depthに
  24反例が残る。この仮説の一般化は棄却した。
- guestのfloat distance worldを採取。PF8/PF16は0/255/510/...、PF32は0/1/2/...。
  Type2ではL1、Type3ではsqrtを含む距離値が現れる。負Thinでも実AEXはpopupで
  距離生成先を分岐するので、popupを無視する一般化はしない。
- workerのdecomp/disasmでは、負Thinは非match画素の最近傍距離ではなく、
  先に8近傍のmatched境界を生成し、選択metricで距離を求める。
  消去条件はdistance < abs(amount)。distance == abs(amount)は保持する。
  正Thinはdistance <= amountで拡張する。
- 一時kernelを「matched boundary→選択metric→depth scale→厳密な不等号」へ
  修正したreplayは独立162セルすべてraw exact。座標や期待wordの補正は行っていない。
  現行coreを同時再生し、既存162セルのsource/output hash一致を要求した。

証拠:

- reports/colorkey_composition_hypotheses_20261001.json
- reports/colorkey_thin_metric_boundaries_20261001.json
- reports/colorkey_thin_boundary_replay_20261001.json

境界: いずれもopaque 13×11 two-key sourceのcore比較。一時sourceの実験であり、
production、installed binary、public Thin+Blur admissionはまだ変更していない。
別source/geometry、mixed-alpha、public materializer経路を閉じるまで
この162 exactを完全互換や一般入力exactとして扱わない。

次の実験: 同じ一般kernelで画像端に接する別geometryとmixed-alphaを比較する。
その後productionへ原因に対応する修正を入れ、合法parameterを通るpublic経路と
既存安全性・exact回帰を検証する。内部Type0 witnessの過去PASSは履歴として保持し、
合法Type2等の証拠に流用しない。

## CK-COMPOSITION-003: 通常ホスト条件のThin復元と本番反映

分類: ホスト条件の取り違えを修正し、合法Thin単独の公開経路を拡張検証。
CK-COMPOSITION-001/002の255距離尺度は通常ホストの仕様という解釈を撤回する。
過去の測定値はそのまま残し、合成contextの結果として扱う。

- 旧worker probeはcontext `+0x120/+0x128`を整数depthで255、floatで1に設定する。
  AEX distance generatorはこの2値を読む。通常のPF_InDataではdownsampleの
  x/y numeratorであり、full-resolutionホストは両方1。
  255はdepth由来の尺度ではなく、probeが指定したホスト条件だった。
- builderを差し替えないexported AEX Smart CPU ownerで合法slider/popupを指定すると、
  255仮説の一時kernelは132/216 exactに留まった。単位距離へ修正すると216/216。
  full builderがpublic Thin Type1/2/3をそのまま使うこともparameter_valuesで確認。
- 負Thinは8近傍matched境界への距離を使い、distance < abs(amount)だけを消去する。
  正Thinはdistance <= amountで拡張する。全depthで距離単位は通常ホストのpixel単位。
- native matched matteはsource alphaが0の画素をseedにしない。
  Thin拡張後もsource alpha0は0のままで、後続Blurのseedにしない。
- native final callbacks PF8 `0x1800029b0` / PF16 `0x1800035b0` /
  PF32 `0x180004170`は、Color Keep offでsource alphaから最終matte alphaを引く。
  PF8/PF16はal/ax幅、PF32はsubss。Blurより前にmaskだけ反転するとfloatの丸めが変わる。
- これらの一般処理をproduction RenderTypedへ反映。Color Keep offは、Replaceを無効にした
  matched matteのThin処理を完了してからsource alphaを引く。座標ごとの期待値補正はしない。
  Blur単独の既存owner処理は今回の変更対象から外した。公開Thin+Blur admissionは閉じたまま。

公開比較は端に接するring・穴・2 keys、opaque/zero-alpha/半透明、17×15/9×7の
3入力 × Color Keep off/on × Type1/2/3 × Thin±1/±4 × PF8/PF16/PF32 = 216設定。
各設定のWindows公開Smart出力に対し、Mac実SDK Classic/Smart両経路がraw exact。
元source `290e150d`を同じ216設定で再生すると97 exact、本番修正後は216 exact。
Mac入力不変・output padding不変・suite/checkinの収支も各実行で確認する。
実行時に供給したworkerのSHAを記録し、過去のpinned workerやnative AEの証拠は継承しない。

証拠と回帰:

- `reports/colorkey_thin_public_owner_production_20261001.json`
- `reports/colorkey_thin_production_validation_20261001.json`
- `tests/test_olmcolorkey_thin_public_owner_20261001.py` は保持した216 Windows witnessを
  現行Mac Classic/Smartで再生する。AEX実体やworkerがなくても回帰可能。
- 既存公開126出力、generic pixel-local、pairwise/ASan/UBSan、ROI/tileを再検証。
- 旧source-bound atomic testは元source/現行とも `pass=0 positives=0 negatives=0`で失敗。
  入力の1-byte変更を拒否する旧期待とgeneric admissionの不整合であり、今回の差分ではない。
  このtestをPASSに書き換えていない。

通常ホストの独立worker/core比較はmixed-alpha 17×15の60セルずつKeep on/offで実施。
本番は双方51/60 exact。Thin/Blurの単独controlsを含む。
残りはBlur側の255尺度とalpha0 seed処理。両方を通常ホスト条件へ直した一時kernelは
双方60/60だが、これだけで公開compositionを開かない。
全Blur経路へ一括適用した別案は既存公開126出力の54セルに回帰したため棄却。
次は合法Around/Type2/Blur4の公開builder経路で、この狭い復元処理を独立geometryに
検証する。必要なら既存公開Blurの条件分岐を復元してから一般化する。

境界: 216セルはRGB、threshold0、premultiplied off、Replace off、通常full-frameに限定。
Thin全範囲・全color space・Replace/premultiplied・native Windows/Mac AE・installed bundle・
downsample/ROIは未完了。完全互換Goalは引き続きactive。

## CK-COMPOSITION-004: 正弦依存先・RGB処理順・1列走査の復元

分類: 合成ホストに加え、旧import stubによる誤ったoracleを検出・隔離。
CK-COMPOSITION-001/002/003のworker/core Blur一致は数値のWindows仕様証拠として使用しない。
Thin単独の公開216設定は別のexported workerによる証拠であり、この問題に依存しない。

事実:

- `aex_loader.py`のmath importsにはdouble `sin`があるがfloat `sinf`がない。
  未実装importはRAX=0で戻り、XMM0を変更しない。native Around callbackが呼ぶ
  `sinf`は恒等関数として観測され、旧linear/overshoot分岐につながった。
  `probe_olmcolorkey_composition_generalization_20261001.py`は今後、未実装sinfがあれば
  通常の実行を拒否する。明示的な履歴stub実行もvalid_numerical_oracle=falseと記録。
  過去reportの値を書き換えて数学依存先が実装されていたことにはしない。
- native `FUN_180005550`のAround曲線はFLOAT32 pi/2/amount、signed phase、
  sinf、+1、*0.5の順。`DAT_18001f6b0`をPEから読むと1.5707963705062866。
  公開AEX ownerと比較し、距離0は0.5、amount以上はinside1/outside0、間はこの曲線に復元。
- native PF8 `FUN_1800085b0`、PF16 `FUN_180008320`はalpha*weightを整数に切り捨てる。
  ceilを使う一時案は整数depthに反例が残り棄却。PF32はfloat multiplyのまま。
  Keep offはその後source alpha - final matte alpha。
- ReplaceはThinより先。負Thinのalpha-only消去後もRGBは残る。
  正Thinがゼロmatteに拡張するとsource RGBAをコピーし、先行Replace RGBを上書きする。
  matched_indexとthin_expandedの一般処理でこの順序を再現。固定座標補正は使用しない。
- 1×7 opaque 2-key/Thin -4/Type1で追加反例。nativeの距離planeを直接採取すると
  `[2,1,2,2,2,1,2]`。Type2/3には同じ反例がない。
  native Type1は幅1でも左右端を走査し、float pixel pointer x=±1が隣接rowへaliasする。
  forward/reverseの順序を、ゼロscratchと範囲付きreadを持つ配列で再現した。
  PEの距離cap定数は4000、最初の非seedは3999。AEX外の未定義メモリreadはMacへ移植しない。

本番変更: Around public2 / Manhattan public2 / Blur4の曲線・単位距離・alpha0 seedを
復元し、Thin public Type1/2/3・visible範囲±100とのcompositionをpublic admissionへ追加。
他のBlur設定は未解決の旧stub依存分岐を含むので、今回の証拠を流用しない。

公開owner検証:

- 3入力（端に接するring/穴、opaque、zero-alpha/半透明、17×15/9×7）× Keep2 ×
  Premultiplied2 × Replace2 × Thin0/±1/±4 × Thin Type1/2/3 × depth3 = 1080設定。
  一時案は954 exact。RGB順序を復元後、本番1080 exact。
- 1×1 opaque、1×7 opaque、9×1 mixed-zero × 同toggle/Type/depth × Thin0/±1/±4/±100 =
  1512設定。一時案は1464 exact（1列・Type1に48反例）。走査復元後、本番1512 exact。
- 両集合で、Windows exported Smart CPU ownerのtyped raw output hashに対して
  Mac実SDK Classic/Smart両方が全設定で一致。実builderのslider/popup/toggle、suite収支、
  入力不変とoutput padding不変も各実行で検証。

証拠:

- `reports/colorkey_around_composition_production_20261001.json`
- `reports/colorkey_around_composition_boundary_production_20261001.json`
- `reports/colorkey_around_composition_validation_20261001.json`に現行sourceの6検証とbindingを記録。
- `tests/test_olmcolorkey_around_composition_owner_20261001.py`は全2592 Windows witnessを
  現行Mac両公開経路へ再生。単画素/1列の54設定を両公開経路でASan/UBSanに通す。
  raw画像や第三者AEXは保管・Pushしない。
- 既存公開126出力、Thin公開216設定、generic pixel-local、pairwise/ASan/UBSan、ROI/tileもPASS。
  旧public composition拒否の2期待だけを新しいadmissionの期待へ変更。

残る境界: native Windows/Mac AE、installed bundle、他のBlur amount/distance/direction、
全color space・threshold・25 keys・HDR、Thin合法範囲±4000、downsample/ROIは未完了。
次は同じ公開ownerを用いてAroundの残りamountと他のdirection/typeを比較し、旧import stubに
依存した分岐・記録を区別する。完全互換Goalはactiveのまま。

## CK-RANGE-005: Thin合法範囲±4000と距離cap

分類: visible UI範囲±100を合法slider範囲±4000と取り違えた公開制限を解消。
範囲だけを広げた一時案は792設定中738 exact。空/solid matteのType1/2で54反例。

native L1/Chessboard生成（PF16 `FUN_1800058a0` / `FUN_1800066f0`、typed同等関数）は
距離cap=4000を使い、最初の非seedをcap-1=3999に初期化する。空seedの場合にも同じ。
Macは無限大1e9を使っていたので、正Thin3999/4000、負Thin-4000で異なるmatteになった。
L1/Chessboardの初期planeを4000、非seedの先頭を3999へ戻し、同じ一般距離走査を使用。
Euclideanへこのcapを流用しない。1列Type1の別走査は前項の復元を維持する。

Thin単独、および復元済みAround/Manhattan/Blur4とのcompositionを合法範囲±4000で
public admissionへ追加。PARAMS_SETUPは元々valid min/max±4000なのでUI定義は変更しない。
拒否境界の回帰は101から4001へ移す。

検証:

- 空matte/solid matteの1×1/5×4、Keep off/on、Type1/2/3、全depth、
  Thin -4000/-3999/-256/-255/-101/0/+101/+255/+256/+3999/+4000。
  Blur4の792設定は修正後792 exact。Thin単独の同じ792設定も792 exact。
- 同じ極値に17×15/9×7の端・穴・alpha0・半透明入力を加え、Premultiplied/Replace
  off/onも加えた5544設定は全てWindows公開Smart→Mac Classic/Smartでraw exact。
- `reports/colorkey_thin_legal_range_generalization_production_20261001.json`
- `reports/colorkey_thin_legal_range_no_blur_production_20261001.json`
- `reports/colorkey_thin_legal_range_validation_20261001.json`
- Around公開回帰にこの2集合を追加。先行2592設定も残し、保持した8928 witnessを
  現行Mac両公開経路へ再生する。先行ASan/UBSan54設定、公開126/Thin216、generic/ROIも再検証。

境界: 11個のslider値と復元した一般distance処理の根拠。全設定・全画像・native AEの
完了証拠にはしない。他Blur設定、全color space/threshold/25 keys、HDR、ROI/downsample、
installed/native hostは残る。次は他Blur設定の旧stub依存分岐を公開ownerで調べる。

## BASELINE-001: 検証証拠の環境差

Thin修正後のgeneric gateも52 PASS/1 FAIL/0 SKIP（既存baselineと同じ）。性能レポートの実行prefixはPython 3.14.6をbindし、
現行実行は3.14.7。verifierがbindingを拒否した。記録を現在のhashへ書き換えるだけで
過去性能の実行時証拠にしない。必要な性能再測定を別項目として残す。

## SM2-REACH-006: 未到達65分類の自然入力と型アクセス

既存114ケースを現行sourceで再生し、出力raw hashとswitch histogramが114/114一致。
その191 indexを除いた65 indexは不一致数でも到達不能数でもなかった。

`FUN_18000c280`の8ビットは中心と8近傍のedge比較を表す。中心を不透明黒にし、
bit=0の近傍を不透明白、bit=1を黒にすると、各bitを独立に作れる。4×3の中心(1,1)では
TOP-RIGHTの特別なguard `x+1 < w-1`も開く。これは全分類に使える小型構成であり、
個々のindexについて最小geometryを証明したという意味ではない。

- 65 index × version1/2 × PF8/PF16/PF32 = 390ケース。
- class planeを注入せず、実AEX classifierとtyped workerを実行。
  390/390で指定した中心indexへ到達し、Mac output/paddingと全画面histogramが一致。
- 実行importは実装済みVCOMPの5種のみ。未実装importを拒否する監査を追加。
  この集合では数学importを実行していない。
- LUTは保持済み10,000要素を使用し、decode/encode hashを記録。
  public parameter builder/Windows AE/native UCRTの新しい証拠ではない。
- `reports/olmsmoother2_switch_reachability_20261001.json`は修正前source
  `b7420807a37ce318b6eedc6285af5735cb344020a84ed2ef869cbb5b448d5ae1`で採った
  AEX比較の記録。過去のbindingは維持する。

ASan/UBSanでPF16のrowbytes=39を再生すると、source line354の構造体loadが
alignment violationになった。数値差ではなく、byte strideを型pointerで読むMac側UB。
入力を整列したlocal pixelへ`memcpy`してから既存loadを実行し、出力も同じ型のlocal
pixelからbyte copyで格納する。分類・丸め・重みの演算とpremultiply診断を維持する。

修正後は114 retainedケースをO2で再生し、新規390ケースをO2とASan/UBSanの両方で
再生して全raw hash/histogramが一致。source input不変と行paddingも確認。
再生結果・現行source hashは別のvalidation reportにbindし、AEX captureのhashを
現在のhashへ付け替えない。

`reports/olmsmoother2_switch_reachability_validation_20261001.json`へ上記再生を記録。
default beta lane 4テスト、Gamma Colors 3テスト、ROI full-frame 3テストも修正後PASS。

この集合と旧191 indexのwitnessを合わせて256 indexへ到達する証拠が揃った。
全scan距離、weight状態、Gamma/key、任意の色/alpha/設定を覆う証明ではない。
分類番号の網羅だけで全分岐の元ソース復元やWindows完全互換を宣言しない。
installed bundle/native AEは更新・再比較していない。完全互換Goalはactive。

追加検証で既存Classic深度の文字列検査がKiraKiraでFAIL。HEADでも同じ条件がFAILし、
`Render`から`ValidateWorldPair`/`GetKiraPixelFormats`への呼び出しを検査が認識しない。
今回のSmoother2画素差とは分け、検査自体を未対応として残す。

## DB-ANGLE-007: 公開builderの角度端数を復元

小型の独自入力7×5（alpha0/半透明/不透明混在）と9×7（不透明）を生成し、
同じARGB8/16/floatのbytesをWindows AEX公開Smart ownerとMac dispatcherへ渡した。
ノイズ・Fade・Sharp・Size Variationなし。0/45/90度のFront4/Back3、Front4のみ、
Back3のみは54/54 exact。実際に出力が入力と異なり、54出力hashも全て異なる。

−45/17.25/123.5度、両側strength 1/1、7/11、31/17では18/54 exact。
17.25/123.5度の36ケースは全depth・両sourceで異なる。
`FUN_180006c50` / asm `0x180006cd0`のsigned word loadはPF_ParamDef+0x3aを読む。
WindowsはAngleの16.16上位16bitを符号付き整数として取り、端数を使用しない。
Mac `InfoFromParams`は65536.0で割って端数を保持していた。

角度をwhole-degreeへ置いた独立候補再生は54/54 exact。これを根拠にMacの実getterを
signed upper-wordの復元へ変更。符号付きdivisionでは負の端数を0へ切り捨てるため、
unsigned shift後に16bit符号を復元する。17.25→17、123.5→123、−17.25→−18、
−0.25→−1、0.25→0。回転・field・writerの画素演算を変更しない。

修正後は実PF_ParamDef→InfoFromParams→本番dispatcherを使い、54 neutral controls、
54 positive-boundary、54 signed-boundaryの162ケースが公開AEXとraw exact。
全部をO2およびASan/UBSanでも再生し、input不変・padding保持と同じraw hashを確認。
既存generic Back/Dual Classic/Smart EffectMain、ROI、operation/memory budgetもPASS。

公開workerのrender-png CLIはtyped Angleを構成できず、角度overrideで入力エラーに
なった。resident v4 payloadの`angle`型を使用し、同一typed raw worldを直接渡して解消。
CLIのエラーをプラグインの画素不一致には分類しない。

修正前のowner/boundary reportを保持し、修正後の3 reportとvalidationを別に保存。
`reports/directionalblur_general_input_validation_20261001.json`にsource/probe/core/workerと
実行をbindする。第三者AEXやnative raw imageはPushしない。

境界: この162ケースのnative側はローカルAEX emulation。Windows AE/native UCRT、
installed bundle、Mac公開checkoutの新しいWindows対比較は未完。
Mac EffectMainの既存別テストを今回の162ケースの公開exact証拠へ流用しない。
Size/Sharp/Noiseの上位word読取りもstaticに見えるが、動的witnessなしに変更しない。
次は同じbuilderの固定小数と一般Fade/Noise経路を調べる。完全互換Goalはactive。

## DB-FIXED-PARTITION-008: 固定小数getterと等分行範囲を復元

公開builder `FUN_180006c50`を実checkout/checkin callbackで実行し、Size Variation、
Front/Back Sharp Tail、Noise Variation、Offsetの47境界値を調べた。14 checkoutと
14 checkinを確認し、実行importはmemsetのみ。手でcontext値を注入した比較ではない。
各値とwhole-number独立controlの全context hashが一致する。

Mac旧getterは19/47一致。WindowsはAngleと同様に16.16上位wordを符号付き整数として
読む。percentの0.75→0、25.75→25、Offsetの−0.25→−1、−17.25→−18を復元し、
実PF_ParamDef→InfoFromParamsで47/47一致。固定小数の一般decodeのみ変更した。

同じtyped raw入力を公開AEX Smart ownerとMacへ渡す45件は修正前14 exact、
24 feature rejection、7 numeric difference。getter修正後37 exact、8 feature rejection、
0 numeric difference。深度16/32で非ゼロSize/Sharp/Noiseを本番dispatcherが拒否する
機能不足は残る。解析専用の明示的core bypassを本番admissionとは分けて記録する。

7×5、9×7、37×29の135件へ広げると、getter修正後のcore候補は102 exact、33 numeric
差。全33差は37×29のgeneric経路。native PF8/PF16/PF32 ownerはmin(height,32)個の
workerへ整数商の等分範囲を配り、余り行を処理しない。omp_get_max_threadsの戻り値は
使用しない。例では回転work height51のうち32行を処理し、19行はpreseeded sourceを保持。
Mac generic wrapperの全行上書き指定を外し、既存coreの等分処理へ戻す。
画素field/rotate/writeback演算や座標別の例外は追加しない。

修正後の解析候補は135/135 raw exact。本番dispatcherでは同集合の111件exactと
24件の機能拒否を確認した。通常の45件も37 exact/8拒否であり、公開135件の完全一致
とは主張しない。47 getterと135候補をO2、ASan/UBSanで再生し、input不変、padding保持、
拒否時の出力不変を確認。既存角度162件も両buildで全hash一致。

既存Back/Dual Classic/Smart EffectMain、deep geometry、ROI、Smart cleanup atomic
17件がPASS。Smart cleanupの疑似SDKに欠けていたPF_Fixed型を補った。
修正前後の5 normalized reportを保持し、historical source hashを付け替えない。
現行source・依存・再生結果はfixed_getter_validation reportへ別にbindする。

native側はローカルAEX emulationであり、Windows AE/native UCRT、installed bundle、
新規Mac公開checkout対Windows比較は未完。全リポジトリgateは再実行していない。
次は深度16/32の非ゼロSize/Sharp/Noise公開経路を、追加witnessと安全性契約に基づき
復元する。Fade、Noise Layer、HDR、大画像、ROI/downsampleも残る。完全互換Goalはactive。

## DB-GENERAL-009: 深度の一般機能候補と負Offsetの安全性境界

本番sourceを変更せず、実PF_ParamDef→InfoFromParamsを使う解析用harnessを拡張。
Windows公開Smart ownerへ同じtyped ARGB16/float bytesを渡し、候補coreのraw hashを比較。
Front7のみ・Back11のみ・Dual7/11、角度123.5/−17.25/17.25、独自mixed-alphaの
1×9、9×7、37×29を使う。Size37.75、Front Sharp31.75、Back Sharp63.75、Noise73.75の
単独と組合せ、Noise Type2/Seed7/Offset−17.25、Fade5/7、全percent100/Fade100/
Seed1000/Offset32767、Gain2.25/Thickness1.25等10組を両depthへ渡した。
全値を公開controlsの合法範囲内で選び、getterが端数を落とす挙動もそのまま使う。

180/180が公開AEX出力とbit exact。本番dispatcherでは180件とも拒否（516）し、
明示的な解析core bypass route1001で得た結果である。公開機能復元とは扱わない。
O2とASan/UBSanで全180 native hashを再生し、input不変・行padding保持を確認。
この証拠はサイズ・設定tupleのwhitelist追加を正当化するためではなく、一般coreと
公開admission/Smart契約の差を切り分けるために残す。

追加の負Offset安全性診断12件では、−32768と−720が各depthでUBSanのunsigned pointer
offset overflow（計4件）。候補Noise generatorは負のtable indexをsize_tへ変換して
tableより前を参照する。−36/−35/−18/32767の8件はこの入力ではsanitizer failureなし。
後者の成功を全Seed・任意worldでの安全証明にはしない。

actual AEX `FUN_1800034e0`の`0x37a4..0x37fd`を再読取りしたstatic fact:
上限100以上だけsubssで折り返し、`0x37b9`でsigned truncation、`0x37e4`で符号拡張、
`0x37f3/0x37f8`でtable[index]/table[index+1]を読む。下限0への折り返しはない。
負Offsetでnativeもallocation外読取りに達する可能性がある、という点は推論。
動的allocation境界witness/native hostの状態依存性は未確認。負値へmodulo/clampを
加えてWindows exactと主張する修正は行わない。

公開admissionを広げる前に、既存neutral EstimateRenderの14 float channel見積もりに
含まれないcomponent visited/pending/componentのvector容量、Noise plane/table、
Fade weight tablesとgather演算量を数える必要がある。Smartのatomic stagingとfull-frame
ROI検査にも同じ予算を適用する。Layer Noise、HDR、downsample、元AEX負Offsetの
定義境界は残件。候補180 exactと安全性診断4 failureを分けて保存し、Goalはactive。

## DB-NOISE-BOUNDS-010: native allocation境界を観測し候補の不正参照を止める

actual builderでOffsetの上位wordを読み、得られた正規化float bitsを変更せず
`FUN_1800034e0`のstack引数へ渡す。generator自体、MT seed/generation、index演算を
差し替えない。AE PF Handle Suite2のAcquire/Release/allocate/lockをhost callbackで
提供し、binaryが要求したallocationサイズと実table baseを記録する。

work15×15/51×51、Seed1/7/1000、Offset−32768/−720/−36/−35/−18/32767の36条件。
Noise planeとは別に101 float＝404 bytesのtableが確保され、`0x37f3/0x37f8`の読取り
直前でbase、signed index、address offsetを観測した。12条件（−32768と−720の全Seed/
work）がtableより前のaddressを使う。最初の範囲外命令で停止し、allocator周辺bytesを
読ませない。残る24条件はgenerator完了、全table readがallocation内。
実importはmemset/powf。powfは登録host mathでありnative UCRT証明ではない。
index生成はpowfの戻り値に依存しない。Windows AE/native allocator実行は未確認。

前項のnative負indexは推論だけだったが、今回の条件では実行上のallocation境界逸脱を
確認できた。元AEXの不正参照後の出力は隣接メモリに依存し得るため、noise値をclamp/
moduloしてbit exactと主張しない。full compatibility Goalの未閉鎖境界として保持する。

`core/dblur_noise.h`のDirectional generatorへ、index<0またはindex>=100ならfalseを
返すチェックを加える。テーブル参照以降の数値演算は変更せず、呼び出し元のstaged
renderは失敗時に出力をcommitしない。Radial generatorは別関数で、今回変更しない。

native境界36条件を再観測。本番PF8と解析PF16/PF32、3 Seed、6 Offsetの54条件を
O2とASan/UBSanで検証（計108実行）。範囲外条件では失敗し、input・output・padding
不変。候補の4 sanitizer failureは0になり、代わりに4件が安全にrender errorを返す。
既存一般機能180候補および固定getter47/候補135も両buildで同じnative hashを維持。
Noise sampler12件と固定生成planeのhash回帰もPASS。

旧sanitizer failure reportと旧native capture hashを保持し、修正後診断・validationを
別reportへ保存。安全な拒否はWindows完全互換達成ではなく、不正参照の解消である。
通常の深度Size/Sharp/Noise/Fade公開機能不足、追加workspace/Noise/Fade予算、Smart
full-frame/atomic契約、native AE/UCRT、installed bundleは引き続き残る。Goalはactive。

## DB-GENERAL-PUBLIC-011: 深度の一般機能をClassic/Smart公開経路へ復元

DB-GENERAL-009の180合法ケースは本番dispatcherで全件拒否だった。既存typed coreが
同じ公開AEX ownerのraw outputと一致する証拠を使い、一般Size/Front・Back Sharp/
Noise Type1・2/FadeのPF16/PF32経路を復元。geometry・設定tupleのwhitelistは追加しない。
SDR world、両side Strength0..4000、percent/Fade0..100、Noise Seed1..1000/Thickness1..100、
signed Offset、unit downsample等のcontrolsとworld検査を使う。Layer Noiseと既存個別
higher-order owner制約は引き続き別の未閉鎖契約。

一般深度は既存full coreをuse_expfloat=1、Windowsの等分行範囲で呼ぶ。実parameter
getterを維持し、画像・component・Noise・回転・writer演算は変更しない。packed source/
destinationへstageし、成功時だけactive bytesを出力へcommitする。

EstimateGeneralDeepRenderを追加。neutralの14 float channel/packed wrapper/strength
weights/Smart atomic spanに加え、component visited/pending/componentの容量増加と
reallocation overlapを含む24 bytes/work pixel、Noise plane +101 float table、Fade
weightsを数える。Fade gather・component traversal・Noise生成の追加演算量を保守的に
積み上げる。既存3 GiB/350M単位の限度を共用し、失敗時はestimateを更新しない。
この限度は全Windows機能を完了させる定義ではなく、現在の安全な実装限界である。

SmartRenderは同じparameter/estimate検査にatomic output spanを渡し、allocateや
source readより前に検査する。full-frame要求とworld geometry/originの検査も一般機能へ
適用。Classicはdispatcherで同じcore/workspace見積もりを使う。

修正後の公開AEX再capture180/180は本番route3（bypassなし）、public_dispatch_error=0。
実SDK translation unitをOLM_DBLUR_TEST_SEAMなしでcompileし、PF World Suite2と実型
parameter checkout/checkinを提供するfake AE hostでClassic/Smart EffectMainを再生。
両公開cmdの全180 native hashが一致。O2とASan/UBSanで計720成功renderを確認。
input不変、odd rowbytes（input+5/output+11）のpadding保持、Smart21 parameterの
checkout/checkin、layer checkin、suite releaseも確認。

partial ROI、param checkout/checkin失敗、layer checkin失敗、output checkout失敗、
演算量超過、Smart stagingメモリ超過、native不正Noise indexとClassicでの演算量/
不正index失敗の10状態を両depth・両buildで計40 failure renderとして検証。未読可能なsource pointerを渡す予算超過ケースも先に拒否。
全失敗でactive output/input/padding不変。checked estimateのoverflow、invalid depth/
Fade/Thickness、reserveの保持と追加workspace/operationの検査もPASS。

既存getter47/固定小数135、一般180候補、角度162を両buildで再生し全native hash維持。
固定小数集合で残っていた24 dispatcher拒否も今回の一般経路で解消。負index native境界
36件再観測と54候補/各buildもPASS。既存Back/Dual EffectMain、ROI、Smart cleanup17件
もPASS。旧capture source/hashを付け替えず、現在のlive再生とproduction/validationを
別に保存する。

このfake hostはWindows AE/native UCRTまたはMac installed bundle実行ではない。
公開360 renderの一致を任意画像/HDR/Layer Noise/downsample/全設定へ一般化しない。
予算で拒否される大画像・強設定、元AEX不正Offsetの状態依存出力も残る。Goalはactive。

## DB-HDR-012: PF32 finite HDR/signed入力の公開拒否を解消

前項のgeneral inputはSDRのみだった。独自ARGB float入力にRGB約0.125..8.1、signed RGB、
alpha−0.5..2、RGB約10^28、負のzero/1の直上/正負最小subnormal/1の直下を作る。
9×7・37×29、Front7/Back11/Dual7+11、角度123.5/−17.25/17.25、neutral/components/
Noise Type2/Size+Sharp+Noise+Fade+Gain2.25の4状態を5 profileへ渡す計120条件。
同一typed raw bytesをWindows公開Smart ownerとMacへ渡した。

SDR gateでは120件とも本番dispatcher拒否。明示的core bypassでは120/120 bit exact。
拒否の原因は画像演算ではなく、GenericPF32SDRInputのchannel0..1条件だった。
Windowsと一致する既存float演算を保持し、PF32入力をfinite検査へ変更する。
alpha/RGBの0..1へのinput clampは追加しない。最終writerのWindows由来の上限演算は
変更しない。PF16の32768上限検査、parameter/world/予算/Smart staging検査も維持する。

変更後は120/120が本番dispatcher route2/3でexact、bypassなし。実SDK・production test
seamなしのfake AE hostでClassicとSmart EffectMainの両方をO2/ASan/UBSanで再生し、
計480成功renderで全native raw hashが一致。input不変、input rowbytes+5/output+11の
padding保持、Smart21 parameter checkout/checkinとlayer/suite cleanupを確認。
各ARGB channelへNaN/+Inf/−Infを入れた12状態をneutral/feature、両公開cmd・両buildで
計96失敗renderとして検証。全て出力を変更せず拒否した。

既存general180のClassic/Smart再生（720成功、40失敗）も両buildでPASS。
既存Back/Dual EffectMainとdeep geometryもPASS。Back/Dualの旧PF32 red1.25拒否検査は
新しいHDR受付と矛盾するため、PF32 red=Infのatomic拒否へ変更。PF16 red32769拒否は
維持。旧production capture hashは付け替えず、現在の再生を別validationへbindする。

出力の120条件一致は任意の有限float、overflow、NaN/Infや実host FP環境の完成証明では
ない。Mac fake AE hostとローカルAEX emulationの比較でありnative AE/UCRT・installed
bundle未完。PF16非SDR、Layer Noise、downsample、旧個別owner契約、大画像/強設定の
予算拒否と全設定/素材は残る。完全互換Goalはactive。

## DB-LAYER-013: 独立Layerのfield witnessと実parameter宣言を分離

sourceと異なる独自Layerを2種類作り、9×7/37×29、Front7/Back11/Dual7+11、
角度123.5/−17.25/17.25、Layer Noise単独/components/Fade+Gain2.25の3設定を
PF16/PF32へ渡す計72条件。worker resident v4のfixture-layers-v1 manifestでslot17へ
typed raw worldをcheckoutし、Windows公開Smart ownerを実行した。画像・Layer・native
raw出力は一時ディレクトリのみ、正規化hashとmetadataを保存する。

native outputは72/72でsourceと異なり、同一source/設定で2 Layerを入れ替えた36組全て
native output hashが変わる。Layer未使用の疑似PASSではない。Mac公開dispatcherは72件
とも拒否（516）。実PF_ParamDef→InfoFromParams後、明示的解析bypass route1001で
既存full typed coreを呼ぶと72/72 raw exact。input/Layer不変、両worldのpadding保持を
O2とASan/UBSanで全72条件（計144再生）確認した。公開復元完了とは扱わない。

重要なparameter contract: AEXの実ParamsSetupはNoise Typeのchoices stringを
`Smooth | Block | Layer`と返すが、valid_max/slider_maxは2。Macの実SDK・test seamなしの
PF_Cmd_PARAMS_SETUPもnum_choices=2、labels=3（21 callback）で一致する。今回の
Type3は宣言範囲外の値を公開ownerが受け入れたstate witnessである。通常AE UIで
Layerを選べる証明ではなく、合法UI入力の72条件とも主張しない。

宣言範囲内のType1/2について、両depth・同じ9×7 sourceをLayer未選択と独立Layer2種類
選択で比較。8 selected-layer outputは全て同じTypeの生成Noise出力とbit exact。
選択LayerだけでType3へ移る挙動はこの集合にない。descriptorとrender branchを混同し、
Macだけnum_choicesを3へ増やす変更は行わない。実AE UIの挙動は未確認。

fixture workerはraw world dumpをcreate-newで保存するため、同じsession directoryを
再使用するとFile existsで止まった。caseごとに固有の一時directoryを使って解消。
このworker契約の失敗をAEXの画素差やPF32不対応とは分類しない。

Layer coreの同寸法・原点0の数字は一致する証拠が得られた。次はType3 stateの公開
admission/Smart checkoutと追加2 field plane/Layer staging予算を復元し、同時に異寸法/
原点、HDR Layer、欠落Layer、ROI/downsampleを検証する。Window/Mac共通の宣言範囲と
枝の到達性を別に保持し、完全互換Goalはactive。native AE/UCRT/installedも未完。

## DB-LAYER-PUBLIC-014: 独立Layerを深度16/32の一般公開経路へ復元

013の72条件を9×7/16×16/37×29へ拡張。各geometry・独立Layer2種類・両depthで
Front/Back/DualのNoise/components/Fade+Gainに加え、旧guard tuple
Angle45/Front8/Sharp50/Noise100も再検証する計120条件。修正前は120/120が解析core
bypassでexact、公開dispatcherは全拒否。同一source/設定のLayer入替60組すべてnative
hashが変わり、Layerを実際に使うことを確認した。入力は独自生成、nativeはローカル
AEX workerの公開Smart entry。raw worldは一時保存のみ。

最初の差はcore演算でなくType3を排除する公開admissionと旧16×16 hash guardだった。
PF16/PF32のType3をgeneral featuresへ通し、同寸法・原点0・分離payload・行幅・depthを
検査する。PF16はsource/Layerとも32768上限、PF32は両方の全channel finiteを検査。
Layerをpacked bufferへmemcpyでstageし、core field生成のunaligned typed loadを避ける。
ClassicはWorldSuiteでLayer形式を確認。SmartはLayer checkout/format検査を含め、全ての
parameter/Layer checkin成功後にのみ出力をcommitする。PF8の旧Layer契約は保持する。

追加予算は2 float field planeと1 packed Layer buffer。field生成/回転の演算量も
32 units/work pixelを保守的に加算し、Smart atomic stagingを含めてallocate/read前に
検査する。Layer Type3は生成Noise planeを使わないため生成用Thickness/Seed/Offset
見積もりを混ぜない。既存checked overflow/3 GiB/350M限度と失敗時estimate不変を維持。
この限度による大画像・強設定の拒否は、完全互換の終了条件ではない。

変更後の公開AEX再captureは120/120 bit exact、全件public_dispatch_error=0・route3。
実SDK・production test seamなしのfake AE hostでClassic/Smart EffectMainを両build
（O2、O1 ASan/UBSan）で再生し計480成功render、native raw hash全一致。source rowbytes
+5、output+11、Layer+7の奇数strideでもinput/Layerとpadding不変を確認した。
Smartは21 parameterと2 Layerのcheckin、suite releaseを確認。

欠落Layer、異寸法、短いrowbytes、原点、形式違い/形式callback失敗、alias、partial ROI、
parameter checkout/checkin失敗、Layer checkin失敗、output checkout失敗、演算量超過、
Smart stagingメモリ超過の24状態×両depth×両buildで96 failure render。PF16各channelの
32769、PF32各channelのNaN/+Inf/−Infは両cmd/両buildで64 failure render。
計160失敗すべてで出力を変更しなかった。予算拒否では未読可能source/Layer pointerを
渡しても先に拒否。Layer formatのClassic検証でfake callbackがparams内worldのcopyを
識別せず一度失敗したが、host callbackのworld識別を修正し全検証を再実行した。

旧独立Layer72条件も現行公開route3でO2/ASan/UBSan再生し144 exact、実ParamsSetupの
choices2/labels3は維持。生成Noise等180条件の両cmd（720成功/40失敗）とHDR120条件の
両cmd（480成功/96失敗）、budget19条件、既存Back/Dual EffectMainと直接Smart cleanup
17状態もPASS。旧capture source hashは付け替えず、新しいlive再生を別validationへbind。
古いtests/test_olmdirectionalblur_smart_cleanup_candidate_20260813.pyはhandoff内の
external validator欠落で実行不能だった。数値差と分類せず、直接source cleanup検証の
成功と分けて記録する。全repository gateは再実行していない。

値3は依然として元AEXの宣言上限2の外であり、通常UI合法入力またはAE project
保存/復元の到達性を証明しない。Macだけchoicesを3へ変更しない。異寸法/原点Layerを
対応済みとせず、HDR Layer、任意float、PF16非SDR、downsample、全設定/素材、元AEX
不正Offset、native AE/UCRT/installedを残件として保持。完全互換Goalはactive。

## 次の順序

1. ColorKeyの他Blur設定を公開ownerで再検証し、旧import stub依存の分岐を復元。
2. 全color/threshold、HDRとnative host/ROI/downsampleを拡張検証。
3. Smoother2の分類到達は今回の集合で確認済み。色・alpha・scan/weightの状態と
   public owner/native hostの比較は残る。計画に沿いDirectionalBlur Dual等の一般入力も進める。

既存の作業ツリー変更は今回のcommitに混ぜない。第三者AEXとnative raw出力をPushしない。
