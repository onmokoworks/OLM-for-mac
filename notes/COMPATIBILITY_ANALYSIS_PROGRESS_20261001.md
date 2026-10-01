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


## CK-AROUND-RANGE-006 — AroundのBlur量・距離方式・workspaceを復元

005後の残件だった他Blur量/距離方式を、exported AEX Smart ownerと実builderで比較。
AroundのBlur量0.1/0.5/1/1.5/2/4/7.3/31.5/100/4000、距離方式1/2/3、Thin0/−4/+4、
Keep off/on、全depthの9×7 mixed-alpha 540条件。正しい同一parameter比較で、変更前は
18exact、30出力差分、492公開拒否だった。Aroundの既存曲線を全合法量/metricへ使い、
PF32の旧Amount2専用planeをこの復元経路で通さない一時案は540/540 exact。

初回の比較ハーネスは指定Blur Typeを後から2へ戻してしまっていた。parameterのnative
propagationだけではMac側の同一設定を証明できないと分かった。FillParams後にもBlur
Type/Amount一致をassertするよう修正して両比較を取得し直した。未公開の誤った集計は
破棄し、invalid_harness reportにhashと無効理由を残す。本番判断には使用しない。

同じ一時案を3独立geometry/alpha入力×Premultiplied2×Replace2へ広げると6480 exact。
1×1/1×7/9×1の別6480条件は6256 exactで、224反例は1列・Thin≠0・Blur Type1に集中。
native typed workerはThin/Blurでlocal_188のfloat distance worldを再利用する。
1列Type1ではx±1 pointerのrow aliasにより、現在rowに残った前段値を読む。そのため
毎回ゼロplaneを作り直したMacでは、前段距離が後段Blurに伝わらなかった。

単にCore Thinのdistanceを渡す案は720中608 exactに留まった。正Thinの判定に使う
matched距離と、nativeがworkspaceへ残すmatched境界距離は出力matteが同じでも異なる。
native workerは正負どちらでもまずboundaryを作ってdistanceを計算する。正Thinは
出力判定を維持しつつ1列・Around Type1で境界distanceを保持、負Thinは元のdistanceを
引継ぐ。後段Box走査へその初期planeを渡し、4000 capを使う一般処理を復元した。
全720条件が一時SDK Classicでexact。固定座標、期待出力byte、epsilon補正は使わない。
AEXのworld外read自体は移植せず、以前と同じ範囲付きrow alias readを保つ。

別にBlur sliderのdouble→float materializationを観測。0/1e−50/1e−40/0.1/1.5、Keep2、
depth3の30条件で、量だけを広げた案は24exact。1e−50はnativeのfloat fieldでは0で
Blurを実行しないが、Macはdoubleの正値を残していた。native FUN_18000de90のfloat
宛先（info+0x40）に合わせClassic/Smart取得時にfloatへ変換すると30exact。
通常UIが極小doubleを生成する証明とは区別する。

本番はAround、Blur0〜4000、Type1/2/3、Thin±4000とのcompositionへ一般化。
Inside/Outsideや旧internal directionにこの証拠を流用しない。source/parameter UI定義は
変更せず、数値処理・入出力staging・cleanup規則を維持する。公開540条件は本番で
全exact、独立1×13 mixed-alpha column540条件も新規native比較で全exact、float境界30も
新規native比較で全exact。基準となるnative raw hashは保持する。

現行productionを実SDK Classic/Smartで全13530条件へO2再生し27060成功render、さらに
幅1・Blur Type1の1620条件とfloat30条件をASan/UBSanで両cmd再生し3300成功render。
合計30360がnative hash一致。入出力padding/source不変、suite acquire/release各2、
world format照会2、color照会4、Smartの33 parameter/1 Layer checkinを各実行で確認。
Blur−1/4001、Thin±4001の48失敗renderは全出力を変更せず拒否。

従来公開126出力、Around/Thinの8928 witness（17856公開再生＋既存sanitizer54条件）、
Thin公開216、generic pairwise、pixel-localとROI/tileの回帰もPASS。古いpixel-local
admission testのAround/Type1/Amount1拒否だけは、今回の根拠に合わせ成功・staging非commit
の期待へ変更。test functionのみのファイルは単なるpython実行では検証されないため、
run_olm_generic_beta_gate --run-test-fileで実行を確認した。full generic gate/性能を再実行
したという主張はしない。

証拠はlocal AEX math substituteと実SDK fake host。Windows UCRT/native AE、installed、
全color/threshold/25 keys/HDR、Inside/Outside、任意geometry/全状態、ROI/downsampleは
未完。取得した全件の一致を全10本の完成には一般化せず、Goalはactive。

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

## DB-LAYER-HDR-015: float→整数のSSE sentinelを復元

014の公開Layer経路へ、RGB約0.125..8.1、signed RGB、alpha−0.5..2、RGB約10^28、
float境界（負zero/1直上/正負最小subnormal/1直下）のLayer5種類を渡す。
sourceはSDRと同じHDR profile、9×7/37×29、Front/Back/Dual、Noise/components/Fade
+Gainの計180条件。ローカルAEXの公開Smart ownerは全件guard付きで正常終了した。
Mac公開dispatcherは144 exact、巨大finite Layerの12条件が数値不一致、24条件が
SIGSEGVとなった。旧reportはそのまま保存し、全native出力hashを変更後にも再確認した。

最初の差はfield算術ではなく散布距離のfloat→整数変換。AEXのFUN_1800013e0は
0x180001450のCVTTSS2SI R9D,XMM0（f3440f2cc8）でspanを整数化し、1未満なら
散布を行わない。範囲外/NaN/Infのmasked invalid resultはINT32_MIN。
元Macのstatic_cast<int>(float)は範囲外で未定義。ARM64で大きな正整数となり、前方では
誤った散布、後方ではrow境界計算のoverflowを起こしていた。

実AEX bytesの同じ1命令をUnicornで実行し、±zero、±1/1.5、subnormal、INT32上下境界
と近傍、±最大finite/Inf/NaNの20 bit patternで結果を確認。trunc_iに明示的な
[-2^31,2^31)判定とINT32_MIN sentinelを復元する。有効範囲は従来どおりzero方向の
truncation。画素のclamp、sample別の書換え、span最大値への飽和は加えない。
同じhelperを使うprepass/table lookupにも命令の変換仕様が適用される。
旧commitのtrunc_iをfloat-cast-overflow sanitizerで1e28fへ適用すると範囲外castの
runtime errorで停止することも確認した（expected diagnostic、exit −6）。

巨大finite入力から正規のspanを作る場合もLayerはStrength以上に散布を広げられるため、
PF32 Layerの予算は読取り前に各有効sideを全work row幅で保守的に見積もる。PF16は
検査済みSDR Layerなので従来のStrengthを使う。field/packed bufferのメモリ見積もりは
014を維持する。PF32 Layerの大画像には、この保守的予算による追加拒否が残る。
有限Layerの範囲を調べて上限を絞る改善は今後の課題であり、全互換を達成した扱いに
しない。350M単位の限度自体も完成定義ではない。

修正後180/180が公開route3でraw bit exact（bypassなし）、native hashは修正前と全一致。
実SDK・production seamなしのClassic/Smart EffectMainをO2とASan/UBSanで再生し
計720成功render。input/Layer不変、奇数stride/padding、Smart21 parameterと2 Layerの
checkin、suite releaseも確認した。整数変換20状態と巨大係数のscatter不変検査をO2と
ASan/UBSan/float-cast-overflowで確認し、checked budget21条件もPASS。

既存general features180（720成功/40失敗）、source HDR120（480成功/96失敗）、
Layer120（480成功/160失敗）もO2/ASan/UBSanで再生しnative hashとatomic failureを
維持。Layer120とHDR Layer180は予算変更後にも再実行し全一致。kernelの変更前状態は
commit0e520eeaとcore hashで別validationへbindし、同じMac entry cpp hashをkernel
全体の不変証明に使わない。旧captureや前項validationのhashを付け替えない。

この比較はローカルAEX emulationとfake AE hostでありnative AE/UCRT・installedでは
ない。巨大Layer180条件の一致を任意finite/overflow/非有限値、near-INT32境界の全散布、
異寸法/原点、PF16非SDR、downsample、全設定/素材へ一般化しない。
通常UIのchoices2/labels3と値3の宣言範囲外stateの区別も維持。完全互換Goalはactive。

## DB-LAYER-DIM-016: 異寸法とNoneでfieldを生成しない規則を復元

Layerをsourceより小さく/大きく/横長で低く/細くて高くする4形状で比較。
source9×7/37×29、Layer profile2種類、Front/Back/Dual、Noise/components/Fade+Gain、
PF16/PF32の計288条件。元AEXの公開Smart entryは正常終了したが、Macは同寸法制限で
全拒否した。最初の仮説はLayerの左上intersectionを使い、外側をzeroにする処理。
解析adapterによるMac出力も、nativeへcropped Layerを渡す対照も0/288 exact。
この失敗を保存し、切抜きやresizeによる近似を本番へ入れない。

静的根拠: FUN_1800057b0のLayer checkout後は、Layerのwidth/heightを
ceil(PF_InData full width/height × render scale)と比較する。両方一致した場合だけ2つの
field planeをallocateする。FUN_1800038d0はmode2でfield pointer+0x80b0がnullなら
Noise係数を1に保ち、Noise opacityとの混合を行わない。fieldをzeroにしてopacity
だけを残す動作とは違う。今回は既に扱っているfull-frame/unit-scale条件で比較する。

反証後にNoise Variation=0の対照へ切替えると288/288でnative raw hashが同じ。
Mac解析adapterも288/288 exact。default None LayerでType3を指定する別54条件
（9×7/16×16/37×29、3方向、3機能、2深度）も、全件Noise無効のnative対照と一致。
Type3の宣言範囲外stateとdescriptorのchoices2/labels3は引き続き区別する。

本番はdeep Layerのdims gateをClassic/Smart/dispatcherで共用する。Noneまたは異寸法
ならrender-localのNoise量を0に正規化して既存neutral/general機能へ渡す。
公開parameter、Layer world、sourceには書き込まない。異寸法Layerをcrop/resizeせず、
データや形式を参照しない。同寸法で実際に使うLayerには形式、rowbytes、origin、
payload分離、PF16 SDR/PF32 finiteの検査を維持する。Smartのunused deep Layerには
payloadのalias検査を適用しないが、checkout済みLayerのcheckinとatomic commitは維持。
PF8の既存契約とcheckout/alias検査は変更しない。

公開再capture288/288 exact、全件route2/3、解析adapterなし。元のnative hashも全保持。
実SDK・production seamなしのfake AE hostで両公開cmdをO2/ASan/UBSanで再生し、
異寸法1152、None216の成功renderで全native hashが一致した。使用しないLayerに未読可能
pointer/rowbytes0/非zero origin/format callback失敗をまとめて渡す場合とsource aliasの
16 renderもnative witnessと一致。fieldが無効なときの検査順を確認した。
source+5/output+11/Layer+7のodd stride、input/Layer/padding不変、Smart21 parameter、
2 Layer（Noneはinput1のみ）のcheckinとsuite releaseも確認。

同寸法でfieldを使用する18失敗状態×両depth×両buildの72失敗renderは全てatomic拒否。
Layer120の両cmd回帰は480成功と140失敗（旧160失敗のうち復元した異寸法/None状態は
失敗として数えない）。HDR Layer180も720成功で全hash維持。生成Noise等180、source
HDR120、既存Back/Dual EffectMain、Smart cleanup17も現行sourceで再検証しPASS。
過去capture hashは付け替えず、新しいlive validationの依存hashへbindする。

非zero原点、ROI/downsample/full-size referenceと実checkout worldの関係、全設定/素材、
PF16非SDR、任意float/near-INT32散布、PF32 Layerの保守的な大画像予算、実host UIと
project保存/復元、native AE/UCRT/installedの完了証拠は残る。完全互換Goalはactive。

## DB-LAYER-BUDGET-017: 実Layer値の上限で大画像の不要な拒否を解消

015のPF32 full-row散布上限は安全側だが、SDR Layerでも全work幅を仮定していた。
720×480、独自の疎なmixed-alpha source、Front7+Back11、Angle17.25、Layer Noise73.75
で、SDR inverse・positive HDR・signed RGBの3 Layerを元AEXの公開Smart ownerへ渡す。
nativeは3件ともguard付きで正常終了し、Noise無効の対照とはすべて出力hashが異なる。
旧Mac Classicは3件とも予算拒否（516）。Layer未使用での疑似一致ではない。

一般規則: 各Layer pixelのabs(alpha) × max(abs(R),abs(G),abs(B))の最大値をdoubleで
走査する。premultiplied luminanceの正の係数和とscalar bilinearの非負weight和は1。
この絶対値上限をNoise opacityと混合し、少なくとも1とする。luminance、補間、Noise
混合、最後のStrength乗算の丸めを覆うため32 float epsilonの余裕を加える。
この値は予算用であり、入力やfield、出力のclamp/補正ではない。

順序は二段階。まず既存のUI/geometry/rowbytes/format/aliasと全workspace/Smart staging
メモリ、unamplified Strengthの予算を検査する。次にfinite Layer scanで上限を取り、
増幅後のspanをwork幅でcapして散布量を見積もる。final estimate成功後にsource finite
検査とpacked staging/renderを行う。Smartもoutput staging前に同じLayer estimateを使う。
未知のLayer上限を呼ぶ内部APIは引き続きfull-rowの既定値を使える。PF16 SDR経路、
生成Noise、pixel kernelは変更しない。UI Strength4000上限はentryで保持し、内部の増幅
spanだけは4000以上も数えられるようにする。

修正後3/3が公開Classicでnative raw bit exact。nativeの元hashは全保持。
実SDK・production seamなしのClassic/SmartをO2とASan/UBSanで再生し12成功render、
全native hash一致。odd stride/padding/input/Layer不変、Smart21 parameter/2 Layerの
checkin、suite releaseも確認した。実fieldとscalar rotatorの出力からspanを計算し、
6 profile（既存HDR5と全float max）、3 geometry、3角度、3 Noise量の162状態を両build
で確認。Strength7/11/4000で全有効spanが見積もり上限内（計324検査）。非有限spanは
015で確認したSSE sentinelで散布しない範囲として区別する。

720×480の高輝度Layer（alpha1/RGB80）ではfinal estimateを超過させ、unreadable source
pointerを渡したClassic/Smartを両buildで確認。4失敗render全てinputを読まず、出力を
変えずに拒否。初期メモリ/演算量でのpoison pointer拒否は既存Layer回帰に含む。
checked budget27条件、既存admission budget、Layer120の480成功/140失敗、HDR Layer
180の720成功、異寸法/Noneの1384成功/72失敗、生成Noise180、source HDR120も現行
sourceで再検証してPASS。履歴reportのbindingを付け替えず、live validationを別に保存。

