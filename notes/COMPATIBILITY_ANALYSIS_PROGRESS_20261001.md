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

## 次の順序

1. ColorKeyの他Blur設定を公開ownerで再検証し、旧import stub依存の分岐を復元。
2. 全color/threshold、HDRとnative host/ROI/downsampleを拡張検証。
3. Smoother2の現行sourceによる114ケース再生と、未到達65分類の到達性調査。

既存の作業ツリー変更は今回のcommitに混ぜない。第三者AEXとnative raw出力をPushしない。
