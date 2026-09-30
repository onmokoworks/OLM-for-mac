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

## BASELINE-001: 検証証拠の環境差

Thin修正後のgeneric gateも52 PASS/1 FAIL/0 SKIP（既存baselineと同じ）。性能レポートの実行prefixはPython 3.14.6をbindし、
現行実行は3.14.7。verifierがbindingを拒否した。記録を現在のhashへ書き換えるだけで
過去性能の実行時証拠にしない。必要な性能再測定を別項目として残す。

## 次の順序

1. CK-COMPOSITION-001のThin中間値・型依存処理の復元。
2. public Classic/Smartと別source/geometryで修正を検証。
3. Smoother2の現行sourceによる114ケース再生と、未到達65分類の到達性調査。

既存の作業ツリー変更は今回のcommitに混ぜない。第三者AEXとnative raw出力をPushしない。