native host確認も着手した。mac-windows-ssh skillの既存r5900x aliasへBatchModeと
ConnectTimeout8秒でread-only PowerShell（AE process/install path照会）を送ったが、SSH
exit255、接続timeout。tailscale statusのlocal backendはStopped。cached Windows peerの
Online表示をlive接続の証拠にしない。AE processやインストール状態は取得できていない。
ネットワーク/鍵/設定は変更しなかった。local AEX emulationと実Windows AEを区別する。

この上限は実行回数を数える最適予算ではない。source alphaによるskipや相殺、SSE無効
span等をすべて使ったtight boundではなく、依然として必要以上の拒否が残り得る。
3 GiB/350Mという実装限度自体、大画像/強設定、非zero origin/ROI/downsample、PF16
非SDR、任意float/near-INT32散布、全素材/設定、実UI/project保存、native AE/UCRT/
installedの全互換は未完。Goalはactive。


## DB-PF16-RANGE-018 — 一般機能のraw uint16入力範囲

未閉鎖だったPF16非SDR境界を、sourceと独立Layerを分けて調べた。typed guest workerの
validate_bytesはbyte数だけを検査し、ARGB uint16 channelを32768でclampしない。
これは元AEXへの入力の証拠であり、通常AE UIが非SDR PF16 worldを生成する証明ではない。

自作profileはRGBのみ拡張、alphaのみ拡張、全channel拡張、32767/32768/32769/
65534/65535境界。2 geometry（9×7、37×29）、source/Layer/両方の3配置、Front/Back/
Dual、Layerのみ/Size・Fade・Sharp併用で144条件。変更前は公開経路144拒否、分析専用の
既存full typed coreは144/144 native raw exactだった。履歴baselineはhashを保持する。

PF16一般機能のsource/Layer SDR検査だけを解除した。完全neutralの別経路は変更しない。
Layer値は65535/32768まで、alphaとの積は約4まで増えるので、SDR時のspan≤Strengthを
流用しない。既存PF32係数上限処理をtyped helperへ共通化し、PF16では各channelを
1/32768で正規化したdouble積を使用。最大absolute premultiplied積、Noise mix、32 float
epsilonの丸め余裕から最終散布上限を計算する。メモリ/UI/geometry等の初期検査後に
Layerを読み、増幅後予算を検査してからsource staging/render。Classic/Smartで同じ規則。
入力値/field/出力のclampや補正、pixel kernelの変更はしていない。

変更後144/144が公開route3でnative raw exact。さらに同じ4 profile、2 geometry、3方向、
Layerなし/生成Noise1/生成Noise2（全てSize/Fade/Sharp併用）の72条件も公開経路でexact。
実SDKのproduction seamなしClassic/SmartをO2、O1 ASan/UBSanで再生し、216条件×4=
864成功renderがnative hash一致。odd stride、padding、source/Layer不変、Smart parameter
21とLayer2のcheckin、suite releaseを確認（未使用Layerもこのfake hostではcheckoutされる）。

実Layer fieldとscalar rotatorを使う上限検査は4 profile×3 geometry×3角度×3 Noise量の
108状態を両buildで再生。Strength7/11/4000のspan全てが見積もり内（216検査）。
720×480、最大uint16全channel Layer、Noise100、Front/Back各80では初期Strength予算は
通るが約4倍の最終予算は拒否。unreadable source pointerを渡したClassic/Smart両buildで
source読取り前に拒否し出力不変（4失敗render）。checked budgetは31条件に拡張。

既存PF32の上限・大画像Layer、独立Layer120、HDR Layer180、異寸法/None、生成Noise、
source HDR、Back/Dual・1280×720、admission budget、Smart cleanupの回帰も現行sourceで
PASS。過去span budget reportのsource/budget bindingは履歴として固定し、live再検証の
bindingは今回のvalidationへ記録。過去native出力hashを現在sourceへ付け替えない。

今回の証拠はlocal exported AEXと実SDK fake host。実Windows AE/UCRT/installed、全素材/
設定、ROI/downsample、旧個別owner契約、完全neutral等のPF16非SDR、任意float/
near-INT32散布、大画像/強設定と保守的予算の拒否は残る。216件の一致を全10本の
完成へ一般化せず、Goalはactiveのまま。


## DB-PF16-NEUTRAL-019 — neutralのSDR拒否を解除

018後に残ったPF16 neutralのSDR境界を、既存neutral kernelへの分析専用bypassで
元AEXと比較した。raw uint16のRGB拡張、alpha拡張、全channel拡張、境界profileと
SDR controlを3 geometry（9×7、16×16、37×29）で使用。Front7/Back11/Dual7+11の
3方向、Gain0/1/2.25に加え、16×16 retained Back1/2/8・Angle45・Gain1を含む150条件。
実AEXに渡す型・パラメーター・source hashを保持し、channel clampは行わない。

変更前はneutral kernelで150/150 native raw exact、公開経路では42exact/108拒否。
SDR control27とretained15は公開経路ですでに通る。残る108は汎用neutralのSDR scan
だけで拒否されていた。GenericPF16SDRInputを除去し、既存のworld/UI/memory/work
予算検査後にRenderGenericNeutral16へ進む。retained、kernel、行分割、pixel数値計算、
既存PF32 nonfinite拒否、geometry/ROI/alias/atomic規則は変更しない。

変更後150/150が公開route2（汎用135）/route1（retained15）でnative raw exact。
取得時のbaseline hashは不変。実SDK・production seamなしClassic/SmartをO2と
O1 ASan/UBSanで再生し、600renderがnative hash一致。odd stride、padding、source不変、
Smart21 parameter/1 Layer checkinとsuite releaseを確認。高値PF16を使ったpartial、
checkout/output/checkin失敗、memory/operation budgetの16失敗renderは出力を変えない。

既存Back-onlyテストの「32769は不正」という期待を除き、PF16高値の受入れと既存の
安全性を今回のtyped oracleで検証した。古いdirect Back-onlyテストに残っていたPF32
1.01/−0.01の拒否期待も、既に復元済みのfinite PF32契約に合わせて成功へ修正。
NaN/±Inf拒否を保持した。同テストの固定portable anchorはO2で一致、sanitizerでは
既存仕様どおりanchorをskipする。Back/Dualの実SDK・1280×720/予算/atomicも両buildで
PASS。汎用deep geometry、HDR source、018の216条件/上限検査も現行sourceで再検証。

古い一般入力3campaign（各54条件）の回帰は、015のCVTTSS2SI修正前のcore hashを
現在のcoreへ要求して停止した。取得時のcore hashを履歴として明示固定し、現在の
productionは旧native outputをO2/ASan/UBSanで324再生して確認した。captureを書き換えず、
live dependency bindingは今回のvalidationへ保存。018のproduction bindingも履歴で固定。
BETA_SUPPORTのDirectionalBlur欄に残るdeep SDR制約を、PF16 raw uint16/ PF32 finiteの
現行契約へ更新した。他プラグインの制限へ一般化しない。

通常AE UIが非SDR PF16 worldを生成するか、実Windows AE/UCRT/installed、任意input/
全設定・大画像/強設定、downsample/ROI/非zero Layer origin、旧個別owner契約、float
整数境界・保守的予算の拒否は未閉鎖。150条件や汎用入力制限の解除で全互換とは
扱わず、Goalはactive。

## CK-IO-RANGE-007 — Inside/Outsideの一般曲線とSSE境界を復元

006で残したInside/Outsideを、同じ元AEXの公開Smart ownerと実parameter builderで
比較した。新しい実SDK harnessはBlur Direction/Type/AmountをFillParams後にもassert。
公開Direction 1/3、Blur Type 1/2/3、Thin 0/−4/+4（Type 2/1/3）、Keep off/on、3深度、
Blur 0/1e−50/1e−40/0.1/0.5/1/1.5/2/4/7.3/31.5/100/4000を独自9×7 mixed-alpha入力へ
適用。変更前は1404条件のうち222 exact、36出力差分、1146公開拒否だった。

静的事実: FUN_1800053a0はmatched matte側だけにInside曲線を適用し、外側を0にする。
FUN_1800056f0はmatched matte側を1とし、外側だけにOutside曲線を適用する。共に
FLOAT32 pi/amountとdistanceの積をdoubleへ変換し、double pi/2を減算／逆順減算して
sinを呼ぶ。doubleで+1した後floatへ変換し、0.5fを乗算する。PE内の定数値とbitsを
確認した。Aroundのsinfへ統合せず、この変換順を復元する。writer後にKeep-offがsource
alphaからfinished matched matteを引く。先にmask/weightを補数にすると丸めが違う。

初案は1392/1404 exact。残る12条件はPF32 Inside・Blur1e−40・Thin0/+4で、通常量の
曲線誤差ではなかった。typed resident ownerで同じraw hashを取得し、元AEXのalphaは
0xffc00000、Mac初案は0x7fc00000と確認（各条件の差分pixel countと最初の8箇所を保持）。
floatのpi/amountが+Infとなり、boundary distance0とのMULSSでinvalidが発生する。
x86 SSEの負quiet NaNをphaseの演算段階で再現し、sin/加算/変換/writerへそのまま渡す。
最終出力のNaN bitsを後から補正しない。通常AE UIが極小doubleを生成する証明とは別。

PF8/PF16 writerの実命令はCVTTSS2SI→低byte/word store。NaN/Inf/範囲外をINT32_MIN、
それ以外をtruncにする定義済みhelperを使い、NaN→C++ intの未定義動作を避けた。
初案のcaptureを変更せず、改訂案は1404条件のClassic/Smart 2808 renderで全raw exact。
float materialization/NaNの324条件はASan/UBSan両cmdの648 renderでもexactだった。

別17×15 mixed-alpha入力×Premultiplied/Replaceの4 toggleでは5616/5616 exact。
1×1 opaque、1×13 mixed-alpha column、9×1 mixed-alpha rowの4212条件も全exact。
1列Type1のThin/Blur workspace再利用は3つの公開directionへ同じnative規則で拡張する。
旧PF32 Amount2専用planeと正Thin/Outside捕捉専用callerを復元済みpublic経路で通さない。
旧internal direction0/4の証拠を公開Inside/Outsideへ読み替えない。

本番はInside/Around/OutsideのBlur 0〜4000、Type1〜3、Thin±4000との合成へ一般化。
新しい公開AEX再取得1404条件はClassic/Smartで全exactで、以前の同じ条件のnative raw
hash・source hash・parameter readbackを全保持した。3つの独立集合の11232条件は重複なし。
production seamなし・実SDK fake hostでO2の22464成功renderが全native hash一致。
幅1・Blur Type1とfloat materialization/NaNの3312条件をASan/UBSanで両cmd再生し、
6624成功renderも全hash一致。合計29088成功render。Blur−1/4001、Thin±4001の
96失敗renderは出力不変で拒否。入出力padding/source不変、suite acquire/release各2、
world format照会2、color照会4、Smart33 parameter/1 Layerのcheckout/checkinを確認。
現行source/依存hashと結果はcolorkey_inside_outside_validation_20261001.jsonへ記録。

従来の公開126出力とcallback13 controls、Thin公開216、Around/Thinの8928 witness、
Around range13530条件、generic pairwise36 cells、pixel-local、ROI/tileの回帰がPASS。
pixel-local admissionのInside/Thin合法tupleだけは今回の根拠に合わせ受入れへ変更。
古いAroundのsource hashは83175141の取得時bindingとして固定し、現行sourceの出力は
別途全再生した。capture/native hashを現在sourceへ付け替えない。full generic gateと
性能の再測定、installed/native AEを実行したという主張はしない。

candidate生成toolsは取得時83175141のsourceを対象とする履歴解析用。現行productionは
--candidateなしで再取得できる。元AEX本体、native raw画像、decompや別repoのworkerは
commit/Pushしない。公開するのは復元source、独自入力生成器、検証とhash/事実の記録。

証拠はlocal exported AEXのmath substituteと実SDK fake host。Windows UCRT/native AE、
Mac installed、全color/threshold/25 keys/HDR、任意geometry/全状態、ROI/downsample、
UI/project保存は未完。全10本の完全互換を達成とは扱わず、Goalはactive。

## CK-TYPED-HDR-008 — typed HDRと初期matteの負ゼロを復元

PNG経由の色変換・channel制限を避け、独自ARGB8/uint16/FLOAT32 bytesをresident exported
Smart ownerへ渡す新しいprobeを作った。設定はslot/type付きv4 payloadを実AEX builderへ
渡す。Macは同じ全scalar/color recordを実SDK PF_ParamDefへ読み、production EffectMain
Classic/Smartで取得する。設定漏れ・重複・不正typeをharnessで拒否する。resident APIは
frameごとのparameter readbackを返さないため、その証拠があるとは主張しない。

初期9×7 mixed-alphaの352条件: SDR、PF16 RGB/alpha/両方のraw高値（最大65535）、PF32
RGB HDR/負RGB/alpha HDR/負alpha/両方を使用。Keep/Premultiplied/Replaceの4 toggle、
pixel-local、Thin正負、3方向Blur、Thin+Inside/Outsideを同じbytesで比較。変更前は
328exact/24差分、公開拒否なし。24差分はPF32 combinedにある負ゼロalphaの符号のみ。
通常HDRや負の非zero alphaに対するこの集合の出力差ではなかった。

静的事実: float classifier FUN_1800035d0はmatched時にalpha wordをsourceからそのまま
コピーし、nonmatched時だけ0をstoreする。FUN_180009960の負Thinはmatte alpha!=0を
条件に消去し、負ゼロを消さない。正Thinはalpha==0かつdistance<=amountでsource RGBAを
FUN_180011670/115f0でコピーする。Blurはmatte alphaが0でweight!=0の場合だけsource
alphaを使い、他はmatte alpha*weight。Keep-offはその後のsource-minus-matteである。

Macはdistance seedからzero alphaを外すとき、出力matteのalphaも常に+0へしていた。
seedのboolとmatteのFLOAT32表現を混同していた。初期matte構築時、元のcolor matchまたは
正Thinのsource copyがあるzero-alpha pixelはsource alphaを保持する。型がPF32で、matched
matteを作るThin/復元済みBlurだけに適用する。bool maskやdistanceを変更せず、最終出力の
符号bitを補正しない。保持した−0へ元のBlur演算と最終減算を適用する。

一時案で初期352条件の両公開cmdが704render exact。O1 ASan/UBSanも704exact。
別1×1/1×9/9×1/17×15の1408条件を元AEXで取得すると一時案も全exact。本番へ反映後、
初期352条件を新規native取得して両cmd全exact。同じinput/parameter/native raw hashを保持。
1760 HDR/符号条件に、下記palette216と既知一致space288を加えた2264 capture rowsを
O2で両cmd4528render再生。HDR1760とcount25 palette36をsanitizerで3592render再生し、
合計8120成功renderが全raw hash一致。これは集合間の重複を排除した2264 unique入力の
主張ではない。範囲外Thin/Blurの48失敗renderは全出力を変えずに拒否した。
source/padding不変、suite acquire/release各2、world format照会2、color照会2*count、
Smart17+8*count parameter（25色では217）と1 Layerのcheckout/checkinを確認した。

RGB palette count1/2/4/5/24/25、通常交互key/最後の色だけ有効/重複色、Per Color off/on、
Threshold0.1、Replace on、Keep off/on、3深度の216条件は変更前から両cmd exact。
最大countの実builder・public checkoutと末尾color/先頭replacement優先の根拠として保持。
色数が25まで通ることと全palette/thresholdの一致は区別する。

color space6種×Force Lower Precision3種×Per Component2×Threshold0/0.1×3深度×Keep2の
432条件も比較した。最初の2実行は216条件目の後、Lab94 scalarが未実装Win64 import
api-ms-win-crt-math-l1-1-0.dll!atan2fでworker exit1となり、出力oracleを得られなかった。
失敗を差分として数えず、専用diagnostic runnerで全条件を測定/参照失敗に分離して取得。
396条件が測定でき、RGB/HSV/YUV/YCrCbの288条件は両cmd exact。Lab76の72とLab94
Per Componentの36は108出力差分。Lab94 scalarの36は参照import失敗（render_error−40）。
元Windowsプラグインがその状態を拒否する証拠ではない。別repoのworkerは変更しない。

最初のLab差は第2keyのgreen側であった。既存の単独cell専用Lab76 offset復元は、一般
inputに適用されていなかった。元comparatorはkeyと比較tripleのa/bへoffsetをin-placeに
加え、failed keyの比較tripleを次のkeyへ再利用する。Lab76はscalar/per-component、
Lab94はper-componentでこの状態を持つ。一時案はこの規則とLab76 scalarのFLOAT32
Euclidean thresholdを一般化し、測定済み396条件のClassic/SmartをO2とASan/UBSanで
計1584render exactにした（colorkey_lab_mutation_candidate_replay）。これは本番変更では
ない。color順序/disabled keys/しきい値境界/precision変換/他geometryを追加して検証し、
旧exactセルの参照経路も監査してから一般化する。Lab94 scalarの依存先不足は別に残す。

本番変更後、Around range13530（30360成功/48 atomic失敗）、Inside/Outside11232
（29088成功/96 atomic失敗）、Thin公開216、従来公開126＋callback13、generic pairwise
36＋sanitizer22、pixel-localとROI/tileの回帰がPASS。source/新harness/設定生成器/参照report
の依存hashはtyped_controls_validationへ記録。旧captureのsource/native hashを付け替えず、
full generic gate/性能、installed/native AEを再実行したという主張はしない。

全色空間/25色全palette/threshold/HDR/任意float/geometry/設定、native Windows UCRT/AE、
Mac installed、ROI/downsample、UIとproject保存は未完。Labの復元案と数値差、未実装参照
関数を別項目として次へ渡す。全10本の完全互換Goalはactive。

## CK-LAB-009 — Lab76/94成分別の比較状態とFLOAT32境界を一般復元

前ターンの単純in-place offset案を独立入力で拡張した。独自13×3 color stripはblack、
green、blue、white、gray、redish、cyan、近傍色を含み、alphaは255/128/0/64。PF16は
各channelをfloor(v*32768/255)で作り、PF32はfloat(v/255)。同じtyped packed bytesを
公開AEXへ渡し、Macはpadding付き同じ入力を実SDK Classic/Smartへ渡す。

Lab76 scalar/成分別とLab94成分別、Force Lower Precision 1/2/3、3深度、Keep off/on、
key順序/逆順/単色/先頭無効/途中無効/重複/全無効/25色の末尾だけ有効で432条件。
Per Color、Premultiplied、Threshold、Replaceも記録した組合せで変えた。これはそれら
全組合せの直積ではない。変更前の本番は196/432一致、単純offset案は422/432一致。
残る10条件はLab76成分別の許容幅であり、符号や最終writerの差ではなかった。

別のopaque 1×1 source(44,75,119)とcyan keyを使い、同じ3比較mode×3precision×3深度の
27族について元AEXの最初のmatchをFLOAT32 bit順で探索した。各探索はmatch/nonmatchを
観測し、最後のnonmatchと最初のmatchは隣接bitsである。その境界の前後6値ずつ162条件を
nativeで取得した。変更前本番105/162、単純offset案131/162。Lab76 scalarにも1条件、
Lab94成分別にも各族の境界1条件が残り、offset復元だけでは一般化できなかった。

FACT: 同じSHA固定AEXの0x1800043a0を読んだ。Lab76はkey/cmpのa/bにそれぞれ
133.03700256347656f/163.48800659179688fを加え、failed keyのcmpを次へ残す。
成分別の許容幅はFLOAT32で、L: thresholdL*151.30099487304688f + epsilon*2709.929931640625f、
a: thresholdA*264.36700439453125f + epsilon*578.7139892578125f、
b: thresholdB*295.572998046875f + epsilon*414.6759948730469fである。
scalarはthreshold*424.4352722167969fとepsilon*同倍率を別々にMULSSしてからADDSSする。
以前の(threshold+epsilon)*倍率は境界で別の結果になる。Lab94の0x180004510成分別は
同じoffsetを加え、各FLOAT32 threshold+epsilonを先にADDSSしてから各成分倍率をMULSSする。
Macのdouble thresholdを含む式ではこの境界がずれていた。Lab94 scalarにはこのoffsetを
適用しない（そのbranchは今回の参照workerでは未測定）。

この演算順とLab76成分別の許容幅を復元した一時案では、独立432＋境界162＋従来396の
990 capture rowsが両cmd/O2/sanitizerで全exact（3960成功render）。本番へ同じ一般規則を
反映した。入力色・サイズ・閾値でfixtureを識別して復元を選ぶ分岐を使わず、従来の
限定Lab76判定をRenderTypedの演算選択から外した。既存限定判定は古いadmission経路の
ため残す。本番も990行の同じ再生3960renderで全exactだった。

元AEXを全432 space設定で再取得すると、測定できる396は本番両cmd全exact。
以前の108不一致を解消した。同じ入力/設定/native output hashを全測定行で維持し、
過去のcapture hashは書き換えていない。Lab94 scalar36は同じatan2f未実装失敗であり、
Windows側非対応やMac数値一致として数えない。

Thin/Blurへの接続も新規native取得した。1×1、1×9、9×1、17×11、3深度、同3比較mode、
reverse/先頭無効/25色末尾/重複、異なる成分閾値、記録したKeep/Per Color/Premultiplied/
Replace/precision、3方向BlurとThin正負の144条件が本番Classic/Smart全exact。
この144行の再生も両cmd/O2/sanitizerで576render全exact。geometry/設定の全直積を主張しない。

typed HDR/最大25色/既知spaceの従来8120再生と48 atomic失敗も本番変更後PASS。
従来公開126 outputとcallback control13、generic pixel-local pairwise/一般beta、ROI/tileは
本番変更後PASS。参照経路は固定local workerと独自PF_ParamDef hostであり、実Windows
UCRT/AE、Mac installed/UI/保存state、全色/閾値/入力/geometry、Lab94 scalar、
ROI/downsampleの完了を主張しない。source/report/tool/testのhashをLab validationへ保持し、
全10本の完全互換Goalはactive。

## CK-LAB94-010 — 参照atan2fを分離しscalarのDOUBLE境界を復元

固定workerのLab94 scalar失敗を調べた。FACT: fmodfのdispatchとdeterministic_fmodfは既に
あり、欠けていたのはapi-ms-win-crt-math-l1-1-0.dll!atan2fだった。render-trace-pngも
失敗時にmemory witnessを返さなかったため、成功したowner recordをscalarのrecordへ
手書きで変えて公開owner証拠として扱うことはしない。

別repoと固定workerは保持し、guest sourceを一時領域へコピーした。追加したのは
atan2fの限定dispatchとXMM0(y)/XMM1(x)→XMM0のlow FLOAT32 return hookのみ。host f32
atan2を使い、引数/戻りbitsの短いlogを保持する。register read/write失敗はguestを停止する。
これはWindows UCRTの復元完了ではない。既存fmodf、powf、他host処理はコピー元を使う。

最初のコピーでrootのtarget cacheを除く指定がvendor/qemu/targetまで除き、Unicornの
C source欠落でbuild失敗した。除外をrootのtargetだけに限定して一時コピーを作り直し、
offline/lockedのrelease buildが成功した。外部の436 source fileと元worker SHAを再確認し、
一切変わっていない。新workerはc996d4fba8d84fd7f6484ca0ad545a370b552484398605d21a6eb07389aecef7。
build reportはコピー元全file hash、2つのpatch適用先hash、patch/builder/worker hashを保持。
元workerのsource/binary対応を推測で宣言しない。公開するのは小さなMPL-2.0参照overlay、
構築器、独自probe、数値結果であり、外部source全体やworker binaryは公開しない。

元AEXの公開resident ownerを新workerで実行した。前の396測定space行は、同じ入力で
全output hashが固定workerの保持済みoracleと一致した。以前測定できなかった36 scalar、
独立色順序scalar144、隣接FLOAT32境界54を加えた630条件は、変更前Macも復元案も両cmd
全exactだった。従って、この一致だけでは本番を変更しなかった。固定workerの36失敗は
そのまま残し、controlled referenceでの測定と区別する。

次にscalarの9境界族（3precision×3depth）について、最後のnonmatchと最初のmatchの
FLOAT32間隔を1/16刻みのDOUBLEで横切った。各族でGlobal/Per Color両方、33値ずつ、
計594条件。変更前の本番は492一致/102不一致、復元案は594全一致。input(44,75,119)、
opaque 1×1、単色cyan、Keep true/Replace false、typed bytesを記録。native builderが
FLOAT32へ丸めたthresholdと、DOUBLEのまま保持したMac thresholdの境界差である。

FACT: 元AEX 0x18000460c以降はFLOAT32 threshold+epsilonをADDSS、CVTPS2PDでdoubleへ
上げ、0x18001f6e8のdouble 352.978（LE cff753e3a50f7640）をMULSDし、FLOAT32へ戻す。
MacはPF_FpLongのthresholdを含めてdouble加算していた。thresholdをfloatへmaterializeし、
float加算→double倍率→float limitへ戻す順序を本番へ復元した。色/しきい値/geometryで
fixtureを識別せず、最終output bitの補正もしない。Lab94Distanceやhost atan2fの値を
Windowsに一致したという推測で変更しない。

本番はcontrolled630＋DOUBLE594の1224 capture rowsをClassic/Smart、O2、ASan/UBSanで
計4896render再生し全exact。元AEXで102差分を新規再取得し、本番両cmd102/102一致、
入力/parameter payload/native hashを保持した。Lab76/94成分別990行3960render、
Lab Thin/Blur合成144行576render、typed HDR/最大25色等8120renderと48 atomic失敗、
旧公開126 output＋13 callback controlもPASS。
これらは重複を除いたunique入力数ではなく、native/controlled hostの証拠境界を保つ。

実Windows UCRTのatan2f、Windows/Mac実AE、全palette/threshold/任意float/HDR/geometry、
ROI/downsample、UI/project保存は未完。参照環境の関数欠落で測定が止まる箇所は分離できたが、
controlled atan2fをnative UCRTへ昇格しない。全10本の完全互換Goalはactive。

## CK-COLOR-HDR-011 — RGB/HSVの距離・正規化・Premultiplied演算を復元

独立13×5 paletteで6色空間、scalar/成分別、3深度、count1/2/4/25、重複・無効key、
Per Color/Keep/Replace/Premultiplied/precisionと異なる成分thresholdを記録した576条件を比較。
PF16はRGB/alphaを32768超まで、PF32はHDR、signed RGB/alpha、負ゼロと隣接FLOAT32、
subnormalを含む13種のbit値を使用した。PF32のalpha_hdr/combined profileは、奇数x+yで
alphaを2倍、偶数で−1倍するので、名前にかかわらずHDRとsigned alphaが混在する。
これはパラメーターの全直積ではない。528条件は元の固定worker、Lab94 scalarの48条件は
校正済みcontrolled host atan2f workerであり、native Windows UCRTへ昇格しない。

変更前はClassic/Smartとも560/576一致、16条件で差分。RGB scalar9、HSV scalar1、
HSV成分別6であり、このcampaignのLab/YUV/YCrCbは一致した。
FACT: 元AEXのRGB comparator 0x4190は平均絶対差ではなくFLOAT32ユークリッド距離を
sqrt(3f)*(FLOAT32 threshold+epsilon)と比較する。HSV converter 0x9e10はG/B branchで
逆数を先に計算し、hueをFLOAT32 inverse 360との積で正規化する。8bit source unpack
0x11450も1/255のFLOAT32逆数乗算であり、color parameterの別normalizationと一致する
とは限らない。3深度のPremultipliedはnormalized RGBとalphaをMULSSし、整数深度でも
中間値を再量子化しない。HSV成分別のCOMISS+JAはunordered結果をgreaterとして拒否しない。
有限subnormal入力でも逆数overflowからNaN hueが生じるので、この分岐規則が必要になる。

独立した1×1 gray sourceと同じbyte値のcolor keyのexported traceでも、source RGBとkey RGB、
変換後hueのFLOAT32丸めが異なることを観測した。source hue 0.2777777910232544、key hue
0.27777794003486633となり、元の比較はhue wrapを通る。見た目が同じ色という理由で値を
補正しない。測定値と保持したlocal traceのhashをvalidationへ記録し、raw traceは公開しない。

最初の距離/HSV演算案は両cmd/O2/sanitizerで2280/2304render一致し、HSV成分別6条件を
残した。source正規化、Premultiplied、unordered分岐も復元した案は2304/2304一致。
同じ一般処理を本番へ適用した。fixture識別や最終byte補正を使わない。本番576条件を
元AEXで再取得しClassic/Smart全exact、入力・parameter payload・workerとnative出力hashを
全行で保持した。本番の同じ再生2304renderもO2/ASan/UBSan全exact。

本番変更後、Lab94 scalar/DOUBLE1224行4896render、Lab状態/境界990行3960render、
Lab Thin/Blur144行576render、従来typed8120renderと48 atomic失敗、旧公開126 outputと
13 callback controlがPASS。generic pairwise36＋sanitizer22、ROI/tileもfunction runnerでPASS。
これらは重複を除いたunique条件数ではない。過去reportのsource/hashを付け替えず、新しい
validationで今回のsource/tool/test/report依存hashと結果を保持する。

全入力・palette・threshold・geometry・設定、native Windows UCRT/AE、Mac installed、
UI/project保存、ROI/downsample・色管理は未完。全10本の完全互換Goalはactive。

## CK-YUV-012 — YUV/YCrCbのFLOAT32しきい値とunordered判定を復元

RGB/HSV/YUV/YCrCbのscalar/成分別、3precision、3深度、opaque blueとPremultiplied付き
partial grayの144族を元AEXで測定した。単色cyan key、Keep on/Replace off、同じtyped
1×1入力で、threshold0のnonmatchと1のmatchを確認してからFLOAT32 bit順で探索。
各族の最後のnonmatchと最初のmatchは隣接bitsであり、両方を再測定した。周囲5個の
FLOAT32値と間隔を1/16で横切る7個のDOUBLE値、計1728条件を公開ownerで取得した。
Per Colorはsampleごとに交互に変える。全設定の直積や任意paletteの単調性は主張しない。

変更前は1536/1728一致。RGB/HSVの864条件は一致し、YUV/YCrCbで192差分。
FACT: YUV comparator 0x4850、YCrCb comparator 0x4910はFLOAT32 thresholdを読み、
MULSS scale→ADDSS epsilonで許容幅を作る。旧MacのDOUBLE threshold+epsilonは異なる
境界になる。両比較のCOMISS+JAはgreaterを拒否し、unorderedを許容する。しきい値を
floatへ丸めてからfloat加算し、greater判定を復元した一時案は両cmd/O2/sanitizerの
6912render全exact。現行復元のunity scaleは測定した境界・color/HDR campaignに支えられた
推論として扱い、resident各frameのscale読出しを得たとは宣言しない。

有限のPF32最大値±0x7f7fffff、alpha2/最大値、RGBの4符号pattern、Premultiplied off/on、
Keep off/on、threshold0/1を同じ4空間・scalar/成分別で比較した512条件も取得。
入力channelはすべて有限だが、積がoverflowし色変換内でInf−Inf等がNaNを作る。
旧Macは448/512一致、YUV32とYCrCb32で64差分。一時案は512全exact。非有限入力を
通した結果や、通常AE UIがこの極端なraw worldを生成する証拠とは混同しない。

さらにFACT: 元比較は第3の色成分の距離を使わないが、第3の許容幅について
YUV 0x48f2/0x48f5、YCrCb 0x4980/0x4983のCOMISS+JBで負値/unorderedを拒否する。
正常UIの非負thresholdでは通る検査だが、元処理の復元から外さない。3深度、両空間、
Global/Per Colorの第3thresholdを−epsilonの前後で変えた108条件を測定した。
60条件は通常UI範囲外の負threshold、48条件は範囲内。旧Macの24差分は全て範囲外の
診断であり、保存projectからの到達性やWindows UIの生成可能性は未検証。
第3thresholdも選択・FLOAT32加算し、limit>=0を確認する案は108全exactだった。

同じ一般処理を本番へ適用。画像やthresholdでfixtureを識別せず、最終byteを補正しない。
境界1728＋finite-overflow512＋第3limit108の2348 capture rowsを両cmd/O2/sanitizerで
9392render再生して全exact。歴史的280差分（通常境界192、極端有限値64、UI範囲外24）を
元AEXから再取得し本番Classic/Smartで全一致、入力・設定payload・native hashを維持した。
一時完全案と本番はコメントだけが異なることも確認した。

従来color/HDR576行2304render、typed2264行の8120成功renderと48 atomic失敗、公開126
output＋13 callback control、generic pairwise36＋sanitizer22、ROI/tileが本番変更後PASS。
Lab-only/full Thin・Blur campaign、full generic gate/性能は今回再実行していない。
source/report/tool/testの依存hashと参照境界を新しいYUV validationへ記録した。

Windows UCRT/実AE、Mac installed、任意入力・palette・geometry・設定、UI/project保存、
ROI/downsample・色管理は未完。全10本の完全互換Goalはactive。

## SM2-COLOR-SCAN-013 — 色・半透明の走査検証と正の小画像の公開受付

4×3の8近傍を自然入力から作り、colored/partialの256分類×2 profileをv1 PF32で測定。
さらに16分類×colored/partial/premul/epsilon×7組のSmoothness/Range/Extra×両version×
3深度を測定した。512＋2688条件の出力とclass planeはすべてローカルAEXと一致。
内部参照はtyped inputから正規化したRGBA scratchと文書化済みconfig ABIを使い、
v2はcaptured LUTを使う。公開builder、入力world unpack、native Windows UCRT/AEの
検証へ昇格しない。Mac observerは一時コピーでclass planeを読むだけで、置き換えない。

最初の集計では2688条件の384件にhistogram差があった。これはnative側がclass plane
から算出した理論index、Mac側が実行したdispatch数で、異なる対象を比較したため。
FACT: Smoothnessは0xc2bbのMOVD→CVTDQ2PS→DIVSS、0xc2c7のUCOMISSで0と比較し、
JP/JNEがactive側へ分岐する。0ではindex生成前に処理を省略する。実AEXの0xc50a
CMP EAX,0xfc直前をread-only hookで観測し、3200条件を再取得した。入力・native出力・
class plane hashを保持し、実dispatchも全一致。384件は双方の実行回数が0であり、
出力の不具合としてソースを変更しない。元の理論histogram reportはそのまま保持する。

7×9/17×19のdiagonal/staircase/islands/ramp_alpha、3組の設定、両version・3深度の
144条件も出力・class plane・実dispatchが一致。scan長やweightを変える独立patternであり、
全走査長・任意float・全設定の証明とは扱わない。

公開経路は固定AEXCompat resident workerの実AEX EffectMain/parameter builder/Smartを
使い、MacのCLI-shim EffectMain SmartPreRender→SmartRenderと比較した。7 geometry
（1×1、1×9、9×1、2×2、4×3、7×9、17×19）×2 pattern×3設定×両version×3深度の
252条件。Gamma None/Key off、gamma値はnative defaultのFLOAT32 2.4をDOUBLEへ昇格。
最初の試行はMac harnessのwidth/height/downsampleとcheckout ref寸法が未設定であり、
互換性差の測定として採用しなかった。host authorityを設定して再測定したbaselineでは
17×19の36条件がexact、小画像216条件がbeta-only最小16×16条件で拒否された。
元AEXの全252条件はSmart成功、guards intact、unsupported suite callsなし、session clean。

小画像の拒否は一般処理へ入る前の受付差。候補ではSmartPreRenderとgeneric admissionの
最小寸法を1へ変更し、同じ252条件のO2/ASan/UBSan504 renderがexact。同じ規則を本番へ
反映した。fixture whitelistや数値本体、LUT、最終byteは変更しない。公開本番再生504 render
と元AEX252条件の再取得も全exact。入力・設定payload・元の出力hashはbaselineと保持。
上限8192、等倍、full-frame、原点/stride/非重複、parameterとatomic cleanupの契約は残る。
これは全Windows geometryの受付完了ではない。

本番の内部3344条件をO2/ASan/UBSan6688 render再生し、出力・class plane・実dispatchが
全一致。従来114 retainedと65分類390行も再生PASS。default beta4、Gamma Colors3、
ROI3のunittestがPASS。新しいpre-render検証は21合法条件、126不正host条件と21 ref寸法
不一致を検査し、拒否時にcallback/outputの契約を保持。実SDKのO2 universal buildも成功。
build成功はnative AE/installed検証の代わりにはしない。依存hashと証拠境界は
reports/olmsmoother2_color_weight_validation_20261001.jsonへ記録する。

tiny geometryのKey/Gamma、任意float/HDR、未測定scan長、native Windows UCRTのLUT構築、
native両AE、UI/project保存、ROI/downsampleと8192上限は未完。全10本の完全互換Goalはactive。

## SM2-KEY-GAMMA-HDR-014 — 空Gamma paletteの受付とPF16書き込みを復元

同じ固定resident workerで公開AEX builder/Smartを実行し、独立parameter-file harnessで
Macの公開SmartPreRender→SmartRenderを比較した。7 geometry、diagonal/ramp_alpha、
Key/Invert、Gamma None/All/Colors、値1.0/1.8/native default 2.4000000953674316、
count0/1/2/3/5、色順・重複・不一致を含む独立15 state、両version・3深度の1260条件。
15 stateの中ではSmoothness/Range/Extraも変更する。全parameterの直積ではない。
変更前は1008 exactと252拒否。拒否はすべてGamma Colors count 0で、元AEXは成功した。

FACT: a9c0はgamma paletteのbegin/endを比較し、count0では一致候補を返さない。
bb10は中心とpolygon sampleに一致候補がなければapplyを0にする。現行Macの数値本体は
同じ空palette規則を持つがgeneric admissionだけがcount>=1を要求していた。通常公開sliderの
count0を受付へ戻す。gamma指数やpaletteのalpha/順序を補正しない。count6の拒否は保持。

さらに4 geometry×2 pattern×3 Key state×両versionについて、PF16のrgb_hdr/alpha_hdr/
combined、PF32のrgb_hdr/rgb_signed/alpha_hdr/alpha_signed/combined/float_bitsを取得した
432条件。PF16はsource uint16を2倍して65535で上限、PF32は2倍または符号変更。
float_bitsは有限subnormal、負ゼロ、1の隣接値、負値・2.0と独立alphaを含む。
これらは著作したtyped worldであり、通常AE UIで生じることの証明ではない。
GammaはNone、Smoothness/Range/Extraは49/2/50。変更前は346 exact、PF16だけ86差分。
PF32の288条件は全exactで、PF16差分の内訳はrgb_hdr/v1=18、alpha_hdr/v1=17・v2=17、
combined/v1=20・v2=14。1×1のv1赤channelでもMacは32768、元はそれを超えるraw word。

FACT: PF16 worker3990の3bdd以降はMULSS（32768）→ADDSS（0.5）、3c02/11/1b/25の
CVTTSS2SI RAX、3c0c/16/20/2aのMOV word AXでARGBを保存する。32768や65535への
clampはない。旧clamp16を、別々のFLOAT32積と加算→signed64 truncation→下位16bitへ
変更する。非有限・signed64範囲外のx86 indefinite値INT64_MINは下位16bitが0なので、
C++の範囲外castを行う前に0を返す。上位/下位bitsを一般規則で扱い、画像別補正はしない。

元AEXの3bdd–3c2f命令区間を、明示したXMM input/scale/halfとread-only停止hookで
切り出して569 tupleを測定。丸め境界、負値、uint16 wrap、signed64境界、非有限と
seed付き512 bit値を含むwriter-only診断であり、公開worldやAE UIの証拠にしない。
全tupleに青2.0を置くため旧Macの全569 raw tupleは不一致だが、569個の独立frame不具合を
意味しない。loader初期MXCSR0の診断を保持し、明示した0x1f80（nearest-even、例外mask）
でも再取得。入力・native出力hashは全て保持された。0x1f80は選択したemulation環境であり、
Windows AEの読出しとは宣言しない。公開保存物はhashとinput bitsのみで、native raw wordは
保持したローカル診断から公開reportへ含めない。

空paletteとwriterの2規則を適用した候補は公開1692条件をO2/ASan/UBSan3384 renderで
全exact。writer-only569 tupleも両buildで全exact。同じ一般処理を本番へ反映し、公開3384
再生と元AEX1692条件の再取得で全exact、baselineの入力・parameter payload・native hashを
維持した。PF8/PF32 writer、LUT、scan/weightは変更しない。

本番変更後、色/scan内部3344条件6688 render、以前の公開252条件504 render、retained114と
65分類390行も回帰PASS。writer-only569 tupleもO2/ASan/UBSan1138再生全exact。
Gamma Colors3、default beta4、ROI3のunittestとuniversal実SDK O2 buildがPASS。
source/report/tool/test依存と実行結果は
reports/olmsmoother2_key_gamma_hdr_validation_20261001.jsonへ記録する。

HDRとGammaを同時に変える入力、全float/geometry/走査長、native Windows UCRT/AE、
Mac installed、UI/project保存、ROI/downsampleと8192上限は未完。全10本Goalはactive。

## SM2-GAMMA-MEMBERSHIP-015 — v2 Gamma Colorsのinverse LUT判定を復元

公開resident AEX SmartとMac public parameter-file harnessで、PF16高値3 profile、PF32の
HDR/signed/alpha/float_bits/seed固定finite profileを比較した。4×3/7×9/17×19、
diagonal/ramp_alpha、独立7 Gamma/key/count/smoothing state、両versionの840条件は変更前から
全exact。random_finiteはRGBをseed付きLCGで-4..4（1/256刻み）、alphaを0/-0.25/0.5/1/2
から構成し、このprofileではpattern名を入力生成へ使わない。840条件を840独立入力とは呼ばない。
通常AE UIでの高値world到達を証明するものではない。

さらにPF32 4×3、4 RGB anchor、3成分・両側境界、5隣接bits・2 alpha・両version・
Gamma Colors/Key/Invert Keyの1440条件を取得した。境界中心はFLOAT32色値±元の許容幅
0x3b008081から見積もり、全transitionを二分探索したとは宣言しない。旧本番は1424 exact、
16差分は全てv2 Gamma Colors。例: RGB(41,83,137)のR下側bits 0x3e22a2a3..a5と
上側0x3e26a6a7..a9。差は72 byteで最初はbyte36。Key/Invertとv1は一致した。

FACT（static）: a9c0はconfig+8のversion flag非zeroでtransferを飛ばす。zeroの場合は
config+16のctxを使い、ctx+16のlengthが0なら4d70の数式、非zeroならaa39/aa4a/aa5cで
4c30を呼ぶ。4c30は入力<=0を0、>=1を1へ戻し、(length-1)*入力をDOUBLEで計算して
index/fractionを求め、隣接FLOAT32要素とDOUBLE積・加算で補間しFLOAT32へ丸める。

FACT（公開read-only trace）: 独立4×3 PNG、Gamma Colors count1/value1.8、色(41,83,137)
のv1/v2をrender-trace-png Smartで取得。v1のflag1ではGammaからの4c30観測0回、v2のflag0で
12回、呼出し元は上記3 RVA。両ctx lengthは10000、v2のinverse LUT先頭4096 byteのSHAは
既存captured encode LUT先頭と一致した。watch上限は4096であり、40000 byte全表のreadbackや
native Windows UCRTのbuilder一致とは呼ばない。PNG traceは境界resident frameとは別の入力と
host経路で、分岐到達の証拠。private trace/PNGを公開せずhashと経路metadataだけ保持する。

INFERENCEと修正: 旧Macのv2 palette判定は常に4d70数式を選んでいたが、公開元AEXの
setupは非空inverse LUTを使う。既存win_srgb_lut_interpolateをv2の候補RGBへ適用する。
v1、比較許容幅、palette値、LUT内容、pow依存先、走査、最終byteは変更しない。
一時候補の2280条件O2/ASan/UBSan4560再生は全exact。本番へ同じ一般規則を反映し、
本番4560再生と固定workerで元AEX2280条件の再取得も全exact。baselineのsource SHAは保持し、
入力・parameter payload・native hashが全て同一であることを新しいtestで検証する。

従来の公開1692条件3384再生、以前の公開252条件504再生、色/scan内部3344条件6688再生は
全exact。retained114と未到達390行、Gamma Colors3/default beta4/ROI3の回帰もPASS。
実SDK arm64/x86_64 O2 buildも成功。native AE/installed実行の代用とはしない。
実行結果と依存hashはreports/olmsmoother2_gamma_membership_validation_20261001.jsonへ記録する。
新probe/replayと保存物はruntimeに組み込まず、fixture別補正やoracle出力の書換えもしない。
任意float/scan長、全設定直積、full LUT/native UCRT/両AE/installed、UI保存、ROI/downsample、
8192上限と全10本の完全互換は引き続き未完。Goalはactive。

## DB-DUAL-INDEPENDENT-020 — 独立typed入力と長いDualを公開経路で比較

DirectionalBlurの次の未検証条件として、同寸法Noise Layerの非zero原点を検討した。
固定workerのResidentLayerEntryはslot/width/height/pathだけを受け付ける。実際にmanifestへ
origin_x=2/origin_y=1を加えるとunknown fieldとして終了した。これはfixture hostの表現能力の
不足であり、元AEXの非zero原点renderの拒否・数値差ではない。旧PF8 origin witnessは内部
render owner経路なので、今回の公開Smart証拠へ昇格しない。原点を0へ偽装した成功も作らない。

入力の独立性と走査長を拡張して、17×11/61×47、PF16/PF32、3 source profile×2 Layer profile、
Front31/Back47/Dual31+47、Layerのみ/components/Fade+Gainの216条件を公開AEXで取得した。
角度は89.99998474121094、-90.00001525878906、179.99998474121094。Size/Sharpには
fractional値、Noise量には73.75と0.25を使う。sourceとLayerのLCG seedは別々に保持する。
sparseは右端・下端・対角以外のalphaを0にしRGBは残す。PF16 raw_rangeはuint16全範囲、
PF32はRGB -2..6、alpha0/-0.5/0.5/1/2。boundaryは負ゼロ・subnormal・1の隣接bits等を含む。
通常AE UIでこれらのworldが生じるという意味ではない。Type3は宣言choices2の外のstateで、
通常UI/project保存の到達性を別に扱う。

FACT: 固定workerのexported Smartは216条件全て成功、guards intact、session clean、
unsupported suite callsなし。実SDKを使うfake AE hostのMac Classic/Smartも全216条件で
元のactive bytesと一致し、数値本体は変更していない。source+5/output+11/Layer+7のstride、
source/Layer/padding不変、拒否時atomic、suite balance、Smartの21 parameterと2 Layerの
checkinを既存の公開harnessで検査する。元側のworldはtightで、Mac側のodd stride証拠と分ける。

O2とASan/UBSanで両公開cmdを再生する新しい回帰を追加し、864 render全exactでPASS。
sourceと数値coreの変更を
強いる新しい反例はまだないため、ここでentrypoint解析を繰り返さず次のRadialBlur topologyへ
切り替える。実行結果・source/core/probe/harness/report hashは
reports/directionalblur_dual_independent_validation_20261001.jsonへ記録する。
非zero Layer原点、native Windows UCRT/AE・installed、通常UI/保存、ROI/downsample、
全入力/全設定/巨大画像と全10本の完全互換は未完。Goalはactive。

## RB-SDK-PARAMETERS-021 — Point比較条件とEdge Fade整数getterを復元

最初の公開getters30条件とtopology252条件は、MacのPointをpixelとして作りながら、
同じ数値をAEXCompatのPoint APIへ送っていた。このAPIは百分率をframe extentへ掛ける。
例えば20×14の(10,7)指定はnative configでは(2,0.9799957275390625)になり、Macの(10,7)と
揃っていない。旧captureとprobeを変更せず保持し、その0/30・24/252という一致件数を
移植本体の差分数や互換進捗として扱わない。これは参照・設定の不一致だった。

FACT: 新しいaligned probeはnative指定だけ100*pixel/extentへ変換する。公開Smartの
read-only 8690 returnを2 familyで採り、両側のCenterが(10,7)となることを確認した。
同時にOuter/Inner Edge Fade 50/37がnative config+0x6c/+0x70へi32で入ることを観測した。
PF_ADD_SLIDERと実SDKのu.sd.valueに対して旧Macはu.fs_d.valueを読んでおり、50/37が0へ
変わっていた。本番はこの2 getterだけをu.sd.valueへ修正し、数値kernelは変更していない。
公開gettersのaligned修正前2/30から修正後4/30へexactが増えた。4条件はZoomの標準と
Outer Fade50、それぞれPF8/PF16。残る20条件は画素差、6条件はOffset設定のMac拒否。

FACT: Angleのimport-free a2a0はADのraw i32を保存する。元8690の87c9..87f4だけを
実行する限定fragmentはraw*DOUBLE 0.017453292500000002をCVTTSD2SIで切り捨てる。
SDK Angle45のraw2949120は51471となる。Zoom4640/Rotation56f0の命令はその整数を
直接DOUBLEへ変換してcos/sinへ渡し、ここには65536除算がない。普通の度→ラジアンへ
「修正」しない。a2b0のOffsetはraw*DOUBLE 2.663161090079238e-07をFLOAT32へ丸める。
SDK Offset1のraw65536はFLOAT32 0x3c8efa35だが、旧Macは整数65536を読んで拒否する。
19 raw値の実leafと限定fragmentを保持し、full builder/exported traceとは区別する。
CLIは非zero typed Angle指定を表せないため、今回の公開traceではAngle/Offsetを省略した。
そのnative defaultのleaf値を記録し、明示的な0指定をtraceしたとは扱わない。
Angle/Offsetの本番修正と非zero公開中間値の採取は次の残件。

固定workerはaligned neutralの両familyでもlog2f未実装で終了する。元workerと外部sourceを
保持した一時コピーを作り、正のFLOAT32の2の冪だけのexact log2とhost FLOAT32 atan2を追加した。
他log2引数は明示的に拒否する。小さいMPL-2.0参照overlayとbuilder/hash manifestを保存し、
元AEX/worker/private trace/PNG/raw frameを公開しない。controlled importをWindows UCRTや
実AEと同一とは呼ばない。frozen worker missing importをAEXの設定非対応とも呼ばない。

FACT: 正しい中心でtopology252条件を再測定すると52 exact、116画素差、84 Mac拒否だった。
2 geometry・7 alpha/RGB pattern・2 family・3 depth・3 stateを使い、alpha0のRGBも残す。
84拒否は全てSize25/Noise0で、fixture component面積の許容集合が残る。標準Size0でも
差があるため、最初から全てを右端component処理の誤りへ帰属させない。gettersのZoom PF32
標準は27 byte差、Rotation標準はPF8 34／PF16 136／PF32 894 byte差があり、最初の
field/sampler値を採る必要がある。座標別の補正やnative出力の書換えは行わない。

本番の282条件をO2/ASan/UBSanのClassic/Smartで1128回再生し、保存した結果と一致した。
この再生には未解決の画素差と拒否が含まれ、1128回全てがAEX exactという意味ではない。
各buildの両cmd合計は112 exact・272画素差・180拒否。さらにSDKの合法整数Edge Fade
0..100を両getter・両cmd・両buildで404回検査し、設定値・input/padding不変・拒否時atomic・
checkout/checkinとsuite balanceを確認した。新しいunittest3本がPASS、既存generic baseline、
baseline sanitizer、Type3 sanitizer、budget、SizeNoise EffectMain、ROI contractの6本もPASS。
旧UI parity test1本のThickness文字列assertは変更前HEADでも同じFAILで、getter修正による
新しい失敗ではない。arm64/x86_64 O2実SDK buildは成功し、installed bundleは変更していない。
reports/radialblur_public_parameter_validation_20261001.jsonに実行結果と依存hashを保持する。
全設定・任意topology・native両AE/UCRT・UI保存・ROI/downsample・全10本の完全互換は未完。
Goalはactive。

## RB-TYPED-ANGLE-022 — 公開非zero Angleと整数化境界を復元

前回の非zero Angle/Offset trace未達はfixture CLIの表現能力の不足だった。hash固定の
controlled referenceを別の一時コピーへ移し、MPL-2.0 CLI parserだけに:angle指定を加えた。
resident v4と同じParameterValue.angleと元のmaterializerを通す。親source/workerは保持し、
元AEX・parameter setter・数学importは変更しない。親と新workerのresident30条件を再取得し、
入力とnative raw hashが全て一致することを校正した。元のfrozen workerもhash不変。

FACT: 公開Smartのtyped Angle12値×2 familyとOffset1/30×2 familyの28条件をread-only trace。
8690 config、a2a0/a2b0 getter、Zoom56f0/Rotation4640 initを採り、Center(10,7)、AD raw、
configの整数角度、Offset FLOAT32、transformのFLOAT32 cos/sinを観測した。private contextの
全byte/addressは公開せず、選んだscalar値・bits・trace/input/output hashだけを保持する。
同じ設定のresident出力とtrace出力も全28条件でraw hashが一致した。Angle45はraw2949120
から51471になり、Offset1は0x3c8efa35、Offset30は0x3f060a92へ変換されていた。

整数化境界のraw -20564372/-7055345/14253070/20963609では、旧kPiによる度変換・65536乗算
と元DOUBLE 0.017453292500000002を使う計算の結果が1ずれる。元AEXの整数値は順に
-358915/-123138/248762/365883。元のADをdoubleの度として読むため、Mac getterはSDKの
u.ad.value/65536へ変更し、kernelの整数化は(angle_degrees*65536)*元DOUBLE定数→truncへ
復元した。ADの32bit整数を2の冪で戻すので、publicのrawをこの順序で再構成できる。
cos/sinへその整数を直接渡す元の挙動を保持し、通常のラジアン引数へ置き換えない。
SDK builderとtransform引数・cos/sin bitsは28条件×O2/sanitizerの56再生で元の観測と一致。
このcos/sin値の一致はcontrolled host mathであり、Windows UCRT実装の証明ではない。

FACT: 本番の公開getters30条件は4→5 exactへ増加し、追加でZoom PF8 Angle45/Ratio2.25が
一致した。他の19画素差と6 Offset拒否は残る。新しいtyped28条件は11 exact、13画素差、
4 Offset拒否。O2/ASan/UBSanの両公開cmdで112回再生して保存した全結果を再現した。
旧Angle計算順だけへ戻した一時コピーでは4つの境界のZoom一致が全て崩れた。本番と
native出力は変更せず、その8 family条件の反証を別reportに保持した。

Rotationは元initの整数引数を再現できても、generic baselineのpolar生成が別のdouble経路を
選ぶため、この4境界で旧計算順へ戻しても出力が変わらなかった。このsource接続の差を
踏まえ、一時コピーだけでgeneric baselineを全て既存二段経路へ通す仮説を検査した。
typed14＋topology126の140 Rotation条件は12 exact・84画素差・44拒否のままで、12 exactは
empty topologyだった。この変更だけでは元の処理へ戻せないため本番へ採用しない。
同じentrypointやflag変更を繰り返さず、自然public経路のpolar field→normalized field→
final samplerで最初の不一致を採ることを次の手法とする。

以前の282条件はO2/ASan/UBSanの両公開cmdで1128回再生した。各buildの両cmd合計は
114 exact・270画素差・180拒否であり、回帰testのPASSを全画素exactとは呼ばない。
Edge Fade合法整数0..100の404設定読み取り検査も保持し、上記112新renderと合わせた
public再生は1644回。新typed test3本と既存public test3本、generic baseline・sanitizer・Type3・
budget・SizeNoise EffectMain・ROIの6回帰がPASS。arm64/x86_64 O2実SDK buildも成功した。
前回確認した旧Thickness文字列assertの既存FAILはUI設定変更で解消したとは扱わない。
実行結果とbindingはreports/radialblur_typed_angle_validation_20261001.jsonへ保存する。
Noise OffsetのFLOAT32化、Rotation/Zoom PF32・一般topology、Size25の面積制限、native両AE/
UCRT、installed、通常UI/保存、ROI/downsample、全10本の完全互換は未完。Goalはactive。

## RB-REFERENCE-AXIS-023 — 最初のZoom sampler差は比較workerの数学関数

前回のstatus確認では保存Windows scalar記録の正ゼロ/負x軸がMacと一致し、次の参照修正を
決める証拠が得られた。今回はその境界だけを変更したcontrolled workerを別コピーでbuild。
元のtyped source/worker、frozen workerとAEX、本番Mac sourceは変更しない。

FACT: 自然公開Zoom、17×11 opaque、PF32、Center(8,5)、neutralの画素(0,5)で、a850の
radiusは両者8（0x41000000）、angleは参照0x40490fda、Mac0x40490fdbだった。保存済み
Windows UCRT 10.0.26100.8875のatan2f(+0,-8)は0x40490fdb。native_rows全577行の既知hash
52bf76720eef963c77db0a9325f3902bbc9986ad9ce853930ca6f7ad0854d2bdを確認した。元return ZIPは
現在のshareに不在で、新しいWindows実行・原ZIPの再検証を行ったという主張はしない。

保存576 atan2f組を動的Rust host関数と比較し、host FLOAT32は556組、double atan2→FLOAT32
は576組で保存Windows scalar値と一致した。正ゼロ/負x軸の16組は全てhost0x40490fda、
Windows0x40490fdb。controlled importはy bits=0かつ有限x<0のときnearest FLOAT32 πを返す
数学上の軸規則へ変更した。xの固定key表や画素座標の補正を使わない。それ以外560組は
旧host関数を保持し、4組の非軸差も消したとは扱わない。負ゼロ・非有限値も変更しない。
INFERENCE: この軸規則は有限の負xへ一般化できるが、任意引数のWindows UCRT実装や
本番Macのdouble-cast全入力一致を証明したものではない。

FACT: 同じ自然公開AEX traceの86回目でangleが0x40490fdbへ変わり、9d80のnormalized RGBA
sampleもMac画素と一致した。旧controlled全raw hashはf2832217a8feb67c2b798a136ec51cb13d03d236bdd0a3a9e68765dd28934aa6、新参照とMacは3de3223f730da49aad23ad76dab9404e6ef48a2e679a217b80bd4d1650a2c856。PNG traceのraw hashは同じ設定のtyped resident出力と一致。
この入力の差は移植kernelの修正対象ではなく、比較器・参照の問題へ分類する。private
trace/context、PNG、raw pixelsは公開せず、選んだscalar bitsとhashを保持する。

FACT: getters30＋topology252＋typed28の310条件を旧参照と新参照で計620回再取得した。
旧参照の310 raw hashは保存済み全行と一致。新参照では97条件のrawが変わり、26条件が
Macと追加でexactになった。既存exactを失った条件は0。gettersは5→7 exact、19→17差分、
6拒否。topologyは52→76 exact、116→92差分、84拒否。typed28は11 exact・13差分・4拒否
のまま。本番Macの全310行のraw/errorは修正前記録から変わっていない。新exactはZoomの
PF16/PF32で、独立geometryと島/ring/diagonal/opaque、neutral/Size100+Noiseも含む。
本番両cmdのO2/ASan/UBSan計1240再生で結果が一致。strict halt設定のsanitizer両cmdも
追加620回再生し、原因と参照のbindingを検査する4本のunittestがPASSした。

reports/radialblur_axis_reference_build_20261001.jsonに親不変とpatch/build identity、
radialblur_atan2_axis_scalar_20261001.jsonに保存Windowsとの576 scalar比較、
radialblur_axis_reference_public_20261001.jsonに310 public行、
radialblur_axis_sampler_first_difference_20261001.jsonに最初の境界、
radialblur_axis_reference_validation_20261001.jsonに実行と現行bindingを保存する。
参照修正を本番修正として数えない。OffsetのFLOAT32化、Rotation・残るZoom field/sampler、
Size25制限、一般UCRT/native両AE、installed、UI保存、ROI/downsample、全10本完全互換は
未完。Goalはactive。

## RB-NOISE-OFFSET-024 — 公開ADからFLOAT32位相とノイズ格子への接続を復元

前回の参照軸修正・310条件再測定・Pushはprogressだった。今回は残っていた公開Noise
Offsetの型・単位を、元getterから自然公開格子と出力まで比較して本番へ接続した。

FACT: import-free a2b0はAD rawのsigned32をDOUBLEへ変換し、元定数
2.663161090079238e-7（bytes399d52a246df913e）で乗算し、FLOAT32へ丸めて書く。
従来MacはAngle型のrecordをu.sd.valueとして読み、A_longに生fixed値を保持していた。
本番getterをu.ad.value→上記定数乗算→floatへ変更し、info.noise_offsetの型もfloatへ変更。
内部noise格子は元からfloat位相を受け取る。UI1°は0x3c8efa35、30°は0x3f060a92であり、
生fixedの65536/1966080をそのまま位相として渡す挙動を復元規則とは扱わない。

FACT: 公開元AEXの初回9680 samplerから、初期化済みcontextとnoise格子をread-only採取。
9380 constructor-entryのderefは未初期化で、返却時にもentry時のpointerを使うため、
その読取りを格子の証拠に使わない。Zoom/Rotation、23×13/31×19、Type1 seed1/Thickness3、
Type1 seed2/Thickness10、Type2 seed1/Thickness10、raw0/1/16384/65536/1966080/5898240/
23592960/INT32_MAXの96条件で、元のAD変換と既存coreのnoise格子全byteが一致した。
格子はsampler前後で不変、PNG traceのraw hashも同じ設定のtyped resident出力と全行一致。
元context/格子の全byteや画像は公開せず、scalar bits・全格子hash・先頭4 floatだけを保持。
これはcontrolled importを使う公開AEXの証拠で、native Windows AE/UCRT比較とは分ける。

FACT: 本番を変更する前に、旧source、getter/typeだけ直すsource、位相profileも直すsource
を別コピーで比較した。旧0/1だけの位相条件では、getterだけ直しても拒否を解消できない。
元の正の位相はTABLE100への加算と100減算wrapで処理され、full signed ADの非負入力では
生成positionが有限でindex0..99に保たれる。既存Type1のseed/thickness組とType2のseed1/
quality/thickness組で、この一般位相規則を採用。noise量と他controlの制限は別に残る。
負位相にはCVTTSS2SIの負indexからtable前を読む境界があり、実際の契約は未検証。
負を正へwrapする新仕様や固定case補正を発明せず、未完として記録する。

既存310条件は94 exact・122差分・94拒否から、99 exact・127差分・84拒否へ変わった。
既存exactを失った条件は0、Offset10拒否はすべて解消し5条件が追加exact、5条件は他の差を
保持する。getters30は10 exact・20差分・0拒否、topology252は76 exact・92差分・84拒否、
typed28は13 exact・15差分・0拒否。Offset0の全行は旧raw/errorと同じ。

独立23×13/31×19の384条件は、2 family・3深度・Type1二組/Type2二組・Noise25/100・
Offset0/1/90/360°を公開residentで取得した。旧32 exact・64差分・288拒否から、129 exact・
255差分・0拒否。追加97 exact。Zoom PF16の64条件は全exactだが、Zoom PF8は33/64、
PF32は32/64、Rotationは0/192 exactである。格子は復元できてもfield/scatter/sampler/writerの
他の境界は閉じていない。31×19は保存Windows scalarでhost atan2f差がある(±8,9)を含むため、
残差を全て移植bugと断定せず、参照を再監査することを次の手法とする。

本番sourceは9a4e9eddec319185c01d2dd289d586aa41e3aafeca7aeefe23d1a86cd3243548。
別コピーの本番候補と同じsource/header hashを確認してから適用した。実SDKのNoise Offset
readerは負値を含む148 raw入力×O2/ASan/UBSanの296再生で元のimport-free getterとbit一致。
694公開条件のO2/strict sanitizer両cmdは2776再生で別コピーの全raw/error/metadataを再現。
新3 unittest、更新したpublic parameter/typed Angle/reference-axisの10 unittestもPASS。
後者は過去source/headerの記録を保持し、現行再生だけを今回のcandidate bindingへ移した。
Edge Fade合法0..100も両getter/両cmd/両build404回維持。現行public再生合計は5040回、
Noise Offset296＋Angle56のSDK scalar再生は352回。旧sourceの別コピー比較3544回、公開AEX
trace96＋resident96＋独立resident384も別に保持する。テストPASSを未解消画素のexactとは
呼ばない。generic baseline・sanitizer・Type3・budget・SizeNoise EffectMain・global polar ROI
の6回帰と共通ROI契約もPASS。arm64/x86_64 O2実SDK buildも成功し、installedは変更しない。

reports/radialblur_noise_offset_field_20261001.json、noise_offset_counterfactual_20261001.json、
noise_offset_validation_20261001.jsonへ根拠・反証・現行bindingを保存する。負位相、任意
seed/thickness/noise量、Rotation/Zoom残差、参照の非軸4 scalar差、Size25制限、一般UCRT/
native両AE、installed、UI保存、ROI/downsample、全10本完全互換は未完。Goalはactive。

## RB-REFERENCE-NONAXIS-025 — 保存Windows scalarを根拠に参照の非軸差を分類

前のNoise Offset復元とPushはprogress。直近の状況回答はstatus再掲のno progressだった。
今回は未Pushだった参照校正を検証し、未知の角度を分けたcheckpointとして保存する。
本番source/header、元AEX、旧参照と固定workerは変更しない。

FACT: 31×19 opaque Zoom PF32の自然公開9d80 samplerとa850角度を採取した。
画素(30,16)/(24,17)の相対(y,x)=(7,15)/(8,9)で、旧host f32角度は
0x3edf8d99/0x3f3a053b、保存Windows UCRT scalarは0x3edf8d98/0x3f3a053cだった。
MacのDOUBLE atan2→FLOAT32は後者と一致。旧参照rawとMacは2画素・5byteだけ相違し、
参照を同じDOUBLE→FLOAT32へ変えると両画素の角度とsampler RGBA、全rawが一致した。
これは移植kernelの修正とは分け、比較参照の差として分類する。

FACT: 親axis参照を別コピーし、callbacks.rsのatan2f importをDOUBLE→FLOAT32へ変更した。
診断上のtrace witness上限は256→1024へ増やした。この2ファイル以外の親source全manifest
と親workerは不変。新worker hashは722255eed6de0246f3918a11837d21eae0cb6cd6286ed1ae2d49f823ee92f4ec。
保存Windows scalar576組を再実行して全組一致。これは保存測定の有限集合に対する校正で、
一般引数のUCRT実装復元や新規Windows実行とは扱わない。

FACT: 23×13/31×19の自然公開Zoom角度299+589=888回を採取。actual builderの中心と基底を
確認し、保存Windows scalarから元AEX定数DOUBLE 6.2831853で負角度をwrapした期待値と比較。
857回はnative scalar測定済みで全bit一致。31×19の下端y=18の31回は相対y=+9で未測定。
この31回の座標を明示し、他857回の一致を全角度のWindows証明へ一般化しない。
両caseのtrace rawはtyped resident rawと一致。private全vector/context/raw/画像は公開しない。

FACT: 既存310＋独立384の694条件を親/校正参照で1388回取得し、親全raw hashが前回記録と一致。
本番MacのO2/strict ASan/UBSan両cmd計2776再生は全行の以前のraw/error/metadataを維持。
参照校正で35条件が追加exact、旧exactを失った条件は0。694条件は228→263 exact、347差分、
84拒否。getters30は12 exact・18差分、topology252は76 exact・92差分・84拒否、typed28は
14 exact・14差分。独立384は161 exact・223差分・0拒否。Zoom PF16/PF32各64/64 exact、
PF8は33/64 exact、Rotation各深度は0/64 exact。参照補正による一致を本番修正の件数に足さない。

4 unittestでnative scalar再実行、全694行の設定・fixture・参照epoch・本番不変、857/31の
既知/未知境界、selected samplerと全rawのbindingを検証しPASS。追加一致35条件と残差代表、
拒否代表を含む47条件はO2/strict sanitizer両cmd188回再生しPASS。本番source/headerは前回
Pushと同じためUniversal buildとgeneric回帰は前回検証をhash bindingで保持し、再実行しない。
reports/radialblur_doublecast_reference_build_20261001.json、doublecast_reference_public_20261001.json、
doublecast_sampler_native_coverage_20261001.json、doublecast_reference_validation_20261001.jsonへ保存。

未完: Zoom PF8、Rotation、Size25制限、任意noise条件と負位相、未測定角度、一般UCRT、
native両AE、installed、通常UI/保存、ROI/downsample、全10本完全互換。Goalはactive。

## RB-ZOOM-PF8-WRITER-026 — 自然samplerの一致を根拠に共通書き戻しを復元

前の参照校正・テスト・e1d2069cのPushはprogress。本番を凍結したままZoom PF8の最初の
差を採取し、field/samplerの問題ではなくwriterの演算順序へ分離して修正した。

FACT: 23×13 opaque、Zoom、Noise100/Type1/seed1/Thickness3/Offset0の公開出力は55byte差。
最初の画素(14,0)でnative samplerのredはFLOAT32 0x3f11918d、旧Macのdebug scalarも同じ。
元writerは0x90、旧Macは0x91を出していた。Mac共通Zoom writerはRGBに1e-4を足し、DOUBLE
255倍をfloorしていた。元AEX 7520 public ownerは7bdd..7bf6でbrightness-scaled RGBを
MINSS 1.0へ上限処理し、7c14で17400 writerを呼ぶ。17400はMULSS 255→CVTTSS2SI→low-byte
ARGB保存。epsilonもDOUBLE乗算も下限clampもなく、alphaはMINSSを経由しない。
旧コメントの173f0は元AEXではpaddingであり、根拠を実際の17400へ修正した。

FACT: 23×13/31×19、Noise25/100の4自然公開caseをtyped residentとPNG traceで取得しraw
hash一致。各4点の9d80 sample RGBAは旧MacのFLOAT32値と全bit一致。17400で保存された
ARGB8を同じ点の出力へ結び付けた。Noise25の両geometryは旧rawもexact、Noise100の55/130
byte差はwriterを復元した別コピーで全raw exact。全context/trace/raw/画像はprivateのまま。

FACT: 本番変更前に694条件を別コピーのO2/strict ASan/UBSan両cmdで2776回比較。
45条件が追加exact、旧exactを失った条件0、raw変更51条件。6条件はwriter以外の差を残す。
誤差を座標やfixture別に補正せず、共通WriteZoomへ元ownerのMINSSとFLOAT32整数化を採用。
本番source hashは877fadcded9fb3b004902195f3041f98a7596154c783749eb0ce21c8277adafa、header不変。

最新694条件は263→308 exact、302差分、84拒否。getters30は12 exact・18差分、topology252は
76→90 exact・78差分・84拒否、typed28は14 exact・14差分。独立384は161→192 exact・192差分。
独立ZoomのPF8/PF16/PF32はそれぞれ64/64 exact、Rotationの各深度64条件は全て差を残す。
比較参照は前回のcontrolled DOUBLE atan2→FLOAT32のまま。保存Windowsの未測定31角度や
任意引数をnative exactへ昇格させない。有限条件のZoom一致を全機能の完成とは扱わない。

本番適用後に3 unittestがPASS。694条件の両cmd/O2/strict sanitizer2776回は別コピーの全
raw/error/metadataを再現。元import-free17400の1098組（整数/255の隣接FLOAT32、負値、負ゼロ、
NaN/Inf、int32変換範囲外と独立bit列）に対し、実SDKの本番writerはO2/strict sanitizer2196回
のARGB byteが一致。RGBには実ownerのMINSS 1を渡し、alphaはそのまま、leaf後のsentinel12byte
とimport未使用を確認した。自然公開証拠に加えるscalar検証で、手製builderの証明ではない。

過去captureは書き換えず、5既存testの現在の期待値だけを最新source/hashへ結び付けた。
既存16 unittestもPASSし、public parameter1532・typed112・axis620・doublecast188の計2452
public再生とNoise Offset296/Angle56のSDK readerを維持。Noise grid96も維持。現在のpublic
再生総数は5228、SDK writer/readerは2548回。新しいfull694再生と同じ処理を行う旧Noise Offset
full再生だけは重複実行せず、そのreader/grid2testを実行した。generic baseline/sanitizer/
Type3/budget/SizeNoise/global polar ROIと共通ROIの7回帰PASS。arm64/x86_64 O2実SDK build成功。
installedは変更しない。元AEX・固定worker・controlled worker・外部SDK入力の不変もhash確認。

reports/radialblur_pf8_writer_public_20261001.json、pf8_writer_validation_20261001.jsonとprobe、
実SDK writer harness、testへ根拠を保存。Rotation、残るZoom、84拒否、任意noise/負位相、
一般UCRT/native両AE、installed、UI保存、ROI/downsample、全10本完全互換は未完。Goalはactive。

## RB-ROTATION-FIELDS-027 — 自然fieldの全量比較とSIMD Gaussian・逆変換の分離復元

直前の進捗説明だけのturnはno progress。元AEXと本番sourceを再確認し、自然公開経路の
Rotation中間fieldを採取する作業へ戻った。本番sourceは877fadcd、HEADは790921e8のまま。

FACT: 23×13 opaque、Rotation、center(11,6)、Outer4、Inner0、repeat、Quality5、Noise25、
Type1/seed1/Thickness3/Offset0のPF32公開出力は620byte差。SDKの本物のparameter unionから
EffectMain Classicへ入り、既存のpassive seamだけで全planeを採取した。手製のnative builderや
contextは使わない。元AEXのnative-owned領域は1800×15、Macは1800×16。末尾の追加行を除き、
polar108000語、source scalar27000語、Cartesian span299語、max alpha27000語は全bit一致。
accum108000語には187差、normalized108000語には157差が残った。追加行の契約は未閉鎖。

FACT: 元B680はvector分岐で1d0e0を呼ぶ。自然public traceでこのdirect callを観測した。
1ebc0の普通のGaussian引数域は64分割の2^fraction mantissaと2*r+2+r*rをFLOAT32順序で
組み合わせる内蔵SIMD exp。単にimported expfの丸めを疑った前の説明は不十分だった。
元tableの64 mantissaは2^(i/64)から生成して全bit確認した。Gaussian引数30000個を7500回の
元import-free vector leafで再実行し、scalar transcriptionと全bit一致。自然B680の30000語も
同じmodelへ全一致。従来DOUBLE exp→FLOAT32とは13090語の差がある。

FACT: 別コピーでRotationGaussianWeightsだけをSIMD polynomialへ置き換えると、代表の
accum/normalizedを含む6plane計378299語が全bit一致。O2とstrict ASan/UBSanも同じ。
全694条件を両公開cmd・両buildで2776再生したところraw変更69、追加exact0、lost exact0。
308 exact・302差分・84拒否は本番のまま。重みの一致だけでrenderer完成と扱わない。

FACT: さらに自然AEXから全299画素の1b10 radius/angleと1000 sampler RGBAを898 read-only
witnessで取得。旧Macは座標598語中183差、sample1196語中573差。Gaussian復元コピーも同じ。
元1ac0 setterはFLOAT32(1/Quality)→DOUBLE 0.017453292500000002乗算→FLOAT32 stepRad→
FLOAT32 reciprocalでangleScaleを作る。Quality5では0x438f3d4d。旧generic finalはDOUBLE座標
経路に入り、このsetter順序も使っていなかった。別コピーのgeneric two-stageのfinalだけを
既存FLOAT32座標/sampler/writerへ接続し、このsetter順を復元すると座標とsampleが全一致し、
代表の最終rawも元AEXと全bit一致。元データへ座標別の補正値は加えない。このinverse候補は
まだ全694条件やsanitizerで検証していないので、本番には反映していない。

参照境界: passive windowの一時workerはcontrolled DOUBLE atan2 parentのコピーだけを変更。
callback/import/math実装とparent source/workerは不変。既存4096byteの上限は維持し、pointer
解決後のbyte offsetを追加した。403window＋dispatcher1件の404witnessは非truncated。
親とwindow workerはZoom/Rotation×3深度×2geometryの12条件、計24resident取得で同じraw。
offset未指定・明示0・16byte窓の実測と、duplicate/offset上限/deref上限/size上限の拒否も確認。
Unicorn RCPPSはFLOAT32除算で、Windows CPUの近似逆数とは異なる。30000の分母ではその
Newton refinementと元のDIVSS逆数が同bitだが、実WindowsのISA分岐・RCPPSを証明しない。

4 unittest PASS。元vector leaf全30000引数、自然SDKのbefore/Gaussian候補の両cmdとstrict
sanitizer、全native planeの再取得、親との24resident取得、窓0/16と不正値、inverseの全画素
再取得を確認。第三者AEX・全trace・raw・plane・画像はprivateのまま。公開するのはprobe、
passive patch/builder、hash/count/scalar根拠だけ。source/headerが前回検証と同hashなので、
既存7gateとUniversal実SDK buildの証拠はhash bindingで維持し、同じ本番を再buildしない。

reports/radialblur_readonly_windows_reference_build_20261001.json、rotation_fields_20261001.json、
rotation_inverse_20261001.json、rotation_fields_validation_20261001.jsonへ保存。
次はinverse候補を全694条件とstrict sanitizerで比較し、差分を閉じる一般処理として本番へ
反映できるか判断する。Size25/負位相/任意noise、未測定UCRT/ISAとnative両AE、通常UI/保存、
ROI/downsample、全10本完全互換は未完。Goalはactive。

## RB-ROTATION-RESTORE-028 — generic two-stageのGaussianとfinalを共通処理へ復元

前回の自然field採取・SIMD/inverse候補の検証・6d0904f8のPushはprogress。元AEXの自然
fieldとinverseに基づく候補を全694条件で比較し、本番へ一般化した。

FACT: 本番を877fadcdへ凍結したまま、別コピーのO2とstrict ASan/UBSan、Classic/Smartで
全694条件を2776再生。FLOAT32 exponentから元1ebc0のSIMD polynomialを使うRotation
Gaussianと、generic two-stage finalのFLOAT32座標/sampler/writer、1ac0 setter順のQuality
angleScaleを復元すると308→505条件がexact。追加exact197、lost exact0、raw変更237。
パラメータ、input、error、callback balanceなどのmetadataは保持。RGB/alphaの固定値や
座標別補正を加えず、実際に生成したfieldを共通final処理へ接続する。

本番変更はRotationGaussianSIMDExpとRotationGaussianWeights、final座標・fraction・
sampler・packerのgateに限る。既存two-stageのpolar生成/scatter、Zoom、noise core、header、
元AEX、固定workerとcontrolled parent/window workerは保持した。本番hashは
 aaa6345af78f66589200b1e7deff1d6d7afa2eeff69ee9be6afaa91d31720593。
候補63304981との差は診断用コメントを本番用へ正しただけで、公開captureに両hashを保持。

最新694条件は505 exact・105差分・84拒否。getters30は15 exact・15差分、topology252は
90 exact・78差分・84拒否、typed28は16 exact・12差分。独立384は全exactとなり、Zoom/Rotation
それぞれPF8/PF16/PF32各64条件が全bit一致。Noise Offsetの有限独立集合での全一致であり、
任意seed/thickness/noise量や負位相、全Quality/入力/geometryの証明にはしない。
残差105はZoom Inner Edge3、Zoom topology neutral/size100_noise各3、Rotation getters12、
Rotation topology neutral/size100_noise各36、Rotation typed Angle12。Size25の42×2拒否も残る。

本番適用後の2 unittest PASS。元import-free SIMD vector leaf30000引数を再実行し、実SDKの
本番Gaussian helperをO2/strict sanitizerで60000回比較、全bit一致。さらにlength1/2/3/4/7/9/
16/31/32/63/100/251/1000/2999/3000の30回で30000-entry tableの整数strideを確認。本番の
全694条件を両cmd/両build2776再生し候補のraw/error/metadataを再現。追加exact197条件は
controlled parentから自然public AEXを再取得し、raw hash、guard、session/suiteを確認した。

既存22 unittest PASS（public parameter3、typed Angle3、axis4、doublecast4、Noise Offset2、
PF8 scalar/historical2、Rotation field/inverse4）。public2452再生、Noise grid96、Offset/Angle
SDK reader352、PF8 writer2196、親/windowの24resident再取得とnative plane/inverseも維持。
古いcaptureは書き換えず、古い証拠のsource bindingはPF8 epochへ明示的に固定した。
field/inverseの歴史再現は6d0904f8から取得する本物の前sourceを使い、現在のpublic期待値は
新reportへ接続。本番全694再生と同じ旧PF8 full testだけ重複実行せず、そのscalar/history
2testを実行した。generic baseline/sanitizer/Type3/budget/SizeNoise/global-polar-ROI/common-ROI
の7gate PASS。実SDK Universal arm64/x86_64 O2 build成功。installedは変更していない。

参照の限界は保持。Unicorn RCPPSは近似ではなくFLOAT32除算、Windows CPU ISA/RCPPSの
一般証明ではない。controlled DOUBLE atan2→FLOAT32の保存Windows scalar576組を超える
native UCRTも未検証。r5900xへ既存aliasでread-only SSHを試したが5秒でtimeoutし、local
Tailscale停止を確認。接続設定は変えず、ローカルの一般処理復元・検証を続ける。

reports/radialblur_rotation_restoration_public_20261001.json、rotation_restoration_validation_20261001.json、
probe、実SDK Gaussian harness、testへ根拠を保存。次は残るRotationのno-noise/neutralとAngle、
Zoom Inner Edge/topology、Size25制限を自然fieldから分離する。Macの追加半径行、任意noiseと
負位相、一般native CPU/UCRT/両AE、UI/保存/ROI/downsample、全10本完全互換は未完。Goalはactive。

## RB-ROTATION-NEUTRAL-ALPHA-029 — feature gateと微小alphaのepsilonを除去

前回の197差分の本番復元・f5a74754のPushはprogress。本番7e72b567へ進める前に、元AEXの
自然no-noise fieldと、透明画素付近の最終samplerを比較して二つの不一致を分離した。

FACT: 元RotationはNoise/Size/Inner/Edgeがゼロでも同じpolar→prepass/scatter→normalized
処理を通る。本番genericはそれらのfeatureがある時だけtwo-stageへ入り、neutralとAngleは
DOUBLE座標と別scatterへ落ちていた。20×14 opaque、17×11 islands、20×14 right/ringの4自然
公開PF32 caseで元fieldを全量採取。元のowned radius範囲に限り、genericを常にtwo-stageへ
接続した候補は6plane計1361827語が全bit一致。Macの追加半径行をcompatibleへ昇格しない。
旧legacyから採れる本物のpolar/scalar/normalized/spanだけも別コピーでpassive採取し、
変更前の全rawを維持した。旧処理には存在しないaccum/maxを捏造して比較しない。

FACT: gateだけの候補は694条件550 exact、45追加・lost0・raw変更54。islandsの代表はfieldが
全一致でも(8,6)のRGBだけ12byte差を残した。自然native 1000 samplerはalpha
6.603953495165626e-13に対しRGB(0.45490193367004395,0.1882352977991104,0.08627450466156006)
を返し、17490 writerへ渡していた。旧Macは同alphaのRGBを0へ落としていた。共通samplerの
1e-8 cutoffが原因。元121a UCOMISS alpha,0→JE→1/alphaの分岐は有限nonzero alphaを正規化
する。Rotation two-stageの全入力でstrict_nonzero_alphaを渡し、geometry/source profileによる
適用条件を除去した。座標別補正や入力画像別の出力表は加えない。

本番はuse_generic_two_stageをuse_generic_baselineへ一般化し、final samplerのstrict条件を
use_aex_two_stageへ接続する13行の変更。source hashは
7e72b5679b15587d1e8efd092a99f7b6f2a4366159780216b2dea5d1f92299c6。
最終694条件は559 exact・51差分・84拒否、54追加exact・lost0・raw変更54。getters30は21 exact、
topology252は126 exact・42差分・84拒否、typed28と独立384は全exact。旧550候補を別reportに
保持し、gateによる45と小alphaによる追加9を区別。51差分はZoom Inner Edge3、Zoom topology
neutral/size100_noise各3、Rotation Edge/Inner Edge各3、Rotation topology Size100+Noise36。

本番の全694条件はO2/strict ASan/UBSan両cmd2776再生で候補を再現。追加exact54条件は
controlled parentから元public AEXを自然再取得してraw hash・guard・session/suiteを確認。
4自然caseの全fieldも再取得し本番で全一致、最終rawも全一致。微小alphaの1000出力と
17490のARGB128を直接watchして両全rawへ結び付け、scalar witnessだけを公開保存した。

単体のnative1000呼出しではR9を画素数と取り違えた初回テストが失敗した。元4ec3の
callsiteからR9はFLOAT32語数（width*4）と確認し、2×2では8へ修正。ソースを誤参照へ
合わせない。ゼロ/負ゼロ、1e-8/1e-12/1e-20と隣接FLOAT32、正負の有限微小値/最小normalを
含む36組は、元import-free1000と実SDKのsamplerでO2/sanitizer72回bit一致。native出力後の
16byte sentinelも保持。NaN/unordered・任意floatのsampler意味は別の未検証境界に残す。

新しい2 testを検証し、既存23 unittestと7gateもPASS。Gaussian native30000引数と本番SDK
60000回/length30回、PF8 writer2196、Offset/Angle reader352、noise grid96、過去field/inverse、
現在の追加public2452再生を維持。新全694と同じ旧restoration/PF8 full再生だけは重複させず、
Gaussian/quantizerと歴史のsource bindingを保持した。実SDK arm64/x86_64 O2 build成功、
installed不変。元AEX、固定/controlled worker、parent440sourceとSDK90入力の不変を検証。

reports/radialblur_rotation_neutral_public_20261001.json、rotation_neutral_alpha_public_20261001.json、
rotation_neutral_alpha_validation_20261001.jsonとprobe/SDK harness/testへ記録。次はRotationの
Edge/Inner EdgeとSize100+Noiseの自然scalar/fade、Zoom Inner Edge/topology、Size25制限を
追う。追加半径行、負位相/任意Noise/Quality、native Windows CPU/UCRT/両AE、通常UI/保存、
ROI/downsample、全10本完全互換は未完。Goalはactive。

## RB-ROTATION-FADE-030 — Edge/Inner Edgeの4語SIMDとscalar端数を分離

前回bed824a7の本番559 exactはprogress。残るRotation Edge/Inner EdgeのPF32自然20×14
opaque入力を元public AEXで取得し、6planeを比較した。polar/scalar/spanは旧本番と全一致。
Edgeはaccum5522/max1249/normalized3643語、Inner Edgeはaccum7236/max2327/normalized5851語が
異なった。元B680の自然呼出しは、共通Gaussian30000表2回に続きfade49/0又は0/36を生成。
RDXは長さの整数引数であり、pointer-watchのaddress値を長さ確認に利用しただけで、そこから
有効なtable bytesを読めたとは扱わない。今回公開probeはRCXの本物の生成tableだけを採る。

FACT: 元B680はlengthを4の倍数までSIMDへ渡し、1d0e0→埋込み1ebc0の指数近似を実行。
残り0–3語はDIVSSの逆数とimported expfを使用する。SIMD逆数はRCPPS後に別々のFLOAT32
2*r - (r*r)*denominatorでrefineする。controlled interpreterのRCPPS seedはFLOAT32 division。
length20/60/70などではdivisionとrefined値が1ULP異なるため、Newton演算順を省略しない。
本番は既存ZoomGaussianWeightsのscalar policyを保持し、Rotation fadeの4語prefixだけを
同じSIMD多項式へ置き換える。ZoomとRotationの共通30000表は変更しない。

本番sourceは82800c32473afbc69db4e67f2f973c527f3f76211f01104e3a88221d038584b6。
自然2caseで6plane計706160語と最終rawが全一致。native owned radius14行に比較を限定し、
Macの15行目は未解決に残す。Edge/Inner Edgeの3深度各1caseが追加exactとなり、694条件は
565 exact・45差分・84拒否、raw変更6・lost0。getters30は27 exact・3差分、typed28と独立384は
全exact。残る45差分はRotation Size100+Noise36、Zoom Inner Edge3とtopology6。

Edge UI2–100で実際に生成されるlength1–99を、元public AEXのresident typed出力と
read-only B680 traceの同じraw hashへ接続して取得。4語prefix計4800語は本番modelと全一致。
scalar150語にはlength10/index8、length19/index17、length51/index50の3語で1ULP差が残る。
元workerのhost expfと既存Mac DOUBLE exp→FLOAT32 policyの差であり、native Windows UCRT
による一般判定は未取得。差を消すためのreference変更やscalar policy変更を行わない。
元の長さ別table全量/trace/PNGはprivateに保持し、hash/countと各8語以下のscalar差だけ公開。
追加99 opaque画像の最終rawは両cmdで全一致するが、丸めや合成がtable差を隠すため、これを
scalar150語の完全互換の証明とは扱わない。

本番O2/strict ASan/UBSanの両cmdで694条件2776と追加99条件396を再生。追加exact6を元AEXから
再取得し、2自然fieldと全99 tableも再取得。実SDK fade helperはO2/sanitizerの198回でmodelを
再現。新2 test、既存25 unittestと7gateはPASS。既存のGaussian30000引数/SDK60000・length30、
PF8 writer2196、Angle/Offset reader352、noise grid96、微小alpha leaf36/SDK72、公開追加2452を
維持。過去のrestoration/PF8 full694の重複だけは省いた。epoch bindingを変更したneutral testは本番2776と4自然fieldを実際に再生しPASS。過去報告とsource bindingは保持した。
実SDK arm64/x86_64 O2 build成功、installedは変更しない。元AEX・固定/controlled worker、
parent440 sourceとSDK90入力の不変を確認。

reports/radialblur_rotation_fade_public_20261001.jsonとfade_validation、probe/SDK harness/testに
記録。次はRotation Size100+Noiseの自然field、Zoom Inner Edge/topology、Size25制限を追う。
native CPUのRCPPS/ISA、一般UCRT、任意入力・設定、両AE/UI/保存/ROI/downsample、全10本は未完。
Goalはactive。

## RB-ROTATION-SIZE-NOISE-RUN-031 — Size/Noiseの共通接続と領域runの右端規則

前回7a7f53feの本番565 exactはprogress。残るRotation Size100+Noise36条件を調べた。
IsGenericSizeNoiseWorldPairは合法として受け付けていたが、use_generic_two_stageには含まれず、
旧DOUBLE座標・legacy scatterへ落ちていた。generic_baselineとgeneric_size_noiseの両方を
元と同じtwo-stageへ接続する。parameter/profile/worldの受入範囲を追加しない。

初回の接続だけの候補は11自然画像で全6planeとrawが一致したが、20×14 opaqueではraw一致でも
source span280語とpolar scalar19326語に差が残った。これを「全field一致」とは扱わず、採取を
追加した。beforeから比較するのは実際にlegacyが使うpolar/normalized/spanの3planeだけ。
legacyには存在しないaccum/maxや使われない初期化scalarをworkerと見なさない。

FACT: 元PF32 ownerの6aa0入口は最大領域面積293、area map全280画素293、size factor全画素
0.9999999403953552を持っていた。旧Macの4-neighbor BFSは面積280、FLOAT32逆数×280で
1.0000001192092896となり、Noise混合へ伝わった。元8930の8ad4はxを増やした後、x==widthを
検査する前にmaskの線形次画素を読む。そこが非zeroならrunのinclusive endpointがwidthまで
伸び、2d30のend-start+1により1個多く数える。20×14全面opaqueは280+13=293になる。
3010の前後行run接続は区間重複であり、行末と次行先頭を水平連結する規則ではない。

FACT: 8dd0はinclusive endpointまでarea値を書き、次行x==0も対象になる。componentは最初の
run順に書くので、後に現れたcomponentが勝つ。Macはvisibleセルの4-neighbor labelを保持し、
行境界で双方のmaskが非zeroなら前行runの面積を1増やす。maximumとcomponent_areasを再計算し、
factor materialization時に次行先頭へ書かれる後のlabelを選ぶ。面積/factorの画像別補正は使わない。
size percent→FLOAT32 0.01、1/max→FLOAT32、area×inverse→×size→+(1-size)の演算順は保持。

自然ownerのmask/area/factorをreadonlyで採取し、14 mask×Size25/100の28条件を検証。
全面、空、1列/1行、左右列、別run、内部merge、穴、交互run、別componentへの上書きを含む。
測定したmaskの末尾guardは全て0。20×14の293、7×5全面39、1×5の9だけでなく、左右別領域の
[5,8]と、先頭セルが上書きされるarea mapもmodel全語一致。実SDKの本物のhelperを3深度・
O2/strict sanitizerの168回で呼び、全factor bytesとsorted component areaを再現した。
任意native allocatorの末尾内容や非有限alphaは、この測定から保証しない。

本番sourceは7e136a1bc3b2c7db22d072ee735e24909d53170cf2f1decef9a51c98d0b072d9。
12自然画像は6plane計3934002語と最終rawが全一致。比較はnative owned radiusだけで行い、
Macの追加行は未解決に残す。694条件は601 exact・9差分・84拒否、追加exact36・raw変更36・lost0。
getters30は27 exact、topology252は162 exact・6差分・84拒否、typed28と独立384は全exact。
残る9はZoom Inner Edge3（20×14 opaqueの3深度）と、PF8 topologyのneutral/size100_noise各3（17×11 islands/diagonal、20×14 diagonal）。

独立23×13/19×17、islands/ring/diagonal/opaque、Noise25/100とType1/2、3深度の96条件を
元public AEX resident typedと本番Classic/Smartへ接続し全exact。旧本番は96全て不一致だった。
接続だけの旧候補96報告はprivateに保持し、最終sourceで96を改めて取得して混同しない。
新36と独立96を元AEXから再取得し、本番O2/strict ASan/UBSanの両cmdで3160再生。
12自然fieldと28 native source mapを再取得、SDK168回も再現。新3 testはPASS。
既存26 unittestと7gateを検証し、変更したfade epoch testも旧565報告のsource bindingと
現行601報告の実出力を分け、3172 public・2自然field・99 table/SDK198回を実際に再生した。
Gaussian/quantizer/Angle/Offset/noise gridと微小alphaを維持。実SDK arm64/x86_64 O2 build成功。
元AEX・固定/controlled worker・parent440 source・SDK90入力の不変を確認。installedは変更しない。

rotation_size_noise_public/independent、size_run_boundaryとsize_noise_validationの報告、probe、
SDK harness、testへ記録。次はZoomの9差分とSize25の84拒否を元の自然field/area mapから追う。
scalar fade3語、Windows RCPPS/ISA/一般UCRT、追加半径行、native両AE/UI/保存/ROI/downsampleと
全10本完全互換は未完。Goalはactive。

## RB-ZOOM-NONZERO-ALPHA-032 — Zoom samplerの正負alphaとゼロ加算

前回75039904の36差分解消とPushはprogress。本番601 exactに残るPF8 Zoom topology6条件を
元AEXの9d80 samplerと17400 writerの自然呼出しから調べた。17×11 islands/diagonal、
20×14 diagonalのneutral/Size100+Noiseが対象で、画像や座標ごとの出力補正は使わない。

FACT: 元9d80はRGBA出力16 bytesをゼロ初期化し、row-major 00,10,01,11の順でalphaと
premultiplied RGBをFLOAT32加算する。9f70 UCOMISS alpha,0と9f73 JEは、有限alphaが
ゼロのときだけ1/alphaによる正規化を省く。正の微小値だけでなく負のalphaも正規化する。
RCX source、RDX output、R8 radius width、R9 angular height、stack5はFLOAT32語単位の
row stride、stack6/7はFLOAT32 radius/angular座標。Rotation1000のABI/加算順と混同しない。

FACT: 旧PF8 Zoom traitはstrict_nonzero_alpha=falseで、共通helperのalpha>1e-8判定へ
接続していた。自然samplerには約1.2e-10、6.6e-13の正値だけでなく、約-0.0143、-0.0427の
負値も存在し、旧処理はRGB蓄積と正規化の両方を省略した。最初のprobeは旧/候補accumの
一致を誤って要求したので失敗した。旧accumは未計算のゼロであることを確認し、入力座標・
周辺cell値が不変であることと、候補sampler全16 bytes/元writer4 bytesの直接一致へ改めた。
正の微小alphaだけに限定した次のassertも負alphaの証拠で失敗し、有限nonzeroの元分岐へ訂正。
参照やworkerを変更して結果を合わせていない。

traitをtrueにするだけの最初の候補は694条件607 exactだったが、追加のimport-free leafで
alpha=-0の出力を元が+0、Macが-0とする差を得た。元のゼロseed加算をalphaとRGBへ復元する。
さらに正負alphaのtapが相殺してalpha=0になるとき、元は蓄積RGBを保持して除算だけを省く。
strict row-major経路ではRGBを計算し、alpha=0なら正規化倍率1として保持する。Rotationの
column-major経路と旧threshold経路の受入条件は保持。NaN/unorderedとdenormal controlは未証明。

最終sourceは507f2b98788e977d26a688723dca620b4f591d7e6071337318f6059bfec583e4。
元9d80のimport-free呼出しで±zero/±1/±min-normal、1e-8/1e-12/1e-20/2^-24/2^-46の
隣接FLOAT32・正負36境界を検証。相殺の正負方向、signed-zero RGBとalpha、非一様signed tapを
加えた44条件でoutput tail guardを保持。実SDKのPF8 traitを使うharnessのO2/strict sanitizer
88回で元の全RGBA bit列と一致した。専用Zoom ABIであり、Rotation leafの証拠を流用しない。

最終候補の自然6条件はreadonly worker traceの最終rawがresident typed取得と同hash、guardと
suite/session正常。11採取点で入力tap/座標は不変、元sampler/候補16 bytesと元writer/候補4 bytes
が一致。694条件は607 exact・3差分・84拒否、新exact6・raw変更6・lost0。本番候補2776再生と
既存の独立96条件384再生がO2/strict ASan/UBSanのClassic/Smartで一致。設定・geometry・
parameter・error/metadata契約を保持し、Size25制限をこの変更で解除していない。

本番2 testはPASS。694＋独立96の3160再生、自然6条件とimport-free native44/SDK88回を
現行sourceで再取得した。既存24 unittestと7 gateもPASS。変更したSize/Noise履歴の3 testは
旧601 sourceのbindingと現行607実出力を分け、3160再生、新36＋独立96の元AEX再取得、
12自然field3934002語、28 run mapとSDK168回を再確認してPASS。Gaussian/PF8 writer/Angle/
Offset/noise grid/Rotation samplerを維持。実SDK arm64/x86_64 O2 build成功。元AEX、固定と
controlled worker、parent440 source、SDK90入力の不変を確認。installedは変更していない。

今回のpublic/leaf report、実SDK harness、probeとtestへ記録。過去Size/Noise601報告の
source bindingを履歴として保持し、testの現行期待値をcurrent607報告へ接続する。
次はZoom Inner Edge3条件とSize25の84拒否を自然fieldとarea mapから追う。
scalar fade3語、Windows RCPPS/ISA/一般UCRT、追加半径行、任意入力・設定、native AE/UI/保存/
ROI/downsampleと全10本完全互換は未完。Goalはactive。

## 次の順序

1. Smoother2のHDR/Gamma合成と色境界の今回の有限集合は検証済み。公開builderのLUT構築とnative依存先を分け、未測定scan長・任意float・独立paletteの最初の差を復元する。
2. ColorKeyの未検証geometry/任意float/paletteとThin/Blur合成を拡張する。今回の境界・overflow比較を全入力の証明とは扱わず、固定workerとcontrolled Lab94参照を分け、native Windows UCRTとの比較を残す。
3. native host/ROI/downsample・通常UI/保存stateと各深度のworld契約を拡張検証。
4. DirectionalBlurの独立216条件は公開比較済み。RadialBlurはAngle/Edge/PointとNoise OffsetのFLOAT32接続を復元した。参照atan2f非軸差は保存Windows scalarの有限集合へ校正済み。Zoom PF8の共通writerは復元済み。Rotationの自然field/scatterは代表全量でGaussian差を分離し、別コピーのinverse復元で代表rawが一致した。generic two-stageのGaussian/finalを本番へ復元し、694条件505 exact、独立384全exactを確認。no-noise/neutral/Angleと微小alphaも本番へ復元し、559 exact、typed28と独立384全exactを確認。Rotation Edge/Inner Edgeも本番へ復元し、565 exact・45差分・84拒否。Size100+Noiseも共通経路と行境界area規則を復元し、本番601 exact・9差分・84拒否。独立96も全exact。Zoomの正負alphaとゼロseed加算も復元し、本番607 exact・3差分・84拒否。次はZoom Inner Edge3とSize25制限を自然fieldから閉じる。scalar fade3語、native RCPPS/ISA/UCRTを未解決に保持。負位相のnative契約・Size25の面積制限・端/穴/島へ進み、その後KiraKira一般入力を比較する。

既存の作業ツリー変更は今回のcommitに混ぜない。第三者AEXとnative raw出力をPushしない。
